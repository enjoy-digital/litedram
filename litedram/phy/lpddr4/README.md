# LPDDR4

This is an overview of the LPDDR4 PHY code.

> Most hyperlinks are permalinks to the code version form the Pull Request that added LPDDR4 support.

## Directory structure

The code is split into several files, most grouped under the `litedram/phy/lpddr4` directory. This inclues:
```
litedram/phy/lpddr4/
├── basephy.py
├── commands.py
├── __init__.py
├── s7phy.py
├── simphy.py
├── sim.py
├── simsoc.py
└── utils.py
test/
└── test_lpddr4.py
```

There are also some modifications to common files:
```
litedram/
├── init.py        # LPDDR4 initialization sequence and other BIOS-related definitions
├── modules.py     # LPDDR4 module: MT53E256M16D1
└── common.py      # defined LPDDR4 burst length
github/workflows/
└── ci.yml         # dependencies for running Verilator
```

## Core

The LPDDR4 PHY is split into vendor-agnostic core that runs only in memory controller's clock domain, and which is then extended by different wrappers.

### Commands

`commands.py` contains modules for translating DFI commands to sequences on LPDDR4 CS/CA lines. LPDDR4 requires sending some of the commands as pairs of subcommands, e.g. READ (cas_n=0, ras_n=1, we_n=1) becomes `READ-1` + `CAS-2`. Each subcommand is sent over 2 clock cycles, so a command can take 2 or 4 clock cycles. In the first stage DFI command is translated into corresponding pair of commands using [DFIPhaseAdapter](https://github.com/antmicro/litedram/blob/bd71391e5cbb18de7327b314896a12b0776e6c89/litedram/phy/lpddr4/commands.py#L69-L80) (one for each phase). Adapters then use [Command](https://github.com/antmicro/litedram/blob/bd71391e5cbb18de7327b314896a12b0776e6c89/litedram/phy/lpddr4/commands.py#L133-L146) to map subcommands to CS/CA sequences based on the command truth table.

As not all LPDDR4 commands seem to directly map to DFI commands (there are more LPDDR4 commands), we handle DFI ZQC and MRS commands in a special manner.
LPDDR4 has a 256-bit Mode Register space, so 8 bits are needed to address a register. We use DFI.address to encode both address *and* value of the MRS (Mode Register Set) command as defined [here](link) (other PHYs use DFI.bank for register address and DFI.address for register value).
ZQC is translated to LPDDR4 MPC (MultiPurpose Command). MPC operand (OP[6:0]) is sent on DFI.address and is interpreted as defined [here](https://github.com/antmicro/litedram/blob/bd71391e5cbb18de7327b314896a12b0776e6c89/litedram/phy/lpddr4/commands.py#L6-L19).
Both MRS and ZQC are handled in the initialization code [here](https://github.com/antmicro/litedram/blob/bd71391e5cbb18de7327b314896a12b0776e6c89/litedram/init.py#L568-L578).

> NOTE: Currently ZQC is performed only during initialization. Doing ZQC during runtime will require specialised Refresher implementation because ZQC has to be done as two different commands and is performed in the background (so other commands can be issued in between) but takes a lot of time (so we cannot just block other commands for that long). It is described [here](https://github.com/antmicro/litedram/blob/bd71391e5cbb18de7327b314896a12b0776e6c89/litedram/modules.py#L980-L982)

In LPDDR4 there are also separate commands for `WRITE` and `MASKED-WRITE`. Masked write has significantly increased `tCCD` (32 tCK vs 8 for non-masked write). Currently the [masked_write](https://github.com/antmicro/litedram/blob/bd71391e5cbb18de7327b314896a12b0776e6c89/litedram/phy/lpddr4/basephy.py#L52) parameter defines which command is used and it defaults to using `MASKED-WRITE` to avoid issues when masking is needed.

Currently both tCCD values are in the module, but [we always use the larger one](https://github.com/antmicro/litedram/blob/bd71391e5cbb18de7327b314896a12b0776e6c89/litedram/modules.py#L983) because we cannot change it dynamically based on the command type. In general `SDRAMModule` and the PHY are created independently, so this would have to be configured in the SoC.

### PHY

`basephy.py` defines `LPDDR4PHY` which is the core of the PHY, wrappers use it as a base class. It is meant to work in the sysclk domain and it converts `self.dfi` to `self.out` of type [LPDDR4Output](https://github.com/antmicro/litedram/blob/bd71391e5cbb18de7327b314896a12b0776e6c89/litedram/phy/lpddr4/basephy.py#L28-L46) which groups all the signals that need to be serialized in given sysclk clock. Concrete implementations of LPDDR4 PHYs derive from this class and (de-)serialize LPDDR4Output (e.g. Series 7 PHY uses I/OSERDESE2 primitives).

`LPDDR4PHY` has 8 DFI phases due to 16n prefetch used in LPDDR4 memory. This way we can write whole burst in a single memory controller's clock cycle. Core PHY implementation already includes `BitSlip` modules and provides CSRs to control read/write bitslips. However any DQ/DQS delays are to be implemented in concrete PHYs.

The PHY instantiates one [DFIPhaseAdapter](https://github.com/antmicro/litedram/blob/bd71391e5cbb18de7327b314896a12b0776e6c89/litedram/phy/lpddr4/basephy.py#L155) for each phase (8 total). Because command sent on any phase can span up to 4 cycles (=4 phases; 1 phase maps to 1 DRAM SDR cycle) there is currently [some logic to prevent any command overlaps](https://github.com/antmicro/litedram/blob/bd71391e5cbb18de7327b314896a12b0776e6c89/litedram/phy/lpddr4/basephy.py#L177-L187), which is currently [optional and disabled by default](https://github.com/enjoy-digital/litedram/blob/996d0add264a2f21ce76ff791026263f5c0bffe3/litedram/phy/lpddr4/basephy.py#L218-L237) to avoid wasting resources. This way sending overlapping commands will be considered undefined behavior (as commands from all phases will simply be ORed). Another result of commands spanning several phases is that commands may span two subsequent sysclk cycles (command on phase 6 will effectively span subsequent phases 6, 7, 0, 1). For constant `BitSlip`s have been used (increasing the latency by 1).

> [ConstBitSlip](https://github.com/antmicro/litedram/blob/bd71391e5cbb18de7327b314896a12b0776e6c89/litedram/phy/lpddr4/utils.py#L32-L47) is just a minor modification of `BitSlip` so maybe it would be good to extend the `BitSlip` class with an option to have a constant slip.

The rest of the PHY is fairly similar to other PHYs, performing DQ/DQS/DMI serialization.

Because concrete implementations will further increase PHY latency, `LPDDR4PHY` provides latency parameters `ser_latency` and `des_latency` that should be passed by the wrapper. These are used in the core to correctly calculate `PhySettings`. The latency calculations have been [written in verbose manner](https://github.com/antmicro/litedram/blob/bd71391e5cbb18de7327b314896a12b0776e6c89/litedram/phy/lpddr4/basephy.py#L80-L111), so it should be easier to analyze those and find possible bugs.

### Double rate PHY

Because we use 8 DFI phases, DDR signals like DQ would require 16:1 serialization. Series 7 FPGAs provide OSERDESE2 that can in theory do up to 14:1, but that is not enough. For this reason [DoubleRateLPDDR4PHY](link) is a wrapper over `LPDDR4PHY` that does partial (de-)serialization, effectively halving the widths of all signals, so that 8:1 serializers can be used. This however increases PHY latency and the current implementations of `Serializer` and `Deserializer` could be improved to add lower latencies than they do now.

## Series 7 PHY

[S7LPDDR4PHY](https://github.com/antmicro/litedram/blob/bd71391e5cbb18de7327b314896a12b0776e6c89/litedram/phy/lpddr4/s7phy.py#L12) wraps `DoubleRateLPDDR4PHY` adding I/OSERDESE2 and I/ODELAYE2 primitives. It is fairly similar to the regular `S7DDRPHY`. Currently variants for different S7 families are available just as in S7DDRPHY.

## Simulation

Along with the implementation of LPDDR4 PHY there are also ways to test the PHY in simulation.

In `lpddr4/simphy.py` there are implementations of `LPDDR4SimPHY` and `DoubleRateLPDDR4SimPHY` that wrap the core and perform serialization using Migen serializers. These classes can also serve as a reference for implementing concrete PHYs. Simulation PHYs are used directly for Migen unit tests. Unit tests are defined in `test_lpddr4.py` ([LPDDR4Tests](https://github.com/antmicro/litedram/blob/bd71391e5cbb18de7327b314896a12b0776e6c89/test/test_lpddr4.py#L403) and [TestSimSerializers](https://github.com/antmicro/litedram/blob/bd71391e5cbb18de7327b314896a12b0776e6c89/test/test_lpddr4.py#L74) that tests `Serializer`/`Deserializer`). The tests just specify sequences of commands on DFI and check expected sequences on pads.

Aside from Migen tests, there is also an implementation of LPDDR4 DRAM simulator in `lpddr4/sim.py`. It has been written based on LPDDR4 documentation. This is basically a command decoder with logic responsible for transmitting data. [SimLogger class](https://github.com/antmicro/litedram/blob/bd71391e5cbb18de7327b314896a12b0776e6c89/litedram/phy/lpddr4/utils.py#L173) has been developed to improve the simulator (could be useful for other simulations) and allows for convenient logging of errors from `comb` context (so is usable inside FSM, [example usage](https://github.com/antmicro/litedram/blob/bd71391e5cbb18de7327b314896a12b0776e6c89/litedram/phy/lpddr4/sim.py#L202-L203)). The simulator reports timing violations and incorrect commands through the logger. The simulator is then used in [SimSoC](https://github.com/antmicro/litedram/blob/bd71391e5cbb18de7327b314896a12b0776e6c89/litedram/phy/lpddr4/simsoc.py#L161-L193) and can be run similarily to `litex_sim`. In [VerilatorLPDDR4Tests](https://github.com/antmicro/litedram/blob/bd71391e5cbb18de7327b314896a12b0776e6c89/test/test_lpddr4.py#L959) there are tests that run the Verilator-based simulations and check for errors/warnings and `Memtest OK`. The simulator allows to test the implementation of all the modules beside the PHY implementaion for concrete FPGA (e.g. `S7LPDDR4PHY`).

The simulator can be run using e.g.
```
python litedram/phy/lpddr4/simsoc.py --log-level info --finish-after-memtest --double-rate-phy --l2-size 0
```
or with tracing enabled (which will also generate a GTKWave savefile for viewing the signals), e.g.
```
python litedram/phy/lpddr4/simsoc.py --log-level info --finish-after-memtest --trace --trace-fst --gtkw-savefile
```
Log level can be controlled in more fine-grained manner by using e.g. `--log-level cmd=info,data=debug`.

The simulation will even perform read leveling, but in essence it only changes bitslip, it [fakes having delays](https://github.com/antmicro/litedram/blob/bd71391e5cbb18de7327b314896a12b0776e6c89/litedram/phy/lpddr4/simsoc.py#L135-L138) and in `init.py` we set `#define SDRAM_PHY_DELAYS 1`.

An example (partial) simulation log can look like:
```
[           50000 ps] [INFO] RESET released
[           50000 ps] [WARN] tINIT1 violated: RESET deasserted too fast
[           50000 ps] [INFO] CKE rising edge
[           50000 ps] [WARN] tINIT3 violated: CKE set HIGH too fast after RESET being released
[          100000 ps] [INFO] FSM reset
--========== Initialization ============--
Initializing SDRAM @0x40000000...
Switching SDRAM to software control.
[      2000052500 ps] [INFO] FSM: RESET -> EXIT-PD
[      2002055000 ps] [INFO] FSM: EXIT-PD -> MRW
[      2199950000 ps] [INFO] RESET asserted
[      2199950000 ps] [INFO] CKE falling edge
[      2205390000 ps] [INFO] RESET released
[     98205990000 ps] [INFO] CKE rising edge
[     98302540000 ps] [INFO] MRW: MR[ 1] = 0x14
[     98351300000 ps] [INFO] MRW: MR[ 2] = 0x09
[     98400160000 ps] [INFO] MRW: MR[11] = 0x00
[     98448960000 ps] [INFO] MPC: ZQC-START
[     98448962500 ps] [INFO] FSM: MRW -> ZQC
[     98497720000 ps] [INFO] MPC: ZQC-LATCH
[     98497722500 ps] [INFO] FSM: ZQC -> NORMAL
Read leveling:
  m0, b0: |[     98731720000 ps] [INFO] ACT: bank=0 row=     0
[     98754895000 ps] [INFO] MASKED-WRITE: bank=0 row=     0 col=   0
[     98763315000 ps] [INFO] READ: bank=0 row=     0 col=   0
[     98767340000 ps] [INFO] PRE: bank = 0
[     98802380000 ps] [INFO] ACT: bank=0 row=     0
[     98825555000 ps] [INFO] MASKED-WRITE: bank=0 row=     0 col=   0
[     98833975000 ps] [INFO] READ: bank=0 row=     0 col=   0
[     98838000000 ps] [INFO] PRE: bank = 0
```

## Further notes

1. There are 2 warnings about timing violation in simulation. This is because LiteDRAM holds `reset_n=1` [constantly](https://github.com/antmicro/litedram/blob/bd71391e5cbb18de7327b314896a12b0776e6c89/litedram/core/multiplexer.py#L163). To perform proper reset we [manually force second reset](https://github.com/antmicro/litedram/blob/bd71391e5cbb18de7327b314896a12b0776e6c89/litedram/init.py#L569-L572). We also make an assumption that power supply is up for at least 200us before the bitstream is loaded (which effectively releses DRAM reset). This is needed to satisfy `tINIT1` timing.

2. There is also a "catch-all" file [utils.py](https://github.com/antmicro/litedram/blob/jboc/lpddr4/litedram/phy/lpddr4/utils.py) which contains some small functions/modules, that could prove useful when implementing other PHYs.

3. In the future `clk_freq` could be included in the `TimingSettings` class to be able to [more precisely define delays](https://github.com/antmicro/litedram/blob/bd71391e5cbb18de7327b314896a12b0776e6c89/litedram/init.py#L563-L566) in `init.py`.
