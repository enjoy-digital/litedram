#
# This file is part of LiteDRAM project.
#
# Copyright (c) 2015-2026 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
# Register appendix of the manual: which designs tools/csr_doc.py elaborates and which register banks
# it documents (the engine is generic, part of the manual kit).

import copy
import importlib.util
import json
import os
import sys
import tempfile

# Configurations: script (path from the repository root), command line and YAML keys changed on a
# generator example. The four generator examples give the PHY banks of four FPGA families (Artix-7,
# Kintex UltraScale+, Lattice ECP5, Gowin GW5A) and the DFI injector; the `xcu1525_ecc` variant
# adds the optional blocks of the core (bandwidth monitor, DFI ECC with per-bit statistics, port
# ECC, read VREF of UltraScale+); the Genesys2 bench target with `--with-bist` adds the BIST and
# the Kintex-7 PHY bank, with the write leveling registers.
CONFIGS = {
    "arty"               : ("litedram/gen.py", ["examples/arty.yml"],               {}),
    "xcu1525"            : ("litedram/gen.py", ["examples/xcu1525.yml"],            {}),
    "versa_ecp5"         : ("litedram/gen.py", ["examples/versa_ecp5.yml"],         {}),
    "tang_mega_138k_pro" : ("litedram/gen.py", ["examples/tang_mega_138k_pro.yml"], {}),
    "xcu1525_ecc"        : ("litedram/gen.py", ["examples/xcu1525.yml"], {
        "sdram_module_nb"    : 9,
        "with_ecc"           : True,
        "with_ecc_bit_stats" : True,
        "with_bandwidth"     : True,
        "with_hpio_vref"     : True,
        "user_ports"         : {"axi_0": {"type": "axi", "id_width": 4, "ecc": True, "data_width": 256}},
    }),
    "genesys2_bist"      : ("bench/genesys2.py", ["--with-bist"], {}),
}

# Banks documented in the appendix (prefix match on the bank name), in order, with their title and
# the Python class that defines them. The longest matching prefix owns a bank.
BANKS = [
    ("ddrctrl",                    "Generator control", "LiteDRAMCoreControl",   "litedram/gen.py"),
    ("sdram_dfii",                 "DFI injector",      "DFIInjector",           "litedram/dfii.py"),
    ("ddrphy_a7",                  "Artix-7 PHY",       "A7DDRPHY",              "litedram/phy/s7ddrphy.py"),
    ("ddrphy_k7",                  "Kintex-7 PHY",      "K7DDRPHY",              "litedram/phy/s7ddrphy.py"),
    ("ddrphy_usp",                 "UltraScale+ PHY",   "USPDDRPHY",             "litedram/phy/usddrphy.py"),
    ("ddrphy_ecp5",                "ECP5 PHY",          "ECP5DDRPHY",            "litedram/phy/ecp5ddrphy.py"),
    ("ddrphy_gw5",                 "Gowin GW5A PHY",    "GW5DDRPHY",             "litedram/phy/gw5ddrphy.py"),
    ("sdram_controller_bandwidth", "Bandwidth monitor", "Bandwidth",             "litedram/core/bandwidth.py"),
    ("sdram_ecc",                  "DFI ECC",           "LiteDRAMDFIECC",        "litedram/core/ecc.py"),
    ("ecc",                        "Port ECC",          "LiteDRAMNativePortECC", "litedram/frontend/ecc.py"),
    ("sdram_generator",            "BIST generator",    "LiteDRAMBISTGenerator", "litedram/frontend/bist.py"),
    ("sdram_checker",              "BIST checker",      "LiteDRAMBISTChecker",   "litedram/frontend/bist.py"),
]

