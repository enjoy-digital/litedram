# Getting started {#getting-started}

This chapter takes you from a fresh machine to a board that calibrates its DRAM and passes a
memory test. It installs the tools, checks them without hardware, runs a simulated SoC with DRAM,
then builds and loads the Arty A7 target. Each step gives the commands, what you should see, and
what to check when you do not.

## Prerequisites {#gs-install}

LiteDRAM is a Python package built on LiteX and needs Python 3.7 or newer. Install LiteX by
following the installation page of its wiki (`litex_setup.py`): it installs Migen, LiteX,
LiteX-Boards and the cores, LiteDRAM included. To work on a clone of the repository, install it
in development mode:

```sh
git clone https://github.com/enjoy-digital/litedram
cd litedram
pip3 install -e .
```

The other tools depend on what you run. The table below lists them.

| Task | Tools |
|------------------------------|------------------------------------------------------------------|
| Unit tests | Python 3, pytest |
| Simulated SoC (`litex_sim`) | Verilator, a C++ compiler, libevent, json-c, RISC-V GCC |
| Generator with a CPU | The RISC-V GCC toolchain, meson and ninja for the BIOS |
| AMD 7-Series, UltraScale(+) | Vivado |
| Lattice ECP5 | Yosys, nextpnr and Trellis |
| Lattice Nexus | Radiant |
| Gowin GW2A, GW5A | Gowin IDE |
| Loading over JTAG | The programmer of the platform: OpenOCD or openFPGALoader |
| Serial console | `litex_term`, installed with LiteX |

`litex_setup.py --gcc=riscv` installs the RISC-V GCC toolchain, as the continuous integration of
the repository does.

## Step 1: check the installation {#gs-check}

The unit tests check the controller, the frontends, the PHYs and the initialization sequences in
Migen simulation, with no board and no FPGA tool. The selection below is the one of the fast
"unit" job of the continuous integration: it leaves out the generator tests, which compile the
BIOS, and the long LPDDR4 and LPDDR5 simulations.

```sh
python3 -m pytest test \
    --ignore=test/test_examples.py \
    --ignore=test/test_lpddr4.py \
    --ignore=test/test_lpddr5.py
```

