# Simulation and verification {#simulation}

This chapter describes how the cores are checked before a bitstream is built: the DRAM model and
its timings checker, the unit tests, the SoC simulations with `litex_sim` and Verilator, and the
continuous integration. It is for contributors who change the gateware and for integrators who want
to reproduce a problem without a board.

## Verification strategy {#sim-strategy}

A DRAM problem on a board is slow to diagnose: the calibration hides it, or a memtest fails once
per hour. Each part is therefore checked in simulation first, at the cheapest level that exercises
it.

| Level | What runs | Memory side | Simulator |
|-----------------------|--------------------------------------|----------------------------|------------------|
| Unit | One module: bank machine, multiplexer, frontend | Python models and drivers | Migen |
| Controller | Controller and crossbar under random traffic | DFI timings checker | Migen |
| PHY | One PHY, DFI sequences in, pad sequences out | Expected pad patterns | Migen |
| Generator | `litedram_gen` on configurations and examples | None (elaboration) | None |
| SoC | CPU, BIOS, core and DRAM model (`litex_sim`) | DFI-level DRAM model | Verilator |
| LPDDR4, LPDDR5 | SoC with the simulation PHY | Pad-level DRAM simulator | Verilator |
| Hardware | Bench or LiteX-Boards target | The DRAM | |

The FPGA PHYs of the vendor families have no model of their I/O primitives in the project. Their
tests check the DFI-to-pad behaviour of the Python logic around the primitives, and the
calibration itself is only checked on a board.

## DRAM model and timings checker {#sim-model}

Most tests need a memory behind the controller but not the electrical details of a PHY. The DRAM
model (`SDRAMPHYModel`) stands for the PHY and the DRAM together, at the DFI.

The model takes the commands of each DFI phase, keeps the data of each bank in memory and returns
the read data with the latency of a real PHY. The figure below shows it in a unit test.

![DFI-level simulation: port drivers send traffic through the crossbar and the controller to the
DRAM model; the timings checker watches every command on the DFI.](sim_model.svg)

The model takes its PHY settings from `get_sdram_phy_settings`, which copies the latencies of a
real PHY of the same memory type. The number of DFI phases follows the memory type.

| Memory | DFI phases | Settings copied from |
|-------------------------------|------------------------|-----------------------------------------------|
| SDR | 1 | `gensdrphy.py` |
| DDR, LPDDR | 2 | `s6ddrphy.py` |
| DDR2, DDR3 | 2 (DDR2), 4 (DDR3) | `s7ddrphy.py` |
| DDR4 | 4 | `usddrphy.py` |

The timings checker (`DFITimingsChecker`) decodes the commands on the DFI and measures the time
between them in picoseconds. It reports a violation of any of these rules, per bank where the rule
is per bank:

| Rule | Between |
|------------------------------|-----------------------------------------------------------------------|
| tRP | PRE and ACT or REF |
| tRCD | ACT and RD or WR |
| tRAS, tRC | ACT and PRE; ACT and ACT |
| tRFC | REF and PRE or ACT |
| tCCD, tWTR | Two column commands; WR and RD |
| tWR, tRTP | WR and PRE; RD and PRE |
| tZQCS | ZQCS and ACT |
| tRRD, tFAW | ACT and ACT on any bank; four ACT in a window |
| tREFI | Late refresh, too many postponed refreshes, refresh rate over 64 ms |

The model builds the checker only when its verbosity is above 0, and prints each command when the
verbosity is above 2: level 1 reports the violations, level 3 also traces the commands, and level 2
prints nothing more than level 1. `test/test_controller_timing.py` instantiates the checker alone, against the
whole controller under random traffic, for DDR2, DDR3 and DDR4 modules.

In the code: `litedram/phy/model.py` (`SDRAMPHYModel`, `DFITimingsChecker`, `BankModel`,
`DFIPhaseModel`).

## Unit tests {#sim-tests}

The tests are Python `unittest` classes in `test/`, run with pytest or `unittest`. The table below
groups the files by area.

| Area | Test files |
|-------------------------|---------------------------------------------------------------------------------|
| Controller | `test_bankmachine`, `test_shared_bankmachines`, `test_multiplexer`, `test_command_chooser`, `test_steerer`, `test_refresh`, `test_controller`, `test_controller_timing`, `test_timing`, `test_dynamic_odt`, `test_bandwidth`, `test_crossbar` |
| Frontends | `test_adapter`, `test_wishbone`, `test_axi`, `test_avalon`, `test_dma`, `test_dma_byte_enable`, `test_fifo`, `test_bist`, `test_ecc` |
| DFI and ECC | `test_dfi`, `test_dfii`, `test_dfi_ecc` |
| PHYs | `test_gensdrphy`, `test_s6ddrphy`, `test_s7ddrphy`, `test_usddrphy`, `test_ecp5ddrphy`, `test_nxddrphy`, `test_gw5ddrphy`, `test_rpcphy`, `test_ddr3_phy_settings`, `test_phy_utils`, `test_sim_utils` |
| LPDDR4, LPDDR5 | `test_lpddr4`, `test_lpddr5` |
| Modules and init | `test_modules`, `test_cl_cwl`, `test_init` |
| Generator | `test_gen`, `test_examples` |

