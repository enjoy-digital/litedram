from litex.gen import *

from litedram.phy import dfi
from litedram import common
from litedram.core.refresher import *
from litedram.core.bankmachine import *
from litedram.core.multiplexer import *


class ControllerSettings:
    def __init__(self, cmd_buffer_depth=8, read_time=32, write_time=16,
                 with_bandwidth=False,
                 with_refresh=True):
        self.cmd_buffer_depth = cmd_buffer_depth
        self.read_time = read_time
        self.write_time = write_time
        self.with_bandwidth = with_bandwidth
        self.with_refresh = with_refresh


class LiteDRAMController(Module):
    def __init__(self, phy_settings, geom_settings, timing_settings,
                 controller_settings=None):
        if controller_settings is None:
            controller_settings = ControllerSettings()
        if phy_settings.memtype in ["SDR"]:
            burst_length = phy_settings.nphases*1  # command multiplication*SDR
        elif phy_settings.memtype in ["DDR", "LPDDR", "DDR2", "DDR3"]:
            burst_length = phy_settings.nphases*2  # command multiplication*DDR
        address_align = log2_int(burst_length)

        self.dfi = dfi.Interface(geom_settings.addressbits,
            geom_settings.bankbits,
            phy_settings.dfi_databits,
            phy_settings.nphases)

        self.settings = settings = controller_settings
        self.settings.phy = phy_settings
        self.settings.geom = geom_settings
        self.settings.timing = timing_settings

        self.lasmic = common.InternalInterface(address_align, settings)
        self.nrowbits = settings.geom.colbits - address_align

        # # #

        self.submodules.refresher = Refresher(self.settings)

        bank_machines = []
        for i in range(2**geom_settings.bankbits):
            bank_machine = BankMachine(i,
                                       self.lasmic.aw,
                                       address_align,
                                       settings)
            bank_machines.append(bank_machine)
            self.submodules += bank_machine
            self.comb += getattr(self.lasmic, "bank"+str(i)).connect(bank_machine.req)

        self.submodules.multiplexer = Multiplexer(settings,
                                                  bank_machines,
                                                  self.refresher,
                                                  self.dfi,
                                                  self.lasmic)

    def get_csrs(self):
        return self.multiplexer.get_csrs()
