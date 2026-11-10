# Examples and targets {#examples}

This chapter describes the ready-made designs of the repository: the generator examples of
`examples/`, the bench targets of `bench/` with their frequency sweep, and the mode register
helpers. Use them to check a board, to start a configuration of your own, or to find the margin of
a memory interface.

## At a glance {#ex-glance}

Each example is a YAML file for the generator (`litedram_gen`), `examples/<name>.yml`: one board,
one PHY, one memory. The generator turns it into a standalone Verilog core with its initialization
firmware.

| Example | Board | PHY | Memory | Width |
|--------------------------------------|-------------------|-----------------------|------------|-----------|
| `ulx3s` | ULX3S | `GENSDRPHY` | SDR | 16 bits |
| `versa_ecp5` | Versa ECP5 | `ECP5DDRPHY` | DDR3 | 16 bits |
| `tang_primer_20k` | Tang Primer 20K | `GW2DDRPHY` | DDR3 | 16 bits |
| `tang_mega_138k_pro` | Tang Mega 138K Pro | `GW5DDRPHY` | DDR3 | 16 bits |
| `nexys4ddr` | Nexys4DDR | `A7DDRPHY` | DDR2 | 16 bits |
| `arty` | Arty A7 | `A7DDRPHY` | DDR3 | 16 bits |
| `genesys2` | Genesys2 | `K7DDRPHY` | DDR3 | 32 bits |
| `kcu105` | KCU105 | `USDDRPHY` | DDR4 | 64 bits |
| `xcu1525` | XCU1525 | `USPDDRPHY` | DDR4 | 64 bits |

The width is eight bits per byte group (`sdram_module_nb`). The second table gives the module and
the clocks. The generator selects the frequency ratio from the PHY and the memory type; the DRAM
data rate is computed here from it, since the YAML files do not state it.

| Example | Module | sys_clk | Ratio | Data rate |
|-----------------------------------|-----------------------------------|-------------|----------|---------|
| `ulx3s` | `MT48LC16M16` | 50 MHz | 1:1 | 50 MT/s |
| `versa_ecp5` | `MT41K64M16` | 50 MHz | 1:2 | 200 MT/s |
| `tang_primer_20k` | `IMD128M16R39CG8GNF` | 48 MHz | 1:2 | 192 MT/s |
| `tang_mega_138k_pro` | `H5TQ4G63EFR` | 50 MHz | 1:2 | 200 MT/s |
| `nexys4ddr` | `MT47H64M16` | 100 MHz | 1:2 | 400 MT/s |
| `arty` | `MT41K128M16` | 100 MHz | 1:4 | 800 MT/s |
| `genesys2` | `MT41J256M16` | 100 MHz | 1:4 | 800 MT/s |
| `kcu105` | `EDY4016A` | 150 MHz | 1:4 | 1200 MT/s |
| `xcu1525` | `MT40A512M8` | 150 MHz | 1:4 | 1200 MT/s |

