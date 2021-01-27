import os
import re
import argparse
from collections import namedtuple, defaultdict

from migen import *

from litex.build.generic_platform import Pins, Subsignal
from litex.build.sim import SimPlatform
from litex.build.sim.config import SimConfig

from litex.soc.interconnect.csr import CSR
from litex.soc.integration.soc_core import SoCCore
from litex.soc.integration.soc_sdram import soc_sdram_args, soc_sdram_argdict
from litex.soc.integration.builder import builder_args, builder_argdict, Builder
from litex.soc.cores.cpu import CPUS

from litedram import modules as litedram_modules
from litedram.core.controller import ControllerSettings
from litedram.phy.model import DFITimingsChecker, _speedgrade_timings, _technology_timings

from litedram.phy.lpddr4.simphy import LPDDR4SimPHY
from litedram.phy.lpddr4.sim import LPDDR4Sim

# Platform -----------------------------------------------------------------------------------------

_io = [
    # clocks added later
    ("sys_rst", 0, Pins(1)),

    ("serial", 0,
        Subsignal("source_valid", Pins(1)),
        Subsignal("source_ready", Pins(1)),
        Subsignal("source_data",  Pins(8)),
        Subsignal("sink_valid",   Pins(1)),
        Subsignal("sink_ready",   Pins(1)),
        Subsignal("sink_data",    Pins(8)),
    ),

    ("lpddr4", 0,
        Subsignal("clk_p",   Pins(1)),
        Subsignal("clk_n",   Pins(1)),
        Subsignal("cke",     Pins(1)),
        Subsignal("odt",     Pins(1)),
        Subsignal("reset_n", Pins(1)),
        Subsignal("cs",      Pins(1)),
        Subsignal("ca",      Pins(6)),
        Subsignal("dqs",     Pins(2)),
        # Subsignal("dqs_n",   Pins(2)),
        Subsignal("dmi",     Pins(2)),
        Subsignal("dq",      Pins(16)),
    ),
]

class Platform(SimPlatform):
    def __init__(self):
        SimPlatform.__init__(self, "SIM", _io)

# Clocks -------------------------------------------------------------------------------------------

class Clocks(dict):  # FORMAT: {name: {"freq_hz": _, "phase_deg": _}, ...}
    def names(self):
        return list(self.keys())

    def add_io(self, io):
        for name in self.names():
            io.append((name + "_clk", 0, Pins(1)))

    def add_clockers(self, sim_config):
        for name, desc in self.items():
            sim_config.add_clocker(name + "_clk", **desc)

class _CRG(Module):
    def __init__(self, platform, domains=None):
        if domains is None:
            domains = ["sys"]
        # request() before creating domains to avoid signal renaming problem
        domains = {name: platform.request(name + "_clk") for name in domains}

        self.clock_domains.cd_por = ClockDomain(reset_less=True)
        for name in domains.keys():
            setattr(self.clock_domains, "cd_" + name, ClockDomain(name=name))

        int_rst = Signal(reset=1)
        self.sync.por += int_rst.eq(0)
        self.comb += self.cd_por.clk.eq(self.cd_sys.clk)

        for name, clk in domains.items():
            cd = getattr(self, "cd_" + name)
            self.comb += cd.clk.eq(clk)
            self.comb += cd.rst.eq(int_rst)

def get_clocks(sys_clk_freq):
    return Clocks({
        "sys":           dict(freq_hz=sys_clk_freq),
        "sys_11_25":     dict(freq_hz=sys_clk_freq, phase_deg=11.25),
        "sys8x":         dict(freq_hz=8*sys_clk_freq),
        "sys8x_ddr":     dict(freq_hz=2*8*sys_clk_freq),
        "sys8x_90":      dict(freq_hz=8*sys_clk_freq, phase_deg=90),
        "sys8x_90_ddr":  dict(freq_hz=2*8*sys_clk_freq, phase_deg=2*90),
    })

# SoC ----------------------------------------------------------------------------------------------

