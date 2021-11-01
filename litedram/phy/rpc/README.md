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

The current code structure is the predecessor of the concepts used in LPDDR4/LPDDR5 PHYs.
RPC-related code is contained in the `litedram/phy/rpc` directory (with some modifications in other
files e.g. `litedram/init.py`). The PHY is split into core part (`basephy.py`) and
platform-dependant backend (`s7phy.py`). The DFI commands from the controller are translated based
on the encoding defined in `commands.py`. There is also a backend for simulation purpose
(`simphy.py`) along with a simulation SoC (`simsoc.py`).

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
