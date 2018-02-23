import unittest

from migen import *

from litex.soc.interconnect.stream import *

from litedram.common import PhySettings, LiteDRAMPort
from litedram.core import *
from litedram.modules import SDRAMModule
from litedram.frontend.crossbar import LiteDRAMCrossbar
from litedram.frontend.bist import _LiteDRAMBISTGenerator
from litedram.frontend.bist import _LiteDRAMBISTChecker
from litedram.frontend.adaptation import LiteDRAMPortCDC

from litedram.phy.model import SDRAMPHYModel

from test.common import *


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
        self.submodules.sdrphy = SDRAMPHYModel(sdram_module,
                                               phy_settings,
                                               we_granularity=0)

        # controller
        self.submodules.controller = LiteDRAMController(
                                         phy_settings,
                                         sdram_module.geom_settings,
                                         sdram_module.timing_settings,
                                         ControllerSettings(with_refresh=False))
        self.comb += self.controller.dfi.connect(self.sdrphy.dfi)
        self.submodules.crossbar = LiteDRAMCrossbar(self.controller.interface,
                                                    self.controller.nrowbits)

        # ports
        write_user_port = self.crossbar.get_port("write", cd="write")
        read_user_port = self.crossbar.get_port("read", cd="read")

        # generator / checker
        self.submodules.generator = _LiteDRAMBISTGenerator(write_user_port, True)
        self.submodules.checker = _LiteDRAMBISTChecker(read_user_port, True)


def main_generator(dut):
    generator = BISTDriver(dut.generator)
    checker = BISTDriver(dut.checker)

    for i in range(16):
        yield

    # write
    yield from generator.reset()
    yield from generator.run(16, 16)

    # read (no errors)
    yield from checker.reset()
    yield from checker.run(16, 16)
    assert checker.errors == 0


class TestBISTAsync(unittest.TestCase):
    def test(self):
        tb = TB()
        generators = {"sys" :   [main_generator(tb)]}
        clocks = {"sys":   10,
                  "write": 12,
                  "read":   8}
        run_simulation(tb, generators, clocks, vcd_name="sim.vcd")
        self.assertEqual(dut.checker.error_count.status, 0)
