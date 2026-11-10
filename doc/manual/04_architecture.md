```{=latex}
\part{The core}
```

```{=html}
<h1 class="part">Part II. The core</h1>
```

# Core architecture {#architecture}

This chapter describes the core: the gateware between a PHY and the user logic that turns memory
requests into DRAM commands. Read it before you build a core by hand, add a port or choose the
controller settings. Banks, rows and timings are explained in [DRAM in a nutshell](#dram-primer),
the DFI in [The DRAM interface and the PHY](#dram-interface).

## At a glance {#arch-glance}

| Item | Value |
|------------------|-----------------------------------------------------------------------------|
| Top-level class | `LiteDRAMCore` (`litedram/core/__init__.py`) |
| Parts | DFI injector, controller, optional DFI ECC, crossbar |
| Inputs | A PHY instance, the geometry and the timings of a module, the `sys` frequency |
| User side | Native ports from `crossbar.get_port()`, one controller word per transfer |
| Controller word | `dfi_databits` x `nphases` bits: one DRAM burst |
| Address mapping | `ROW_BANK_COL`, with an optional minimum bank alignment |
| Memory side | DFI with one phase per DRAM clock of a controller cycle |
| Clock | `sys` for the whole core; ports may run in other clock domains |
| Software access | DFI injector registers: the BIOS initializes and calibrates the DRAM through them |

## Architecture {#arch-overview}

The core has four parts in a row, as the figure below shows. The crossbar shares the controller
between the ports. The controller turns requests into DRAM commands and schedules them. The
optional DFI ECC adds check bits on the way to the PHY. The DFI injector lets software drive the
PHY directly.

![Core architecture. Follow the cyan DFI path: the controller drives the PHY through the optional
DFI ECC and the DFI injector, which sits between the controller and the PHY so that the BIOS can
take over the DFI through registers.](arch_blocks.svg)

The core is independent of the memory type and of the FPGA family. Everything that depends on them
lives in the PHY, which presents a DFI to the core and describes itself with a settings object.
One core therefore works with every PHY of [DDR PHYs](#phys) and [LPDDR4, LPDDR5 and RPC DRAM
PHYs](#lpddr-phys).

The injector sits below the controller on purpose. During calibration, software sends commands and
reads data on the raw DFI, with the controller disconnected. The controller latencies then play no
part, so a calibration that passes does not prove them: only a memory test through the controller
does ([Initialization and calibration](#calibration)).

## Building a core {#arch-usage}

A core needs a PHY, a module and the `sys` clock frequency. In a LiteX SoC, `add_sdram` builds it
and connects the CPU; [Integration](#integration) describes that path. The example below builds the
core by hand for the DDR3 of an Arty A7, the PHY and module that `bench/arty.py` passes to
`add_sdram`.

```python
from litedram.modules           import MT41K128M16
from litedram.phy               import s7ddrphy
from litedram.core              import LiteDRAMCore
from litedram.core.controller   import ControllerSettings

# PHY: Artix-7 DDR3, 4 DFI phases (1:4).
self.ddrphy = s7ddrphy.A7DDRPHY(platform.request("ddram"),
    memtype      = "DDR3",
    nphases      = 4,
    sys_clk_freq = sys_clk_freq)

# Module: geometry, and timings in sys_clk cycles at 1:4.
module = MT41K128M16(sys_clk_freq, "1:4")

# Core: injector, controller, crossbar.
self.sdram = LiteDRAMCore(self.ddrphy,
    geom_settings       = module.geom_settings,
    timing_settings     = module.timing_settings,
    clk_freq            = sys_clk_freq,
    controller_settings = ControllerSettings(read_time=64, write_time=32))

# A port for user logic, in sys at the controller width.
port = self.sdram.crossbar.get_port()
```

The table below lists the parameters of `LiteDRAMCore`. The controller settings are described in
[Settings](#ctrl-settings). Ports are requested from the crossbar before the design is finalized.

| Parameter | Default | Meaning |
|-----------------------------|----------|-------------------------------------------------|
| `phy` | none | The PHY instance: its `dfi` and its `settings` |
| `geom_settings` | none | Banks, rows and columns of the module |
| `timing_settings` | none | Timings of the module in `sys` cycles |
| `clk_freq` | none | Frequency of `sys`, for the refresh and ZQ calibration timers |
| `with_ecc` | `False` | DFI ECC on 72-bit memories |
| `with_ecc_bit_stats` | `False` | With the DFI ECC: one error counter per DQ bit |
| `controller_settings` | defaults | A `ControllerSettings` object |

## Settings {#arch-settings}

Four settings objects describe a core. The PHY and the module fill three of them, so a user
usually writes only the fourth. The table below lists them.

| Object | Filled by | Content |
|-----------------------------|------------------------|-----------------------------------------|
| `PhySettings` | The PHY | Memory type, widths, phases, CL, CWL, latencies, calibration capabilities |
| `GeomSettings` | The module | Bank, row and column bits |
| `TimingSettings` | The module | tRP, tRCD, tWR, tWTR, tREFI, tRFC, tFAW, tCCD, tRRD, tRC, tRAS, tZQCS, tRTP |
| `ControllerSettings` | The user | Command buffers, bank machines, read and write windows, refresh, ODT, mapping |

The units differ between the objects. CL and CWL in `PhySettings` count DRAM clocks, as in the mode
registers. The read and write latencies of the PHY count `sys` cycles. Every timing of
`TimingSettings` counts `sys` cycles, rounded up by the module class; [Memory modules](#modules)
explains the conversion.

The PHY also declares its calibration capabilities: write leveling, write latency calibration,
write DQ-DQS training, read leveling, and the number of delay taps and bitslips. The core does not
use them. The generator of `sdram_phy.h` turns them into defines that select the BIOS calibration
steps ([Calibration steps](#cal-steps)).

## The controller word {#arch-data-width}

The core moves data in controller words. A word is the data of one DRAM burst: the DFI data width
of one phase times the number of phases. On DDR memories the DFI data width of a phase is twice
the DQ width, one bit per edge of the DRAM clock.

The burst length is fixed per memory type, and the PHY ratio matches it: a burst of 8 on DDR3 and
DDR4 fills the 4 phases of a 1:4 PHY. The table below gives examples.

| Memory | DQ width | Ratio | Controller word |
|-----------------------|----------|-------|-----------------|
| DDR3, one x16 chip | 16 | 1:4 | 128 bits |
| DDR2, one x16 chip | 16 | 1:2 | 64 bits |
| DDR3 or DDR4, 64-bit | 64 | 1:4 | 512 bits |

A port can use another width: the crossbar then adds a converter ([Crossbar](#fe-crossbar)). The
bandwidth of the DRAM does not change with the port width; only the bytes per transfer do.

## Address mapping {#arch-address-mapping}

A port addresses controller words, not bytes. The crossbar splits each address into a row, a bank
and a column, as the figure below shows. The bank field selects the bank machine; the bank machine
sends the row with ACT and the column with RD or WR.

![ROW_BANK_COL mapping of a port word address. Look at the bank field in the middle: consecutive
words stay in one row of one bank, and the bank changes only when the column field
wraps.](arch_address.svg)

The column field holds the column bits without the burst offset, since a word is a whole burst.
The bank machine appends zeros for the burst offset. On memories with more than 10 column bits it
also skips A10, which carries the auto-precharge flag. With several ranks, the rank bits are the
upper bits of the bank field.

On an Arty A7 with one MT41K128M16 at 1:4, the module has 14 row bits, 3 bank bits and 10 column
bits. A burst of 8 takes 3 column bits, so the port address has 7 column bits, 3 bank bits and 14
row bits: 24 bits of 16-byte words, 256 MiB.

`ROW_BANK_COL` is the only mapping (`address_mapping`). A linear stream thus fills a row of one
bank before it moves to the next bank. The `bank_byte_alignment` setting moves the bank field up to
a minimum byte distance: with `0x10000`, the bank changes every 64 KiB, the set size of a 256 KiB
4-way L2 cache.

## DFI injector {#arch-dfi-injector}

The DFI injector chooses who drives the DFI of the PHY: the controller, software or an external
DFI. It has one group of registers per DFI phase, so that software can issue any command on any
phase and read back the data. The BIOS uses it for the initialization sequence and for every
calibration step ([Initialization and calibration](#calibration)).

The `sel` field of the control register selects the source. It resets to hardware control: the
controller drives the DFI. With `sel` cleared, the per-phase registers drive it, and the control
register also drives CKE, ODT and RESET_N. The table below lists the registers of the injector.

| Register | Content |
|-----------------------------------|--------------------------------------------------------|
| `dfii_control` | `sel` (1: hardware, 0: software), `cke`, `odt`, `reset_n` |
| `dfii_pi<n>_command` | `cs`, `we`, `cas`, `ras`, `wren`, `rden`, `cs_top`, `cs_bottom` of phase n |
| `dfii_pi<n>_command_issue` | A write issues the command of phase n for one cycle |
| `dfii_pi<n>_address` | Address bus of phase n |
| `dfii_pi<n>_baddress` | Bank address bus of phase n |
| `dfii_pi<n>_wrdata` | Write data of phase n |
| `dfii_pi<n>_rddata` | Read data of phase n, captured on `rddata_valid` |

In a LiteX SoC these registers sit in the `sdram` bank (`sdram_dfii_control`). The `cs_top` and
`cs_bottom` fields select one half of a clam-shell DDR4 layout; the injector then drives two chip
selects per rank. A design can also drive the DFI from its own logic through `ext_dfi`, selected
by `ext_dfi_sel` while `sel` is set.

## DFI ECC {#arch-dfi-ecc}

Memories with an ECC byte lane, such as 72-bit DIMMs, carry 8 check bits per 64 data bits. The DFI
ECC uses them for SECDED: it corrects one wrong bit per 64-bit beat and detects two. It sits between
the controller and the injector, so the controller sees a 64-bit memory while the calibration
still sees all 72 bits.

On writes, it appends the check bits of each beat on the ECC lane. On reads, it rebuilds the
72-bit codeword, corrects it and registers the result, which adds one cycle to the read latency of
the controller. The data bits stay on DQ 0 to 63 in order, so a raw read of the data lanes is the
data.

The check bits cover a whole 64-bit word, so writes must be full words. The L2 cache of a LiteX SoC
and the BIST write full words. A frontend with partial writes needs read-modify-write, which the
AXI frontend offers ([AXI](#fe-axi)). The table below lists the registers of the DFI ECC.

| Register | Content |
|--------------------|-------------------------------------------------------------------|
| `enable` | Correction on (reset 1) |
| `clear` | A write clears the counters |
| `sec` | Beats with a corrected single-bit error |
| `ded` | Beats with a detected double-bit error |
| `bitsel`, `bitcnt` | With `with_ecc_bit_stats`: corrected errors of the DQ bit `bitsel` |

The per-bit counters cost about 4000 flip-flops on a 72-bit 1:4 PHY and stay off the data path. The
read eye scan of the BIOS CK phase leveling uses them when they exist ([Per-family
differences](#cal-families)). [Port ECC](#fe-ecc) compares this ECC with the ECC of a port.

## Clock domains {#arch-clocks}

The whole core runs in `sys`: crossbar, controller, DFI ECC and injector. The PHY runs its
serializers on faster clocks (`sys2x` or `sys4x`) and drives the DRAM clock, as the figure below
shows. A port in another clock domain gets a clock domain crossing from the crossbar.

![Clock domains. Look at the two crossings: the port CDC between user logic and `sys`, and the PHY
between `sys` and its serializer clocks.](arch_clocks.svg)

The ratio between `sys` and the DRAM clock is the number of DFI phases: 1:1 for the SDR PHY, 1:2
or 1:4 for the DDR PHYs. A 1:4 ratio lets the controller run at a quarter of the DRAM clock, at
the cost of a wider controller word.

Some PHYs go further with `DFIRateConverter`. It wraps a PHY so that the controller runs at a
lower clock with more phases: the ECP5 PHY at 1:4 is a 1:2 PHY behind this converter. The core
does not see the difference; [DDR PHYs](#phys) describes the wrappers.

## In the code {#arch-code}

| Class | File and role |
|--------------------------|----------------------------------------------------------------|
| `LiteDRAMCore` | `litedram/core/__init__.py`: injector, controller, ECC, crossbar |
| `DFIInjector` | `litedram/dfii.py`: software and external access to the DFI |
| `LiteDRAMController` | `litedram/core/controller.py`: bank machines, multiplexer, refresher |
| `LiteDRAMDFIECC` | `litedram/core/ecc.py`: SECDED on the ECC lanes |
| `LiteDRAMCrossbar` | `litedram/core/crossbar.py`: ports, arbitration, address mapping |
| `PhySettings` | `litedram/common.py`: settings objects and the native port |
| `Interface` | `litedram/phy/dfi.py`: DFI record, `DFIRateConverter` |

Where to go next: [Controller](#controller) for the command scheduling, [Ports and
frontends](#frontends) for the user side, [Initialization and calibration](#calibration) for the
software side.