`test_init` compares the generated initialization headers with the reference files of
`test/reference/` (SDR, DDR3 and DDR4, in C and in Python). `test_modules` checks the module
timings against SPD dumps of real DIMMs (`test/spd_data/`). `test_gen` runs the generator on small
configurations, with and without `--sim`, and checks the ports and clocks of the core.

`test/primitives/` holds two scripts that are not unit tests. They simulate the Xilinx OSERDESE2 and
OSERDESE3 primitives with the Vivado simulator, to check the serializer timing that the PHYs
assume.

### Commands {#sim-commands}

```sh
# Unit suite, as the CI job "unit" runs it
python3 -m pytest test --ignore=test/test_examples.py \
    --ignore=test/test_lpddr4.py --ignore=test/test_lpddr5.py
# One area
python3 -m pytest -v test/test_multiplexer.py
# Whole suite (RISC-V GCC and Verilator needed)
python3 -m pytest test
# Full suite with the slow configurations, as the CI job "full" runs it
LITEDRAM_TEST_FULL=1 python3 -m unittest discover -s test -p "test_*.py"
```

`LITEDRAM_TEST_FULL=1` enables configurations that some files keep optional because they are slow:
the 4-phase DFI ECC configuration of `test_dfi_ecc` and the larger cases of
`test_shared_bankmachines`. `test_examples` needs the RISC-V GCC toolchain, and the Verilator tests
of `test_lpddr4` and `test_lpddr5` need Verilator.

## SoC simulation with litex_sim {#sim-litex-sim}

The LiteX simulator runs a whole SoC in Verilator: CPU, BIOS, core and DRAM model. It is the
quickest way to see the BIOS initialization of a DRAM, or to run software on it, without a board.

```sh
# SoC with an SDR module, as in the getting started chapter
litex_sim --with-sdram
# DDR3 module, 16 bits wide, with the timings checker on
litex_sim --with-sdram --sdram-module MT41K128M16 --sdram-data-width 16 --sdram-verbosity 1
# Same with the BIST generator and checker
litex_sim --with-sdram --with-sdram-bist
```