class SimSoC(SoCCore):
    def __init__(self, clocks, log_level, auto_precharge=False, with_refresh=True, trace_reset=0,
            disable_delay=False, masked_write=True, **kwargs):
        platform     = Platform()
        sys_clk_freq = clocks["sys"]["freq_hz"]

        # SoCCore ----------------------------------------------------------------------------------
        super().__init__(platform,
            clk_freq      = sys_clk_freq,
            ident         = "LiteX Simulation",
            ident_version = True,
            cpu_variant   = "minimal",
            **kwargs)

        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = _CRG(platform, clocks.names())

        # Debugging --------------------------------------------------------------------------------
        platform.add_debug(self, reset=trace_reset)

        # LPDDR4 -----------------------------------------------------------------------------------
        sdram_module = litedram_modules.MT53E256M16D1(sys_clk_freq, "1:8")
        pads = platform.request("lpddr4")
        self.submodules.ddrphy = LPDDR4SimPHY(
            sys_clk_freq       = sys_clk_freq,
            aligned_reset_zero = True,
            masked_write       = masked_write,
        )
        # fake delays (make no nsense in simulation, but sdram.c expects them)
        self.ddrphy._rdly_dq_rst         = CSR()
        self.ddrphy._rdly_dq_inc         = CSR()
        self.add_csr("ddrphy")

        for p in ["clk_p", "clk_n", "cke", "odt", "reset_n", "cs", "ca", "dq", "dqs", "dmi"]:
            self.comb += getattr(pads, p).eq(getattr(self.ddrphy.pads, p))

        controller_settings = ControllerSettings()
        controller_settings.auto_precharge = auto_precharge
        controller_settings.with_refresh = with_refresh

        self.add_sdram("sdram",
            phy                     = self.ddrphy,
            module                  = sdram_module,
            origin                  = self.mem_map["main_ram"],
            size                    = kwargs.get("max_sdram_size", 0x40000000),
            l2_cache_size           = kwargs.get("l2_size", 8192),
            l2_cache_min_data_width = kwargs.get("min_l2_data_width", 128),
            l2_cache_reverse        = False,
            controller_settings     = controller_settings
        )
        # Reduce memtest size for simulation speedup
        self.add_constant("MEMTEST_DATA_SIZE", 8*1024)
        self.add_constant("MEMTEST_ADDR_SIZE", 8*1024)

        # LPDDR4 Sim -------------------------------------------------------------------------------
        self.submodules.lpddr4sim = LPDDR4Sim(
            pads          = self.ddrphy.pads,
            settings      = self.sdram.controller.settings,
            sys_clk_freq  = sys_clk_freq,
            log_level     = log_level,
            disable_delay = disable_delay,
        )
        self.add_csr("lpddr4sim")

        self.add_constant("CONFIG_SIM_DISABLE_BIOS_PROMPT")
        if disable_delay:
            self.add_constant("CONFIG_SIM_DISABLE_DELAYS")

        # Reuse DFITimingsChecker from phy/model.py
        nphases = self.sdram.controller.settings.phy.nphases
        timings = {"tCK": (1e9 / sys_clk_freq) / nphases}
        for name in _speedgrade_timings + _technology_timings:
            timings[name] = sdram_module.get(name)

        self.submodules.dfi_timings_checker = DFITimingsChecker(
            dfi          = self.ddrphy.dfi,
            nbanks       = 2**self.sdram.controller.settings.geom.bankbits,
            nphases      = nphases,
            timings      = timings,
            refresh_mode = sdram_module.timing_settings.fine_refresh_mode,
            memtype      = self.sdram.controller.settings.phy.memtype,
            verbose      = False,
        )

        # Debug info -------------------------------------------------------------------------------
        def dump(obj):
            print()
            print(" " + obj.__class__.__name__)
            print(" " + "-" * len(obj.__class__.__name__))
            d = obj if isinstance(obj, dict) else vars(obj)
            for var, val in d.items():
                if var == "self":
                    continue
                print("  {}: {}".format(var, val))

        print("=" * 80)
        dump(clocks)
        dump(self.ddrphy.settings)
        dump(sdram_module.geom_settings)
        dump(sdram_module.timing_settings)
        print()
        print("=" * 80)

# GTKWave ------------------------------------------------------------------------------------------

class SigTrace:
    def __init__(self, name, alias=None, color=None, filter_file=None):
        self.name = name
        self.alias = alias
        self.color = color
        self.filter_file = filter_file

def strip_bits(name):
    if name.endswith("]") and "[" in name:
        name = name[:name.rfind("[")]
    return name

def regex_map(sig, patterns, on_match, on_no_match, remove_bits=True):
    # Given `patterns` return `on_match(sig, pattern)` if any pattern matches or else `on_no_match(sig)`
    alias = sig.alias
    if remove_bits:  # get rid of signal bits (e.g. wb_adr[29:0])
        alias = strip_bits(alias)
    for pattern in patterns:
        if pattern.search(alias):
            return on_match(sig, pattern)
    return on_no_match(sig)