The data rate is the system clock times the number of DFI phases, times two for the double data
rate memories. Every example runs the `vexriscv` CPU except `ulx3s`, which runs `serv`. The
boards are described in [Supported FPGAs and boards](#boards), and
[Build options](#build-options) lists every key of the YAML files.

## Generating an example {#ex-generate}

The generator reads the YAML file, elaborates the core and writes the Verilog, the register map
and the software headers. It never runs the FPGA toolchain: the project that integrates the core
synthesizes it.

```sh
# Core, firmware and headers in build/ (RISC-V GCC needed for the firmware)
litedram_gen examples/arty.yml
# Same without compiling the firmware, with the register map
litedram_gen examples/arty.yml --no-compile --csr-csv csr.csv --output-dir build/arty
# Same core around the DFI-level DRAM model, for a testbench
litedram_gen examples/arty.yml --sim --no-compile --output-dir build/arty_sim
```

| Output | Content |
|----------------------------------------------------------------------|--------------------------------|
| `gateware/litedram_core.v` | The core: PHY, controller, user ports, CPU and its ROM |
| `gateware/litedram_core.xdc` | False paths of the reset synchronizers (Vivado) |
| `gateware/litedram_core_rom.init` | Contents of the ROM: the initialization firmware |
| `software/include/generated/` | `csr.h`, `soc.h`, `mem.h` and `sdram_phy.h` |

With `--no-compile` the firmware is not built and the ROM of the core stays empty: use it to check
an elaboration or to get the register map, not to run on a board. With `--sim` the core has no
vendor primitive and no build script; [Simulation and verification](#simulation) shows how to use
it.

The test `test/test_examples.py` runs the generator on the nine examples, firmware included, so it
needs the RISC-V GCC toolchain. It is the quickest check that a change of the core still builds
with every PHY of the generator.

## What each example shows {#ex-details}

The examples share their structure: general keys, PHY and module, electrical settings, clocks, then
the user ports. They differ in the points below.

**User ports.** `arty.yml` has one port of each type: AXI, Wishbone, Avalon-MM, native and FIFO.
`genesys2.yml`, `kcu105.yml`, `ulx3s.yml`, `nexys4ddr.yml`, `versa_ecp5.yml` and `xcu1525.yml` have
the same ports without Avalon-MM. The Gowin examples have a single port: Wishbone on the Tang Primer 20K, AXI on the
Tang Mega 138K Pro.

**ECC on a port.** The AXI port of `kcu105.yml` sets `ecc: true` with a 256-bit `data_width`. The
generator then puts the port ECC between the AXI bridge and the crossbar, and the AXI bridge does a
read-modify-write for partial writes ([Ports and frontends](#frontends)).

**SDR clocking.** `ulx3s.yml` runs the SDRAM at 50 MHz from the 25 MHz board clock. The PLL of the
core makes the system clock and drives the `sdram_clk` output 90 degrees after it
(`sdram_clk_phase`). It is the only example with the `serv` CPU.

**Lattice and Gowin devices.** The ECP5 and Gowin examples name the device (`device`), and the Gowin
ones also the device name for the PLL (`devicename`). `versa_ecp5.yml` sets the clock of the ECP5
initialization logic (`init_clk_freq`).

The Gowin examples turn the DRAM termination off (`rtt_nom: disabled`). The Tang Mega 138K Pro runs
its DDR3 in DLL-off mode (`dll_off`, CL6 and CWL6), at 1:2 (`sdram_rate`).

**UltraScale(+) and DDR4.** The two DDR4 examples set a command latency of one cycle
(`cmd_latency`) and their own termination values. `xcu1525.yml` lists the read VREF scan
(`with_hpio_vref`, `hpio_vref_tune`) and the DFI ECC (`with_ecc`, `with_ecc_bit_stats`), all
disabled: they show where the keys go.

**DDR2.** `nexys4ddr.yml` is the only DDR2 example. It has no electrical keys: the generator
applies them to DDR3 and DDR4 only.

## Bench targets {#ex-bench}

The targets of `bench/` build a complete LiteX SoC around the core for one board, with the BIOS in a
writable ROM and remote access to the registers. They exist to test the PHYs on hardware: run the
calibration, read its log and sweep the clock frequency.

| Target | Board | PHY | Module | Width | Remote access |
|-------------------|---------------|---------------------|------------------------|----------|----------------|
| `arty` | Arty A7 | `A7DDRPHY` | `MT41K128M16` | 16 bits | UARTBone, Etherbone (MII) |
| `genesys2` | Genesys2 | `K7DDRPHY` | `MT41J256M16` | 32 bits | UARTBone, Etherbone (RGMII) |
| `kc705` | KC705 | `K7DDRPHY` | `MT8JTF12864` | 64 bits | UARTBone, Etherbone |
| `kcu105` | KCU105 | `USDDRPHY` | `EDY4016A` | 64 bits | UARTBone, Etherbone (SFP) |
| `xcu1525` | XCU1525 | `USPDDRPHY` | `MT40A512M8` | 64 bits | UARTBone |

All the targets run the system clock at 125 MHz with a 1:4 PHY, so the DRAM runs at 1000 MT/s
(computed). The KC705 module is a DDR3 SO-DIMM. The XCU1525 target uses one of the four DDR4
channels of the board, selected with `--channel`. The design is the same on every target:

- A first PLL makes the system clock, the reference clock of the delays and the clock of the
  bridges; its reconfiguration port is exposed as registers.
- A second PLL, fed by the first one, makes the system clock and the fast clocks of the PHY.
- The BIOS console is a crossover UART (`--uart crossover`, the default), read through a bridge;
  `--uart serial` puts it on the serial pins instead.
- A counter of system clock cycles (`crg_sys_clk_counter`) lets the host measure the clock.
- The 64 KiB ROM is writable, so that a new BIOS loads without a new bitstream.

```sh
# Build and load the bitstream (volatile: the flash is not written)
python3 bench/kc705.py --build --load
# Open the BIOS console through the Ethernet bridge
litex_server --udp &
litex_term crossover
```

Without `--build`, a target only elaborates the SoC and compiles its BIOS; the five targets do so
with the LiteX-Boards platforms of their boards. `--with-bist` and
`--with-analyzer` add the hardware tests and the DFI analyzer that [Debugging](#debugging) uses;
`--load-bios`, `--sys-clk-freq` and `--test` act on a running board through the bridge. [Bench
target options](#opt-bench) lists every option.

## Frequency sweep {#ex-sweep}

The calibration finds windows at one frequency; the sweep shows how they move and where they
close. With `--test`, the target reprograms the system clock step by step on a running board and
logs a complete BIOS boot at each step. The bridge (`litex_server`) must be running.

1. Load the BIOS of the build into the ROM and reboot the SoC.
2. Read the output divider of the first PLL through its reconfiguration port.
3. For each frequency of the range, compute the divider of the PLL output; skip it when that
   divider was already tested.
4. Write the new divider, measure the system clock with `crg_sys_clk_counter` over 0.5 s and print
   it.
5. Reboot the SoC and print the BIOS output, read from the crossover UART, for 40 s.

| Target | Range | Step |
|-------------------------------------------|--------------------------------------|----------------------|
| `arty` | 60 to 149 MHz | 1 MHz |
| `genesys2` | 60 to 179 MHz | 1 MHz |
| `kc705` | 60 to 179 MHz | 1 MHz |
| `kcu105` | 80 to 179 MHz | 1 MHz |
| `xcu1525` | 80 to 179 MHz | 1 MHz |

Only distinct dividers are tested, so the real steps are coarser than 1 MHz at high frequency. The
second PLL follows the first one, so all the clocks of the PHY move together.

Each target computes the dividers from the VCO of the first PLL (`main_pll`), the one it
reprograms. Each step prints the measured system clock and the whole calibration log, which
[Reading the boot log](#debug-boot-log) explains.

```sh
python3 bench/genesys2.py --test | tee sweep.log
```

## Mode register helpers {#ex-mr-gen}

Two scripts compute the DDR3 and DDR4 mode registers for given latencies and terminations, and
print them as `sdram_mr_write` commands for the BIOS. They help to try another termination on a
running board without a rebuild. The output below is the DDR3 script run with CL 7 and CWL 6.

```console
$ python3 bench/ddr3_mr_gen.py --cl 7 --cwl 6
DDR3 Timing Settings:
cl:  7
cwl: 6
DDR3 Electrical Settings:
rtt_nom: 60ohm (RZQ/4)
rtt_wr:  60ohm (RZQ/4)
ron:     34ohm (RZQ/7)
Commands to be used with LiteX BIOS:
sdram_mr_write 0 2608
sdram_mr_write 1 2054
sdram_mr_write 2 520
```

`--list` prints the supported values. The DDR3 script writes a burst length of 8 and a write
recovery of 10 cycles into MR0. The DDR4 script prints MR0 to MR2 the same way; its defaults are
CL 9, CWL 9, `40ohm` and `120ohm`.

A new CL or CWL in the DRAM does not change the read and write latencies of the PHY, which are
fixed at build time; the helpers are safest for the terminations. [Forcing settings from the
BIOS](#debug-force) lists the other settings that change at run time.

## LiteX-Boards targets {#ex-litex-boards}

Most boards with a DRAM have a target in LiteX-Boards, outside this repository; it adds the PHY and
the module with `add_sdram`. Elaborating one of them is a quick check of a change of the core on a
board family:

```sh
python3 -m litex_boards.targets.digilent_arty --build --no-compile
```

Where to go next: [Getting started](#getting-started) for a first build, [Integration](#integration)
for a design of your own, and [Debugging](#debugging) for the boot log of a bench target.