# Notes printed after the title of a bank family: what the register descriptions do not say. Each
# PHY bank is called `ddrphy` in a build; the appendix lists it under one name per FPGA family, and
# splits the `sdram` bank into its blocks (see PHY_RENAMES and SPLITS below).
NOTES = {
    "ddrctrl": [
        "Built by the generator only (`litedram_gen`); a LiteX SoC has no such bank. The",
        "firmware writes `init_done` at the end of the initialization, and `init_error` too when",
        "it failed. The generated core drives its `init_done` and `init_error` outputs from them,",
        "and its user ports wait for `init_done` by default ([Integration](#integration)).",
    ],
    "sdram_dfii": [
        "The registers of the DFI injector are in the `sdram` bank, so their full names start",
        "with `sdram_dfii_`. Each DFI phase has a group of six `pi<n>_` registers, `0x18` bytes",
        "apart: the table shows phase 0, the 1:4 PHYs have four groups and the 1:2 PHYs two. The",
        "`sel` field of `control` gives the DFI to the controller (`1`, at reset) or to software",
        "(`0`). Software writes a command into `pi<n>_command` and pulses `pi<n>_command_issue`;",
        "[Initialization and calibration](#calibration) describes how the BIOS uses them.",
    ],
    "ddrphy_a7": [
        "Every PHY has a `ddrphy` bank. The appendix lists it under one name per family only to",
        "keep the families apart; in a build, the full names start with `ddrphy_`. The",
        "registers have the same meaning in every family that has them:",
        "",
        "| Registers | Role |",
        "|------------------------------------|----------------------------------------------------------|",
        "| `rst` | Reset of the PHY, pulsed by the BIOS before the initialization |",
        "| `dly_sel` | One bit per byte group: the groups that the delay and bitslip strobes act on |",
        "| `rdly_dq_rst`, `rdly_dq_inc` | Reset or step the read delay of the selected groups |",
        "| `rdly_dq_bitslip_rst`, `rdly_dq_bitslip` | Reset or step the read bitslip of the selected groups |",
        "| `wdly_dq_bitslip_rst`, `wdly_dq_bitslip` | Reset or step the write bitslip of the selected groups |",
        "| `wlevel_en`, `wlevel_strobe` | Write leveling mode, and one DQS pulse in that mode |",
        "| `half_sys8x_taps` | Delay taps in a quarter of tCK; the BIOS derives the tCK taps from it |",
        "| `rdphase`, `wrphase` | DFI phase of the read and write commands |",
        "",
        "The Artix-7 PHY has no ODELAY, so it has no write delay registers.",
    ],
    "ddrphy_k7": [
        "The Kintex-7 and Virtex-7 PHYs with ODELAY add the delays of write leveling: `cdly_`",
        "for the clock and command lines, `wdly_dq_` and `wdly_dqs_` for the data and strobes",
        "of the selected groups. Built with `with_odelay=False`, they have the bank of the",
        "Artix-7 PHY.",
    ],
    "ddrphy_usp": [
        "The UltraScale and UltraScale+ PHYs read back the delays they set (`cdly_value`,",
        "`wdly_dqs_inc_count`, `half_sys8x_taps`). The BIOS clears `en_vtc` while it has",
        "software control of the DFI, so that the voltage and temperature compensation does not",
        "move the delays during leveling. `rd_vref` exists only with `with_hpio_vref` (DDR4 on",
        "UltraScale+, `xcu1525_ecc`).",
    ],
    "ddrphy_ecp5": [
        "`burstdet_seen` has one bit per byte group, set when the PHY saw a read burst on its",
        "strobe since `burstdet_clr`; the BIOS reads it during read leveling. The 1:4 wrapper",
        "with `rate_crossing` adds a `rate` register, not used by the BIOS.",
    ],
    "ddrphy_gw5": [
        "The GW5A PHY at 1:2, as in the example. `rdly_dq_dir` sets the direction of the read",
        "delay steps. At 1:4 with the DLL on, the PHY adds `wdly_dq_rst`, `wdly_dq_inc` and",
        "`wdly_dq_dir`. The GW2A PHY has the bank of this table.",
    ],
    "sdram_controller_bandwidth": [
        "Present with `with_bandwidth` (a `ControllerSettings` key). The registers are in the",
        "`sdram` bank (full names `sdram_controller_bandwidth_<register>`). A write to `update`",
        "copies the read and write commands counted over the last period of 2^24 cycles into",
        "`nreads` and `nwrites`; `data_width` is the controller data width in bits.",
    ],
    "sdram_ecc": [
        "Present with `with_ecc` on a 72-bit memory (`xcu1525_ecc`: nine byte groups). The",
        "registers are in the `sdram` bank (full names `sdram_ecc_<register>`); `bitsel` and",
        "`bitcnt` exist only with `with_ecc_bit_stats`. A write to `clear` resets the counters.",
    ],
    "ecc": [
        "One bank per user port with `ecc: true` in a generator configuration, named",
        "`ecc_<port name>` (`ecc_axi_0` here). `sec_errors` and `ded_errors` count the",
        "corrected and the detected errors; a write to `clear` resets them.",
    ],
    "sdram_generator": [
        "Present with `with_bist` (`add_sdram(with_bist=True)`, the `--with-bist` option of the",
        "bench targets, `litex_sim --with-sdram-bist`). `base` and `end` are byte addresses,",
        "`length` a number of bytes; `ticks` is the duration of the last run in clock cycles.",
        "The BIOS commands `sdram_bist` and `sdram_hw_test` exist only with both BIST banks.",
    ],
    "sdram_checker": [
        "Same layout as the generator, plus `errors`: the words read back with a wrong value.",
    ],
}

# Opening paragraph of the appendix and the sentence that ends the access paragraph.
INTRO = ["This appendix lists the registers of the LiteDRAM cores: DFI injector, PHYs, controller",
         "options and frontends. It is generated from the register definitions of the gateware,",
         "elaborated on six configurations without running an FPGA toolchain. Offsets are in bytes",
         "from the base of the bank; the base addresses depend on the SoC and are in the `csr.csv`",
         "of a build. In the table below, `key=value` is a key of the example changed for the",
         "appendix, and `ECC AXI port` replaces the user ports with one AXI port with ECC."]
