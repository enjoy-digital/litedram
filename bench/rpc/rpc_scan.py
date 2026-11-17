#!/usr/bin/env python3
# Host-driven RPC DRAM bring-up over UARTBone: init sequence, UTR read, alignment scans.
import sys, time, argparse
from litex import RemoteClient

CS, WE, CAS, RAS, WRDATA, RDDATA = 0x01, 0x02, 0x04, 0x08, 0x10, 0x20
SEL, CKE, ODT, RESET_N = 0x01, 0x02, 0x04, 0x08

class RPC:
    def __init__(self, bus):
        self.bus = bus
        self.r   = bus.regs
    def cmd(self, phase, cmd, address=0, bank=0):
        getattr(self.r, f"sdram_dfii_pi{phase}_address").write(address)
        getattr(self.r, f"sdram_dfii_pi{phase}_baddress").write(bank)
        getattr(self.r, f"sdram_dfii_pi{phase}_command").write(cmd)
        getattr(self.r, f"sdram_dfii_pi{phase}_command_issue").write(1)
    def control(self, v):
        self.r.sdram_dfii_control.write(v)
    def init(self):
        self.r.ddrphy_reset_fsm.write(1)
        self.control(ODT|RESET_N);                         time.sleep(0.001)
        self.cmd(0, CS)                                    # Hold CS# low.
        self.control(ODT)                                  # Special commands: ON.
        self.cmd(0, RAS|CS);                               time.sleep(0.001) # PU RESET.
        self.control(ODT|RESET_N)
        self.cmd(0, RAS|WE|CS, address=0x400)              # Precharge all.
        self.cmd(0, RAS|CAS|WE|CS, address=0x240, bank=1)  # MRS: CL=8.
        self.control(ODT)
        self.cmd(0, WE|CS, address=0x400);                 time.sleep(0.001) # ZQ init.
        self.control(ODT|RESET_N)
        return self.r.ddrphy_reset_done.read(), self.r.ddrphy_init_done.read()
    def utr(self, en, op=0):
        self.control(ODT)
        self.cmd(0, RAS|CAS|WE|CS, address=(en & 1) | ((op & 3) << 1))
        self.control(ODT|RESET_N)
    def read(self, address=0, bank=0):
        self.r.ddrphy_burstdet_clr.write(1)
        self.cmd(3, CAS|CS|RDDATA, address=address, bank=bank)
        data = 0
        for p in range(4):
            data |= getattr(self.r, f"sdram_dfii_pi{p}_rddata").read() << (64*p)
        return self.r.ddrphy_burstdet_seen.read(), data
    def rdly(self, n):
        self.r.ddrphy_dly_sel.write(0b11)
        self.r.ddrphy_rdly_dq_rst.write(1)
        for _ in range(n):
            self.r.ddrphy_rdly_dq_inc.write(1)
        self.r.ddrphy_dly_sel.write(0)
    def shifts(self, stb=None, dqs=None, db=None, rd_en=None, rd_ph=None):
        if stb   is not None: self.r.ddrphy_stb_shift.write(stb)
        if dqs   is not None: self.r.ddrphy_dqs_shift.write(dqs)
        if db    is not None: self.r.ddrphy_db_shift.write(db)
        if rd_en is not None: self.r.ddrphy_rd_en_sel.write(rd_en)
        if rd_ph is not None: self.r.ddrphy_rd_en_phase.write(rd_ph)

