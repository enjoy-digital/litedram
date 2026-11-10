# Build options {#build-options}

This appendix lists the options of every tool of the project: the keys of the generator YAML files,
the settings of the controller, the options of the bench targets and helpers, the options of the
simulations, and the constants of the BIOS that change the calibration. The chapters explain when
to use them; this appendix gives their names and defaults.

## Generator command line {#opt-gen-cli}

`litedram_gen` (or `python3 -m litedram.gen`) takes one YAML file and the usual options of the
LiteX `Builder`.

| Option | Default | Effect |
|-------------------------------|--------------------------------|--------------------------------------|
| `config` | required | YAML file of the core |
| `--name` | `litedram_core` | Name of the generated module and files |
| `--sim` | off | Core around the DFI-level DRAM model, no vendor primitive |
| `--output-dir` | `build` | Output directory |
| `--no-compile` | off | Do not compile the firmware |
| `--csr-csv` | none | Write the register map as CSV |
| `--csr-json` | none | Write the register map as JSON |

## Generator YAML keys {#opt-gen}

The keys below are read by `litedram/gen.py`. Keys whose name contains `clk_freq` are converted to
floats, and the strings `"True"`, `"False"` and `"None"` to their Python values. Unknown keys are
ignored. "Required (X)" means required by the PHYs X only.

### General {#opt-gen-general}

| Key | Default | Meaning |
|-------------------------------|----------------------|------------------------------------------------|
| `cpu` | required | CPU of the firmware (`vexriscv`, `serv`), or `None` for a `wb_ctrl` bus |
| `cpu_variant` | `standard` | Variant of the CPU |
| `csr_data_width` | `32` | Data width of the CSR bus |
| `uart` | `rs232` | Firmware UART: `rs232` pins or a `fifo` interface |
| `speedgrade` | required (Xilinx) | Speed grade of the FPGA, for the PLL |
| `device` | required (Lattice, Gowin) | Device name, as `LFE5U-45F-6BG381C` |
| `devicename` | required (Gowin) | Gowin device name for the PLL, as `GW2A-18C` |

### PHY and module {#opt-gen-phy}

| Key | Default | Meaning |
|---------------------------------------------|----------------|----------------------------------------|
| `sdram_phy` | required | PHY class: `GENSDRPHY`, `ECP5DDRPHY`, `GW2DDRPHY`, `GW5DDRPHY`, `A7DDRPHY`, `K7DDRPHY`, `V7DDRPHY`, `USDDRPHY`, `USPDDRPHY` |
| `memtype` | required | `SDR`, `DDR2`, `DDR3` or `DDR4`, matching the PHY |
| `sdram_module` | required | Module class of `litedram.modules` |
| `sdram_module_speedgrade` | module default | Speed grade of the module |
| `cl`, `cwl` | speed grade or PHY | CAS latency and CAS write latency |
| `sdram_module_nb` | required | Number of byte groups (data width / 8) |
| `sdram_rank_nb` | required (DDR2 to DDR4) | Number of ranks |
| `cmd_latency` | required (Xilinx) | Additional command latency |
| `cmd_delay` | `0` | Command and address delay (ECP5, Gowin) |
| `dm_swap` | `False` | Swap the data mask lines 0 and 1 (ECP5, Gowin) |
| `cmd_gearing` | `x2` | ECP5 output primitives of CK and commands: `x2` or `x1` (experimental) |
| `ck_phase` | `45` | ECP5 with `x1` gearing: CK phase from the PLL, in degrees |
| `dll_off` | `False` | DDR3 DLL-off mode, CL6 and CWL6 (Gowin) |
| `sdram_rate` | `1:2` | Frequency ratio of the GW5A PHY: `1:2` or `1:4` |
| `with_hpio_vref` | `False` | Read VREF scan, UltraScale+ with DDR4 |
| `hpio_vref_tune` | `31` | Reset code of the read VREF, 0 to 72 |

