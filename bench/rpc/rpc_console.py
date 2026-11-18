#!/usr/bin/env python3
# RPC DRAM bring-up through the BIOS console (mem_write/mem_read on the CSRs): no bridge needed.
#
# ./rpc_console.py --csr-csv csr.csv utr               Utility Register reads (4 patterns).
# ./rpc_console.py --csr-csv csr.csv ops               Activate/write/read/precharge/refresh.
# ./rpc_console.py --csr-csv csr.csv wrscan            STB/DQS/DB write shifts scan (UTR reads).
# ./rpc_console.py --csr-csv csr.csv rdscan            DQSBUF READ position scan (UTR reads).
# ./rpc_console.py --csr-csv csr.csv wrmap             STB/DQS/DB write shifts map (WORD write/read).
# ./rpc_console.py --csr-csv csr.csv wlvlmap           Write leveling delay map (WORD write/read).
# ./rpc_console.py --csr-csv csr.csv wdlymap           Write delay (DB against DQS) map (WORD write/read).
# ./rpc_console.py --csr-csv csr.csv stbmap            STB/CS# shift and output delay map (WORD write/read).
# ./rpc_console.py --csr-csv csr.csv rdmap             DQSBUF READ position/read clock selection map (WORD read).
#
# The SDRAM is left under software control during the tests and given back to the controller at
# the end: run sdram_init from the BIOS afterwards.

import re
import sys
import time
import argparse

import serial

CS, WE, CAS, RAS, WRDATA, RDDATA = 0x01, 0x02, 0x04, 0x08, 0x10, 0x20
SEL, CKE, ODT, RESET_N           = 0x01, 0x02, 0x04, 0x08

ANSI = re.compile(r"\x1b\[[0-9;]*m")
DUMP = re.compile(r"0x[0-9a-f]{8}  ((?:[0-9a-f]{2} )+)")

UTR_PATTERNS = {
    0: "0000 ffff 0000 ffff",
    1: "ffff ffff 0000 0000",
    2: "0000 0000 ffff ffff",
    3: "ffff 0000 ffff 0000",
}

class Console:
    def __init__(self, port, baudrate, csr_csv):
        self.serial = serial.Serial(port, baudrate, timeout=0.01)
        self.csrs   = {}
        for line in open(csr_csv):
            fields = line.strip().split(",")
            if fields[0] == "csr_register":
                self.csrs[fields[1]] = (int(fields[2], 16), int(fields[3]))
        self.run("", timeout=2)

    def run(self, command, timeout=5):
        self.serial.write((command + "\n").encode())
        out   = ""
        start = time.time()
        while time.time() - start < timeout:
            data = self.serial.read(256)
            if not data:
                continue
            out += data.decode(errors="replace")
            if ANSI.sub("", out).endswith("litex> "):
                break
        return ANSI.sub("", out).replace("\r", "")

    def dump(self, address, length):
        data = []
        for line in self.run(f"mem_read 0x{address:08x} {length}").split("\n"):
            m = DUMP.match(line)
            if m:
                data += [int(x, 16) for x in m.group(1).split()]
        return data

    def write(self, name, value):
        self.run(f"mem_write 0x{self.csrs[name][0]:08x} 0x{value:x}")

    def read(self, name):
        address, n = self.csrs[name]
        data  = self.dump(address, 4*n)
        value = 0
        for k in range(n): # CSR big ordering: the first word is the most significant.
            value = (value << 32) | int.from_bytes(bytes(data[4*k:4*k + 4]), "little")
        return value

