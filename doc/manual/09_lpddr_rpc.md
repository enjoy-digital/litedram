# LPDDR4, LPDDR5 and RPC DRAM PHYs {#lpddr-phys}

**In development:** these PHYs work, but their code, their options and their status change more
than those of the DDR PHYs. This chapter gives their architecture, the state they have reached and
how to try them. The developer notes of `litedram/phy/lpddr4/README.md` and
`litedram/phy/rpc/README.md` hold the details.

LPDDR4, LPDDR5 and RPC DRAM use few pins and long bursts, and encode their commands on a small
command bus instead of RAS, CAS and WE pins. Their PHYs therefore translate the DFI commands
themselves, unlike the DDR PHYs of [DDR PHYs](#phys). This chapter is for the designers who target
one of these memories on a 7-Series FPGA.

## At a glance {#lp-glance}

| PHY | Memory | FPGA | Phases | Status |
|--------------------|----------|------------|----------|--------------------------------------|
| `A7LPDDR4PHY` | LPDDR4 | Artix-7 | 8 | Validated on Antmicro hardware |
| `K7LPDDR4PHY` | LPDDR4 | Kintex-7 | 8 | Validated on Antmicro hardware |
| `V7LPDDR4PHY` | LPDDR4 | Virtex-7 | 8 | Validated on Antmicro hardware |
| `A7LPDDR5PHY` | LPDDR5 | Artix-7 | 1 | Validated on Antmicro hardware |
| `K7LPDDR5PHY` | LPDDR5 | Kintex-7 | 1 | Validated on Antmicro hardware |
| `V7LPDDR5PHY` | LPDDR5 | Virtex-7 | 1 | Validated on Antmicro hardware |
| `A7RPCPHY` | RPC DRAM | Artix-7 | 4 | Low frequency, on a modified Arty A7 |

Each memory also has a simulation PHY and a pad-level DRAM simulator, used by the unit tests and
by a Verilator SoC ([How to try them](#lp-try)). The generator does not support these PHYs: a
design instantiates them directly ([Integration](#integration)).

DDR5 is not supported: the repository has no DDR5 code.

## Architecture {#lp-architecture}

The three PHYs are split in two parts. A base PHY, written once per memory, runs in the controller
clock domain and holds all the protocol logic. A backend, written once per FPGA family or for
simulation, serializes its outputs to the pins. The figure below shows that split.

![Structure of the LPDDR4, LPDDR5 and RPC PHYs: a base PHY translates the DFI into an output record;
a 7-Series backend serializes it to the DRAM pins, or a simulation PHY to a pad-level DRAM
simulator.](lp_structure.svg)

**Base PHY.** It turns each DFI command into the command sequence of the memory, builds the data
and strobe words of a whole burst, and holds the read and write bitslips. It writes everything
into an output record, one word per pin per controller cycle (`LPDDR4Output` for LPDDR4).

**Backend.** It serializes the output record with the FPGA primitives and adds the delays. It
tells the base PHY the latencies of its serializers, so that the base PHY can compute the read and
write latencies of the settings. The 7-Series backends use the `OSERDESE2`, `ISERDESE2`,
`IDELAYE2` and `ODELAYE2` primitives.

**Simulation.** A simulation PHY serializes the same record with Migen logic and feeds a DRAM
simulator. The simulator decodes the commands, models the data and reports timing violations and
illegal commands in its log. It tests everything except the FPGA backend.

The RPC PHY came first and introduced this split; the LPDDR4 and LPDDR5 PHYs refined it. The RPC
README lists the parts that would follow the LPDDR4 structure in a rewrite.

## LPDDR4 {#lp-lpddr4}

An LPDDR4 burst is 16 beats long. The PHY uses 8 DFI phases, so that one controller cycle carries
a whole burst, and the DRAM clock runs at 8 times the controller clock. The figure below shows how
one DFI command becomes pin activity.

![LPDDR4 command translation: the phase adapter turns one DFI read into two subcommands, READ-1
and CAS-2, each held for two DRAM clocks on the CS and CA pins.](lp_command.svg)

**Commands.** An LPDDR4 command is one or two subcommands, each sent over two DRAM clocks on CS
and the 6 CA pins. A read, for example, becomes READ-1 then CAS-2. One adapter per DFI phase does
this translation (`DFIPhaseAdapter`); a command can therefore span four phases and cross into the
next controller cycle.

**Overlaps.** The adapters of all phases are ORed onto the pins. The controller timings must keep
commands from overlapping; an optional check (`extended_overlaps_check`) catches overlaps at a
cost in logic and is off by default.

**Mode registers and MPC.** LPDDR4 mode registers have a 6-bit address, wider than the 3 bank
bits, so the PHY declares 6 DFI bank bits. A DFI MRS becomes a mode register write: the register
address travels on the DFI bank field and the 8-bit value on the DFI address.

A DFI ZQC carries
the commands that DFI lacks, selected by its bank field: the multipurpose command MPC, such as the
ZQ calibration start and latch, and the mode register read MRR.

**Masked writes.** LPDDR4 has a WRITE and a MASKED-WRITE command; the second has a much longer
tCCD, 32 DRAM clocks instead of 8. The PHY uses MASKED-WRITE by default, so that byte masks work
(`masked_write`). The module always uses the longer tCCD, since the controller has a single one.

**Double-rate stage.** At 8 phases, each DQ pin needs a 16:1 serializer, and `OSERDESE2` stops at
8:1 in DDR mode. A first stage serializes from `sys` to `sys2x` in the fabric
(`DoubleRateLPDDR4PHY`), and the backend does the remaining 8:1 in `sys8x`.

**7-Series backend.** It reads with 32 delay taps and declares write leveling, write latency
calibration, write DQ-DQS training and read leveling. Without output delays, the Artix-7 variant
needs a `sys8x_90` clock, shifted by 90 degrees, for DQS.

| Parameter | Values | Role |
|-------------------------|------------------------|------------------------------------------|
| `sys_clk_freq` | Controller clock | The DRAM clock is 8 times it |
| `iodelay_clk_freq` | 200, 300 or 400 MHz | `IDELAYCTRL` reference |
| `masked_write` | True by default | MASKED-WRITE instead of WRITE |
| `cmd_delay` | None by default | Command delay forced by the BIOS |

The CAS latencies follow the set A table of the MT53E256M16D1 without DBI, from the DRAM clock.
The base PHY adds one controller cycle of read latency, which a code comment attributes to tests
on hardware.

## LPDDR5 {#lp-lpddr5}

LPDDR5 separates the command clock CK from the data clock WCK, which runs at 2 or 4 times CK
(`wck_ck_ratio`). The PHY uses a single DFI phase per CK cycle: one controller cycle carries a
whole burst of 16 beats. The rate converter can add phases, so that the controller runs slower
than CK ([Rate conversion](#phys-rate-converter)).

**Commands.** The PHY translates RAS, CAS and WE commands into the CA encoding of LPDDR5 itself,
which is not how the DFI specification defines it. A command is one or two LPDDR5 commands, each
on two CK edges. The adapter also inserts the WCK synchronization bits into the CAS commands until
WCK is synchronized.

**Latencies.** The read and write latencies come from the JEDEC tables of LPDDR5, with the
write latency of set A and the read latency of set 0, for the data rate of WCK. A frequency range
table also gives the mode register value of the range.

**7-Series backend.** It serializes CK, the commands and the data in `sys4x` from `sys`, the
data in SDR mode at a WCK ratio of 2 and in DDR mode at 4. It reads with 32 delay taps and declares
the same calibration steps as the LPDDR4 backend. The Artix-7 variant needs a `sys4x_90` clock.

The LPDDR5 module of the simulation SoC is an example module, defined in
`litedram/phy/lpddr5/simsoc.py`; the module database has no LPDDR5 class
([Memory modules](#modules)).

## RPC DRAM {#lp-rpc}

RPC DRAM, from Etron, delivers DDR3-class bandwidth on 22 or 24 pins. It has no command or address
pins: commands travel on the data bus and on a serial strobe line. The table below lists its pins.

| Pin | Role |
|-------------|------------------------------------------------------------------|
| CLK, CLK# | Differential clock |
| CS# | Chip select |
| DQS, DQS# | Differential data strobe, phase-aligned to CLK |
| DB[15:0] | Data, and parallel commands |
| STB | Serial commands, held low before each transaction |

The first command of a sequence is a parallel command on DB; the following ones are serial
commands on STB. DB and STB are centered on CLK, while DQS is aligned to it.

**Implementation.** The ratio is 1:4 and the burst is 16 beats, so a burst spans two controller
cycles. The PHY inserts DQS and STB preambles, which adds command latency. A state machine allows
only the commands that are legal in the current mode.

**DFI use.** Not every RPC command maps to a DFI command. The PHY reuses the DFI `reset_n` signal
to modify the encoding, since RPC DRAM has no reset pin. The module lengthens tWR by one
controller cycle at 200 MHz, because the write data is serialized over two controller cycles.

**Clocks.** The 7-Series backend needs two copies of the fast clock, shifted by 90 and 180 degrees
(`sys4x_90`, `sys4x_180`).

**Hardware test.** No board with RPC DRAM existed when the PHY was written. It was tested on an
Arty A7 whose DDR3 chip was replaced by a pin-compatible RPC DRAM (EM6GA16L). That chip needs
1.5 V instead of the 1.35 V of the board DDR3.

The target reprograms the power management IC of the board over I2C at start-up, which needs I2C
pins wired to the J11 pads of the board (`litedram/phy/rpc/arty.py`). The README reports
hardware issues, possibly the termination of CS and STB, that kept the PHY from reaching a high
frequency.

## How to try them {#lp-try}

The simulation SoCs run a LiteX SoC with a CPU, the BIOS, the controller, the simulation PHY and
the DRAM simulator in Verilator. The BIOS runs its initialization, its calibration and its memory
test against the simulator. The commands below run the LPDDR4 SoC until the memory test ends.

```sh
# LPDDR4, double-rate PHY, no L2 cache (masked writes exercised)
python3 litedram/phy/lpddr4/simsoc.py --finish-after-memtest \
    --double-rate-phy --l2-size 0
# LPDDR4 with a trace for GTKWave
python3 litedram/phy/lpddr4/simsoc.py --finish-after-memtest \
    --trace --trace-fst --gtkw-savefile
```

| Option | Role |
|--------------------------------|----------------------------------------------------------|
| `--finish-after-memtest` | Stop when the BIOS memory test ends |
| `--double-rate-phy` | LPDDR4: use the simulation PHY with the double-rate stage |
| `--l2-size 0` | No L2 cache, so partial writes reach the DRAM as masked writes |
| `--log-level` | Simulator log level, globally or per part (`cmd=info,data=debug`) |
| `--wck-ck-ratio` | LPDDR5: WCK to CK ratio, 2 or 4 |
| `--dfi-converter-ratio` | LPDDR5: controller to CK ratio through the rate converter |
| `--no-refresh` | Disable the refresher |
| `--disable-delay` | Skip the CPU delays of the init sequence |

The LPDDR5 SoC takes the same options at `litedram/phy/lpddr5/simsoc.py`. The RPC directory has a
simulation SoC too (`litedram/phy/rpc/simsoc.py`), which the tests do not run.

The simulator log reports each state change, mode register write and command, and a warning for
each timing violation. In the simulation PHYs the delays are faked: read leveling only moves the
bitslips. The tests check the log for errors and warnings and wait for `Memtest OK`.

```sh
python3 -m pytest -v test/test_lpddr4.py test/test_lpddr5.py \
    test/test_rpcphy.py
```

The LPDDR4 and LPDDR5 tests take about 10 minutes each, so the unit job of the CI skips them and
the full job runs them ([Simulation and verification](#simulation)).

## Limitations {#lp-limitations}

- **Status.** The repository records no rate or bandwidth for these PHYs, and the generator does
  not support them.
- **LPDDR4 ZQ calibration.** It runs only at initialization. Periodic ZQ calibration needs a
  refresher that issues its two commands in the background, which does not exist.
- **LPDDR4 tCCD.** The module always uses the masked write tCCD of 32 DRAM clocks, even when
  `masked_write` is off.
- **LPDDR4 and LPDDR5 reset.** The controller holds `reset_n` high from the start, so the init
  sequence forces a second reset, and the simulator warns that the first one was too short. The
  LPDDR4 notes assume the supply was up for 200 µs before the bitstream loads.
- **Refresh during init.** Some simulation tests disable the refresher: the controller sends
  refreshes while only mode register commands are allowed (marked FIXME).
- **LPDDR5 DFI.** The PHY encodes the CA commands itself, outside the DFI specification.
- **RPC.** 4 DFI phases where 8 would carry a burst per cycle; serial commands unused, so no
  pipelining; `reset_n` reused for the encoding; tWR increased by one cycle; two shifted clocks.
  The module timings carry a note that they may need further verification.
- **RPC frequency.** Validated at low frequency only, on a modified board.

## In the code {#lp-code}

| File | Content |
|----------------|-----------------------------------------------------------------------|
| `basephy.py` | Base PHY: `LPDDR4PHY` and `DoubleRateLPDDR4PHY`, `LPDDR5PHY`, RPC `BasePHY` |
| `commands.py` | DFI phase adapters and command encodings |
| `s7phy.py` | 7-Series backends and their A7, K7 and V7 classes, `A7RPCPHY` |
| `simphy.py` | Simulation PHYs |
| `sim.py` | Pad-level DRAM simulators (LPDDR4, LPDDR5) |
| `simsoc.py` | Verilator simulation SoCs |
| `arty.py` | RPC: Arty A7 target with the PMIC setup |

The files are in `litedram/phy/lpddr4/`, `litedram/phy/lpddr5/` and `litedram/phy/rpc/`. The init
sequences of the three memories are in `litedram/init.py`, and the tests in `test/test_lpddr4.py`,
`test/test_lpddr5.py` and `test/test_rpcphy.py`.

Where to go next: [DDR PHYs](#phys) for the PHY contract and the common datapath,
[Memory modules](#modules) for the LPDDR4 and RPC modules,
[Simulation and verification](#simulation) for the simulators.
