# Debugging {#debugging}

This chapter explains how to debug a DRAM interface on a board: a calibration that finds no window,
a memtest that fails, a design that passes at boot and fails under load.

It describes the method, how to read the calibration output of the BIOS, the tests and registers to
use at each step, and ends with a troubleshooting table. Read it before touching hardware.

## Method {#debug-method}

The approach is to observe before changing anything. The BIOS already prints most of the answer at
boot: what it believes the memory is, the windows it found and whether a memtest passed. Registers
and tests come next; a logic analyzer capture is only worth taking once the question is narrow.

1. Check the design: the console answers and the identifier matches the build.
2. Read the boot log: the summary line of the memory, then the calibration tables.
3. Check the memory through the controller: memtest, then the BIST for larger areas.
4. Change one setting at a time from the BIOS console, and run the calibration and the memtest
   again.
5. Capture a narrow LiteScope trace on the DFI only when the question is about timing.
6. Reproduce the finding in simulation, fix it there, then check again on the board
   ([Simulation and verification](#simulation)).

Each view observes one part of the memory path, as the figure below shows. A memtest exercises the
whole path from the CPU; the BIST starts at the crossbar; the leveling tables look at the PHY and
the DRAM alone.

![Debug views: the dotted arrows show which part of the memory path each view
observes.](debug_taps.svg)

| View | Tool | Tells |
|------------------------|----------------------------------------------|------------------------------------------|
| Boot log | BIOS console | Memory seen by the software, calibration windows, memtest |
| Memory tests | `mem_test`, `mem_speed`, `sdram_test` | Errors through the CPU and the L2 cache |
| BIST | `sdram_bist`, `sdram_hw_test` | Errors and bandwidth through a port, without the CPU |
| Registers | `litex_cli` | PHY delays, ECC counters, bandwidth monitor |
| DFI trace | LiteScope | Commands and data of each DFI phase, cycle by cycle |

The register names of this chapter are those of [Register reference](#registers). The `AGENTS.md`
file of the repository and the LiteX wiki page on debugging a SoC on hardware describe the same
method.

## Access to the console and registers {#debug-access}

The BIOS console is usually a UART. The bench targets put it on a crossover UART instead, read
through a bridge (UARTBone or Etherbone) with `litex_server`; the bridge also gives access to every
register by name, through the `csr.csv` of the build. The identifier must match the build before
any other step.

```sh
# Bridge over Ethernet (bench targets with Etherbone), or over the serial port
litex_server --udp &
litex_server --uart --uart-port /dev/ttyUSBx &
# BIOS console over the bridge
litex_term crossover
# Identifier, then the PHY registers
litex_cli --csr-csv csr.csv --ident
litex_cli --csr-csv csr.csv --regs --filter ddrphy
```

On a design without a bridge, the BIOS console is the only view: everything in this chapter up to
[BIST and controller registers](#debug-bist) still applies.

## Reading the boot log {#debug-boot-log}

The BIOS prints a summary of the SoC, then initializes the DRAM: software control of the DFI, the
leveling steps that the PHY supports, hardware control, a memtest and a measurement of the speed.

The capture below is a complete DRAM initialization on an ECPIX-5 board (Lattice ECP5, DDR3, two
byte groups, 300 MT/s at 1:2), from the history of LiteX-Boards.

```console
[...]
--=============== SoC ==================--
CPU:            FireV-STANDARD @ 75MHz
BUS:            WISHBONE 32-bit @ 4GiB
CSR:            32-bit data
ROM:            128KiB
SRAM:           8KiB
L2:             8KiB
SDRAM:          524288KiB 16-bit @ 300MT/s (CL-6 CWL-5)

--========== Initialization ============--
Initializing SDRAM @0x40000000...
Switching SDRAM to software control.
Read leveling:
  m0, b00: |01110000| delays: 02+-01
  m0, b01: |00000000| delays: -
  m0, b02: |00000000| delays: -
  m0, b03: |00000000| delays: -
  best: m0, b00 delays: 02+-01
  m1, b00: |01110000| delays: 02+-01
  m1, b01: |00000000| delays: -
  m1, b02: |00000000| delays: -
  m1, b03: |00000000| delays: -
  best: m1, b00 delays: 02+-01
Switching SDRAM to hardware control.
Memtest at 0x40000000 (2.0MiB)...
  Write: 0x40000000-0x40200000 2.0MiB
   Read: 0x40000000-0x40200000 2.0MiB
Memtest OK
Memspeed at 0x40000000 (Sequential, 2.0MiB)...
  Write speed: 13.6MiB/s
   Read speed: 23.4MiB/s
[...]
```

Check the `SDRAM` line first: it is what the software believes, computed from the build. It gives
the size, the data width, the data rate and the CL and CWL of the mode registers.

The data rate is the system clock times the number of DFI phases times two: here 75 MHz, two phases,
300 MT/s. A wrong value means a wrong build, not a calibration problem.

The steps between the two "Switching" lines depend on the PHY, as [Initialization and
calibration](#calibration) explains. An SDR PHY has no leveling at all: the log goes straight to the
memtest, as on this TEC0117 board (Gowin GW1NR-9, 16-bit SDR SDRAM, 25 MT/s).

```console
[...]
--=============== SoC ==================--
CPU:            VexRiscv_Lite @ 25MHz
BUS:            WISHBONE 32-bit @ 4GiB
CSR:            32-bit data
ROM:            24KiB
SRAM:           4KiB
L2:             0KiB
SDRAM:          8192KiB 16-bit @ 25MT/s (CL-2 CWL-2)

--========== Initialization ============--
Initializing SDRAM @0x40000000...
Switching SDRAM to software control.
Switching SDRAM to hardware control.
Memtest at 0x40000000 (2MiB)...
  Write: 0x40000000-0x40200000 2MiB
   Read: 0x40000000-0x40200000 2MiB
Memtest OK
Memspeed at 0x40000000 (2MiB)...
  Write speed: 5MiB/s
   Read speed: 6MiB/s
[...]
```

After a failed memtest, the BIOS prints the error counts and "Memtest KO", and the initialization
fails: the generator core then sets its `init_error` output. With `SDRAM_LEVELING_RETRIES` above 1,
the BIOS first runs the leveling again and prints "Memtest failed, leveling again" with the attempt
number.

The captures of this chapter come from the history of LiteX and LiteX-Boards. The BIOS of the
documented revision prints the same tables; some headers differ, and the Artix-7 PHY now keeps the
CL of the module where older logs show it plus one.

## Read leveling tables {#debug-read-leveling}

Read leveling finds, for each byte group, the read delay and the bitslip at which the data written
beforehand reads back correctly ([Initialization and calibration](#calibration)). The BIOS prints
one line per byte group and bitslip. The capture below is the first byte group of an Arty A7 (DDR3,
16 bits, 800 MT/s, 32 delay taps, 8 bitslips).

```console
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
[...]
```

- `m0` is the byte group (module), `b02` the bitslip: the read data shifted by that many bit times.
- Each character is one delay tap, from 0 on the left: `1` when the pattern read back without
  error at that delay, `0` otherwise.
- `delays: 19+-07` is the centre of the longest window of ones and its half width, in taps; `-`
  means no window.
- `best:` is the bitslip kept, the one with the most passing taps, and its window measured again.

A healthy table has one bitslip with a wide window, and its neighbours with partial windows at the
ends of the delay line: the start of `b02` and the end of `b04` here. The next byte group (`m1`) of
the same capture has the same windows.

A PHY with more than 32 taps prints one character every `taps/32` taps, so the line stays 32
characters long, but the `delays:` values are still in taps.

The ECP5 PHY has 8 delay steps and 4 bitslips: its windows are a few steps wide, as `02+-01` in the
ECPIX-5 capture above. The Gowin PHYs have 256 delay steps, printed 8 per character. The ECP5 and
GW5A PHYs also require the PHY to see the read burst of each byte group (`burstdet_seen`).

## Write leveling and write latency {#debug-write-leveling}

The PHYs with write leveling (Kintex-7 and Virtex-7 with ODELAY, UltraScale and UltraScale+) align
the strobe of each byte group with the clock at the DRAM. The DRAM samples the clock on each strobe
pulse and returns the value on the data lines; the BIOS scans the strobe delay and looks for the
transition from 0 to 1.

The capture below, from a 64-bit DDR3 interface on a KC705 (eight byte groups), shows the scan
before and after a delay of the clock and command lines.

```console
Before (delay = 0 taps):
Write leveling:
m0: |11000000000000011111111111| delay: 15
m1: |00000000000000111111111111| delay: 14
m2: |11110000000000000111111111| delay: 17
m3: |11110000000000000011111111| delay: 18
m4: |11111111110000000000000111| delay: 00
m5: |11111111110000000000000111| delay: 00
m6: |11111111111000000000000001| delay: 00
m7: |11111111111000000000000011| delay: 00

After (delay = 12 taps):
Write leveling:
m0: |11111111111111000000000000| delay: 00
m1: |11111111111100000000000001| delay: 00
m2: |00011111111111110000000000| delay: 03
m3: |00011111111111110000000000| delay: 03
m4: |00000000111111111111110000| delay: 08
m5: |00000000111111111111110000| delay: 08
m6: |00000000001111111111111000| delay: 10
m7: |00000000001111111111111000| delay: 10
```

Each character is one tap of the strobe delay; `delay:` is the tap of the 0 to 1 transition that the
BIOS keeps. Without delay on the clock, the transitions of `m0` to `m3` sit in the middle of the
scan and those of `m4` to `m7` at its very end.

With 12 taps of delay on the clock and command lines, the transitions of `m2` to `m7` move to the
first half of the scan, while those of `m0` and `m1` leave it or reach its last tap.

The fly-by routing makes each byte group see the clock at another time, so no single clock delay
suits them all. The BIOS therefore scans the clock and command delay (`Cmd/Clk`) first, on the PHYs
that have it, and keeps the one that levels the most byte groups closest to the centre of the scan.

The KC705 capture below ends the same procedure with a clock and command delay of 11 taps. `m0` and
`m1` have no transition (`-`) and keep a write delay of 0.

Write latency calibration then picks, for each byte group, the write bitslip, in steps of one clock,
with which a read window exists: `m0:6` is the bitslip kept, `-` would mean none. The memtest of
that boot passed.

```console
[...]
| best: 11
  Setting Cmd/Clk delay to 11 taps.
  Data scan:
  m0: |11111111111110000000000001| delay: -
  m1: |11111111111000000000000001| delay: -
  m2: |00111111111111100000000000| delay: 02
  m3: |00111111111111100000000000| delay: 02
  m4: |00000001111111111111100000| delay: 07
  m5: |00000000111111111111100000| delay: 08
  m6: |00000000011111111111110000| delay: 09
  m7: |00000000011111111111110000| delay: 09
Write latency calibration:
m0:6 m1:6 m2:6 m3:6 m4:6 m5:6 m6:6 m7:6
[...]
```

## Memtest and memspeed {#debug-memtest}

The memtest writes and reads through the CPU, the L2 cache and the controller, so it checks what the
calibration does not: the latencies of the controller.

The DFI injector used during the calibration does not depend on them, so a passing calibration with
a failing memtest points to the read or write latency of the PHY settings, not to the delays.

The memtest has three parts, and a failure prints the error count of each:

| Part | Area | Writes | A failure points first to |
|-------------------|----------------|----------------------------------------|---------------------------------|
| Bus | 512 bytes | Alternating `0xaaaaaaaa` and `0x55555555` | No DRAM response, a stuck data line |
| Address | 32 KiB | The index of each word | Wrong module geometry, address or bank lines |
| Data | Test size | Pseudo-random words | Margin: delays, latencies, termination |

The boot memtest covers 2 MiB (`MEMTEST_DATA_SIZE`); `mem_test` and `mem_speed` test any area from
the console. The capture below shows both on a 256 MiB main RAM, from the history of LiteX.

```console
litex> mem_test 0x40000000 0x1000
Memtest at 0x40000000 (4KiB)...
  Write: 0x40000000-0x40001000 4KiB
   Read: 0x40000000-0x40001000 4KiB
Memtest OK

litex> mem_speed 0x40000000 0x1000
Memspeed at 0x40000000 (4KiB)...
  Write speed: 352KiB/s
   Read speed: 288KiB/s
```

`sdram_test` runs the memtest over 1/32 of the main RAM. Memspeed measures the CPU path, in MiB/s:
the CPU, the L2 cache and the bus limit it, far below the DRAM. Use it to compare two builds of the
same SoC, and the BIST for the bandwidth of the DRAM.

## BIST and controller registers {#debug-bist}

A design built with the BIST (`with_bist`, the `--with-bist` option of the bench targets) writes and
checks DRAM areas in hardware, at the speed of a port, without the CPU. The BIOS has two commands
for it:

| Command | Effect |
|----------------------------------------------------------------------------|--------------------------------|
| `sdram_bist <burst_length> <random>` | Write and read loops until a key is pressed; prints the write and read speeds in MiB/s, the MiB tested and the errors every 100 loops |
| `sdram_hw_test <origin> <size> [burst]` | Write and check an area, then print "N errors found" |

`random` set to 1 places each burst at a pseudo-random address; the data is always pseudo-random.
The host can also drive the BIST registers through the bridge ([BIST
generator](#reg-sdram-generator)). The controller has two more sources of information when they are
built:

- The bandwidth monitor (`with_bandwidth`) counts the read and write commands over a period: write
  `sdram_controller_bandwidth_update`, then read `nreads` and `nwrites`. The bandwidth is
  `(nreads + nwrites) x data_width` bits per period of 2^24 cycles.
- The DFI ECC (`with_ecc`) counts the corrected and the detected errors (`sdram_ecc_sec`,
  `sdram_ecc_ded`). With `with_ecc_bit_stats` it also counts the corrected errors per data line:
  write a line number to `sdram_ecc_bitsel` and read `sdram_ecc_bitcnt`. A count that grows on a few
  lines only points to those lines, not to the whole interface.

## Forcing settings from the BIOS {#debug-force}

The BIOS has commands to change one calibration setting at a time, then to run the calibration or
the memtest again, without a new bitstream. They exist only on the PHYs that have the matching
registers.

| Command | Effect |
|----------------------------------------------------------------|-------------------------------------|
| `sdram_init` | Whole initialization: reset, mode registers, leveling, memtest |
| `sdram_cal` | Leveling only, with the forced settings |
| `sdram_force_rdphase <phase>` | DFI phase of the reads |
| `sdram_force_wrphase <phase>` | DFI phase of the writes |
| `sdram_force_cmd_delay <taps>` | Clock and command delay, instead of its scan |
| `sdram_force_dat_delay <m> <taps>` | Write delay of byte group `m` |
| `sdram_force_bitslip <m> <bitslip>` | Write bitslip of byte group `m` |
| `sdram_rst_cmd_delay`, `sdram_rst_dat_delay <m>`, `sdram_rst_bitslip <m>` | Back to the scan |
| `sdram_mr_write <reg> <value>` | Write a mode register of the DRAM |

`sdram_init` clears the forced delays and bitslips and restores the read and write phases of the
build; `sdram_cal` keeps them. After a change, `sdram_test` or `mem_test` checks the result through
the controller. The mode register helpers of [Mode register helpers](#ex-mr-gen) compute
`sdram_mr_write` values. A design built with `SDRAM_DEBUG` also has `sdram_debug`, a series of
memtests with error statistics.

## LiteScope on the DFI {#debug-litescope}

When the question is about cycles, such as a read latency off by one or a command on the wrong
phase, a trace of the DFI answers it.

The bench targets add a LiteScope analyzer on the whole DFI of the PHY with `--with-analyzer`: 256
samples in the system clock domain, its signal list written to `analyzer.csv`. A custom design adds
the same analyzer:

```python
from litescope import LiteScopeAnalyzer
self.analyzer = LiteScopeAnalyzer([self.ddrphy.dfi],
    depth        = 256,
    clock_domain = "sys",
    csr_csv      = "analyzer.csv")
```

The capture runs on the host through the bridge with `litescope_cli`, which lists the signals of
`analyzer.csv` and triggers on one of them. Trigger on the read enable of the read phase, then
check three things:

- The commands appear on the read and write phases of the build (`rdphase`, `wrphase`).
- The read data arrives `read_latency` cycles after the read enable, with its valid flag.
- The write data is presented `write_latency` cycles after the write command.

The whole DFI of a 64-bit interface at 1:4 is wide. Keep the capture narrow: one phase, or the
command and enable signals without the data, so that the depth covers several accesses.

## Frequency margin {#debug-margin}

A calibration that passes says that a window exists, not how wide it is. The windows narrow as the
frequency rises, and an interface with little margin fails with temperature or under load.

Two captures on Arty A7 boards show it: at 800 MT/s the best window is `19+-07` (above); at
400 MT/s, below, it spans almost the whole delay line.

```console
[...]
SDRAM:          262144KiB 16-bit @ 400MT/s (CL-7 CWL-5)

--========== Initialization ============--
Initializing SDRAM @0x10000000...
Switching SDRAM to software control.
Read leveling:
  m0, b00: |00000000000000000000000000000000| delays: -
  m0, b01: |11111111111111111111111111100000| delays: 13+-13
  m0, b02: |00000000000000000000000000001111| delays: 30+-02
  m0, b03: |00000000000000000000000000000000| delays: -
  m0, b04: |00000000000000000000000000000000| delays: -
  m0, b05: |00000000000000000000000000000000| delays: -
  m0, b06: |00000000000000000000000000000000| delays: -
  m0, b07: |00000000000000000000000000000000| delays: -
  best: m0, b01 delays: 13+-13
[...]
```

The frequency sweep of the bench targets ([Frequency sweep](#ex-sweep)) prints such a log at each
system clock of a range, which shows where the windows close.

Under heavy traffic the eye can be narrower than during the calibration: on a 72-bit DDR3 interface
at 933 MT/s on 7-Series HR banks, the recorded eye was 8 taps or more under the BIST and 2 to 3 taps
with two concurrent read streams. The per-line ECC counters find such lines in operation.

## Troubleshooting {#debug-troubleshooting}

The table lists the symptoms seen most often, with the first thing to check.

| Symptom | Likely cause | Check |
|---------------------------------------|-------------------------------------|-----------------------------------------------------|
| No BIOS output at all | Bitstream, serial port or baud rate | `--load` again, the port of the board, 115200 baud, `--ident` |
| Wrong size, rate, CL or CWL on the `SDRAM` line | Build: module, clock or PHY ratio | YAML or target, `sdram_phy.h` |
| Every read leveling line at `0` | No DRAM response: clock, reset, CKE, init sequence | PLL lock, pinout, `rst` of the PHY |
| One byte group always at `0` | That byte group: pins, DQS, data mask | Pinout, `dm_swap`, byte groups used |
| Narrow windows (`+-00`, `+-01` on 32 taps) | Little margin | Lower clock, termination, delay reference clock |
| Write leveling `delay: -` on some groups | Clock and command delay | Cmd/Clk scan, `cmd_delay`, `cmd_latency` |
| Leveling passes, memtest data errors | Controller latencies | `read_latency`, `write_latency`, `sdram_force_rdphase` |
| Memtest address errors | Module geometry | Module class, ranks, size |
| Memtest bus errors | No data path at all | Leveling log, main RAM region |
| Errors under load, memtest passes | Eye narrower under traffic | BIST, ECC per-line counters, sweep |
| Generator core ports never answer | `init_done` not written | `ddrctrl_init_done`, `block_until_ready` |
| SDR memtest fails | SDRAM clock phase | `sdram_clk_phase`, `sdram_cal` |
| ECP5 1:4 with `rate_crossing` fails | The `rate` register is not searched by the BIOS | Custom initialization |
| Calibration takes minutes | Many taps (UltraScale(+)) | Fast paths of the BIOS above 128 taps |

The fast paths of the BIOS are on by default for PHYs with more than 128 taps; they took the full
calibration of the XCU1525 to about 25 seconds, recorded in the history of LiteX. The custom
initialization hook (`CONFIG_SDRAM_CUSTOM_INIT`) replaces the whole sequence for memories that need
their own training.

Where to go next: [Initialization and calibration](#calibration) for the algorithms behind the
tables, [Register reference](#registers) for the registers, and [Performance and
resources](#performance) for bandwidth measurements.