`python3 -m pytest test` runs the whole suite. It needs the RISC-V GCC toolchain and Verilator,
and takes much longer; [Unit tests](#sim-tests) describes it.

The generator can then elaborate a standalone core without any vendor tool. With `--no-compile`,
it writes the Verilog and the register map, and stops before the BIOS and the gateware builds.

```sh
litedram_gen examples/arty.yml --no-compile \
    --output-dir build/arty --csr-csv build/arty/csr.csv
```

**What you should see.** All selected tests pass. The generator writes
`build/arty/gateware/litedram_core.v` and `build/arty/csr.csv`, whose register names start with
`ddrphy`, `sdram` and `ddrctrl`.

**If not.** An import error names the missing package: LiteX for `litex`, PyYAML for the YAML
reader of the generator. Rerun the LiteX installation or `pip3 install -e .`.

## Step 2: simulate a SoC with DRAM {#gs-sim}

`litex_sim` builds a LiteX SoC with a VexRiscv CPU and runs it in Verilator. With `--with-sdram`,
its main RAM is a DRAM behind a LiteDRAM core, with a simulation model in place of the PHY and the
chip. The BIOS initializes this DRAM and tests it as on a board.

```sh
litex_sim --with-sdram
```

**What you should see.** The simulation compiles, then the BIOS banner and the initialization
appear in the terminal. The capture below comes from the LiteX documentation; the banner of the
BIOS is cut.

```console
--================ SoC =================--
CPU:		VexRiscv @ 1MHz
BUS:		wishbone 32-bit data/32-bit addr
CSR:		32-bit data big ordering
ROM:		128.0KiB
SRAM:		8.0KiB
L2:		8.0KiB
SDRAM:		64.0MiB 32-bit @ 1MT/s (CL-2 CWL-2)
MAIN RAM:	64.0MiB
--=========== Initialization ===========--
Initializing SDRAM @0x40000000...
Switching SDRAM to software control.
Switching SDRAM to hardware control.
Memtest at 0x40000000 (8.0KiB)...
Memtest OK
Memspeed at 0x40000000 (Sequential, 8.0KiB)...
  Write speed: 1.6MiB/s
   Read speed: 491.5KiB/s
[...]
litex>
```

The `SDRAM` line gives the size, the data width, the data rate and the latencies of the memory:
here an SDR chip, `MT48LC16M16` by default, on a 32-bit bus. The simulation runs at a nominal
1 MHz, so its rate and its speeds mean nothing. The model has no calibration, so no leveling
appears between the two "Switching" lines.

**If not.** A Verilator or compiler error stops the build: check that Verilator and the RISC-V
toolchain are in the `PATH`. `--sdram-module` selects another chip from `litedram/modules.py`,
and [Simulation and verification](#simulation) lists the other options.

## Step 3: build the Arty A7 target {#gs-build}

The Arty A7 has a 16-bit DDR3L chip, an `MT41K128M16`, driven by `A7DDRPHY` at 1:4. Its
LiteX-Boards target runs the system clock at 100 MHz by default, so the DDR3 runs at 400 MHz,
800 MT/s. The command below builds the SoC with its default CPU, VexRiscv.

```sh
python3 -m litex_boards.targets.digilent_arty --build
```

**What you should see.** LiteX writes the Verilog and compiles the BIOS, then Vivado synthesizes
and implements the design. The bitstream is `build/digilent_arty/gateware/digilent_arty.bit`.

**If not.** Vivado reports its errors in the logs of `build/digilent_arty/gateware`. The A7-100
version of the board needs `--variant a7-100`. Without Vivado, `--build --no-compile` writes the
Verilog of the SoC and stops before the BIOS and the Vivado builds.

## Step 4: load the board and open the console {#gs-load}

Connect the USB cable of the Arty A7: it carries both the JTAG and the UART of the board. Load the
bitstream, then open the serial console of the BIOS, at 115200 baud by default.

```sh
python3 -m litex_boards.targets.digilent_arty --load
litex_term /dev/ttyUSBx
```

`--load` programs the FPGA through JTAG with OpenOCD. It writes the volatile configuration memory
only: a power cycle brings back the bitstream of the flash. `/dev/ttyUSBx` stands for the serial
port of the board. Press the reset button of the board, or type `reboot`, to see the boot again.

**What you should see.** The BIOS banner, then the description of the SoC and the initialization
of the DRAM. The capture below was made on an Arty A7 at 800 MT/s, with a Cortex-M1 CPU in place
of VexRiscv; the banner is cut.

```console
--=============== SoC ==================--
CPU:		ARM Cortex-M1 @ 100MHz
BUS:		WISHBONE 32-bit @ 4GiB
CSR:		32-bit data
ROM:		128KiB
SRAM:		8KiB
L2:		8KiB
SDRAM:		262144KiB 16-bit @ 800MT/s (CL-7 CWL-5)

--========== Initialization ============--
Initializing SDRAM @0x10000000...
Switching SDRAM to software control.
Read leveling:
  m0, b00: |00000000000000000000000000000000| delays: -
  m0, b01: |00000000000000000000000000000000| delays: -
  m0, b02: |11111111110000000000000000000000| delays: 05+-05
  m0, b03: |00000000000011111111111111000000| delays: 19+-07
  m0, b04: |00000000000000000000000000011111| delays: 30+-02
  m0, b05: |00000000000000000000000000000000| delays: -
  m0, b06: |00000000000000000000000000000000| delays: -
  m0, b07: |00000000000000000000000000000000| delays: -
  best: m0, b03 delays: 19+-07
  m1, b00: |00000000000000000000000000000000| delays: -
  m1, b01: |00000000000000000000000000000000| delays: -
  m1, b02: |11111111110000000000000000000000| delays: 05+-05
  m1, b03: |00000000000011111111111111000000| delays: 19+-07
  m1, b04: |00000000000000000000000000001111| delays: 30+-02
  m1, b05: |00000000000000000000000000000000| delays: -
  m1, b06: |00000000000000000000000000000000| delays: -
  m1, b07: |00000000000000000000000000000000| delays: -
  best: m1, b03 delays: 19+-07
Switching SDRAM to hardware control.
Memtest at 0x10000000 (2.0MiB)...
  Write: 0x10000000-0x10200000 2.0MiB
   Read: 0x10000000-0x10200000 2.0MiB
Memtest OK
Memspeed at 0x10000000 (Sequential, 2.0MiB)...
  Write speed: 16.5MiB/s
   Read speed: 19.3MiB/s
```

**If not.** A silent console points to the bitstream or the serial port: load the board again,
try the other serial port of the board (its USB chip shows two), and check the 115200 baud. A
calibration that fails is the subject of [If the calibration fails](#gs-failures).

## Step 5: read the calibration output {#gs-calibration}

The BIOS first takes control of the DRAM through software registers, sends the JEDEC
initialization sequence, then calibrates the PHY. `A7DDRPHY` has no write leveling, so its
calibration is the read leveling alone. [Initialization and calibration](#calibration) describes
every step and the PHYs that run them.

The read leveling tunes each byte lane, `m0` and `m1` on this 16-bit bus. For each bitslip, `b00`
to `b07`, it sweeps the 32 taps of the input delay line and reads a test pattern back. Each
character of a line is one tap: `1` when the pattern came back right, `0` when it did not.

The `delays` field gives the center of the longest run of passing taps and its half-width:
`19+-07` is a window of about 14 taps centered on tap 19. The `best` line is the bitslip kept for
the lane, the one with the best window. A window of several taps on every lane is a healthy
result.

After the calibration, the BIOS hands the DRAM back to the controller and runs a memory test and a
speed test through the CPU. "Memtest OK" means that the data written through the whole path, from
the CPU to the DRAM and back, read back right. The speeds are in MiB/s, as the BIOS prints them.

The speeds measure the CPU and its caches more than the DRAM: they change with the CPU and the L2
size, so do not compare them across SoCs. The address, `0x10000000` here, is the main RAM base of
the CPU; it is `0x40000000` with VexRiscv.

## Step 6: test from the console {#gs-console}

The BIOS has commands to test the DRAM again and to rerun its initialization. The addresses below
assume VexRiscv, with the main RAM at `0x40000000`; `mem_list` prints the memory map of your SoC.

```console
litex> mem_list
litex> mem_test 0x40000000 0x1000000
litex> mem_speed 0x40000000 0x1000000
litex> sdram_init
```

`mem_test <addr> [maxsize]` writes and reads back a pattern over a range, 16 MiB here, and ends
with "Memtest OK" or "Memtest KO" and error counts. `mem_speed <addr> <size> [readonly] [random]`
measures the write and read speeds. `sdram_test` tests a 32nd of the main RAM, and `sdram_init`
reruns the initialization and the calibration.

`sdram_cal` reruns the calibration alone. The bench target `bench/arty.py` builds the same board
with `--with-bist`, which adds `sdram_bist` and `sdram_hw_test`: hardware tests that measure the
DRAM without the CPU in the path. [Examples and targets](#examples) describes it.

## If the calibration fails {#gs-failures}

A failed initialization ends with "Memtest KO" and the error counts, then "Memory
initialization failed". The calibration output tells where to look. The list below gives the
usual cases on a board of LiteX-Boards; [Debugging](#debugging) goes further.

- **No window at all**: every line reads `delays: -`. The DRAM does not answer: check that the
  board variant, the module and the system clock of the target match the hardware. On a board of
  your own, check the pinout, the IO standards and the VREF ([Requirements for a custom
  board](#boards-custom)).
- **Windows on some lanes only**: one byte lane has no window. Suspect the pins, the termination
  or the strobe of that lane.
- **Windows everywhere, but "Memtest KO"**: the calibration passes but the data is wrong through
  the controller. The calibration runs through software registers and does not check the latencies
  of the controller; a memory test does.
- **Narrow windows or memory errors that come and go**: the interface runs close to its limit.
  Lower the system clock with `--sys-clk-freq`, which lowers the DRAM rate with it, and compare.

The [Troubleshooting](#debug-troubleshooting) table of the Debugging chapter lists the other
symptoms, with the first thing to check for each.

## Step 7: generate a standalone core {#gs-standalone}

The same Arty A7 configuration exists as a standalone Verilog core, for designs built without
LiteX. `examples/arty.yml` describes the DRAM, the PHY, the clocks and five user ports, one of
each type.

```sh
litedram_gen examples/arty.yml
```

**What you should see.** The generator compiles the firmware of the core and writes the Verilog
in `build/gateware/`, with `litedram_core.xdc` for Vivado. It does not run Vivado: the core is
built with the project that instantiates it.

**If not.** A missing RISC-V compiler stops the firmware build; install it, or set `cpu: None` to
initialize the DRAM from your own logic. [Integration](#integration) describes the ports, the
YAML keys and the initialization without a CPU.

Where to go next: [Integration](#integration) to add LiteDRAM to your own design, [Examples and
targets](#examples) for the other boards, [Debugging](#debugging) when a step fails.
