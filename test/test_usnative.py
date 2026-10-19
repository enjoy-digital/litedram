#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""DDR pin extraction, resolved resource identity and unsupported-input checks."""

import unittest

from litex.build.generic_platform import GenericPlatform, IOStandard, Pins, Subsignal
from litedram.phy.usnative.pins import device_family, extract_ddr_pins


def platform_resource(*, data_width=16, dqs_width=2, duplicate=False,
                      missing=None, connector=False, channel=0):
    widths = dict(a=14, ba=2, bg=1, act_n=1, dq=data_width,
                  dqs_p=dqs_width, dqs_n=dqs_width, clk_p=1, clk_n=1,
                  cke=1, odt=1, reset_n=1, dm=dqs_width)
    fields, connections = [], {}
    offset = 1 + channel * 100
    for name, width in widths.items():
        if name == missing:
            continue
        pins = [f"A{i}" for i in range(offset, offset + width)]
        if duplicate and name == "dq":
            pins[0] = "A1"
        offset += width
        if connector:
            aliases = []
            for pin in pins:
                connections[pin] = pin
                aliases.append("ddr:" + pin)
            pins = aliases
        fields.append(Subsignal(name, Pins(" ".join(pins)), IOStandard("SSTL12")))
    return ("ddram", channel, *fields), connections


class TestUSNativePins(unittest.TestCase):
    def extract(self, part="xcau25p-ffvb676-2-e", **kwargs):
        resource, connections = platform_resource(**kwargs)
        platform = GenericPlatform(part, [resource], connectors=[("ddr", connections)])
        return extract_ddr_pins(platform, platform.request("ddram"))

    def test_family_gate(self):
        for part, family in [("xcku040-ffva1156-2-e", "ULTRASCALE"),
                             ("xcau25p-ffvb676-2-e", "ULTRASCALE_PLUS"),
                             ("xczu7ev-ffvc1156-2-e", "ULTRASCALE_PLUS"),
                             ("xcu280-fsvh2892-2L-e-es1", "ULTRASCALE_PLUS")]:
            with self.subTest(part=part):
                self.assertEqual(device_family(part), family)
        for part in ["xc7a200t", "xcvc1902", "LFE5U-85F", "xcspartan", "xcau25"]:
            with self.subTest(part=part):
                with self.assertRaises(ValueError):
                    self.extract(part=part)

    def test_connector_resolution(self):
        direct, connector = self.extract(), self.extract(connector=True)
        self.assertEqual(direct, connector)
        self.assertEqual(direct.fingerprint, connector.fingerprint)

    def test_widths_and_fingerprint(self):
        narrow = self.extract()
        wide = self.extract(data_width=32, dqs_width=4)
        self.assertEqual(sum(p.signal == "dq" for p in wide.pins), 32)
        self.assertNotEqual(narrow.fingerprint, wide.fingerprint)
        self.assertNotEqual(narrow.fingerprint, self.extract(part="xcku5p-ffvb676-2-e").fingerprint)

    def test_bad_resources(self):
        for kwargs, message in [({"duplicate": True}, "Duplicate"),
                                ({"data_width": 15}, "multiple of eight"),
                                ({"dqs_width": 1}, "DQS width"),
                                ({"missing": "dqs_n"}, "Missing DDR4")]:
            with self.subTest(kwargs=kwargs):
                with self.assertRaisesRegex(ValueError, message):
                    self.extract(**kwargs)

    def test_channel_isolation(self):
        resources = [platform_resource(channel=n)[0] for n in range(2)]
        platform = GenericPlatform("xcau25p-ffvb676-2-e", resources)
        pads0 = platform.request("ddram", 0)
        pads1 = platform.request("ddram", 1)
        pins0 = extract_ddr_pins(platform, pads0)
        pins1 = extract_ddr_pins(platform, pads1)
        self.assertFalse({p.package_pin for p in pins0.pins} &
                         {p.package_pin for p in pins1.pins})

    def test_x4_strobes_without_masks(self):
        pins = self.extract(data_width=16, dqs_width=4, missing="dm")
        self.assertEqual(sum(p.signal == "dqs_p" for p in pins.pins), 4)

    def test_unresolved_and_missing_constraints(self):
        for fault in ("unassigned", "missing", "standard"):
            resource, _ = platform_resource()
            platform = GenericPlatform("xcau25p-ffvb676-2-e", [resource])
            pads = platform.request("ddram")
            rows = platform.constraint_manager.get_sig_constraints()
            index = next(i for i, row in enumerate(rows) if row[0] is pads.dq)
            signal, pins, others, origin = rows[index]
            if fault == "missing":
                rows.pop(index)
            else:
                rows[index] = (signal, ["X"] + pins[1:] if fault == "unassigned" else pins,
                               [] if fault == "standard" else others, origin)
            platform.constraint_manager.get_sig_constraints = lambda: rows
            with self.subTest(fault=fault):
                with self.assertRaises(ValueError):
                    extract_ddr_pins(platform, pads)


if __name__ == "__main__":
    unittest.main()
