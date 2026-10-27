# Standalone core generation

LiteDRAM is normally used as a Python package inside a LiteX SoC. For a traditional flow (no
Migen/LiteX at build time, versioned/packaged core, ...), a standalone Verilog core (DRAM
controller + PHY + init/calibration firmware, with native, Wishbone, Avalon, AXI or FIFO user
ports) can be generated from a YAML description with `litedram_gen` (`python3 -m litedram.gen`):
```sh
$ litedram_gen examples/arty.yml                 # Output in ./build (--output-dir to change)
$ litedram_gen --name my_core examples/arty.yml  # Name of the generated module/files
$ litedram_gen --sim examples/arty.yml           # Same core built around the DFI-level simulation PHY
```
This produces the Verilog netlist and its memory initialization files under `build/gateware/`,
the init/calibration firmware under `build/software/` and the register map with `--csr-csv`
(the usual LiteX `Builder` arguments are accepted). The generated module exposes the DRAM pads,
the clock/reset inputs of the selected PHY, `user_clk`/`user_rst`, `init_done`/`init_error` and
one `user_port_<name>_*` (or `user_fifo_<name>_*`) interface per user port.

## YAML keys

The keys read by `litedram/gen.py` are listed below. Keys containing `clk_freq` are converted to
floats and the strings `"True"`/`"False"`/`"None"` to the Python values; unknown keys are ignored.
`required (...)` means required only for the PHYs in parentheses.

### General

| Key | Type / choices | Default | Meaning |
|-----|----------------|---------|---------|
| `cpu` | `vexriscv`, `serv`, ... or `None` | required | CPU running the init/calibration firmware; `None` exposes a `wb_ctrl` Wishbone control bus instead |
| `cpu_variant` | string | `standard` | CPU variant |
| `csr_data_width` | int | `32` | CSR bus data width |
| `uart` | `rs232`, `fifo` | `rs232` | Firmware UART: RS232 pins or a valid/ready/data FIFO interface (CPU only) |
| `speedgrade` | int (`-1`, `-2`, ...) | required (A7/K7/V7/US/USP) | FPGA speedgrade, used to configure the PLL/MMCM |
| `device` | string | required (GENSDRPHY/ECP5) | Lattice device name (e.g. `LFE5U-45F-6BG381C`) |

### PHY / SDRAM module

| Key | Type / choices | Default | Meaning |
|-----|----------------|---------|---------|
| `sdram_phy` | `GENSDRPHY`, `ECP5DDRPHY`, `A7DDRPHY`, `K7DDRPHY`, `V7DDRPHY`, `USDDRPHY`, `USPDDRPHY` | required | PHY class from `litedram.phy` (selects the vendor platform and CRG) |
| `memtype` | `SDR`, `DDR2`, `DDR3`, `DDR4` | required | DRAM type; must match the PHY (GENSDRPHY: SDR, ECP5: DDR3, A7/K7/V7: DDR2/DDR3, US/USP: DDR3/DDR4) |
| `sdram_module` | string | required | SDRAM module/chip class name from `litedram.modules` (e.g. `MT41K128M16`) |
| `sdram_module_nb` | int | required | Number of byte groups (DQ width = 8 x `sdram_module_nb`, one DM/DQS pair per group) |
| `sdram_rank_nb` | int | required (DDR2/DDR3/DDR4) | Number of ranks (number of `cs_n`/`cke`/`odt`/`clk` pins) |
| `cmd_latency` | int | required (A7/K7/V7/US/USP) | Additional command latency added to CL/CWL |
| `cmd_delay` | int (`< 128`) | `0` | ECP5DDRPHY only: command/address DELAYG delay value |
| `dm_swap` | bool | `False` | ECP5DDRPHY only: swap DM lines 0 and 1 |
| `with_hpio_vref` | bool | `False` | USPDDRPHY/DDR4 only: per-byte read VREF scan through HPIO_VREF (`rd_vref` CSR) |
| `hpio_vref_tune` | int (`0`-`72`) | `31` | Read VREF reset code (58 + 0.5 x code % of VCCO for codes 15-72, 31 = 73.5%) |

### Frequencies

