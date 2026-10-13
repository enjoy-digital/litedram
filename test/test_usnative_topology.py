#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Synthetic topology cases; real-device query results are integration checks."""

import unittest

from litedram.phy.usnative.pins import DDRPin, DDRPinMap
from litedram.phy.usnative.topology import parse_vivado_map, vivado_query


def topology_fixture(x4=False):
    pins, rows = [], []
    for lane in range(2):
        positions = [2, 3, 4, 5, 8, 9, 10, 11] if x4 else [0, 1, 2, 3, 4, 5, 8, 9]
        signals = [("dq", lane * 8 + bit, pos) for bit, pos in enumerate(positions)]
        if x4:
            signals += [("dqs_p", lane * 2, 0), ("dqs_n", lane * 2, 1),
                        ("dqs_p", lane * 2 + 1, 6), ("dqs_n", lane * 2 + 1, 7)]
        else:
            signals += [("dqs_p", lane, 6), ("dqs_n", lane, 7), ("dm", lane, 10)]
        for signal, index, position in signals:
            y = 13 * lane + position
            pin = f"A{y + 1}"
            nibble = "L" if position < 6 else "U"
            master = position % 2 == 0
            mate = f"A{y + (2 if master else 0)}"
            function = f"IO_L1{'P' if master else 'N'}_T{lane}{nibble}_N{position}_DBC_64"
            pins.append(DDRPin(signal, index, pin, "SSTL12"))
            rows.append([pin, "64", function, f"IOB_X0Y{y}",
                         "HPIOB_M" if master else "HPIOB_S", mate, str(int(master)),
                         str(position), str(position - (6 if nibble == "U" else 0)),
                         f"BITSLICE_RX_TX_X0Y{y}",
                         f"BITSLICE_CONTROL_X0Y{2 * lane + (nibble == 'U')}", str(lane)])
    return DDRPinMap("xcau25p-ffvb676-2-e", "ULTRASCALE_PLUS", tuple(pins)), rows


def encode(pin_map, rows):
    header = f"USNATIVE\t1\t{pin_map.fingerprint}\t{pin_map.part}\t2026.1\n"
    columns = "pin\tbank\tfunction\tsite\tsite_type\tmate\tmaster\tbyte_position\tnibble_position\tnative_site\tcontrol_site\tbyte\n"
    return header + columns + "".join("\t".join(row) + "\n" for row in rows) + f"END\t{len(pin_map.pins)}\n"


class TestUSNativeTopology(unittest.TestCase):
    def test_original_ultrascale_hpiob(self):
        pins, rows = topology_fixture()
        for row in rows:
            row[4] = 'HPIOB'
        # The original UltraScale device uses a common HPIOB type; polarity
        # still comes from the separately validated package-pin properties.
        original = DDRPinMap('xcku040-ffva1156-2-e', 'ULTRASCALE', pins.pins)
        sites = parse_vivado_map(original, encode(original, rows), vivado_version='2026.1')
        self.assertTrue(sites['dqs_p', 0].master)
        self.assertFalse(sites['dqs_n', 0].master)
        with self.assertRaisesRegex(ValueError, 'Unsupported native bank/site'):
            parse_vivado_map(pins, encode(pins, rows), vivado_version='2026.1')

    def test_valid_groups(self):
        pins, rows = topology_fixture()
        sites = parse_vivado_map(pins, encode(pins, rows), vivado_version="2026.1")
        self.assertEqual(sites["dq", 8].byte, 1)
        self.assertEqual(sites["dqs_p", 0].native_site, "BITSLICE_RX_TX_X0Y6")

    def test_stale_or_incomplete_export(self):
        pins, rows = topology_fixture()
        text = encode(pins, rows)
        for bad in [text.replace("2026.1", "2025.2"),
                    text.replace(pins.fingerprint, "0" * 64),
                    text.replace("USNATIVE\t1", "USNATIVE\t2"),
                    text[:text.rfind("END")]]:
            with self.subTest(header=bad.splitlines()[0]):
                with self.assertRaises(ValueError):
                    parse_vivado_map(pins, bad, vivado_version="2026.1")

    def test_missing_duplicate_and_extra_pins(self):
        pins, rows = topology_fixture()
        for bad in [rows[:-1], rows + [rows[0]], rows + [["Z99"] + rows[0][1:]]]:
            with self.assertRaises(ValueError):
                parse_vivado_map(pins, encode(pins, bad), vivado_version="2026.1")

    def test_bad_pair_bank_and_native_site(self):
        pins, rows = topology_fixture()
        cases = [(8, 5, "A99"), (8, 6, "0"), (0, 4, "HDIOB"),
                 (0, 9, ""), (0, 9, rows[1][9]), (0, 8, "5"),
                 (0, 10, ""), (0, 10, "BITSLICE_CONTROL_X0Y99"),
                 (0, 2, rows[0][2].replace("T0L", "T1L"))]
        for row, column, value in cases:
            bad = [r.copy() for r in rows]
            bad[row][column] = value
            with self.subTest(row=row, column=column):
                with self.assertRaises(ValueError):
                    parse_vivado_map(pins, encode(pins, bad), vivado_version="2026.1")

    def test_query_rejects_tcl_tokens(self):
        pins, _ = topology_fixture()
        with self.assertRaises(ValueError):
            vivado_query(DDRPinMap("xcau25p;exit", pins.family, pins.pins))
        with self.assertRaises(ValueError):
            vivado_query(DDRPinMap(pins.part, pins.family, (DDRPin("dq", 0, "[exit]", "SSTL12"),)))
        with self.assertRaises(ValueError):
            vivado_query(DDRPinMap("xc7a200t-fbg484-2", pins.family, pins.pins))

    def test_single_ended_command_site(self):
        pins, rows = topology_fixture()
        pins = DDRPinMap(pins.part, pins.family,
                         pins.pins + (DDRPin("a", 0, "A13", "SSTL12"),))
        rows.append(["A13", "64", "IO_T0U_N12_64", "IOB_X0Y12", "HPIOB_SNGL",
                     "", "0", "12", "6", "BITSLICE_RX_TX_X0Y12", "BITSLICE_CONTROL_X0Y1", "0"])
        sites = parse_vivado_map(pins, encode(pins, rows), vivado_version="2026.1")
        self.assertEqual(sites["a", 0].position, 12)

    def test_data_moved_to_other_byte(self):
        pins, rows = topology_fixture()
        rows[0][2] = rows[0][2].replace("T0L", "T1L")
        rows[0][9] = "BITSLICE_RX_TX_X0Y50"
        rows[0][10] = "BITSLICE_CONTROL_X0Y2"
        rows[0][11] = "1"
        with self.assertRaisesRegex(ValueError, "outside its strobe group"):
            parse_vivado_map(pins, encode(pins, rows), vivado_version="2026.1")

    def test_x4_nibble_groups(self):
        pins, rows = topology_fixture(x4=True)
        sites = parse_vivado_map(pins, encode(pins, rows), vivado_version="2026.1")
        self.assertEqual(sites["dq", 0].nibble, "L")
        self.assertEqual(sites["dq", 4].nibble, "U")
        # Swap two DQ assignments within the byte but across strobe nibbles.
        moved = tuple(DDRPin(pin.signal, {0: 4, 4: 0}.get(pin.index, pin.index),
                             pin.package_pin, pin.iostandard) if pin.signal == "dq" else pin
                      for pin in pins.pins)
        pins = DDRPinMap(pins.part, pins.family, moved)
        with self.assertRaisesRegex(ValueError, "outside its strobe group"):
            parse_vivado_map(pins, encode(pins, rows), vivado_version="2026.1")
