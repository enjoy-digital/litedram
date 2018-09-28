from migen import *

from litedram.phy import dfi
from litedram import common
from litedram.core.refresher import *
from litedram.core.bankmachine import *
from litedram.core.multiplexer import *


class ControllerSettings:
    def __init__(self,
                 cmd_buffer_depth=8, cmd_buffer_buffered=False,
                 read_time=32, write_time=16,
                 with_bandwidth=False,
                 with_refresh=True,
                 with_auto_precharge=True,
                 with_reordering=False):
        self.cmd_buffer_depth = cmd_buffer_depth
        self.cmd_buffer_buffered = cmd_buffer_buffered
        self.read_time = read_time
        self.write_time = write_time
        self.with_bandwidth = with_bandwidth
        self.with_refresh = with_refresh
        self.with_auto_precharge = with_auto_precharge
        self.with_reordering = with_reordering


class LiteDRAMController(Module):
    def __init__(self, phy_settings, geom_settings, timing_settings,
                 controller_settings=ControllerSettings()):
        self.settings = settings = controller_settings
        self.settings.phy = phy_settings
        self.settings.geom = geom_settings
        self.settings.timing = timing_settings

        burst_lengths = {
        	"SDR":   1,
        	"DDR":   4,
        	"LPDDR": 4,
        	"DDR2":  4,
        	"DDR3":  8
        }
        address_align = log2_int(burst_lengths[phy_settings.memtype])

        self.dfi = dfi.Interface(
            geom_settings.addressbits,
            geom_settings.bankbits,
            phy_settings.nranks,
            phy_settings.dfi_databits,
            phy_settings.nphases)

        self.nrowbits = settings.geom.colbits - address_align

        self.interface = common.LiteDRAMInterface(address_align, settings)

        # # #

        self.submodules.refresher = Refresher(self.settings)

        bank_machines = []
        for i in range(phy_settings.nranks*(2**geom_settings.bankbits)):
            bank_machine = BankMachine(i,
                                       self.interface.address_width,
                                       address_align,
                                       phy_settings.nranks,
                                       settings)
            bank_machines.append(bank_machine)
            self.submodules += bank_machine
            self.comb += getattr(self.interface, "bank"+str(i)).connect(bank_machine.req)

        self.submodules.multiplexer = Multiplexer(settings,
                                                  bank_machines,
                                                  self.refresher,
                                                  self.dfi,
                                                  self.interface)

    def get_csrs(self):
        return self.multiplexer.get_csrs()