| Key | Type | Default | Meaning |
|-----|------|---------|---------|
| `sys_clk_freq` | float (Hz) | required | System/controller clock; DRAM clock = sys_clk x1 (SDR), x2 (ECP5 DDR3, A7/K7/V7 DDR2) or x4 (A7/K7/V7 DDR3, US/USP) |
| `input_clk_freq` | float (Hz) | required (ECP5/A7/K7/V7/US/USP) | Input clock (PLL/MMCM reference); GENSDRPHY clocks `sys_clk` directly from `clk` |
| `iodelay_clk_freq` | float (Hz) | required (A7/K7/V7/US/USP) | IDELAYCTRL reference clock frequency |
| `init_clk_freq` | float (Hz) | required (ECP5) | ECP5 init clock domain frequency |

### Electrical settings

DDR3/DDR4 only; applied by ECP5DDRPHY, A7/K7/V7 with DDR3 and US/USP. An omitted key keeps the
default of `litedram/init.py`.

| Key | Type / choices | Default | Meaning |
|-----|----------------|---------|---------|
| `rtt_nom` | DDR3: `disabled`, `20ohm`, `30ohm`, `40ohm`, `60ohm`, `120ohm`; DDR4: `disabled`, `34ohm`, `40ohm`, `48ohm`, `60ohm`, `80ohm`, `120ohm`, `240ohm` | `60ohm` (DDR3), `40ohm` (DDR4) | Nominal on-die termination (non-writes) |
| `rtt_wr` | DDR3: `disabled`, `60ohm`, `120ohm`; DDR4: `disabled`, `80ohm`, `120ohm`, `240ohm`, `high-z` | `60ohm` (DDR3), `120ohm` (DDR4) | Dynamic on-die termination (writes) |
| `ron` | DDR3: `34ohm`, `40ohm`; DDR4: `34ohm`, `48ohm` | `34ohm` | Output driver impedance |

### Controller

Every `ControllerSettings` parameter is accepted and only overridden when present (`refresh_cls`
excepted since it expects a Python class).

| Key | Type / choices | Default | Meaning |
|-----|----------------|---------|---------|
| `cmd_buffer_depth` | int | `8` | Depth of the per-bank command buffers |
| `cmd_buffer_buffered` | bool | `False` | Buffered (registered) command buffers |
| `read_time` | int | `32` | Maximum cycles of reads before switching to writes |
| `write_time` | int | `16` | Maximum cycles of writes before switching to reads |
| `with_bandwidth` | bool | `False` | Bandwidth monitoring CSRs |
| `with_refresh` | bool | `True` | Periodic refresh |
| `refresh_zqcs_freq` | float | `1e0` | ZQ short calibration frequency (Hz) |
| `refresh_postponing` | int | `1` | Maximum number of postponed refreshes |
| `with_auto_precharge` | bool | `True` | Auto-precharge after reads/writes |
| `address_mapping` | `ROW_BANK_COL` | `ROW_BANK_COL` | Address mapping scheme |
| `bank_byte_alignment` | int | `0` | Minimum byte distance between consecutive banks (e.g. L2 cache set size) |

### User ports

`user_ports` (required) is a dictionary of `name: {options}`; each port is exposed as
`user_port_<name>_*` (`user_fifo_<name>_*` for `fifo`) IOs of the generated module. Per-port
options:

| Key | Type / choices | Default | Meaning |
|-----|----------------|---------|---------|
| `type` | `native`, `wishbone`, `avalon`, `axi`, `fifo` | required | Port interface type |
| `block_until_ready` | bool | `True` | Hold the port off until the DRAM init is done without error |
| `data_width` | int | controller data width | Port data width (crossbar port width; required with `ecc`; FIFO data width for `fifo`) |
| `ecc` | bool | `False` | `native`/`wishbone`/`avalon`/`axi`: add ECC on the port (`data_width` required; AXI gets read-modify-write) |
| `id_width` | int | required (`axi`) | AXI ID width |
| `base` | int | required (`fifo`) | FIFO base address in DRAM (bytes) |
| `depth` | int | required (`fifo`) | FIFO depth (bytes) |

## Examples

Complete configurations in `examples/`:
- `ulx3s.yml`: SDR (MT48LC16M16) with the generic SDR PHY on Lattice ECP5.
- `versa_ecp5.yml`: DDR3 (MT41K64M16) with the ECP5 DDR3 PHY.
- `nexys4ddr.yml`: DDR2 (MT47H64M16) with the Artix-7 PHY (1:2).
- `arty.yml`: DDR3 (MT41K128M16) with the Artix-7 PHY (1:4).
- `genesys2.yml`: DDR3 (MT41J256M16) with the Kintex-7 PHY.
- `kcu105.yml`: DDR4 (EDY4016A) with the Kintex UltraScale PHY.
- `xcu1525.yml`: DDR4 (MT40A512M8) with the UltraScale+ PHY.
