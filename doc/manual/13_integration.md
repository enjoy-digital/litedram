# Integration {#integration}

This chapter explains how to add LiteDRAM to your own design. It starts with a LiteX SoC, the
native way, then covers the ports for user logic, the clocks and the constraints. It ends with the
standalone Verilog core for designs built without LiteX, and a checklist to port LiteDRAM to a new
board or memory.

## At a glance {#integ-glance}

| Item | Value |
|---------------------------|------------------------------------------------------------------|
| Language | Python (Migen, LiteX); Verilog through `litedram_gen` |
| LiteX helper | `add_sdram` of the LiteX SoC class |
| Core class | `LiteDRAMCore`: controller, crossbar, DFI injector, optional ECC |
| User interface | Native ports of the crossbar; Wishbone, AXI, Avalon, DMA and FIFO frontends |
| Initialization | LiteX BIOS, firmware of the generated core, or your own logic |
| Reference designs | LiteX-Boards targets, `bench/`, `examples/` |

## Integration in a LiteX SoC {#integ-litex}

A LiteX SoC with DRAM is a chain of parts, shown in the figure below. The CPU reaches the DRAM
through an L2 cache and a port of the crossbar. The controller turns the requests of all the ports
into DRAM commands, and the PHY drives the pins. User logic takes ports of its own on the same
crossbar.

![LiteDRAM in a LiteX SoC. The CPU goes through the L2 cache; the cyan arrow is a port that user
logic requests from the crossbar with get_port(), and the BIST takes two more when it is
enabled. The PHY is built by the target and passed to the core.](integ_soc.svg)

The `add_sdram` method of the LiteX SoC class builds this chain from a PHY and a module. The
example below is the DRAM part of the Arty A7 target of LiteX-Boards: a 16-bit DDR3 on
`A7DDRPHY` at 1:4. The clock generator stands for the one of your board.

```python
from litex.soc.integration.soc_core import SoCCore

from litedram.modules import MT41K128M16
from litedram.phy     import s7ddrphy

class MySoC(SoCCore):
    def __init__(self, platform, sys_clk_freq=100e6, **kwargs):
        # Your clock generator: sys, sys4x, sys4x_dqs (90 degrees), IDELAYCTRL.
        self.crg = _CRG(platform, sys_clk_freq)
        SoCCore.__init__(self, platform, sys_clk_freq, ident="My SoC",
            **kwargs)

        # PHY: Artix-7, DDR3 at 1:4, on the ddram pins of the platform.
        self.ddrphy = s7ddrphy.A7DDRPHY(platform.request("ddram"),
            memtype      = "DDR3",
            nphases      = 4,
            sys_clk_freq = sys_clk_freq)

        # Core, main RAM region and CPU connection.
        self.add_sdram("sdram",
            phy           = self.ddrphy,
            module        = MT41K128M16(sys_clk_freq, "1:4"),
            l2_cache_size = 8192)
```

`add_sdram` builds a `LiteDRAMCore` from the settings of the PHY and of the module, and maps the
DRAM as the `main_ram` region, sized from the module geometry. It connects the CPU through its own
memory buses when it has some, AXI or native; otherwise through a Wishbone slave, the L2 cache and
a bridge to a native port.

The LiteX `Builder` then writes `sdram_phy.h` with the initialization sequence and the
capabilities of the PHY, and the BIOS initializes and calibrates the DRAM at every boot. The main
parameters of `add_sdram` are below.

| Parameter | Default | Use |
|-------------------------------------|--------------|---------------------------------------|
| `name` | `"sdram"` | Name of the core and of its registers |
| `phy` | required | The PHY instance |
| `module` | required | The module instance, see below |
| `origin` | `main_ram` | Base address of the DRAM in the memory map |
| `size` | module size | Smaller main RAM region than the module |
| `with_bist` | `False` | BIST generator and checker, on two ports |
| `with_soc_interconnect` | `True` | `False`: core only, no main RAM, no CPU path |
| `l2_cache_size` | 8192 | L2 cache in bytes; 0 for none |
| `l2_cache_min_data_width` | 128 | Minimum refill width of the L2 cache, in bits |
| other keywords | | `LiteDRAMCore` and `ControllerSettings` parameters |