def regex_filter(patterns, negate=False, **kwargs):
    patterns = list(map(re.compile, patterns))
    def filt(sigs):
        return list(filter(None, map(lambda sig: regex_map(sig, patterns,
            on_match = lambda s, p: (s if not negate else None),
            on_no_match = lambda s: (None if not negate else s),
            **kwargs), sigs)))
    return filt

def regex_sorter(patterns, unmatched_last=True, **kwargs):
    def sort(sigs):
        order = {re.compile(pattern): i for i, pattern in enumerate(patterns)}
        return sorted(sigs, key=lambda sig: regex_map(sig, order.keys(),
            on_match    = lambda s, p: order[p],
            on_no_match = lambda s: len(order) if unmatched_last else -1,
            **kwargs))
    return sort

def suffixes2re(strings):
    return ["{}$".format(s) for s in strings]

def prefixes2re(strings):
    return ["^{}".format(s) for s in strings]

def strings2re(strings):
    return suffixes2re(prefixes2re(strings))

def wishbone_sorter(**kwargs):
    suffixes = ["cyc", "stb", "ack", "we", "sel", "adr", "dat_w", "dat_r"]
    return regex_sorter(suffixes2re(suffixes), **kwargs)

def dfi_sorter(phases=True, nphases_max=8, **kwargs):
    suffixes = [
        "cas_n", "ras_n", "we_n",
        "address", "bank",
        "wrdata_en", "wrdata", "wrdata_mask",
        "rddata_en", "rddata", "rddata_valid",
    ]
    if phases:
        patterns = []
        for phase in range(nphases_max):
            patterns.extend(["p{}_{}".format(phase, suffix) for suffix in suffixes])
    else:
        patterns = suffixes
    return regex_sorter(suffixes2re(patterns), **kwargs)

def regex_colorer(color_patterns, default=None, **kwargs):
    colors = {}
    for color, patterns in color_patterns.items():
        for pattern in patterns:
            colors[re.compile(pattern)] = color

    def add_color(sig, color):
        sig.color = color

    def add_colors(sigs):
        for sig in sigs:
            regex_map(sig, colors.keys(),
                on_match = lambda s, p: add_color(s, colors[p]),
                on_no_match = lambda s: add_color(s, default),
                **kwargs)
        return sigs
    return add_colors

def dfi_per_phase_colorer(nphases_max=8, **kwargs):
    colors = ["normal", "yellow", "orange", "red"]
    color_patterns = {}
    for p in range(nphases_max):
        color = colors[p % len(colors)]
        patterns = color_patterns.get(color, [])
        patterns.append("p{}_".format(p))
        color_patterns[color] = patterns
    return regex_colorer(color_patterns, default="indigo", **kwargs)

def dfi_in_phase_colorer(**kwargs):
    return regex_colorer({
        "normal": suffixes2re(["cas_n", "ras_n", "we_n"]),
        "yellow": suffixes2re(["address", "bank"]),
        "orange": suffixes2re(["wrdata_en", "wrdata", "wrdata_mask"]),
        "red":    suffixes2re(["rddata_en", "rddata", "rddata_valid"]),
    }, default="indigo", **kwargs)

