#!/usr/bin/env python3

from litex.gen import *

from litex.soc.interconnect.stream import *

from litedram.common import PhySettings, LiteDRAMPort
from litedram.core import *
from litedram.modules import SDRAMModule
from litedram.frontend.crossbar import LiteDRAMCrossbar
from litedram.frontend.bist import LiteDRAMBISTGenerator
from litedram.frontend.bist import LiteDRAMBISTChecker
from litedram.frontend.adaptation import LiteDRAMPortCDC


from litedram.phy.model import SDRAMPHYModel

class SimModule(SDRAMModule):
    # geometry
    nbanks = 2
    nrows  = 2048
    ncols  = 2
    # timings
    tRP   = 1
    tRCD  = 1
    tWR   = 1
    tWTR  = 1
    tREFI = 1
    tRFC  = 1


class TB(Module):
    def __init__(self):
        # phy
        sdram_module = SimModule(1000, "1:1")
        phy_settings = PhySettings(
            memtype="SDR",
            dfi_databits=1*16,
            nphases=1,
            rdphase=0,
            wrphase=0,
            rdcmdphase=0,
            wrcmdphase=0,
            cl=2,
            read_latency=4,
            write_latency=0
        )
        self.submodules.sdrphy = SDRAMPHYModel(sdram_module, phy_settings, we_granularity=0)

        # controller
        self.submodules.controller = LiteDRAMController(
                                         phy_settings,
                                         sdram_module.geom_settings,
                                         sdram_module.timing_settings,
                                         ControllerSettings(with_refresh=False))
        self.comb += self.controller.dfi.connect(self.sdrphy.dfi)
        self.submodules.crossbar = LiteDRAMCrossbar(self.controller.interface,
                                                    self.controller.nrowbits)

        # write port
        write_user_port = self.crossbar.get_port("write", cd="write")
        read_user_port = self.crossbar.get_port("read", cd="read")

        # generator / checker
        self.submodules.generator = LiteDRAMBISTGenerator(write_user_port)
        self.submodules.checker = LiteDRAMBISTChecker(read_user_port)


def main_generator(dut):
    for i in range(100):
        yield
    # init
    yield dut.generator.reset.storage.eq(1)
    yield dut.checker.reset.storage.eq(1)
    yield
    yield dut.generator.reset.storage.eq(0)
    yield dut.checker.reset.storage.eq(0)
    yield
    # write
    yield dut.generator.base.storage.eq(16)
    yield dut.generator.length.storage.eq(16)
    for i in range(32):
        yield
    yield dut.generator.shoot.re.eq(1)
    yield
    yield dut.generator.shoot.re.eq(0)
    for i in range(32):
        yield
    while((yield dut.generator.done.status) == 0):
        yield
    # read
    yield dut.checker.base.storage.eq(16)
    yield dut.checker.length.storage.eq(16)
    for i in range(32):
        yield
    yield dut.checker.shoot.re.eq(1)
    yield
    yield dut.checker.shoot.re.eq(0)
    for i in range(32):
        yield
    while((yield dut.checker.done.status) == 0):
        yield
    # check
    print("errors {:d}".format((yield dut.checker.error_count.status)))
    yield

if __name__ == "__main__":
    tb = TB()
    generators = {
        "sys" :   [main_generator(tb)]
    }
    clocks = {"sys":   10,
              "write": 12,
              "read":   8}
    run_simulation(tb, generators, clocks, vcd_name="sim.vcd")
