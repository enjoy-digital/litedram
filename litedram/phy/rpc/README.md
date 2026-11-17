# RPC DRAM PHY

[Reduced Pin Count DRAM from Etron](https://etronamerica.com/products/rpc-dram/) is a memory that can deliver DDR3/DDR3L-level
bandwidth using a reduced number of pins (22 or 24). The pins used in RPC are:

* `CLK/CLK#` - differential clock
* `CS#` - chip select
* `DQS/DQS#` - differential data strobe (with optional `DQS0/DQS0#`)
* `DB[15:0]` - similar to `DQ` in DDR3, used for parallel commands, DDR
* `STB` - single serial line, used for serial commands and held low before each transaction, DDR

`DQS` is phase-aligned to `CLK` and other signals are center-aligned to `CLK`.

Unlike in DDR3, RPC doesn't use command/address lines. The commands are encoded on DB/STB lines.
There are 2 types of commands: serial (on STB) and parallel (on DB). Every first command in a
sequence is a parallel command, and any subsequent ones are transmitted as serial commands.

## Hardware tests

Due to the lack of ready boards with RPC DRAM (at the time of development of this PHY) it has been
tested on a modified Arty A7 board. The onboard DDR3 DRAM has been replaced with an [RPC DRAM in a
pin-compatible package](https://store.nacsemi.com/products/detail?part=EM6GA16LBX-12H&stock=ETRN00000000019).
The DDR3 DRAM on Arty A7 normally operates on 1.35V, but the RPC DRAM chip requires 1.5V to work.
To adjust the DRAM voltage, the Power Management IC on Arty A7 was being reconfigured on board
startup. This requires adding I2C pins to the design and connecting them to J11 (exposed pads near
DC jack and user LEDs).

Example code to configure PMIC to use 1.5V:

```c
#include <i2c.h>
unsigned char vbuck2_15 = 0x78;
i2c_write(0x58, 0xa3, &vbuck2_15, sizeof(vbuck2_15));  // Vbuck2A
i2c_write(0x58, 0xb4, &vbuck2_15, sizeof(vbuck2_15));  // Vbuck2B
```

There were however hardware-related issues (possibly wrong CS/STB termination) that prevented
reaching high frequency operation.

A backend for Lattice CertusPro-NX (`nxphy.py`, `NXRPCPHY`) targets the Lattice CertusPro-NX Voice
and Vision Machine Learning board (LFCPNX-VVML-EVN: 2 x EM6GA16LBXA-12H on a 1.5V bank), with the
`lattice_certuspro_nx_vvml` target of LiteX-Boards (`--with-rpcdram`). It builds with Radiant
(timing met at sys_clk 50MHz, CLK 200MHz) and passes the BIOS memory test on the first DRAM of the
board (32MiB, 16-bit, 400MT/s):

```
Read leveling:
  m0, b00: |0111111110000000| delays: 04+-03
  m1, b00: |0111111110000000| delays: 05+-04
Memtest at 0x40000000 (2.0MiB)...
Memtest OK
Memspeed at 0x40000000 (Sequential, 2.0MiB)...
  Write speed: 17.9MiB/s
   Read speed: 26.9MiB/s
```

`mem_test` over the 32MiB also passes. The write shifts and the read enable position were first
settled in a simulation of the PHY with Lattice's primitive models (QuestaSim) and a timing-aware
RPC DRAM model (see `bench/vvml_rpc/sim` in LiteX-Boards), then on the board: STB/CS# need one
more UI there than in simulation.

What the DRAM needs from the controller, found on this board:

* One Request Packet at a time: the commands are sent as a single stream, at least 8 tCK apart
  (Serial Packet after each Request Packet) and not during a burst (`tCCD` covers the latency, the
  burst and tBESL). This is done in the Multiplexer for the RPC memtype.
* A refresh command burst refreshes all the rows of the selected banks (100ns per row in Fast
  Refresh) and no command is accepted until it is done: `tRFC` is the duration of this burst
  (1.64ms for the 4 banks) and `tREFI` its period (32ms).

## Implementation

Important implementation notes:

* Frequency ratio between the controller and DRAM is 1:4.
* There is some additional command latency due to the need to insert DQS and STB preamble.
* Not all RPC commands can be represented with DFI commands, so DFI.reset_n is used to modify the
  encoding (as it is not used to reset the PHY due to the lack of reset pin in RPC).
* DRAM module tWR has to be artificially increased by 1 because data is being serialized over 2
  controller clock cycles (problem would go away after switching to 8 DFI phases).
* A Finite State Machine is used to ensure only correct commands are being sent (during
  initialization or in UTR mode).
* Series 7 backend reqires two phase-shifted clocks: sys4x_90 and sys4x_180.
* Nexus backend uses a single edge clock (sys4x, with sys from ECLKDIV) and X4 gearing: CLK
  (`ODDRX4`) and DQS (`ODDRX4DQS`) are aligned to it, DB (`ODDRX4DQ`) is sent 90 degrees ahead with
  the DQSBUF write clocks and STB/CS# (`ODDRX4`) get a static output delay. On Nexus a pin is only
  bidirectional at X4 with the memory primitives, so reads are captured with the DQS of the DRAM
  (`IDDRX4DQ` and the DQSBUF read clock), not on the edge clock as on Series 7. The latencies of
  the output primitives differ (DB comes out 3 UIs after DQS for the same input), so STB/CS#, DQS
  and DB each have a write shift CSR (in UIs). For reads, the DQSBUF `READ` input gates the DQS: it
  has to open during the DQS preamble and to last as long as the burst (8 tCK); its position is
  set by CSRs (sys_clk cycles, tCK) and by the DQSBUF read clock selection, which the read leveling
  scans as the delay. The DQSBUF returns the burst aligned on sys_clk over the two cycles flagged
  by `DATAVALID`. Only the first DRAM (rank) is used: STB/CS# of the others are held high.

The current code structure is the predecessor of the concepts used in LPDDR4/LPDDR5 PHYs.
RPC-related code is contained in the `litedram/phy/rpc` directory (with some modifications in other
files e.g. `litedram/init.py`). The PHY is split into core part (`basephy.py`) and
platform-dependant backend (`s7phy.py`). The DFI commands from the controller are translated based
on the encoding defined in `commands.py`. There is also a backend for simulation purpose
(`simphy.py`) along with a simulation SoC (`simsoc.py`) and a behavioural DRAM model (`sim.py`:
parallel commands, single WORD reads/writes with data masks). The simulation SoC runs the BIOS
initialization and memory test against the model in Verilator:

```sh
python3 litedram/phy/rpc/simsoc.py
```

Currently this PHY is functional however it has some limitations that need to be addressed. The code
structure could also be refreshed basing on the LPDDR4 code. Potential improvements include the
following:

* Main flaw is the usage of 4 DFI phases. Switching to 8 phases (due to BL=16, DDR) would allow to
  transmit a single data burst in a single controller clock cycle, greatly simplify the core logic.
* Serial commands are not being used, which prevents pipelining. Implementing proper usage of serial
  commands would allow to improve performance.
* Some parts of the implementation could be replaced with common utilities from `phy/utils.py`.
* `RPCPads` (which was also used to map DDR3 pads to RPC ones) should be replaced with similar
  output structure like the one in LPDDR4 PHY.
* All the `do_*_serialization` abstract methods could be removed, letting the platform backend
  use `self.out` of the base class.
* Command encoding could be modified not to depend on DFI.reset_n but use ZQC as in LPDDR4.
* Series 7 PHY could avoid two phase-shifted clocks by using correct clock reset.