class LitexGTKWSave:
    def __init__(self, vns, savefile, dumpfile, filtersdir=None, prefix="TOP.sim."):
        self.vns = vns   # Namespace output of Builder.build, required to resolve signal names
        self.prefix = prefix
        self.savefile = savefile
        self.dumpfile = dumpfile
        self.filtersdir = filtersdir
        if self.filtersdir is None:
            self.filtersdir = os.path.dirname(self.dumpfile)

    def __enter__(self):
        # pyvcd: https://pyvcd.readthedocs.io/en/latest/vcd.gtkw.html
        from vcd.gtkw import GTKWSave
        self.file = open(self.savefile, "w")
        self.gtkw = GTKWSave(self.file)
        self.gtkw.dumpfile(self.dumpfile)
        self.gtkw.treeopen("TOP")
        self.gtkw.sst_expanded(True)
        return self

    def __exit__(self, type, value, traceback):
        self.file.close()
        print("\nGenerated GTKWave save file at: {}\n".format(self.savefile))

    def name(self, sig):
        bits = ""
        if len(sig) > 1:
            bits = "[{}:0]".format(len(sig) - 1)
        return self.vns.get_name(sig) + bits

    def signal(self, signal):
        self.gtkw.trace(self.prefix + self.name(signal))

    def common_prefix(self, names):
        prefix = os.path.commonprefix(names)
        last_underscore = prefix.rfind("_")
        return prefix[:last_underscore + 1]

    def group(self, signals, group_name=None, alias=True, closed=True,
            filter=None, sorter=None, colorer=None, translation_files=None, **kwargs):
        translation_files = translation_files or {}
        if len(signals) == 1:
            return self.signal(signals[0])

        names = [self.name(s) for s in signals]
        common = self.common_prefix(names)

        make_alias = (lambda n: n[len(common):]) if alias else (lambda n: n)
        sigs = [SigTrace(name=n, alias=make_alias(n)) for i, n in enumerate(names)]
        if translation_files is not None:
            for sig, file in zip(sigs, translation_files):
                sig.filter_file = file

        for mapper in [filter, sorter, colorer]:
            if mapper is not None:
                sigs = list(mapper(sigs))

        with self.gtkw.group(group_name or common.strip("_"), closed=closed):
            for s in sigs:
                self.gtkw.trace(self.prefix + s.name, alias=s.alias, color=s.color,
                    translate_filter_file=s.filter_file, **kwargs)

    def by_regex(self, regex, **kwargs):
        pattern = re.compile(regex)
        for sig in self.vns.pnd.keys():
            m = pattern.search(self.vns.pnd[sig])
        signals = list(filter(lambda sig: pattern.search(self.vns.pnd[sig]), self.vns.pnd.keys()))
        assert len(signals) > 0, "No match found for {}".format(regex)
        return self.group(signals, **kwargs)

    def clocks(self, **kwargs):
        clks = [cd.clk for cd in self.vns.clock_domains]
        self.group(clks, group_name="clocks", alias=False, closed=False, **kwargs)

    def add(self, obj, **kwargs):
        if isinstance(obj, Record):
            self.group([s for s, _ in obj.iter_flat()], **kwargs)
        elif isinstance(obj, Signal):
            self.signal(obj)
        else:
            raise NotImplementedError(type(obj), obj)

    def make_fsm_state_translation(self, fsm):
        # generate filter file
        from vcd.gtkw import make_translation_filter
        translations = list(fsm.decoding.items())
        filename = "filter__{}.txt".format(strip_bits(self.name(fsm.state)))
        filepath = os.path.join(self.filtersdir, filename)
        with open(filepath, 'w') as f:
            f.write(make_translation_filter(translations, size=len(fsm.state)))
        return filepath

    def iter_submodules(self, fragment):
        for name, module in getattr(fragment, "_submodules", []):
            yield module
            yield from self.iter_submodules(module)

    def fsm_states(self, soc, **kwargs):
        # TODO: generate alias names for the machines, because the defaults are hard to decipher
        fsms = list(filter(lambda module: isinstance(module, FSM), self.iter_submodules(soc)))
        states = [fsm.state for fsm in fsms]
        files = [self.make_fsm_state_translation(fsm) for fsm in fsms]
        self.group(states, group_name="FSM states", translation_files=files, **kwargs)

# Build --------------------------------------------------------------------------------------------

def generate_gtkw_savefile(builder, vns, trace_fst):
    dumpfile = os.path.join(builder.gateware_dir, "sim.{}".format("fst" if trace_fst else "vcd"))
    savefile = os.path.join(builder.gateware_dir, "sim.gtkw")
    soc = builder.soc

    with LitexGTKWSave(vns, savefile=savefile, dumpfile=dumpfile) as gtkw:
        gtkw.clocks()
        gtkw.add(soc.bus.slaves["main_ram"], sorter=wishbone_sorter())
        # all dfi signals
        gtkw.add(soc.ddrphy.dfi, sorter=dfi_sorter(), colorer=dfi_in_phase_colorer())
        # each phase in separate group
        with gtkw.gtkw.group("dfi phaseX", closed=True):
            for i, phase in enumerate(soc.ddrphy.dfi.phases):
                gtkw.add(phase,
                    group_name = "dfi p{}".format(i),
                    sorter     = dfi_sorter(phases=False),
                    colorer    = dfi_in_phase_colorer())
        # only dfi command signals
        gtkw.add(soc.ddrphy.dfi,
            group_name = "dfi commands",
            filter     = regex_filter(suffixes2re(["cas_n", "ras_n", "we_n"])),
            sorter     = dfi_sorter(),
            colorer    = dfi_per_phase_colorer())
        # only dfi data signals
        gtkw.add(soc.ddrphy.dfi,
            group_name = "dfi wrdata",
            filter     = regex_filter(suffixes2re(["wrdata"])),
            sorter     = dfi_sorter(),
            colorer    = dfi_per_phase_colorer())
        gtkw.add(soc.ddrphy.dfi,
            group_name = "dfi wrdata_mask",
            filter     = regex_filter(suffixes2re(["wrdata_mask"])),
            sorter     = dfi_sorter(),
            colorer    = dfi_per_phase_colorer())
        gtkw.add(soc.ddrphy.dfi,
            group_name = "dfi rddata",
            filter     = regex_filter(suffixes2re(["rddata"])),
            sorter     = dfi_sorter(),
            colorer    = dfi_per_phase_colorer())
        # dram apds
        gtkw.by_regex("pads_",
            filter = regex_filter(["clk_n$", "_[io]$", "_oe$"], negate=True),
            sorter = regex_sorter(suffixes2re(["cke", "odt", "reset_n", "clk_p", "cs", "ca", "dq", "dqs", "dmi"])),
            colorer = regex_colorer({
                "yellow": suffixes2re(["cs", "ca"]),
                "orange": suffixes2re(["dq"]),
            }),
        )
        gtkw.fsm_states(soc)