`add_sdram` lives in LiteX (`litex/soc/integration/soc.py`). When the module is built from SPD
data, it also stores the SPD bytes in a ROM, `sdram_spd`, so that they can be checked at run
time.

### The module {#integ-module}

The module describes the DRAM: geometry, timings and speed grades. It is built with the system
clock and the frequency ratio of the PHY, here `"1:4"`, and converts its timings into system clock
cycles. `SDRAMModule.from_spd_data` builds one from a dump of the SPD EEPROM of a DIMM.
[Memory modules](#modules) lists the classes and explains how to add one.

### The PHY parameters {#integ-phy}

The 7-Series PHYs take the parameters below; the other PHYs follow the same pattern.
[DDR PHYs](#phys) gives the parameters of each one, and [Build options](#build-options) the
complete lists.

| Parameter | Default | Use |
|------------------------|--------------|--------------------------------------------------|
| `pads` | required | The `ddram` record of the platform |
| `memtype` | `"DDR3"` | `"DDR2"` or `"DDR3"` |
| `nphases` | 4 | 2 or 4, the frequency ratio 1:2 or 1:4 |
| `sys_clk_freq` | 100e6 | System clock, to compute the latencies |
| `iodelay_clk_freq` | 200e6 | Reference clock of the IDELAYCTRL |
| `cl`, `cwl` | from rate | CAS latency and CAS write latency |
| `cmd_latency` | 0 | Extra latency added to CL and CWL |

The termination and the driver strength of the DRAM are written in its mode registers at
initialization. To change them, add them to the settings of the PHY; an omitted value keeps its
default. The values are strings in ohms, as below for a DDR3:

```python
self.ddrphy.settings.add_electrical_settings(
    rtt_nom = "40ohm",
    rtt_wr  = "120ohm",
    ron     = "34ohm")
```

### Controller parameters {#integ-controller}

The other keyword arguments of `add_sdram` go to `LiteDRAMCore`: the `ControllerSettings` keys
and the DFI ECC. The example below enables the dynamic ODT of DDR3 and the bandwidth registers.
[Controller](#controller) describes each option.

```python
self.add_sdram("sdram",
    phy              = self.ddrphy,
    module           = MT41K128M16(sys_clk_freq, "1:4"),
    with_dynamic_odt = True,
    with_bandwidth   = True)
```

`with_ecc=True` adds the SECDED ECC at DFI level, for PHYs with a ninth byte lane (72-bit
interfaces). The main RAM then holds 64 data bits per 72-bit beat.

## Ports for user logic {#integ-ports}

User logic gets its own path to the DRAM with a port of the crossbar. `get_port()` returns a
native port: a command channel, a write data channel and a read data channel, described in
[Ports and frontends](#frontends). The crossbar arbitrates between the ports, the CPU included,
so a port shares the bandwidth of the DRAM with the others.

```python
port = self.sdram.crossbar.get_port(
    mode         = "both",
    data_width   = None,
    clock_domain = "sys")
```

| Argument | Default | Use |
|------------------|------------|------------------------------------------------------------|
| `mode` | `"both"` | `"read"`, `"write"` or `"both"` |
| `data_width` | controller | Other widths add a converter |
| `clock_domain` | `"sys"` | Other domains add a clock domain crossing |
| `reverse` | `False` | Order of the words in a width converter |

The native width of a port is the data of one DRAM burst: 128 bits for the 16-bit DDR3 of the
Arty A7 at 1:4. Port addresses are in port words from the start of the DRAM, which the CPU sees at
the origin of `main_ram`. Keep the region of user logic away from the memory of the software.

### DMA and FIFO frontends {#integ-dma}

The DMA frontends move streams of DRAM words. With `with_csr=True`, each one generates its own
addresses from registers: `base` and `length` in bytes, `enable`, `done`, `loop` and `offset`. The
example below stores a stream of user logic in DRAM and plays it back. `user_source` and
`user_sink` stand for streams of your logic, with a `data` field of the port width.

```python
from litedram.frontend.dma import LiteDRAMDMAReader, LiteDRAMDMAWriter

# Writer: stores the stream from base to base + length.
self.dram_writer = LiteDRAMDMAWriter(
    port     = self.sdram.crossbar.get_port(mode="write"),
    with_csr = True)
self.comb += user_source.connect(self.dram_writer.sink)

# Reader: plays the same region back as a stream.
self.dram_reader = LiteDRAMDMAReader(
    port     = self.sdram.crossbar.get_port(mode="read"),
    with_csr = True)
self.comb += self.dram_reader.source.connect(user_sink)
```

The software sets `base` and `length`, then `enable`, after the BIOS has initialized the DRAM.
Without registers, a DMA takes the addresses on its `sink` instead, with the data for the
writer.

`LiteDRAMFIFO` turns a region of the DRAM into a large FIFO for a stream. With `with_bypass`,
the data skips the DRAM while the small FIFOs of the frontend are enough. `base` and `depth` are
in bytes; the region below starts at 128 MiB into the DRAM.

```python
from litedram.frontend.fifo import LiteDRAMFIFO

self.dram_fifo = LiteDRAMFIFO(
    data_width  = 128,
    base        = 0x08000000,
    depth       = 0x01000000,
    write_port  = self.sdram.crossbar.get_port(mode="write"),
    read_port   = self.sdram.crossbar.get_port(mode="read"),
    with_bypass = True)
```

AXI, Wishbone and Avalon masters connect to a port through a bridge, such as
`LiteDRAMAXI2Native`. [Ports and frontends](#frontends) describes each frontend and its
parameters.

## Clocks and constraints {#integ-clocks}

The PHY works in several clock domains that the clock generator of the target creates: the system
clock of the controller, faster clocks for the serializers and, on some families, a shifted clock
and a delay reference. The figure below shows those of the Arty A7 target.

![Clocks of a 7-Series DDR3 PHY at 1:4, as the Arty A7 target makes them. One PLL makes the
system clock, the 4x clock of the serializers, a 4x clock shifted by 90 degrees for the strobes
and the 200 MHz reference of the IDELAYCTRL.](integ_clocks.svg)

The table below lists the clock domains each PHY expects from the clock generator. The domain
names are those of the LiteX-Boards targets and of the generator.

| PHY | Clock domains |
|-----------------------------|----------------------------------------------------------------|
| `GENSDRPHY` | `sys`, and a phase-shifted copy for the SDRAM clock pin |
| `HalfRateGENSDRPHY` | `sys`, `sys2x`, and a phase-shifted `sys2x` for the clock pin |
| `A7DDRPHY`, DDR3 | `sys`, `sys4x`, `sys4x_dqs` at 90 degrees, IDELAYCTRL reference |
| `A7DDRPHY`, DDR2 at 1:2 | `sys`, `sys2x`, `sys2x_dqs` at 90 degrees, IDELAYCTRL reference |
| `K7DDRPHY`, `V7DDRPHY` | `sys`, `sys4x`, IDELAYCTRL reference |
| `USDDRPHY`, `USPDDRPHY` | `sys4x`, `sys` divided from it, IDELAYCTRL reference |
| `ECP5DDRPHY` | `sys2x` on the edge clock, `sys` divided from it, `init` |
| `NexusDDRPHY` | `sys2x`, `sys`, `init` |
| `GW2DDRPHY`, `GW5DDRPHY` | `sys2x` or `sys4x`, `sys` divided from it, `init` |

`K7DDRPHY` on HR banks, with `with_odelay=False`, needs `sys4x_dqs` like `A7DDRPHY`. The
IDELAYCTRL reference runs at 200 MHz on the 7-Series targets; UltraScale needs at least 200 MHz
and UltraScale+ at least 300 MHz. The ECP5 PHY at 1:4 adds a `sys4x` edge clock.

The constraints come from the platform and the target, not from LiteDRAM. A LiteX-Boards platform
constrains its input clock, and the toolchain derives the PLL outputs from it. The platform also
sets the IO standards, the termination and the VREF of the DRAM pins, as [IO standards, VREF and
termination](#boards-vref) shows.

## Standalone core with litedram_gen {#integ-standalone}

The generator builds a standalone Verilog core from a YAML file, for designs built without LiteX:
another HDL flow, a versioned core, or a design reviewed as Verilog. The core holds the clock
generator, the PHY, the controller, the crossbar, the user ports and, optionally, a CPU that runs
the initialization.

```sh
# Core in ./build (--output-dir to change it).
litedram_gen examples/arty.yml
# Name of the generated module and files.
litedram_gen --name my_core examples/arty.yml
# Same core around the DFI-level simulation model.
litedram_gen --sim examples/arty.yml
```

The generator writes the Verilog and its memory files in `build/gateware/`, and the firmware in
`build/software/`. It accepts the arguments of the LiteX `Builder`, such as `--csr-csv` for the
register map. It never runs the vendor tools: the core is built by the project that instantiates
it.

A `--sim` core has no vendor primitives and no build script. It replaces the PHY and the DRAM by a
model at DFI level, so a testbench can check a master against the ports with any simulator.

### Ports of the core {#integ-standalone-ports}

The figure below shows the port groups of the generated module, `litedram_core` by default.

![Port groups of a core made by litedram_gen. User logic sees the user ports and the status of
the initialization; the initialization runs from the CPU of the core, or from your logic through
wb_ctrl.](integ_standalone.svg)

| Ports | Direction | Use |
|-----------------------------|-----------|-------------------------------------------------------|
| `clk`, `rst` | in | Input clock and reset of the clock generator |
| `pll_locked` | out | The PLL of the core is locked |
| `user_clk`, `user_rst` | out | Clock and reset of the user ports: the system clock |
| `init_done`, `init_error` | out | The initialization is over, and its result |
| `ddram_*`, `sdram_*` | pads | The DRAM pins, DDR or SDR |
| `user_port_<name>_*` | both | One group per user port |
| `user_fifo_<name>_*` | both | One group per `fifo` user port |
| `uart_*` | both | Console of the CPU: RS232 pins or a FIFO interface |
| `wb_ctrl_*` | both | Wishbone control bus, with `cpu: None` |
| `sdram_clk` | out | Clock of an SDR SDRAM, when the core has a PLL |

The user ports run in `user_clk`. With `block_until_ready`, the default, a port holds its master
off until `init_done` is set without `init_error`. [Ports and frontends](#frontends) gives the
protocol of the native and Wishbone ports.

### YAML configuration {#integ-yaml}

The YAML file describes the PHY, the DRAM, the clocks, the CPU and the user ports. The example
below is a 16-bit DDR3 on an Artix-7: `examples/arty.yml` reduced to two user ports, with the
Wishbone port in pipelined mode.
[Build options](#build-options) lists every key with its default.

```yaml
{
    # General.
    "speedgrade": -1,         # FPGA speedgrade, for the PLL.
    "cpu":        "vexriscv", # CPU of the initialization, or None.
    "memtype":    "DDR3",
    "uart":       "rs232",

    # PHY and DRAM.
    "sdram_phy":       "A7DDRPHY",
    "sdram_module":    "MT41K128M16",
    "sdram_module_nb": 2,     # Byte groups: 16-bit data bus.
    "sdram_rank_nb":   1,
    "cmd_latency":     0,

    # Clocks: DDR3 at 4 x sys_clk_freq.
    "input_clk_freq":   100e6,
    "sys_clk_freq":     100e6,
    "iodelay_clk_freq": 200e6,

    # User ports.
    "user_ports": {
        "native_0":   {"type": "native"},
        "wishbone_0": {"type": "wishbone", "pipelined": True},
    },
}
```

| Port type | Interface | Required options |
|---------------|-----------------------------------------------------|---------------------|
| `native` | Native port of the crossbar | none |
| `wishbone` | Wishbone classic, or B4 pipelined with `pipelined` | none |
| `avalon` | Avalon-MM | none |
| `axi` | AXI | `id_width` |
| `fifo` | Stream FIFO in DRAM | `base`, `depth` |

Every port also takes `block_until_ready` and `data_width`; `native`, `wishbone`, `avalon` and
`axi` take `ecc` for an ECC on the port. The generator supports the SDR PHY on ECP5 and the
7-Series, UltraScale(+), ECP5, GW2A and GW5A DDR PHYs; the Spartan-6, Nexus, LPDDR4, LPDDR5 and
RPC PHYs are used from Python only.

### Initialization {#integ-init}

With a CPU in the core, as in `examples/arty.yml`, the core initializes the DRAM by itself at
power-up. Its firmware runs the same initialization and calibration as the BIOS of a LiteX SoC,
prints them on its UART, and sets `init_done`. The output is the one of [Getting
started](#gs-load).

With `cpu: None`, the core has no CPU and no firmware. It exposes `wb_ctrl`, a Wishbone slave to
its registers, and your logic or an external CPU runs the initialization. The generated
`sdram_phy.h` has `init_sequence()`, which sends the JEDEC commands only; the whole sequence is
below.

1. Switch the DFI to software control (`sdram_dfii_control`).
2. Reset the PHY (`ddrphy_rst`), on the PHYs that have it.
3. Run `init_sequence()`.
4. Run the write and read leveling, on the PHYs that support it.
5. Switch the DFI back to hardware control.
6. Optionally, run a memory test.
7. Write 1 to `ddrctrl_init_done`, and to `ddrctrl_init_error` on a failure.

Step 7 is required with `block_until_ready`: the user ports do not answer before
`ddrctrl_init_done` is set, and `init_sequence()` does not write it. This also holds for a `--sim`
core, which needs no calibration.

`csr.csv` gives byte addresses, while `wb_ctrl_adr` is a word address: shift the byte address
right by 2. A register at `0x1004` is at `wb_ctrl_adr = 0x401`. [Initialization and
calibration](#calibration) describes each step of the sequence.

### Constraints and SDR clocking {#integ-standalone-constraints}

The generated constraints neither constrain the input clock nor set the IO standards and
locations of the DRAM pins: the project that integrates the core does. Three steps are needed.

- Define `clk` at `input_clk_freq`, for example `create_clock -period 10.000 [get_ports clk]`
  for 100 MHz with Vivado. The toolchain then derives the PLL outputs.
- Take the IO standards, the termination and the VREF from a LiteX-Boards platform with the same
  FPGA family and memory type.
- With Vivado, add the generated `litedram_core.xdc`: it holds the false paths of the reset
  synchronizers of the core.

An SDR SDRAM needs a clock phase-shifted from the system clock. With `input_clk_freq`, on ECP5
only, the core has a PLL and drives the `sdram_clk` output, shifted by `sdram_clk_phase`
(90 degrees by default). Without it, `clk` is the system clock and your design drives the SDRAM
clock pin with a phase-shifted copy; do not forward `user_clk` to it.

## Porting to a new board or memory {#integ-porting}

A new board needs a platform, a clock generator, a PHY and a module. The checklist below follows
the order of a bring-up; start from the LiteX-Boards target closest to your board.

1. **Platform**: describe the DRAM pins as a `ddram` or `sdram` record, with the IO standards,
   the termination and the VREF of a board with the same FPGA family and memory type
   ([Requirements for a custom board](#boards-custom)).
2. **Module**: find the chip or the DIMM in `litedram/modules.py`, or add a class from its
   datasheet ([Memory modules](#modules)). Check the geometry: rows, columns, banks and data
   width.
3. **Clocks**: create the clock domains of the PHY ([Clocks and constraints](#integ-clocks)).
   Start with a system clock below the default of the target; a lower DRAM rate gives wider
   calibration windows.
4. **PHY**: choose the class of the family, the memory type and the ratio. Use `PHYPadsReducer`
   to start with some byte lanes only.
5. **Core**: call `add_sdram` with the PHY and the module, or write the YAML file of the
   generator from the closest example.
6. **Bring-up**: build, load and read the calibration output of the BIOS, as [Getting
   started](#gs-calibration) shows. Then raise the system clock step by step and keep a margin.

Calibration does not check every timing: run a memory test through the controller at each new
frequency, with `mem_test` from the BIOS or the BIST. [Debugging](#debugging) explains how to
read a failure.

Where to go next: [Ports and frontends](#frontends) for the user interfaces, [Examples and
targets](#examples) for complete designs, [Debugging](#debugging) when the DRAM does not
calibrate.
