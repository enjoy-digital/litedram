```{=latex}
\part{Use it}
```

```{=html}
<h1 class="part">Part IV. Use it</h1>
```

# Supported FPGAs and boards {#boards}

This chapter lists the FPGA families and memory types that LiteDRAM supports, the boards that
use it, and what a board of your own needs to run it. Read it before choosing hardware, or before
drawing the DRAM part of a schematic.

## At a glance {#boards-glance}

LiteDRAM has one PHY per FPGA family and memory type, and a generic SDR PHY that runs on any
FPGA. The table below gives the PHY class of each family, its memory types and its frequency
ratios; [DDR PHYs](#phys) describes each PHY.

| FPGA family | PHY class | Memory | Ratio | Status |
|-------------------|-----------------------------------|--------------|---------|----------------|
| Any FPGA | `GENSDRPHY` | SDR | 1:1 | Validated |
| Any FPGA | `HalfRateGENSDRPHY` | SDR | 1:2 | Validated |
| Spartan-6 | `S6HalfRateDDRPHY` | DDR, LPDDR, DDR2, DDR3 | 1:2 | No calibration |
| Spartan-6 | `S6QuarterRateDDRPHY` | DDR3 | 1:4 | No calibration |
| Artix-7, Spartan-7 | `A7DDRPHY` | DDR2, DDR3 | 1:2, 1:4 | Validated |
| Kintex-7 | `K7DDRPHY` | DDR2, DDR3 | 1:2, 1:4 | Validated |
| Virtex-7 | `V7DDRPHY` | DDR2, DDR3 | 1:2, 1:4 | Validated |
| Kintex UltraScale | `USDDRPHY` | DDR3, DDR4 | 1:4 | Validated (DDR4) |
| Kintex/Virtex UltraScale+ | `USPDDRPHY` | DDR3, DDR4 | 1:4 | Validated (DDR4) |
| Altera Cyclone V | `CycloneVDDRPHY` | DDR3 | 1:4 | Validated on Cyclone V GT DDR3B |
| Lattice ECP5 | `ECP5DDRPHY` | DDR3 | 1:2, 1:4 | Validated |
| Lattice Nexus (CrossLink-NX, Certus-NX) | `NexusDDRPHY` | DDR3 | 1:2 | Validated |
| Gowin GW2A | `GW2DDRPHY` | DDR3 | 1:2 | Validated |
| Gowin GW5A | `GW5DDRPHY` | DDR3 | 1:2, 1:4 | Validated |
| Artix-7, Kintex-7, Virtex-7 | LPDDR4, LPDDR5 PHYs | LPDDR4, LPDDR5 | see Part III | In development |
| Artix-7 | `A7RPCPHY` | RPC DRAM | 1:4 | In development |

"Validated" means that a design with this PHY runs on hardware, calibration and memory test
included. The SDR PHY is vendor-neutral: LiteX-Boards uses it on Intel, Efinix and Gowin devices
as well as on AMD and Lattice ones.

The Spartan-6 PHYs have no calibration at boot: their delays and bitslips are set when the design
is built and may need adjustments for a board.

The 7-Series PHYs run DDR3 at 1:4 only; DDR2 runs at 1:2 or 1:4. Their class accepts DDR4 in its
checks, but its header and the README list DDR2 and DDR3 only. The LPDDR4, LPDDR5 and RPC DRAM
PHYs are described in [LPDDR4, LPDDR5 and RPC DRAM PHYs](#lpddr-phys). DDR5 and HBM are not
supported.

## How a board gets DRAM {#boards-litex-boards}

Most users meet LiteDRAM through LiteX-Boards, the collection of LiteX platforms and targets.
More than 140 of its targets instantiate a LiteDRAM PHY. A target creates the clocks, the PHY and
the module of its board, then calls `add_sdram` of the LiteX SoC, which builds the core and maps
the DRAM as the main RAM of the CPU.

Building a target therefore gives a complete SoC with the DRAM initialized by the BIOS at boot.
The command below builds and loads the Arty A7 target, the board of [Getting
started](#getting-started):

```sh
python3 -m litex_boards.targets.digilent_arty --build --load
```

Most targets leave the DRAM out when the main RAM is made of on-chip memory, with
`--integrated-main-ram-size`. This helps to bring up the rest of a board before the DRAM, or to
build with a toolchain that does not support the DRAM PHY of the family.

## Representative boards {#boards-representative}

The boards below cover every validated PHY and every memory type. Each one has a target in
LiteX-Boards, named after its vendor and board: `digilent_arty` for the Arty A7, `xilinx_kc705`
for the KC705, `lambdaconcept_ecpix5` for the ECPIX-5. The widths are those of the data bus of the
board.

| Board | Memory | Module | PHY |
|------------------|---------------|----------------------------|----------------------|
| Arty A7 | DDR3, 16-bit | `MT41K128M16` | `A7DDRPHY` |
| Nexys4DDR | DDR2, 16-bit | `MT47H64M16` | `A7DDRPHY` |
| Acorn CLE-215+ | DDR3, 16-bit | `MT41K512M16` | `A7DDRPHY` |
| Genesys2 | DDR3, 32-bit | `MT41J256M16` | `K7DDRPHY` |
| KC705 | DDR3 SO-DIMM, 64-bit | `MT8JTF12864` | `K7DDRPHY` |
| YPCB-00338-1P1 | DDR3, 72-bit | `MT41K256M8` | `K7DDRPHY` |
| KCU105 | DDR4, 64-bit | `EDY4016A` | `USDDRPHY` |
| XCU1525 | DDR4 DIMMs, 64-bit | `MT40A512M8` | `USPDDRPHY` |
| Cyclone V GT Development Kit | DDR3B, 64-bit | 4 × `MT41K128M16` | `CycloneVDDRPHY` |
| ECPIX-5 | DDR3, 16-bit | `MT41K256M16` | `ECP5DDRPHY` |
| Cam Link 4K | DDR3, 16-bit | `MT41K64M16` | `ECP5DDRPHY` |
| ULX3S | SDR, 16-bit | `MT48LC16M16` | `GENSDRPHY` |
| Colorlight 5A-75B | SDR, 32-bit | `M12L16161A` | `GENSDRPHY` |
| Certus-NX Versa | DDR3, 16-bit | `MT41K64M16` | `NexusDDRPHY` |
| Tang Primer 20K | DDR3, 16-bit | `IMD128M16R39CG8GNF` | `GW2DDRPHY` |
| Tang Mega 138K Pro | DDR3, 32-bit | `H5TQ4G63EFR` | `GW5DDRPHY` |

Several targets select their PHY options on the command line. The ECPIX-5 and Cam Link 4K
targets take `--sdram-rate 1:4` for the ECP5 PHY at 1:4, and the Tang Mega 138K Pro target takes
`--ddr3-rate`. The ULX3S target selects another SDR chip with `--sdram-module`, and the XCU1525
target one of its four DIMM channels with `--ddram-channel`.

The Cyclone V GT Development Kit's native DDR3B PHY passed BIOS memtest and LiteDRAM BIST at
600 MT/s.
[Altera Cyclone V](#phys-cyclone-v) describes the PHY datapath.

The YPCB-00338-1P1 target drives its 72-bit DDR3 from the HR banks of a Kintex-7, with the CK
phase write leveling of the 7-Series PHY. [DDR PHYs](#phys) explains this mode.

The Acorn CLE-215+, shown below, is an Artix-7 board on an M.2 form factor with a 16-bit DDR3. It
is a low cost board to try the 7-Series PHY.

![The SQRL Acorn CLE-215+, an Artix-7 board with a 16-bit DDR3, next to a coin for
scale.](acorn_cle215.jpg){width=60%}

The Colorlight 5A-75B, shown below, is a Lattice ECP5 board with a 32-bit SDR SDRAM, driven by the
generic SDR PHY. Its target, `colorlight_5a_75x`, selects the chip from the board revision.

![The Colorlight 5A-75B, a Lattice ECP5 board with SDR SDRAM.](colorlight_5a75b.jpg){width=70%}

## Bench targets of this repository {#boards-bench}

The `bench/` directory holds five targets that test LiteDRAM itself, on the Arty A7, Genesys2,
KC705, KCU105 and XCU1525. Each one is a LiteX SoC with the DRAM of its board and a bridge to its
registers, with options for the BIST, a LiteScope analyzer on the DFI and a frequency sweep.
[Bench targets](#ex-bench) describes them.

The YAML files of `examples/` configure the generator for nine boards, from the ULX3S to the
XCU1525; [Examples and targets](#examples) lists them too.

## Requirements for a custom board {#boards-custom}

A board of your own needs three things for LiteDRAM: the DRAM pins on suitable FPGA pins, the IO
standards, termination and reference voltage of the memory type, and the clocks of the PHY. The
quickest way is to start from a LiteX-Boards platform with the same FPGA family and memory type.

### Pinout {#boards-pinout}

The figure below shows the signal groups between the FPGA and a DDR3 DRAM. The clock, the command
and address pins and the control pins go from the PHY to the DRAM. The data pins are bidirectional
and grouped in byte lanes of eight DQ pins, each with its own DM pin and DQS strobe pair.

![Signals of a DDR3 interface. The cyan arrows are the byte lanes, one per 8 data bits; the other
groups go one way, from the PHY to the DRAM. The VREF supply feeds the FPGA bank and the
DRAM.](boards_pinout.svg)

A platform describes these pins as one record, `ddram` for DDR memories and `sdram` for SDR, with
the subsignal names below. The PHY takes the record from `platform.request()`.

| Memory | Subsignals |
|------------|------------------------------------------------------------------------------|
| SDR | `a`, `ba`, `ras_n`, `cas_n`, `we_n`, `cs_n`, `dm`, `dq`, `cke`; the clock pin is separate |
| DDR2, DDR3 | `a`, `ba`, `ras_n`, `cas_n`, `we_n`, `cs_n`, `dm`, `dq`, `dqs_p`, `dqs_n`, `clk_p`, `clk_n`, `cke`, `odt`, `reset_n` |
| DDR4 | as DDR3, plus `bg` and `act_n` |

The PHY captures the data of each byte lane with the strobe of that lane, as [The DRAM interface
and the PHY](#dram-interface) explains. Place the DQ, DM and DQS pins of a lane as the FPGA vendor
requires for a memory byte group, and the DRAM clock on a pair that can drive a differential
output.

Some PHYs add rules of their own:

- **Artix-7 and Kintex-7 HR banks** have no output delay line. `A7DDRPHY`, and `K7DDRPHY` with
  `with_odelay=False`, then take the strobe from a 90 degree clock of the clock generator.
- **ECP5** command pins with the default `cmd_gearing` (`x2`) need the left or right banks; the
  experimental `x1` gearing also allows the top banks.
- **Fewer byte lanes**: `PHYPadsReducer` keeps only some byte lanes of a record, as
  `bench/arty.py` does; `PHYPadsCombiner` joins chips with separate command buses into one
  controller.

### IO standards, VREF and termination {#boards-vref}

The FPGA side needs the IO standard of the memory type, the input termination of the data pins
and a reference voltage for the input receivers. LiteDRAM sets none of them: the platform of the
board does. The examples below come from LiteX-Boards platforms.

- **Arty A7, DDR3L**: `SSTL135`, with `DIFF_SSTL135` on the clock and strobe pairs, an internal
  split termination of 40 ohm on DQ and DQS (`IN_TERM=UNTUNED_SPLIT_40`), and
  `INTERNAL_VREF 0.675` on bank 34.
- **KC705, DDR3**: `SSTL15`, with the DCI variant `SSTL15_T_DCI` on the data pins.
- **KCU105, DDR4**: `SSTL12_DCI` on the command pins, `POD12_DCI` on the data pins, and
  `INTERNAL_VREF 0.84` on banks 44 to 46.
- **ECPIX-5, DDR3**: `SSTL15_I`, `TERMINATION=75` on DQ, and a 100 ohm differential resistor on
  DQS.

The DRAM side has its own termination and driver strength, set in its mode registers at
initialization. The defaults are 60 ohm for both terminations and 34 ohm for the driver on DDR3;
DDR4 uses 40 ohm, 120 ohm and 34 ohm. [Integration in a LiteX SoC](#integ-litex) shows how to
change them.

### Clocks {#boards-clocks}

The board needs an oscillator on a clock input of the FPGA; a PLL of the FPGA makes every clock
of the PHY from it. The 7-Series and UltraScale PHYs also need a reference clock for their delay
lines: 200 MHz on the Arty A7, at least 300 MHz on UltraScale+. [Clocks and
constraints](#integ-clocks) lists the clocks of each PHY.

An SDR SDRAM needs a phase-shifted copy of the system clock on its clock pin, which the clock
generator of the target makes. Without it, the reads have no timing margin.

Where to go next: [Getting started](#getting-started) to run a first board,
[Integration](#integration) to add LiteDRAM to your own design, [Memory modules](#modules) to
describe a new chip.
