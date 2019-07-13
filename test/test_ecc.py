# This file is Copyright (c) 2018-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# License: BSD

import unittest
import random

from migen import *

from litedram.common import *
from litedram.frontend.ecc import *

from litex.gen.sim import *


class TestECC(unittest.TestCase):
    def test_ecc_wrapper(self):
        # 32 bits + 8 bits ecc
        port_from = LiteDRAMNativePort("both", 24, 32*8)
        port_to = LiteDRAMNativePort("both", 24, 40*8)
        ecc = LiteDRAMNativePortECC(port_from, port_to)

        # 64 bits + 8 bits ecc
        port_from = LiteDRAMNativePort("both", 24, 64*8)
        port_to = LiteDRAMNativePort("both", 24, 72*8)
        ecc = LiteDRAMNativePortECC(port_from, port_to)
