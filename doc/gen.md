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
A `--sim` core has no vendor primitives and no build script: instantiate it in your own testbench,
with the simulator of your choice.

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
| `device` | string | required (GENSDRPHY/ECP5/GW2A/GW5A) | Lattice or Gowin device name (e.g. `LFE5U-45F-6BG381C`, `GW2A-LV18PG256C8/I7`) |
| `devicename` | string | required (GW2A/GW5A) | Gowin device name for the PLL configuration (e.g. `GW2A-18C`, `GW5AST-138B`) |

### PHY / SDRAM module

| Key | Type / choices | Default | Meaning |
|-----|----------------|---------|---------|
| `sdram_phy` | `GENSDRPHY`, `ECP5DDRPHY`, `GW2DDRPHY`, `GW5DDRPHY`, `A7DDRPHY`, `K7DDRPHY`, `V7DDRPHY`, `USDDRPHY`, `USPDDRPHY` | required | PHY class from `litedram.phy` (selects the vendor platform and CRG) |
| `memtype` | `SDR`, `DDR2`, `DDR3`, `DDR4` | required | DRAM type; must match the PHY (GENSDRPHY: SDR, ECP5/GW2A/GW5A: DDR3, A7/K7/V7: DDR2/DDR3, US/USP: DDR3/DDR4) |
| `sdram_module` | string | required | SDRAM module/chip class name from `litedram.modules` (e.g. `MT41K128M16`) |
| `sdram_module_nb` | int | required | Number of byte groups (DQ width = 8 x `sdram_module_nb`, one DM/DQS pair per group) |
| `sdram_rank_nb` | int | required (DDR2/DDR3/DDR4) | Number of ranks (number of `cs_n`/`cke`/`odt`/`clk` pins) |
| `cmd_latency` | int | required (A7/K7/V7/US/USP) | Additional command latency added to CL/CWL |
| `cmd_delay` | int (`< 128`) | `0` | ECP5DDRPHY/GW2DDRPHY/GW5DDRPHY only: command/address delay value |
| `dm_swap` | bool | `False` | ECP5DDRPHY/GW2DDRPHY/GW5DDRPHY only: swap DM lines 0 and 1 |
| `dll_off` | bool | `False` | GW2DDRPHY/GW5DDRPHY only: DDR3 DLL-off mode (CL6/CWL6, for DDR clocks <= 125 MHz) |
| `sdram_rate` | `1:2`, `1:4` | `1:2` | GW5DDRPHY only: PHY frequency ratio (GW2DDRPHY is 1:2) |
| `with_hpio_vref` | bool | `False` | USPDDRPHY/DDR4 only: per-byte read VREF scan through HPIO_VREF (`rd_vref` CSR) |
| `hpio_vref_tune` | int (`0`-`72`) | `31` | Read VREF reset code (58 + 0.5 x code % of VCCO for codes 15-72, 31 = 73.5%) |

### Frequencies

| Key | Type | Default | Meaning |
|-----|------|---------|---------|
| `sys_clk_freq` | float (Hz) | required | System/controller clock; DRAM clock = sys_clk x1 (SDR), x2 (ECP5/GW2A DDR3, GW5A at 1:2, A7/K7/V7 DDR2) or x4 (GW5A at 1:4, A7/K7/V7 DDR3, US/USP) |
| `input_clk_freq` | float (Hz) | required (ECP5/GW2A/GW5A/A7/K7/V7/US/USP), optional (GENSDRPHY on ECP5) | Input clock (PLL/MMCM reference); the Gowin PHYs also run their init from it; see SDR clocking below for GENSDRPHY |
| `sdram_clk_phase` | int (degrees) | `90` | GENSDRPHY with `input_clk_freq`: `sdram_clk` phase relative to `sys_clk` |
| `iodelay_clk_freq` | float (Hz) | required (A7/K7/V7/US/USP) | IDELAYCTRL reference clock frequency |
| `init_clk_freq` | float (Hz) | required (ECP5) | ECP5 init clock domain frequency |

