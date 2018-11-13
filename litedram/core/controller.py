"""LiteDRAM Controller."""

from migen import *

from litedram.common import *
from litedram.phy import dfi
from litedram.core.refresher import *
from litedram.core.bankmachine import *
from litedram.core.multiplexer import *


class ControllerSettings(Settings):
    def __init__(self,
                 cmd_buffer_depth=8, cmd_buffer_buffered=False,
                 read_time=32, write_time=16,
                 with_bandwidth=False,
                 with_refresh=True,
                 with_auto_precharge=True,
                 address_mapping="ROW_BANK_COL"):
        self.set_attributes(locals())


class LiteDRAMController(Module):
    def __init__(self, phy_settings, geom_settings, timing_settings,
                 controller_settings=ControllerSettings()):
        address_align = log2_int(burst_lengths[phy_settings.memtype])
        self.settings = settings = controller_settings
        self.settings.phy = phy_settings
        self.settings.geom = geom_settings
        self.settings.timing = timing_settings

        self.dfi = dfi.Interface(
            geom_settings.addressbits,
            geom_settings.bankbits,
            phy_settings.nranks,
            phy_settings.dfi_databits,
            phy_settings.nphases)

        self.interface = interface = LiteDRAMInterface(address_align, settings)

        # # #

        # refresher
        refresher = Refresher(settings)
        self.submodules += refresher

        # bank machines
        bank_machines = []
        for i in range(phy_settings.nranks*(2**geom_settings.bankbits)):
            bank_machine = BankMachine(i,
                interface.address_width,
                address_align,
                phy_settings.nranks,
                settings)
            bank_machines.append(bank_machine)
            self.submodules += bank_machine
            self.comb += getattr(interface, "bank"+str(i)).connect(bank_machine.req)

        # multiplexer
        self.submodules.multiplexer = Multiplexer(
            settings, bank_machines, refresher, self.dfi, interface)

    def get_csrs(self):
        return self.multiplexer.get_csrs()
