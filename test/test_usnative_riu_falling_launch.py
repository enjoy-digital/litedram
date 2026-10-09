#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Check the native sampling contract with actual generated transaction RTL."""

import shutil
import tempfile
import unittest
import subprocess

from pathlib import Path

from migen.fhdl import verilog
from litedram.phy.usnative import riu_falling_launch
from litedram.phy.usnative.riu_transaction import RIUTransaction


class TestRIUFallingLaunch(unittest.TestCase):
    @unittest.skipUnless(shutil.which('iverilog') and shutil.which('vvp'), 'Icarus Verilog is required')
    def test_native_edge_and_response_contract(self):
        bridge = RIUTransaction(3, [0, 0, 1], timeout=64)
        names = ['request', 'write', 'reset', 'address', 'select', 'wdata',
                 'busy', 'valid', 'error', 'rdata', 'native_address',
                 'native_select', 'native_wdata', 'native_write',
                 'native_rdata', 'native_valid']
        for name in names:
            getattr(bridge, name).name_override = name
        source = Path(riu_falling_launch.__file__).with_suffix('.v')
        contract = Path(__file__).parent/'reference/usnative_riu_edge.v'
        with tempfile.TemporaryDirectory(prefix='usnative_riu_') as directory:
            directory = Path(directory)
            generated = directory/'bridge.v'
            generated.write_text(str(verilog.convert(bridge, ios={getattr(bridge, n) for n in names}, name='bridge')))
            executable = directory/'sim.vvp'
            compile_result = subprocess.run([shutil.which('iverilog'), '-g2005', '-s', 'tb',
                '-o', str(executable), str(generated), str(source), str(contract)],
                capture_output=True, text=True, timeout=60)
            self.assertEqual(compile_result.returncode, 0, compile_result.stdout+compile_result.stderr)
            result = subprocess.run([shutil.which('vvp'), str(executable)],
                capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
            self.assertIn('PASS native edge samples=310', result.stdout)