def words(data):
    return " ".join("%04x" % ((data >> (16*n)) & 0xffff) for n in range(16))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csr-csv", default="csr.csv")
    parser.add_argument("--port",    default=1234, type=int)
    parser.add_argument("test", choices=["ident", "idle", "utr-scan", "utr", "utr-scan2", "utr-scan3"])
    parser.add_argument("--stb", default=4, type=int)
    parser.add_argument("--dqs", default=4, type=int)
    parser.add_argument("--db",  default=1, type=int)
    parser.add_argument("--rd-en", default=4, type=int)
    parser.add_argument("--rd-ph", default=0, type=int)
    parser.add_argument("--rdly",  default=5, type=int)
    args = parser.parse_args()
    bus = RemoteClient(csr_csv=args.csr_csv, port=args.port)
    bus.open()
    rpc = RPC(bus)
    if args.test == "ident":
        s = ""
        for i in range(64):
            c = bus.read(bus.bases.identifier_mem + 4*i) & 0xff
            if c == 0: break
            s += chr(c)
        print("ident:", s)
    if args.test == "idle":
        # Burst detection without any read command (floating DQS?).
        rpc.shifts(stb=args.stb, dqs=args.dqs, db=args.db)
        print("init:", rpc.init())
        for rd_en in range(12):
            rpc.shifts(rd_en=rd_en)
            rpc.r.ddrphy_burstdet_clr.write(1)
            # rddata_en without a command.
            rpc.cmd(3, RDDATA)
            print(f"rd_en {rd_en:2d}: burstdet {rpc.r.ddrphy_burstdet_seen.read():02b}")
    if args.test == "utr":
        rpc.shifts(stb=args.stb, dqs=args.dqs, db=args.db, rd_en=args.rd_en, rd_ph=args.rd_ph)
        rpc.rdly(args.rdly)
        print("init:", rpc.init())
        for op in range(4):
            rpc.utr(1, op)
            for _ in range(2):
                seen, data = rpc.read()
                print(f"op {op}: burstdet {seen:02b} data {words(data)}")
            rpc.utr(0, op)
    if args.test == "utr-scan":
        t0 = time.time()
        for db in range(16):
            for dqs in range(16):
                rpc.shifts(stb=args.stb, dqs=dqs, db=db)
                rpc.init()
                rpc.utr(1, 0)
                res = []
                for rd_en in range(2, 10):
                    rpc.shifts(rd_en=rd_en)
                    seen, data = rpc.read()
                    res.append((seen, data))
                rpc.utr(0, 0)
                hits = "".join(str(s) for s, d in res)
                nz   = [(i + 2, words(d)[:39]) for i, (s, d) in enumerate(res) if d != 0]
                if any(s for s, d in res) or nz:
                    print(f"db {db:2d} dqs {dqs:2d} burstdet(rd_en 2..9) {hits} data {nz[:2]}", flush=True)
        print("scan done in %.1fs" % (time.time() - t0))
    if args.test == "utr-scan2":
        t0 = time.time()
        for stb in range(0, 10):
            for db in range(0, 13):
                for dqs in [db + 2, db + 3]:
                    rpc.shifts(stb=stb, dqs=dqs, db=db)
                    rpc.init()
                    rpc.utr(1, 0)
                    res = []
                    for rd_en in [3, 5, 7]:
                        rpc.shifts(rd_en=rd_en)
                        seen, data = rpc.read()
                        res.append((seen, data))
                    rpc.utr(0, 0)
                    ws = set()
                    for s_, d in res:
                        ws |= set((d >> (16*n)) & 0xffff for n in range(16))
                    ws -= {0, 7}
                    if any(s_ for s_, d in res) or ws:
                        print(f"stb {stb:2d} db {db:2d} dqs {dqs:2d} burstdet {[s_ for s_, d in res]} {words(res[1][1])}", flush=True)
        print("scan done in %.1fs" % (time.time() - t0))
    if args.test == "utr-scan3":
        t0 = time.time()
        for stb in range(0, 16):
            for db in range(0, 13):
                for dqs in [db + 2, db + 3]:
                    rpc.shifts(stb=stb, dqs=dqs, db=db, rd_en=args.rd_en)
                    rpc.init()
                    res = []
                    for op in range(4):
                        rpc.utr(1, op)
                        rpc.read()
                        seen, data = rpc.read()
                        res.append(data)
                        rpc.utr(0, op)
                    if len(set(res)) >= 3:
                        print(f"stb {stb:2d} db {db:2d} dqs {dqs:2d}", flush=True)
                        for op in range(4):
                            print(f"   op {op}: {words(res[op])}", flush=True)
        print("scan done in %.1fs" % (time.time() - t0))
    bus.close()

if __name__ == "__main__":
    main()