The memory types per PHY are: SDR for `GENSDRPHY`; DDR3 for the ECP5 and Gowin PHYs; DDR2 and DDR3
for the 7-Series PHYs; DDR3 and DDR4 for the UltraScale(+) PHYs. The read VREF code gives 58% plus
0.5% per code of VCCO for the codes 15 to 72; 31 is 73.5%.

### Clocks {#opt-gen-clocks}

| Key | Default | Meaning |
|-------------------------------------|--------------------|--------------------------------------------|
| `sys_clk_freq` | required | System clock of the controller, in Hz |
| `input_clk_freq` | required (DDR PHYs) | Input clock of the PLL; optional for `GENSDRPHY` on ECP5 |
| `sdram_clk_phase` | `90` | `GENSDRPHY` with a PLL: phase of `sdram_clk`, in degrees |
| `iodelay_clk_freq` | required (Xilinx) | Reference clock of the delays |
| `init_clk_freq` | required (ECP5) | Clock of the ECP5 initialization logic |

The DRAM clock is the system clock times 1 (SDR), 2 (ECP5, GW2A, GW5A at 1:2, 7-Series with DDR2) or
4 (GW5A at 1:4, 7-Series with DDR3, UltraScale(+)). The Gowin PHYs run their initialization from the
input clock.

With `GENSDRPHY` and an `input_clk_freq`, the core has a PLL and an `sdram_clk` output; without it,
`clk` is the system clock and the integrator drives the SDRAM clock pin.

### Electrical settings {#opt-gen-electrical}

DDR3 and DDR4 only; applied by the ECP5 and Gowin PHYs, the 7-Series PHYs with DDR3 and the
UltraScale(+) PHYs. An omitted key keeps the default of `litedram/init.py`.

| Key | Default | DDR3 values | DDR4 values |
|--------------------|----------------------|---------------------------------|------------------------------------|
| `rtt_nom` | `60ohm` (DDR3), `40ohm` (DDR4) | `disabled`, `20ohm`, `30ohm`, `40ohm`, `60ohm`, `120ohm` | `disabled`, `34ohm`, `40ohm`, `48ohm`, `60ohm`, `80ohm`, `120ohm`, `240ohm` |
| `rtt_wr` | `60ohm` (DDR3), `120ohm` (DDR4) | `disabled`, `60ohm`, `120ohm` | `disabled`, `80ohm`, `120ohm`, `240ohm`, `high-z` |
| `ron` | `34ohm` | `34ohm`, `40ohm` | `34ohm`, `48ohm` |

### Core {#opt-gen-core}