**SDR clocking.** The SDRAM clock has to be phase-shifted from `sys_clk`, otherwise the reads have
no margin. There are two modes with `GENSDRPHY`:
- With `input_clk_freq` (ECP5 only): a PLL in the core generates `sys_clk` from `clk`, and the core
  drives the new `sdram_clk` output (to connect to the SDRAM clock pin) and `pll_locked`. `sys_clk_freq`
  can differ from the board clock, as in `examples/ulx3s.yml` (25 MHz board clock, 50 MHz SDRAM).
- Without it: there is no PLL and no SDRAM clock output. `clk` is used directly as `sys_clk`, and
  the integrator has to generate it at `sys_clk_freq` and drive the SDRAM clock pin with a
  phase-shifted copy. `user_clk` is `sys_clk`: do not forward it to the SDRAM clock pin.

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
| `read_time` | int | `64` | Maximum cycles of reads before switching to writes |
| `write_time` | int | `32` | Maximum cycles of writes before switching to reads |
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
| `pipelined` | bool | `False` | `wishbone`: Wishbone B4 pipelined mode (adds a `stall` output, several transfers in flight) instead of classic |
| `pipelined_depth` | int | `8` | `wishbone`: transfers in flight in pipelined mode |
| `base` | int | required (`fifo`) | FIFO base address in DRAM (bytes) |
| `depth` | int | required (`fifo`) | FIFO depth (bytes) |

## Native port protocol

A `native` user port is the controller's own interface (`LiteDRAMNativePort` in Python, exposed
as `user_port_<name>_*` by the generated core). It is three independent channels in the `user_clk`
domain, and the Wishbone/Avalon/AXI user ports are bridges built on it (`litedram/frontend/`).
Masters that do not speak it natively should prefer one of those: the bridge then owns the
handshakes described here.

| Channel | Signals | Direction (core side) |
|---------|---------|-----------------------|
| Command | `cmd_valid`, `cmd_ready`, `cmd_we`, `cmd_addr` | in, out, in, in |
| Write data | `wdata_valid`, `wdata_ready`, `wdata_we`, `wdata_data` | in, out, in, in |
| Read data | `rdata_valid`, `rdata_ready`, `rdata_data` | out, in, out |

`cmd_addr` is in port words (`data_width/8` bytes). The port `data_width` is the controller's
unless the `data_width` option is set: DRAM data width x 2 x frequency ratio, i.e. the data of one
DRAM burst (the burst length is fixed per DRAM type: 4 for DDR2, 8 for DDR3/DDR4), e.g. 64 bits
for a x16 DDR2 at 1:2, 128 bits for a x16 DDR3 at 1:4, 512 bits for a x64 DDR3/DDR4 at 1:4. A
wider or narrower `data_width` goes through a width converter in the crossbar (several DRAM
accesses per transfer, or several transfers per access): it changes the bytes per transfer, not
the bandwidth, which is the DRAM's. `wdata_we` has one bit per byte, `1` writes the byte.

**Command channel.** A command is accepted on a cycle where `cmd_valid` and `cmd_ready` are both
high; `cmd_we` selects a write (`1`) or a read (`0`) of one port word. `cmd_ready` is
combinational from `cmd_valid` (and the controller state), so `cmd_valid` must not depend on
`cmd_ready`. Several commands can be outstanding: each bank queues up to `cmd_buffer_depth`
commands, and the crossbar does not grant a port in another bank while it has pending commands
in one, so the commands of a port always execute and complete in order.

**Write data channel.** The controller does not wait for `wdata_valid` (it is currently ignored).
For every accepted write command it asserts `wdata_ready` for one cycle when the write is sent to
the DRAM and samples `wdata_data`/`wdata_we` on that cycle. The master has to present the data of
its oldest accepted write from the acceptance of the command until that pulse, and move to the
next write's data on the pulse. On an idle controller the pulse comes a few cycles after the
command; data presented later is not waited for: the write goes out with whatever is on the bus
and the pulse is lost, which corrupts the data and deadlocks a master waiting for the handshake.
A FIFO filled with the data when the command is accepted and popped by `wdata_ready` is the usual
implementation (see `LiteDRAMWishbone2Native` in `litedram/frontend/wishbone.py`).

