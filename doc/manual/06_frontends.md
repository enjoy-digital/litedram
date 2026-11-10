# Ports and frontends {#frontends}

This chapter describes the user side of the core: the native ports of the crossbar and the
frontends built on them. Read it to connect your own logic to the DRAM, to pick a bus bridge or a
DMA engine, or to test the memory from gateware. The ports and their address mapping come from
[Core architecture](#architecture).

## At a glance {#fe-glance}

| Frontend | Class | Typical use |
|--------------------|---------------------------------------------------------|---------------------------|
| Native port | `LiteDRAMNativePort` | Custom logic, the other frontends |
| Wishbone | `LiteDRAMWishbone2Native` | CPU bus behind the L2 cache |
| Wishbone pipelined | `LiteDRAMWishbonePipelined2Native` | Several Wishbone transfers in flight |
| AXI | `LiteDRAMAXI2Native` | CPU memory buses, AXI masters |
| Avalon-MM | `LiteDRAMAvalonMM2Native` | Avalon masters |
| DMA | `LiteDRAMDMAReader`, `LiteDRAMDMAWriter` | Streams to and from memory |
| DRAM FIFO | `LiteDRAMFIFO` | Large FIFOs in DRAM |
| BIST | `LiteDRAMBISTGenerator`, `LiteDRAMBISTChecker` | Memory tests from gateware |
| Port ECC | `LiteDRAMNativePortECC` | SECDED on any memory width |

## Native port {#fe-native-port}

A native port is the interface of the crossbar itself. It has three independent streams: commands,
write data and read data. Every other frontend is a bridge built on a native port, and owns the
handshakes described here. The table below lists the signals.

| Stream | Signals | Direction |
|------------|------------------------------------------|-------------------------------|
| `cmd` | `valid`, `ready`, `last`, `we`, `addr` | To the core, except `ready` |
| `wdata` | `valid`, `ready`, `data`, `we` | To the core, except `ready` |
| `rdata` | `valid`, `ready`, `data` | From the core, except `ready` |

A command moves one controller word: `we` is 1 for a write and 0 for a read, and `addr` counts
words. The byte enables of `wdata` (`we`) have one bit per byte; a 1 writes the byte. A port has a
mode: `both`, `read` or `write`.

`cmd.last` and the port `flush` signal only matter on a port narrower than the controller word
([Width converters](#fe-converters)).

The two data streams are not ordinary streams, as the figure below shows. The core does not wait
for write data: it pulses `wdata.ready` when it sends the WR, and samples the data on that cycle.
It does not wait for the reader either: `rdata.valid` pulses once per read, in command order.

![Native port exchange. Look at the cyan pulses: the write data is sampled on the `wdata_ready`
pulse, which comes a few cycles after the command, and the read data must be captured on the
`rdata_valid` pulse.](fe_native_port.svg)

Four rules follow from this exchange, on a port at the controller width in `sys`:

- The command is accepted on a cycle with `cmd.valid` and `cmd.ready`. The crossbar raises
  `cmd.ready` only for a port that requests, so `cmd.valid` must not wait for `cmd.ready`.
- The data of the oldest accepted write stays on `wdata` from the command until the
  `wdata.ready` pulse. Data presented later is not waited for: the write goes out with what is on
  the bus. A FIFO filled with the data when the command is accepted is the usual solution.
- `rdata.ready` is ignored: the master captures or buffers the data on the `rdata.valid` pulse.
  The read data bus is shared by every port, so `rdata.data` is only meaningful with
  `rdata.valid`.
- Several commands may be outstanding. The crossbar does not grant a port to another bank while it
  has requests in one, so the commands of a port complete in order.

A port behind a CDC or an up-converter is friendlier: its FIFOs honour `rdata.ready`, and the
up-converter sends a write only once its data is assembled. Capturing on `rdata.valid` and
presenting the write data with the command stays correct on every port.

These rules are the ones of the generated core, where a native port appears as
`user_port_<name>_*` signals ([Integration](#integration)).

## Crossbar {#fe-crossbar}

The crossbar shares the controller between the ports. Each bank has a round-robin arbiter that
picks among the ports that request it. A port that holds requests in one bank is locked: the other
arbiters skip it until those requests complete. The figure below shows the ports, the arbiters and
the shared data path.

![Crossbar. Look at the two paths: commands go through the per-bank arbiters to the bank machines,
while write and read data use one shared path to the multiplexer.](fe_crossbar.svg)

The data path is shared. The write data comes from the port whose bank machine issued the WR,
selected after the write latency of the PHY. The read data goes to every port, and the
`rdata.valid` pulse of the right port tells it apart.

`get_port()` creates a port and its adapters. The table below lists its parameters.

| Parameter | Default | Meaning |
|-------------------|-----------------------|---------------------------------------------------|
| `mode` | `"both"` | `"both"`, `"read"` or `"write"` |
| `data_width` | controller word | Width of the port; another width adds a converter |
| `clock_domain` | `"sys"` | Clock domain of the port; another domain adds a CDC |
| `reverse` | `False` | Reverse the order of the sub-words in a converted word |

### Clock domain crossing {#fe-cdc}

A port in another clock domain goes through asynchronous FIFOs (`LiteDRAMNativePortCDC`): 8
commands, 16 write data words and 32 read data words. The controller does not stall on read data,
so the CDC accepts a read only while the data of the reads in flight fits in its FIFO. A slow
reader stalls the commands instead of losing data.

The read FIFO also bounds the read throughput. A stream of reads only sustains one word per cycle
when the read FIFO covers the round trip of a read, counted in cycles of the port clock.

### Width converters {#fe-converters}

A port wider than the controller word goes through a down-converter. Each user command becomes N
controller commands to consecutive addresses, and the read data of the N commands is regrouped.

A narrower port goes through an up-converter. Consecutive commands to the same controller word are
grouped into one DRAM access, with up to 8 reads in flight. A burst that stops before filling the
word must be closed by `cmd.last` on its last command or by a pulse on the port `flush`. The
Wishbone and Avalon bridges do it for you.

## Choosing a frontend {#fe-choosing}

The right frontend depends on the master and on the traffic. The table below gives the usual
choices.

| Need | Frontend |
|--------------------------------------------|------------------------------------------------|
| A CPU in a LiteX SoC | `add_sdram`: Wishbone with an L2 cache, or the CPU memory bus |
| A master with bursts and IDs | AXI |
| A simple bus master, one transfer at a time | Wishbone classic |
| Several transfers in flight on Wishbone | Wishbone pipelined |
| A data stream to or from memory | DMA reader and writer |
| A FIFO larger than the block RAM | DRAM FIFO |
| A memory test without a CPU | BIST |
| Protection of the data on any memory | Port ECC |

A frontend does not add bandwidth: the DRAM gives the same words per second to every port. A
master gets most of it with the full controller width, several commands in flight and long
sequential runs, which keep the rows open.

## Wishbone {#fe-wishbone}

`LiteDRAMWishbone2Native` is a Wishbone classic slave: one transfer at a time, `cyc` and `stb`
held until `ack`. It adapts the widths: a narrow Wishbone bus groups incrementing bursts into one
controller word, a wide one splits each transfer. `err` is never asserted. This is the bridge that
`add_sdram` puts behind the L2 cache of a LiteX SoC.

The classic slave looks at `stb` only while it waits for a command. A master that pulses `stb` for
one cycle per transfer and counts the `ack` later loses the second transfer and waits forever.
Such a master needs the pipelined bridge.

`LiteDRAMWishbonePipelined2Native` is a Wishbone B4 pipelined slave. It accepts a transfer on each
cycle with `cyc`, `stb` and no `stall`, and returns the `ack` later, in order. Up to `depth`
transfers (8 by default) are in flight before `stall` rises. The Wishbone and native widths must
match.

A classic master must not use the pipelined bridge: its `stb` held until `ack` would count as
repeated transfers. Dropping `cyc` with transfers in flight completes them without `ack` and
stalls new transfers until they drain.

`LiteDRAMNative2Wishbone` goes the other way: it drives a Wishbone slave from a native port of the
same width.

## AXI {#fe-axi}

`LiteDRAMAXI2Native` is an AXI slave on a native port of the same width. It has a write path and a
read path, each with a buffer, and a round-robin arbiter between them for the commands. It supports
FIXED and INCR bursts, WRAP bursts with `with_wrap`, and IDs. The table below lists its
parameters.

| Parameter | Default | Meaning |
|-------------------------------|---------|-------------------------------------------|
| `w_buffer_depth` | 16 | Write buffer depth |
| `r_buffer_depth` | 16 | Read buffer depth |
| `base_address` | 0 | Address of the DRAM on the AXI bus |
| `with_read_modify_write` | `False` | Read-modify-write of partial writes |
| `with_wrap` | `True` | WRAP bursts |

The responses are always OKAY and the bridge does not reorder transactions. Read-modify-write
reads the word, merges the written bytes and writes it back whole. A memory that only takes full
words needs it, such as a DFI ECC core or a port ECC.

In a LiteX SoC, `add_sdram` connects a CPU with an AXI memory bus through this bridge, with an AXI
width converter when the widths differ.

## Avalon-MM {#fe-avalon}

`LiteDRAMAvalonMM2Native` is an Avalon-MM slave with bursts. `max_burst_length` (16 by default)
is the depth of its write burst buffers, not a burst limit: `waitrequest` holds the master when
they fill.

The bridge adds a width converter when the Avalon and native widths differ.
`base_address` places the DRAM on the Avalon bus and `burst_increment` sets the address step of a
burst.

## DMA reader and writer {#fe-dma}

The DMA frontends turn streams into memory accesses. The reader takes addresses on its `sink` and
returns one data word per address on its `source`. The writer takes an address and a data word on
its `sink` and writes them. Both work on a native port or on an AXI port.

The reader reserves room in its FIFO before it sends a read, so that read data is never lost.
`fifo_depth` (16 by default) is therefore the number of reads in flight. The writer buffers
`fifo_depth` writes. With `with_be`, the writer takes a byte enable per byte with each word.

With `with_csr`, an engine drives the addresses from registers. The table below lists them.

| Register | Content |
|------------|---------------------------------------------------------------------|
| `base` | Start address in bytes, word aligned |
| `length` | Length in bytes, a multiple of the word size |
| `enable` | 1 starts the engine; 0 stops and resets it |
| `done` | The last address was issued (not yet in DRAM) |
| `loop` | Restart from `base` after the last address |
| `offset` | Current offset, in words |

## DRAM FIFO {#fe-fifo}

`LiteDRAMFIFO` stores a FIFO in DRAM, through one write port and one read port. It holds as many
bytes as `depth`, from `base`, and adapts the stream width to the width of its ports with
converters.
The figure below shows its paths.

![DRAM FIFO. Look at the two paths from sink to source: the bypass between the two small FIFOs,
and the cyan path through the converters and the DRAM.](fe_fifo.svg)

With `with_bypass`, the FIFO starts in bypass mode: data goes from the pre-FIFO to the post-FIFO
directly. Once the post-FIFO is full and the pre-FIFO holds a whole word, the data takes the DRAM
path. It returns to bypass when the DRAM path is empty. Without bypass, the stream width must
equal the port width.

## BIST {#fe-bist}

The BIST tests the memory from gateware, without a CPU in the data path. The generator writes a
pattern through one port; the checker reads it back through another port and counts the words that
differ. The figure below shows them.

![BIST. Follow the cyan paths: the generator writes through the crossbar, the checker reads the
same area back, and both report to registers.](fe_bist.svg)

The data is a counter or a pseudo-random sequence from an LFSR; the address is incremental or
pseudo-random. Both modes wrap inside the area from `base` to `end`, so `end` must be set in both
modes, with a power-of-2 size. Both engines run in the clock domain of their port; their
registers cross to `sys`. The table below lists the registers.

| Register | Content |
|------------|------------------------------------------------------------------|
| `reset` | A write resets the engine |
| `start` | A write starts a run |
| `done` | The run is complete |
| `base` | Start byte address, aligned to the port width |
| `end` | End byte address, excluded; `end` - `base` a power of 2 |
| `length` | Bytes to write or check, a multiple of the port width |
| `random` | `data` and `addr` fields: pseudo-random data or addresses |
| `ticks` | Cycles of the last run |
| `errors` | Checker only: words that did not match |

In a LiteX SoC, `add_sdram(with_bist=True)` adds a generator and a checker on two ports
(`sdram_generator`, `sdram_checker`). The BIOS command `sdram_bist` runs them and reports the
throughput, and the CK phase leveling uses them as a traffic test ([Per-family
differences](#cal-families)).

## Port ECC {#fe-ecc}

`LiteDRAMNativePortECC` adds SECDED between a user port and a wider crossbar port. It splits each
user word into `burst_cycles` pieces (8 by default) and stores each piece with its check bits. The
user port is therefore narrower than the crossbar port, and the check bits take part of the
capacity and of the bandwidth.

The table below compares it with the DFI ECC of the core ([DFI ECC](#arch-dfi-ecc)).

| Item | Port ECC | DFI ECC |
|---------------------|---------------------------------------------|---------------------------------------|
| Memory | Any width | 72 bits per 64 data bits |
| Scope | One port | Every port of the core |
| Cost | Capacity and bandwidth of the check bits | The ECC byte lane of the memory |
| Partial writes | Not supported within an ECC word | Not supported within a 64-bit word |
| Registers | `enable`, `clear`, `sec_errors`, `ded_errors` | `enable`, `clear`, `sec`, `ded` |

`with_error_injection` adds an 8-bit `flip` register that inverts the low 8 bits of each written
codeword, to test the correction. `with_we_error_detection` adds `we_errors`, which counts writes with partial byte
enables. The generator `ecc` option of a port builds this frontend; on an AXI port it also turns on
read-modify-write.

## In the code {#fe-code}

| Class | File |
|--------------------------------------------|---------------------------------------|
| `LiteDRAMNativePort` | `litedram/common.py` |
| `LiteDRAMCrossbar` | `litedram/core/crossbar.py` |
| `LiteDRAMNativePortCDC`, `LiteDRAMNativePortConverter` | `litedram/frontend/adapter.py` |
| `LiteDRAMWishbone2Native`, `LiteDRAMWishbonePipelined2Native` | `litedram/frontend/wishbone.py` |
| `LiteDRAMAXI2Native` | `litedram/frontend/axi.py` |
| `LiteDRAMAvalonMM2Native` | `litedram/frontend/avalon.py` |
| `LiteDRAMDMAReader`, `LiteDRAMDMAWriter` | `litedram/frontend/dma.py` |
| `LiteDRAMFIFO` | `litedram/frontend/fifo.py` |
| `LiteDRAMBISTGenerator`, `LiteDRAMBISTChecker` | `litedram/frontend/bist.py` |
| `LiteDRAMNativePortECC` | `litedram/frontend/ecc.py` |

Where to go next: [Integration](#integration) to add ports in a SoC or a generated core,
[Simulation and verification](#simulation) to test a master before hardware, [Debugging](#debugging)
for the BIST in practice.