Every key of [Controller settings](#opt-controller) is accepted, except `refresh_cls`, and overrides
the default only when present. Two more keys add the DFI ECC of the core:

| Key | Default | Meaning |
|-----------------------------------------|---------------|----------------------------------------------|
| `with_ecc` | `False` | SECDED on a 72-bit memory (nine byte groups) |
| `with_ecc_bit_stats` | `False` | With the ECC, a corrected-error counter per data line |

### User ports {#opt-gen-ports}

`user_ports` (required) is a dictionary of `name: {options}`. Each port appears as
`user_port_<name>_*` signals of the core, or `user_fifo_<name>_*` for a FIFO.

| Key | Default | Meaning |
|--------------------------------------|-----------------------|----------------------------------------|
| `type` | required | `native`, `wishbone`, `avalon`, `axi` or `fifo` |
| `block_until_ready` | `True` | Hold the port until the initialization ends without error |
| `data_width` | controller width | Width of the port (required with `ecc`) |
| `ecc` | `False` | Port ECC (`native`, `wishbone`, `avalon`, `axi`) |
| `id_width` | required (`axi`) | Width of the AXI IDs |
| `with_wrap` | `True` | `axi`: support of WRAP bursts |
| `pipelined` | `False` | `wishbone`: B4 pipelined mode with a `stall` output |
| `pipelined_depth` | `8` | `wishbone`: transfers in flight in pipelined mode |
| `base` | required (`fifo`) | Base address of the FIFO in the DRAM, in bytes |
| `depth` | required (`fifo`) | Depth of the FIFO, in bytes |

An AXI port with `ecc` also gets a read-modify-write for the partial writes. A port that only issues
FIXED and INCR bursts can set `with_wrap: False`, which saves about 180 LUTs.

## Controller settings {#opt-controller}

`ControllerSettings` holds the parameters of the controller. The generator takes them from the YAML
file; `add_sdram` takes them as keyword arguments or as a `controller_settings` object.

| Key | Default | Meaning |
|----------------------------------------|--------------------------|------------------------------------|
| `cmd_buffer_depth` | `8` | Depth of the command buffer of each bank machine |
| `cmd_buffer_buffered` | `False` | Registered command buffers |
| `nbankmachines` | one per bank | Bank machines, shared by consecutive banks when fewer |
| `read_time` | `64` | Cycles of reads before switching to pending writes |
| `write_time` | `32` | Cycles of writes before switching to pending reads |
| `with_bandwidth` | `False` | Bandwidth monitor registers |
| `with_refresh` | `True` | Periodic refresh |
| `refresh_cls` | `Refresher` | Class of the refresher |
| `refresh_zqcs_freq` | `1e0` | Frequency of the ZQ short calibrations, in Hz |
| `refresh_postponing` | `1` | Refreshes that can be postponed and issued together |
| `with_dynamic_odt` | `False` | ODT only around writes (DDR3, single rank) |
| `with_auto_precharge` | `True` | Auto-precharge after reads and writes |
| `address_mapping` | `ROW_BANK_COL` | Address mapping, the only one available |
| `bank_byte_alignment` | `0` | Minimum byte distance between bank changes |

`nbankmachines` must be a power of two and needs a single rank. [Controller](#controller) explains
the read and write windows, the refresh and the address mapping.

## Bench target options {#opt-bench}

The five targets of `bench/` share their options; [Bench targets](#ex-bench) describes them.

| Option | Default | Effect |
|----------------------------------|-----------------------|---------------------------------------------|
| `--uart` | `crossover` | BIOS console: `crossover` (through a bridge) or `serial` |
| `--build` | off | Build the bitstream; without it, elaborate and compile the BIOS only |
| `--with-bist` | off | BIST generator and checker |
| `--with-analyzer` | off | LiteScope on the DFI, 256 samples, `analyzer.csv` |
| `--load` | off | Load the bitstream into the FPGA (volatile) |
| `--load-bios` | off | Load the BIOS of the build into the ROM through the bridge, then reboot |
| `--sys-clk-freq` | none | Reprogram the first PLL to this system clock, then measure it |
| `--test` | off | Frequency sweep with the BIOS log at each step ([Frequency sweep](#ex-sweep)) |
| `--channel` | `0` | `xcu1525` only: DDR4 channel, 0 to 3 |

The mode register helpers take `--cl`, `--cwl`, `--rtt_nom`, `--rtt_wr`, `--ron` and `--list`. Their
defaults are CL 5, CWL 5, `60ohm`, `60ohm` and `34ohm` for DDR3 (`bench/ddr3_mr_gen.py`), and CL
9, CWL 9, `40ohm`, `120ohm` and `34ohm` for DDR4 (`bench/ddr4_mr_gen.py`).

## Simulation options {#opt-sim}

### litex_sim {#opt-sim-litex}

| Option | Default | Effect |
|---------------------------------------------|-------------------------|-------------------------------|
| `--with-sdram` | off | Main RAM in the DRAM model |
| `--sdram-module` | `MT48LC16M16` | Module class |
| `--sdram-data-width` | `32` | Data width of the memory |
| `--sdram-init` | none | Initial contents (`.bin` or `.json`); no memtest |
| `--sdram-from-spd-dump` | none | Module from an SPD dump |
| `--sdram-verbosity` | `0` | Timings checker (above 0), command trace (above 2) |
| `--with-sdram-bist` | off | BIST generator and checker |

### LPDDR4, LPDDR5 and RPC simulation SoCs {#opt-sim-lpddr}

The scripts `litedram/phy/lpddr4/simsoc.py`, `litedram/phy/lpddr5/simsoc.py` and
`litedram/phy/rpc/simsoc.py` share most of their options.

| Option | Default | Effect |
|---------------------------------------------|--------------------|------------------------------------|
| `--sys-clk-freq` | `50e6` LPDDR4, `100e6` others | System clock of the SoC |
| `--finish-after-memtest` | off | Stop after the memtest of the BIOS (LPDDR4, LPDDR5) |
| `--log-level` | `all=INFO` | Log level of the DRAM simulator, per category (LPDDR4, LPDDR5) |
| `--double-rate-phy` | off | Two-stage serialization of the 7-Series PHY (LPDDR4) |
| `--wck-ck-ratio` | `2` | WCK:CK ratio, 2 or 4 (LPDDR5) |
| `--dfi-converter-ratio` | `1` | Ratio between the system clock and CK (LPDDR5) |
| `--no-masked-write` | off | WRITE instead of MASKED-WRITE (LPDDR4, LPDDR5) |
| `--disable-delay` | off | Remove the delays of the CPU (LPDDR4, LPDDR5) |
| `--auto-precharge` | off | Auto-precharge in the controller |
| `--no-refresh` | off | No refresh |
| `--trace`, `--trace-fst` | off | Waveform, VCD or FST |
| `--trace-start`, `--trace-end` | `0`, `-1` | Cycles of the waveform |
| `--gtkw-savefile` | off | GTKWave save file |
| `--no-run` | off | Generate the files only (LPDDR4, LPDDR5) |
| `--opt-level` | `O3` | Optimization level of the Verilator build (LPDDR4, RPC) |

The LPDDR4 and LPDDR5 scripts also take the options of the LiteX `Builder` and `SoCCore`, such as
`--output-dir` and `--l2-size`.

### Benchmarks {#opt-sim-bench}

`test/run_benchmarks.py` takes a YAML file of benchmarks, with `--names`, `--regex` and
`--not-regex` to select some, `--html` and `--plot` for the outputs, `--njobs` for parallel runs
and `--results-cache` to reuse results. `test/benchmark.py` runs one benchmark; its options set the
module, the data width, the BIST length and data, the number of generators and checkers, and an
access pattern file.

### Test environment {#opt-sim-env}

`LITEDRAM_TEST_FULL=1` enables the slow configurations of `test/test_dfi_ecc.py` and
`test/test_shared_bankmachines.py` ([Simulation and verification](#simulation)).

## BIOS constants {#opt-bios}

The DRAM code of the BIOS (`liblitedram`) reads constants of the SoC, defined with `add_constant`
in the design and written to the generated `soc.h`. They change the initialization without a
change of the BIOS sources.

- `SDRAM_LEVELING_RETRIES` (default 1): leveling attempts when the boot memtest fails.
- `SDRAM_MEMTEST_SIZE` (default `MEMTEST_DATA_SIZE`, 2 MiB): size of the boot memtest.
- `SDRAM_TEST_DISABLE`: no memtest nor memspeed at boot, as `litex_sim --sdram-init` sets it.
- `SDRAM_READ_LEVELING_FAST`, `SDRAM_WRITE_LATENCY_CALIBRATION_FAST`: sparse scans first, on by
  default above 128 taps.
- `SDRAM_MPR_READ_LEVELING_DISABLE`: no MPR read leveling on DDR4.
- `SDRAM_WRITE_LEVELING_CMD_DELAY_DEBUG`: print the whole write leveling scan at each clock and
  command delay.
- `SDRAM_LEVELING_SCAN_DISPLAY_HEX_DIV`: print the error counts of the scans in hexadecimal,
  divided by this value, instead of `0` and `1`.
- `SDRAM_DEBUG`: add the `sdram_debug` command.
- `CONFIG_SDRAM_CUSTOM_INIT`: replace the whole sequence with `sdram_custom_init()`.

The generator writes the constants of the PHY into `sdram_phy.h` (`SDRAM_PHY_*`): type, phases,
latencies, delays, bitslips and capabilities. [Initialization and calibration](#calibration)
describes them.