class RPC:
    def __init__(self, console):
        self.con = console

    def cmd(self, phase, cmd, address=0, bank=0):
        self.con.write(f"sdram_dfii_pi{phase}_address",       address)
        self.con.write(f"sdram_dfii_pi{phase}_baddress",      bank)
        self.con.write(f"sdram_dfii_pi{phase}_command",       cmd)
        self.con.write(f"sdram_dfii_pi{phase}_command_issue", 1)

    def control(self, value):
        self.con.write("sdram_dfii_control", value)

    def init(self):
        self.con.write("ddrphy_reset_fsm", 1)
        self.control(ODT|RESET_N)
        self.cmd(0, CS)                               # Hold CS# low.
        self.control(ODT)                             # Special commands: ON.
        self.cmd(0, RAS|CS); time.sleep(0.01)         # Power-up reset.
        self.control(ODT|RESET_N)
        self.cmd(0, RAS|WE|CS, 0x400)                 # Precharge all.
        self.cmd(0, RAS|CAS|WE|CS, 0x240, 1)          # MRS: CL=8.
        self.control(ODT)
        self.cmd(0, WE|CS, 0x400); time.sleep(0.01)   # ZQ init.
        self.control(ODT|RESET_N)

    def utr(self, enable, op=0):
        self.control(ODT)
        self.cmd(0, RAS|CAS|WE|CS, (enable & 1) | ((op & 3) << 1))
        self.control(ODT|RESET_N)

    def wrdata(self, words):
        for p in range(4):
            value = 0
            for k in range(4):
                value |= words[4*p + k] << (16*k)
            address = self.con.csrs[f"sdram_dfii_pi{p}_wrdata"][0]
            self.con.run(f"mem_write 0x{address:08x} 0x{value >> 32:08x}")
            self.con.run(f"mem_write 0x{address + 4:08x} 0x{value & 0xffffffff:08x}")

    def read(self, address=0, bank=0):
        self.con.write("ddrphy_burstdet_clr", 1) # Also clears the captured burst.
        self.cmd(3, CAS|CS|RDDATA, address, bank)
        base = self.con.csrs["sdram_dfii_pi0_rddata"][0]
        last = self.con.csrs["sdram_dfii_pi3_rddata"][0]
        data = self.con.dump(base, last + 8 - base)
        ws   = []
        for p in range(4):
            offset = self.con.csrs[f"sdram_dfii_pi{p}_rddata"][0] - base
            value  = (int.from_bytes(bytes(data[offset:offset + 4]), "little") << 32) | \
                      int.from_bytes(bytes(data[offset + 4:offset + 8]), "little")
            ws += [(value >> (16*k)) & 0xffff for k in range(4)]
        return " ".join(f"{w:04x}" for w in ws)

    def rdly(self, n):
        self.con.write("ddrphy_dly_sel", 0b11)
        self.con.write("ddrphy_rdly_dq_rst", 1)
        for _ in range(n):
            self.con.write("ddrphy_rdly_dq_inc", 1)
        self.con.write("ddrphy_dly_sel", 0)

    def rdpos(self, tck, rdly):
        # READ position: tCK (sys_clk cycles, then tCK) and read clock selection.
        self.con.write("ddrphy_rd_en_sel",   tck//4)
        self.con.write("ddrphy_rd_en_phase", tck % 4)
        self.con.write("ddrphy_dly_sel", 0b11)
        self.con.write("ddrphy_rdly_dq_bitslip_rst", 1) # Position of the read leveling: 0.
        self.con.write("ddrphy_dly_sel", 0)
        self.rdly(rdly)

def main():
    parser = argparse.ArgumentParser(description="RPC DRAM bring-up through the BIOS console.")
    parser.add_argument("test", choices=["utr", "ops", "wrscan", "rdscan", "rdmap", "wrmap", "wlvlmap", "wdlymap", "stbmap"])
    parser.add_argument("--csr-csv",  default="csr.csv")
    parser.add_argument("--port",     default="/dev/ttyUSB1")
    parser.add_argument("--baudrate", default=115200, type=int)
    parser.add_argument("--rdly",     default=5,  type=int, help="DQSBUF read clock selection.")
    parser.add_argument("--tck",      default=19, type=int, help="DQSBUF READ position (tCK).")
    parser.add_argument("--stb-delay", default=14, type=int, help="Static STB/CS# delay of the build (stbmap).")
    parser.add_argument("--wlvl-max", default=320, type=int, help="Last delay of wlvlmap/wdlymap.")
    parser.add_argument("--wlvl-step", default=8, type=int, help="Delay step of wlvlmap/wdlymap.")
    args = parser.parse_args()

    con = Console(args.port, args.baudrate, args.csr_csv)
    rpc = RPC(con)
    settings = {name: con.read(name) for name in [
        "ddrphy_stb_shift", "ddrphy_dqs_shift", "ddrphy_db_shift", "ddrphy_rd_en_sel", "ddrphy_rd_en_phase"]}
    # The read leveling of the BIOS is lost (read clock selection, READ position): run sdram_init after.
    rpc.control(ODT|RESET_N) # Software control.

    if args.test == "utr":
        rpc.rdpos(args.tck, args.rdly)
        for op in range(4):
            # On the board, only the first UTR enable after an initialization returns data (not
            # investigated): initialize before each pattern.
            rpc.init()
            rpc.utr(1, op)
            data = rpc.read()
            rpc.utr(0, op)
            ok = data == " ".join([UTR_PATTERNS[op]]*4)
            print(f"op {op}: {data} {'OK' if ok else 'KO'}")

    if args.test == "ops":
        def check(tag, expected, address, bank):
            data = rpc.read(address, bank)
            ok   = data == " ".join(f"{expected + k:04x}" for k in range(16))
            print(f"{tag:28s}: {data} {'OK' if ok else 'KO'}", flush=True)
        rpc.init(); rpc.rdpos(args.tck, args.rdly)
        rpc.cmd(0, RAS|CS, 0x123, 1)                                  # Activate bank 1.
        rpc.wrdata([0x1000 + k for k in range(16)]); rpc.cmd(3, CAS|WE|CS|WRDATA, 0x20, 1)
        check("write/read", 0x1000, 0x20, 1)
        rpc.wrdata([0x2000 + k for k in range(16)]); rpc.cmd(3, CAS|WE|CS|WRDATA, 0x40, 1)
        check("other column", 0x2000, 0x40, 1)
        check("first column", 0x1000, 0x20, 1)
        rpc.cmd(2, RAS|CS, 0x055, 2)                                  # Activate bank 2 (phase 2).
        rpc.wrdata([0x3000 + k for k in range(16)]); rpc.cmd(3, CAS|WE|CS|WRDATA, 0x00, 2)
        check("other bank", 0x3000, 0x00, 2)
        rpc.cmd(0, RAS|WE|CS, 0x400); rpc.cmd(0, RAS|CS, 0x123, 1)    # Precharge all, activate.
        check("after precharge", 0x1000, 0x20, 1)
        rpc.cmd(0, RAS|WE|CS, 0x400); rpc.cmd(0, RAS|CAS|CS, 0x400)   # Precharge all, refresh.
        time.sleep(0.01)
        rpc.cmd(0, RAS|CS, 0x123, 1); check("after refresh", 0x1000, 0x20, 1)
        rpc.cmd(0, RAS|CS, 0x055, 2); check("after refresh, other bank", 0x3000, 0x00, 2)

    if args.test == "wrscan":
        # The READ position follows the command (STB). The DRAM answers when a pattern is read.
        expected = UTR_PATTERNS[1]
        for stb in range(16):
            for dqs in [stb + d for d in (0, -1, 1, -2, 2)]:
                for db in [dqs + d for d in (-3, -2, -4)]:
                    if not (0 <= dqs < 16 and 0 <= db < 16):
                        continue
                    con.write("ddrphy_stb_shift", stb)
                    con.write("ddrphy_dqs_shift", dqs)
                    con.write("ddrphy_db_shift",  db)
                    rpc.init(); rpc.utr(1, 1)
                    hits = []
                    for dt in (-1, 0, 1):
                        rpc.rdpos(args.tck + (stb - settings["ddrphy_stb_shift"])//2 + dt, args.rdly)
                        data = rpc.read()
                        if expected in data:
                            hits.append((dt, data))
                    rpc.utr(0, 1)
                    if hits:
                        print(f"stb {stb:2d} dqs {dqs:2d} db {db:2d}: {hits}", flush=True)

    if args.test == "rdmap":
        # Write a WORD, then read it for each READ position/read clock selection:
        # O: correct, +/-: one word late/early, digit: number of wrong words (9: 9 or more).
        words = [0x1000 + 0x0111*k for k in range(16)]
        rpc.init(); rpc.rdpos(args.tck, args.rdly)
        rpc.cmd(0, RAS|CS, 0x123, 1)
        rpc.wrdata(words); rpc.cmd(3, CAS|WE|CS|WRDATA, 0x20, 1)
        print("          rdly 0123456789abcdef")
        for tck in range(args.tck - 2, args.tck + 4):
            line = ""
            for rdly in range(16):
                rpc.rdpos(tck, rdly)
                data = [int(w, 16) for w in rpc.read(0x20, 1).split()]
                if data == words:
                    line += "O"
                elif data[1:] == words[:-1]:
                    line += "+"
                elif data[:-1] == words[1:]:
                    line += "-"
                else:
                    line += str(min(9, sum(a != b for a, b in zip(data, words))))
            print(f"READ {tck:2d} tCK: {line}", flush=True)

    if args.test == "wrmap":
        # Write a WORD and read it back for each STB/DQS/DB write shift around the current ones
        # (the READ position has to be right: see rdscan/rdmap).
        # O: correct, +/-: one word late/early, digit: number of wrong words (9: 9 or more).
        words = [0x1000 + 0x0111*k for k in range(16)]
        for stb in range(settings["ddrphy_stb_shift"] - 2, settings["ddrphy_stb_shift"] + 3):
            for dqs in range(settings["ddrphy_dqs_shift"] - 2, settings["ddrphy_dqs_shift"] + 3):
                line = ""
                for db in range(max(0, dqs - 7), dqs + 1):
                    con.write("ddrphy_stb_shift", stb)
                    con.write("ddrphy_dqs_shift", dqs)
                    con.write("ddrphy_db_shift",  db)
                    rpc.init(); rpc.rdpos(args.tck, args.rdly)
                    rpc.cmd(0, RAS|CS, 0x123, 1)
                    rpc.wrdata([0]*16);  rpc.cmd(3, CAS|WE|CS|WRDATA, 0x20, 1)
                    rpc.wrdata(words);   rpc.cmd(3, CAS|WE|CS|WRDATA, 0x20, 1)
                    data = [int(w, 16) for w in rpc.read(0x20, 1).split()]
                    if data == words:
                        line += "O"
                    elif data[1:] == words[:-1]:
                        line += "+"
                    elif data[:-1] == words[1:]:
                        line += "-"
                    else:
                        line += str(min(9, sum(a != b for a, b in zip(data, words))))
                print(f"stb {stb:2d} dqs {dqs:2d} db {max(0, dqs - 7)}..{dqs}: {line}", flush=True)

    if args.test == "wlvlmap":
        # Write a WORD and read it back for each write leveling delay (DQS/DB against CLK), with
        # DQS/DB one UI earlier, as set, one UI later.
        # O: correct, +/-: one word late/early, digit: number of wrong words (9: 9 or more).
        words = [0x1000 + 0x0111*k for k in range(16)]
        step  = args.wlvl_step
        for d in (-1, 0, 1):
            dqs, db = settings["ddrphy_dqs_shift"] + d, settings["ddrphy_db_shift"] + d
            if db < 0:
                continue
            con.write("ddrphy_dqs_shift", dqs)
            con.write("ddrphy_db_shift",  db)
            con.write("ddrphy_dly_sel", 0b11); con.write("ddrphy_wlvl_rst", 1); con.write("ddrphy_dly_sel", 0)
            line = ""
            for n in range(args.wlvl_max//step + 1):
                rpc.init(); rpc.rdpos(args.tck, args.rdly)
                rpc.cmd(0, RAS|CS, 0x123, 1)
                rpc.wrdata([0]*16);  rpc.cmd(3, CAS|WE|CS|WRDATA, 0x20, 1)
                rpc.wrdata(words);   rpc.cmd(3, CAS|WE|CS|WRDATA, 0x20, 1)
                data = [int(w, 16) for w in rpc.read(0x20, 1).split()]
                if data == words:
                    line += "O"
                elif data[1:] == words[:-1]:
                    line += "+"
                elif data[:-1] == words[1:]:
                    line += "-"
                else:
                    line += str(min(9, sum(a != b for a, b in zip(data, words))))
                con.write("ddrphy_dly_sel", 0b11)
                for _ in range(step):
                    con.write("ddrphy_wlvl_inc", 1)
                con.write("ddrphy_dly_sel", 0)
            print(f"dqs {dqs:2d} db {db:2d} wlvl 0..{args.wlvl_max} (step {step}): {line}", flush=True)
        con.write("ddrphy_dly_sel", 0b11); con.write("ddrphy_wlvl_rst", 1); con.write("ddrphy_dly_sel", 0)

    if args.test == "wdlymap":
        # Write a WORD and read it back for each write delay (DB against DQS), increased then
        # decreased from the default (90 degrees).
        # O: correct, +/-: one word late/early, digit: number of wrong words (9: 9 or more).
        words = [0x1000 + 0x0111*k for k in range(16)]
        def wdly(csr):
            con.write("ddrphy_dly_sel", 0b11); con.write(csr, 1); con.write("ddrphy_dly_sel", 0)
        for direction in (0, 1):
            con.write("ddrphy_wdly_dir", direction)
            wdly("ddrphy_wdly_rst")
            line = ""
            for n in range(args.wlvl_max//args.wlvl_step + 1):
                rpc.init(); rpc.rdpos(args.tck, args.rdly)
                rpc.cmd(0, RAS|CS, 0x123, 1)
                rpc.wrdata([0]*16);  rpc.cmd(3, CAS|WE|CS|WRDATA, 0x20, 1)
                rpc.wrdata(words);   rpc.cmd(3, CAS|WE|CS|WRDATA, 0x20, 1)
                data = [int(w, 16) for w in rpc.read(0x20, 1).split()]
                if data == words:
                    line += "O"
                elif data[1:] == words[:-1]:
                    line += "+"
                elif data[:-1] == words[1:]:
                    line += "-"
                else:
                    line += str(min(9, sum(a != b for a, b in zip(data, words))))
                con.write("ddrphy_dly_sel", 0b11)
                for _ in range(args.wlvl_step):
                    con.write("ddrphy_wdly_move", 1)
                con.write("ddrphy_dly_sel", 0)
            print(f"wdly {'-' if direction else '+'}0..{args.wlvl_max} (step {args.wlvl_step}): {line}", flush=True)
        con.write("ddrphy_wdly_dir", 0)
        wdly("ddrphy_wdly_rst")

    if args.test == "rdscan":
        for tck in range(args.tck - 3, args.tck + 4):
            for rdly in range(0, 16, 2):
                rpc.rdpos(tck, rdly)
                res = []
                for op in (1, 0):
                    rpc.init(); rpc.utr(1, op); res.append(rpc.read()); rpc.utr(0, op)
                ok = (res[0] == " ".join([UTR_PATTERNS[1]]*4)) and (res[1] == " ".join([UTR_PATTERNS[0]]*4))
                print(f"sel {tck//4} phase {tck % 4} rdly {rdly:2d}: {'OK' if ok else 'KO'} {res[0]}", flush=True)

    if args.test == "stbmap":
        # Write a WORD and read it back for each STB/CS# shift (as set, one UI earlier/later) and
        # output delay (0 to 127 from --stb-delay, the static delay of the build: steps of about
        # 12.5ps). O: correct, x: wrong data, .: no data.
        words = [0x1000 + 0x0111*k for k in range(16)]
        step  = 8
        def move(n, direction):
            con.write("ddrphy_stb_dly_dir", direction)
            for _ in range(n):
                con.write("ddrphy_stb_dly_move", 1)
        print("delay  " + " ".join(f"{d:3d}" for d in range(0, 128, step)))
        for stb in range(settings["ddrphy_stb_shift"] - 1, settings["ddrphy_stb_shift"] + 2):
            con.write("ddrphy_stb_shift", stb)
            con.write("ddrphy_stb_dly_rst", 1)
            move(args.stb_delay, 1)
            line = ""
            for d in range(0, 128, step):
                rpc.init(); rpc.rdpos(args.tck, args.rdly)
                rpc.cmd(0, RAS|CS, 0x123, 1)
                rpc.wrdata([0]*16);  rpc.cmd(3, CAS|WE|CS|WRDATA, 0x20, 1)
                rpc.wrdata(words);   rpc.cmd(3, CAS|WE|CS|WRDATA, 0x20, 1)
                data  = [int(w, 16) for w in rpc.read(0x20, 1).split()]
                line += "  " + ("O" if data == words else ("x" if any(data) else ".")) + " "
                move(step, 0)
            print(f"stb {stb}: {line}", flush=True)
        con.write("ddrphy_stb_dly_rst", 1)

    # Restore the PHY settings and give the SDRAM back to the controller.
    for name, value in settings.items():
        con.write(name, value)
    rpc.control(SEL)

if __name__ == "__main__":
    main()