def main():
    parser = argparse.ArgumentParser(description="Generic LiteX SoC Simulation")
    builder_args(parser)
    soc_sdram_args(parser)
    parser.add_argument("--sdram-verbosity",      default=0,               help="Set SDRAM checker verbosity")
    parser.add_argument("--trace",                action="store_true",     help="Enable Tracing")
    parser.add_argument("--trace-fst",            action="store_true",     help="Enable FST tracing (default=VCD)")
    parser.add_argument("--trace-start",          default=0,               help="Cycle to start tracing")
    parser.add_argument("--trace-end",            default=-1,              help="Cycle to end tracing")
    parser.add_argument("--trace-reset",          default=0,               help="Initial traceing state")
    parser.add_argument("--sys-clk-freq",         default="50e6",          help="Core clock frequency")
    parser.add_argument("--auto-precharge",       action="store_true",     help="Use DRAM auto precharge")
    parser.add_argument("--no-refresh",           action="store_true",     help="Disable DRAM refresher")
    parser.add_argument("--log-level",            default="all=INFO",      help="Set simulation logging level")
    parser.add_argument("--disable-delay",        action="store_true",     help="Disable CPU delays")
    parser.add_argument("--gtkw-savefile",        action="store_true",     help="Generate GTKWave savefile")
    parser.add_argument("--no-masked-write",      action="store_true",     help="Use LPDDR4 WRITE instead of MASKED-WRITE")
    parser.add_argument("--no-run",               action="store_true",     help="Don't run the simulation, just generate files")
    args = parser.parse_args()

    soc_kwargs     = soc_sdram_argdict(args)
    builder_kwargs = builder_argdict(args)

    sim_config = SimConfig()
    sys_clk_freq = int(float(args.sys_clk_freq))
    clocks = get_clocks(sys_clk_freq)
    clocks.add_io(_io)
    clocks.add_clockers(sim_config)

    # Configuration --------------------------------------------------------------------------------
    cpu = CPUS[soc_kwargs.get("cpu_type", "vexriscv")]
    if soc_kwargs["uart_name"] == "serial":
        soc_kwargs["uart_name"] = "sim"
        sim_config.add_module("serial2console", "serial")
    args.with_sdram = True
    soc_kwargs["integrated_main_ram_size"] = 0x0
    soc_kwargs["sdram_verbosity"]          = int(args.sdram_verbosity)

    # SoC ------------------------------------------------------------------------------------------
    soc = SimSoC(
        clocks         = clocks,
        auto_precharge = args.auto_precharge,
        with_refresh   = not args.no_refresh,
        trace_reset    = int(args.trace_reset),
        log_level      = args.log_level,
        disable_delay  = args.disable_delay,
        masked_write   = not args.no_masked_write,
        **soc_kwargs)

    # Build/Run ------------------------------------------------------------------------------------
    builder_kwargs["csr_csv"] = "csr.csv"
    builder = Builder(soc, **builder_kwargs)
    build_kwargs = dict(
        sim_config  = sim_config,
        trace       = args.trace,
        trace_fst   = args.trace_fst,
        trace_start = int(args.trace_start),
        trace_end   = int(args.trace_end)
    )
    vns = builder.build(run=False, **build_kwargs)

    if args.gtkw_savefile:
        generate_gtkw_savefile(builder, vns, trace_fst=args.trace_fst)

    if not args.no_run:
        builder.build(build=False, **build_kwargs)

if __name__ == "__main__":
    main()