**Read data channel.** For every accepted read command, `rdata_valid` is high for one cycle with
the data on `rdata_data`, in command order. `rdata_ready` is ignored: the data has to be captured
(or buffered) on that cycle. `rdata_data` is the controller's read data bus, shared by all the
ports: it also carries the data of the other ports' reads, so it is only meaningful with
`rdata_valid`.

**Reset and init.** The port is only meaningful in `user_clk`/`user_rst`. With `block_until_ready`
(the default) the three channels are held off until `init_done` is set without `init_error`;
without it the master has to wait for `init_done` itself.

## Wishbone port protocol

By default a `wishbone` user port is a Wishbone **classic** slave (`adr`, `dat_w`, `dat_r`, `sel`,
`cyc`, `stb`, `we`, `ack`, `err`), as everywhere in LiteX: one transfer at a time, `cyc` and `stb` held
high until the `ack` cycle, the next transfer only after it. `adr` is in port words
(`data_width/8` bytes), `err` is never asserted and, with `block_until_ready`, the port does not
answer before the DRAM init is done.

The classic port has no `stall` and no pipelining: a master that pulses `stb` for one cycle per
transfer and counts the `ack`s later is not supported by it. The bridge only looks at `stb` while
it waits for a command, so the second pulse is lost while the first transfer is in flight, and the
master then waits forever for an `ack` that will never come. `cmd_buffer_depth` is not involved:
it is the depth of the controller's per-bank command queues, which the native, AXI and pipelined
Wishbone ports (several commands in flight) can fill.

**Pipelined mode** (`"pipelined": true` on the port) makes the port a Wishbone B4 pipelined slave
with a `stall` output: a beat is accepted on every cycle where `cyc` and `stb` are high and `stall`
is low, the master can present the next beat right after, and the `ack`s (with `dat_r` for reads)
come later, in order, one per transfer. Up to `pipelined_depth` transfers (default 8) are in
flight before `stall` is held. A classic master must not be connected to a pipelined port: its
`stb` held until `ack` would be seen as repeated beats. Dropping `cyc` with transfers in flight
aborts them: no `ack`, and new beats are stalled until they are drained.

For more throughput than one transfer per round trip, use the full port `data_width` (one
transfer moves a whole DRAM word), the pipelined mode, an `axi` port (several outstanding bursts)
or a `native` port. `cti`/`bte` are not exposed, so every transfer is a single cycle.

A core generated with `--sim` (the same core around the DFI-level DRAM model) is the simplest way
to check a master against these rules before going to hardware.

## Examples

Complete configurations in `examples/`:
- `ulx3s.yml`: SDR (MT48LC16M16) with the generic SDR PHY on Lattice ECP5.
- `versa_ecp5.yml`: DDR3 (MT41K64M16) with the ECP5 DDR3 PHY.
- `tang_primer_20k.yml`: DDR3 (IMD128M16R39CG8GNF) with the Gowin GW2A PHY (1:2).
- `tang_mega_138k_pro.yml`: DDR3 (H5TQ4G63EFR) with the Gowin GW5A PHY (1:2, DLL-off).
- `nexys4ddr.yml`: DDR2 (MT47H64M16) with the Artix-7 PHY (1:2).
- `arty.yml`: DDR3 (MT41K128M16) with the Artix-7 PHY (1:4).
- `genesys2.yml`: DDR3 (MT41J256M16) with the Kintex-7 PHY.
- `kcu105.yml`: DDR4 (EDY4016A) with the Kintex UltraScale PHY.
- `xcu1525.yml`: DDR4 (MT40A512M8) with the UltraScale+ PHY.