`--sdram-module` takes any class of `litedram.modules`, and `--sdram-from-spd-dump` builds the
module from an SPD dump instead. `--sdram-init` preloads the memory from a `.bin` or `.json` file
and skips the boot memtest. [litex_sim options](#opt-sim-litex) lists them with their defaults.

The model computes its timings for a 100 MHz clock, whatever the clock of the simulation: the
module timings are converted at that frequency. The BIOS runs the same initialization as on a
board, but the model has no delays to scan: [Getting started](#getting-started) shows the boot
log, with its memtest and memspeed.

## Generated core in a testbench {#sim-gen}

A core generated with `--sim` holds the same controller and user ports as the hardware core, around
the DFI-level model instead of a PHY. It has no vendor primitive, so any Verilog simulator runs it,
and it is the simplest way to check a master against the port protocols.

The core needs no DRAM initialization, but its user ports wait for `ddrctrl_init_done` like the
hardware core, by default. With a CPU, the firmware writes it; with `cpu: None`, the testbench
writes it through the `wb_ctrl` bus ([Initialization](#integ-init)). The generator removes the
Verilator harness of LiteX from a `--sim` core, since the core is instantiated in the user's
testbench, and `test_gen` checks it.

## LPDDR4 and LPDDR5 simulations {#sim-lpddr}

The LPDDR4 and LPDDR5 PHYs have a pad-level simulation: a SoC with the BIOS and the core drives a
simulation PHY, whose pads connect to a DRAM simulator (`sim.py`) that decodes the commands. The
figure below shows the structure, the same for both memories.

![Pad-level simulation of the LPDDR PHYs: the BIOS initializes the DRAM through the core and the
simulation PHY; the DRAM simulator decodes the commands on the pads and logs them, with the timing
violations.](sim_lpddr_soc.svg)

The simulation PHY (`LPDDR4SimPHY`, `LPDDR5SimPHY`) serializes the data with Migen logic instead of
FPGA primitives; `--double-rate-phy` selects the two-stage serialization of the 7-Series LPDDR4
PHY. The DRAM simulator checks the initialization sequence, the commands and their timings, and
reports through a logger with levels per category.

```sh
# LPDDR4: initialization, read leveling and memtest, then stop
python3 litedram/phy/lpddr4/simsoc.py --finish-after-memtest --double-rate-phy --l2-size 0
# Same with a waveform and a GTKWave save file
python3 litedram/phy/lpddr4/simsoc.py --finish-after-memtest --trace --trace-fst --gtkw-savefile
# LPDDR5 with a WCK:CK ratio of 4
python3 litedram/phy/lpddr5/simsoc.py --finish-after-memtest --wck-ck-ratio 4
```

`--log-level` sets the level per category, as in `--log-level cmd=info,data=debug`. The README of
the LPDDR4 PHY shows a log of such a run; the excerpt below is its start, a simulation, with the
BIOS output between the simulator messages.

```console
[           50000 ps] [INFO] RESET released
[           50000 ps] [WARN] tINIT1 violated: RESET deasserted too fast
[           50000 ps] [INFO] CKE rising edge
[           50000 ps] [WARN] tINIT3 violated: CKE set HIGH too fast after RESET being released
[          100000 ps] [INFO] FSM reset
--========== Initialization ============--
Initializing SDRAM @0x40000000...
Switching SDRAM to software control.
[...]
[     98302540000 ps] [INFO] MRW: MR[ 1] = 0x14
[     98351300000 ps] [INFO] MRW: MR[ 2] = 0x09
[     98400160000 ps] [INFO] MRW: MR[11] = 0x00
[     98448960000 ps] [INFO] MPC: ZQC-START
[...]
```

The two warnings come from the controller, which starts with the DRAM reset released; the
initialization then resets the DRAM again.

The Verilator tests of `test_lpddr4` and `test_lpddr5` run these simulations, wait for "Memtest OK"
and fail on any other warning or error of the log. The RPC DRAM has a simulation SoC too
(`litedram/phy/rpc/simsoc.py`), whose simulation PHY generates the read data itself, without a DRAM
simulator.

## Benchmarks in simulation {#sim-benchmarks}

`test/benchmark.py` measures the controller in a `litex_sim` SoC with BIST generators and checkers:
modules, data widths, sequential or random data, alternating or grouped writes and reads, or an
access pattern from a CSV file. `test/run_benchmarks.py` runs the configurations of
`test/benchmarks.yml` and can write an HTML summary and plots.

```sh
python3 test/run_benchmarks.py test/benchmarks.yml --html --njobs 4
```

The harness reads the BIST durations from the log of each run and computes the bandwidth, the
efficiency (commands per cycle) and the latency of a single access, with the system clock fixed at
100 MHz. [Performance and resources](#performance) explains how to read bandwidth figures.

## Continuous integration {#sim-ci}

The CI workflow (`.github/workflows/ci.yml`) has two jobs. Both install LiteX and its cores with
`litex_setup.py`, then the project from the checkout.

| Job | When | Content |
|-------------|-----------------------------------|---------------------------------------------------------|
| `unit` | Every push and pull request | pytest on `test/` without `test_examples`, `test_lpddr4`, `test_lpddr5`; Python 3.9 and 3.12 |
| `full` | Push to `master`, manual run, weekly schedule | All tests with RISC-V GCC and Verilator, `LITEDRAM_TEST_FULL=1` |

The `unit` job needs no external tool: every test it runs is a Migen simulation. The `full` job
builds Verilator from source at a fixed revision and runs the complete suite with `unittest`. The
documentation workflow (`.github/workflows/doc.yml`) checks the figures and this manual; the
[Maintaining the manual](#maintenance) appendix describes it.

## Adding a test {#sim-add-test}

A new test goes in `test/test_<area>.py`, next to the tests of the same block.

- Prefer a Migen unit test with the DRAM model, the port drivers of `test/common.py` and the timings
  checker; keep Verilator for what needs the BIOS or the pads.
- For a PHY, drive DFI sequences and check the pad patterns, as `test_lpddr4` does; the helpers
  are in `test/phy_common.py` and `litedram/phy/sim_utils.py`.
- Keep slow configurations behind `LITEDRAM_TEST_FULL`, and skip a test whose external tool is
  missing.
- Seed every random generator, so that a failure replays.
- Run the unit suite before a pull request, and say which board ran a change of a PHY.

Where to go next: [Debugging](#debugging) for the hardware side, and [Simulation
options](#opt-sim) for every option of the simulation scripts.