USAGE = ["The BIOS and the host tools use these names through", "the generated `csr.h` and `csr.csv`, so they rarely need the offsets."]
MAIN_BANK = "Registers of the top-level `main` bank of the SoC."


# Every PHY names its bank `ddrphy`: the bank is renamed after the family of the configuration so
# that each family gets its own table. The `sdram` bank holds the registers of the DFI injector and
# of the optional controller blocks: they are split into banks named after their prefix, with their
# offsets kept from the base of the `sdram` bank.
PHY_RENAMES = {
    "arty"               : "ddrphy_a7",
    "xcu1525"            : "ddrphy_usp",
    "xcu1525_ecc"        : "ddrphy_usp",
    "versa_ecp5"         : "ddrphy_ecp5",
    "tang_mega_138k_pro" : "ddrphy_gw5",
    "genesys2_bist"      : "ddrphy_k7",
}
SPLITS = {"sdram": ["dfii", "controller_bandwidth", "ecc", "generator", "checker"]}


def _rename(soc, csr_json, old, new):
    soc.csr.regions[new] = soc.csr.regions.pop(old)
    csr_json["csr_bases"][new] = csr_json["csr_bases"][old]
    for reg in list(csr_json["csr_registers"]):
        if reg.startswith(old + "_"):
            csr_json["csr_registers"][new + reg[len(old):]] = csr_json["csr_registers"][reg]


def _split_banks(soc, csr_json):
    for bank, subs in SPLITS.items():
        region = soc.csr.regions.get(bank)
        if region is None:
            continue
        keep = list(region.obj)
        for sub in subs:
            regs = []
            for csr in [c for c in keep if c.name.startswith(sub + "_")]:
                keep.remove(csr)
                c = copy.copy(csr)
                c.name = csr.name[len(sub) + 1:]
                regs.append(c)
            if sub == "dfii":
                # One phase shown: the other phases repeat the layout of phase 0.
                regs = [c for c in regs if not (c.name.startswith("pi") and not c.name.startswith("pi0_"))]
            if regs:
                name = f"{bank}_{sub}"
                soc.csr.regions[name] = copy.copy(region)
                soc.csr.regions[name].obj = regs
                csr_json["csr_bases"][name] = csr_json["csr_bases"][bank]
        region.obj = keep


def _load(repo_root, script):
    """Import a script of the repository under a unique module name."""
    name = "manual_" + script.replace("/", "_").replace(".py", "")
    spec = importlib.util.spec_from_file_location(name, os.path.join(repo_root, script))
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def elaborate(name, repo_root):
    """Run the main() of the generator or of a bench target with its Builder replaced by one that
    elaborates without the toolchain; return (soc, csr_json, module, argv)."""
    import yaml
    script, argv, overrides = CONFIGS[name]
    sys.path.insert(0, repo_root)
    sys.path.insert(0, os.path.join(repo_root, os.path.dirname(script)))
    from litex.soc.integration.builder import Builder
    captured = {}
    old_cwd  = os.getcwd()

    with tempfile.TemporaryDirectory() as tmp:
        class CaptureBuilder(Builder):
            def __init__(self, soc, *args, **kwargs):
                kwargs.update(output_dir=tmp, csr_csv=os.path.join(tmp, "csr.csv"),
                    csr_json=os.path.join(tmp, "csr.json"), compile_software=False,
                    compile_gateware=False)
                Builder.__init__(self, soc, **kwargs)
                captured["soc"] = soc

            def build(self, *args, **kwargs):
                kwargs["run"] = False
                return Builder.build(self, *args, **kwargs)

        run_argv = list(argv)
        if overrides:
            # Variant of a generator example: the example with some keys changed, in a temporary file.
            config = yaml.load(open(os.path.join(repo_root, argv[0])).read(), Loader=yaml.Loader)
            config.update(overrides)
            path = os.path.join(tmp, os.path.basename(argv[0]))
            with open(path, "w") as f:
                yaml.dump(config, f)
            run_argv = [path] + argv[1:]

        os.chdir(repo_root)
        mod = _load(repo_root, script)
        mod.Builder = CaptureBuilder
        old_argv = sys.argv
        sys.argv = [script] + run_argv
        try:
            mod.main()
        finally:
            sys.argv = old_argv
            os.chdir(old_cwd)
        captured["json"] = json.load(open(os.path.join(tmp, "csr.json")))

    # Memories mapped on the CSR bus have no register definitions: keep the register banks only.
    soc, csr_json = captured["soc"], captured["json"]
    for bank, region in list(soc.csr.regions.items()):
        if not isinstance(region.obj, list):
            del soc.csr.regions[bank]
    _rename(soc, csr_json, "ddrphy", PHY_RENAMES[name])
    _split_banks(soc, csr_json)
    module = os.path.splitext(os.path.basename(script))[0]
    if script.startswith("bench/"):
        module = "bench/" + module
    shown = argv + [f"{k}={v}" for k, v in overrides.items() if k != "user_ports"]
    if "user_ports" in overrides:
        shown.append("ECC AXI port")
    return soc, csr_json, module, shown
