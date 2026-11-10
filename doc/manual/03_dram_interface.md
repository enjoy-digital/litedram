# The DRAM interface and the PHY {#dram-interface}

This chapter explains what happens on the wires between the FPGA and the DRAM, and why a DRAM
interface must be tuned at boot. It covers the signals, the strobes, the board topology, the
leveling procedures, the termination and the reference voltages, then the clocks of the FPGA and
the DFI interface between the controller and the PHY.

Each section ends with the part of LiteDRAM that implements the mechanism. The previous chapter,
[DRAM in a nutshell](#dram-primer), explained the commands and the timings; [Initialization and
calibration](#calibration) gives the exact steps the BIOS runs.

## The signals {#iface-signals}

A DRAM interface has two halves. The *command and address* half goes one way, from the controller
to the DRAM, and is shared by every chip of a rank. The *data* half is bidirectional and split
into *byte lanes*, each with its own strobe. The figure below shows the signals.

![The signals between the FPGA and the DRAM. The PHY sends the clock, the commands and the control
pins; the data (DQ, DM) and the strobes (DQS) go both ways, one strobe per byte
lane.](iface_signals.svg)

| Signal | Direction | Role |
|---------------------|---------------|-----------------------------------------------------------|
| CK, CK# | To the DRAM | Differential clock; commands are sampled on its rising edge |
| CS#, RAS#, CAS#, WE# | To the DRAM | Command encoding; ACT_n added on DDR4 |
| A, BA, BG | To the DRAM | Row or column address, bank, bank group (DDR4) |
| CKE | To the DRAM | Clock enable; low for power down and self refresh |
| ODT | To the DRAM | Turns on the termination of the DRAM's data pins |
| RESET# | To the DRAM | Reset (DDR3 and later) |
| DQ | Both | Data, 4, 8 or 16 per chip |
| DQS, DQS# | Both | Data strobe, one differential pair per byte lane (per nibble on x4 chips) |
| DM | To the DRAM | Data mask, one per byte lane: masks bytes during a write |

A byte lane is 8 DQ, their DQS pair and their DM. Each lane is routed on its own, so each one can
arrive at a slightly different time, and each one is tuned on its own.

In LiteDRAM, the pads of the DRAM are a record from the platform file, with fields named after
these signals (`dq`, `dqs_p`, `a`, `ba`, `cs_n`). The PHY counts the lanes from it. Two helpers
of `litedram/common.py` reshape the pads: `PHYPadsReducer` keeps some lanes only, and
`PHYPadsCombiner` merges chips with separate command buses into one controller.

## Double data rate and the strobe {#iface-dqs}

SDR memory transfers one word per clock, sampled on the rising edge of the clock that the
controller sends. DDR memories transfer two words per clock, one on each edge, and at these rates
the clock from the controller cannot be trusted to sample the data: the delays of the board and of
the chips are too large.

The data therefore travel with their own clock, the strobe DQS: the side that sends the data also
sends DQS, and the receiver samples DQ with it. This is a *source-synchronous* interface. Both
travel the same path, so their delays cancel. The figure below shows how DQS is aligned with DQ.

![DQS against DQ. Follow the dotted lines down from the DQS edges: on a write (left) each edge
falls in the middle of a data bit, ready for the DRAM to sample; on a read (right) each edge falls
on a bit transition, and the receiver must delay DQS by a quarter of a clock before
sampling.](iface_dqs.svg)

On writes the controller sends DQS *centre aligned*, its edges in the middle of each bit. On reads
the DRAM sends DQS *edge aligned*, on the bit transitions, and the receiver delays it by a quarter
of a clock. Before the burst, DQS is driven for a *preamble*, and after it for a *postamble*,
without carrying data.

In LiteDRAM, the DDR PHYs shift the write DQS by a quarter of a clock from DQ, with the means of
its FPGA:

- The Artix-7 PHY clocks its DQS serializers from a clock shifted by 90 degrees, `sys4x_dqs`,
  which the target builds (`bench/arty.py`).
- The PHYs with output delays (Kintex-7 and Virtex-7 HP banks, UltraScale) delay DQS by a quarter
  of a clock.
- The Lattice and Gowin PHYs take the shifted write clock of the DQS block of their FPGA.

On reads, the PHYs differ:

- The Xilinx PHYs do not use DQS. They sample DQ with their own fast clock, through an input
  delay that read leveling tunes per lane.
- The Lattice and Gowin PHYs use the DQS blocks of their FPGA, which delay DQS by 90 degrees,
  capture DQ with it and report when they saw a burst (*burst detect*).

## Fly-by topology and write leveling {#iface-flyby}

DDR3 and DDR4 route the clock, command and address pins as one bus that passes by every chip in
turn and ends on a termination: the *fly-by* topology. It keeps these heavily loaded signals clean
at high rates, but each chip receives the clock a little later than the previous one. The figure
below shows it.

![Fly-by topology. The clock, the commands and the address pass by the chips one after the other
and end on a termination (VTT); the data lanes go point to point. Each chip sees the clock later
than the previous one, while its data lane has its own length.](iface_flyby.svg)

The data lanes are point to point, so their delays do not follow the clock. A chip needs DQS to
arrive close to its own CK edge (tDQSS). With fly-by routing the skew between the first and the
last chip can exceed a clock period, so each lane needs its own DQS delay.

*Write leveling* measures that delay. The controller sets the DRAM into write leveling mode with a
mode register bit (MR1 bit A7 on DDR3 and DDR4), then sends DQS pulses. The DRAM samples its CK
with each DQS rising edge and returns the sampled value on DQ. The controller delays DQS step by
step until DQ goes from 0 to 1: DQS is then aligned with CK at that chip.

In LiteDRAM, the PHYs expose write leveling through registers: `wlevel_en` enables the mode,
`wlevel_strobe` sends one DQS pulse, and per-lane output delays move DQS and DQ. The BIOS runs the
scan (`sdram_write_leveling` in `liblitedram`).

Write leveling needs output delays: the Kintex-7 and Virtex-7 PHYs in HP banks and the UltraScale
PHYs have them. The Artix-7 has none: with one static DQS phase, only some lanes of a fly-by
memory meet tDQSS. Its optional CK phase shift mode (`with_ck_phase_shift`, DDR3 at 1:4) moves CK
against all the lanes instead ([CK phase shift](#phys-s7-ck-phase)).

## Write latency and DQ-DQS training {#iface-write-latency}

Write leveling aligns DQS with CK within one clock period, but a lane can be one whole clock
early or late: the DRAM then writes the burst shifted by a few words. *Write latency calibration*
writes a known pattern, reads it back, and moves each lane by whole clocks until the pattern is
right.

*DQ-DQS training* then centres DQ against DQS on writes. It sweeps the output delay of the DQ pins
of each lane, writes and reads back a pattern at each step, and keeps the middle of the passing
range. It relies on a working read side, which read leveling then refines.

In LiteDRAM, the write latency is moved by write bitslips (`wdly_dq_bitslip`) and DQ by output
delays (`wdly_dq`). Each PHY declares which calibrations it supports in its settings
(`write_leveling`, `write_latency_calibration`, `write_dq_dqs_training`, `read_leveling`); the
BIOS runs only those.

## Read leveling {#iface-read-leveling}

On reads, the controller does not know when the data arrive. The DRAM answers CL clocks after RD,
but the board and the I/Os add a delay that differs per lane. Two settings must be found for each
lane: a coarse one, which fast clock cycle holds the first word, and a fine one, where in the bit
to sample.

The coarse setting is a *bitslip*: the deserializer output is shifted by whole bits until the
words line up. The fine setting is an input delay, from a few picoseconds to about a hundred per
step depending on the FPGA (78 ps on 7-Series with a 200 MHz reference). *Read
leveling* writes a pattern, then for each bitslip sweeps the delay and reads the pattern back. The
figure below shows such a scan.

![A read leveling scan, example for one lane. For each bitslip the delay taps are swept and each
read is checked: cyan taps returned the right data. The BIOS keeps the bitslip with the widest
passing window and sets the delay at its centre (green).](iface_read_leveling.svg)

The window is the *data eye* seen through the delay line. A wide window means a robust interface;
a narrow one points to a signal integrity or clocking problem. DDR3 and DDR4 can also return a
fixed pattern from their *MPR* (multi-purpose register), so the read side can be tuned before
anything has been written.

The PHYs that capture with DQS have one more problem: DQS is not driven between bursts, so the
receiver must listen to it only during a read. The FPGA's DQS block opens this gate and reports a
burst detect, which read leveling uses to confirm that the read window is right.

In LiteDRAM, each PHY declares its number of delay taps and bitslips in its settings (`delays`,
`bitslips`), and exposes them through registers (`rdly_dq_inc`, `rdly_dq_bitslip`, and
`burstdet_seen` on the Lattice and Gowin PHYs). The BIOS runs the scan and prints one line per
lane and bitslip. On DDR4 it reads the MPR patterns, except on registered DIMMs and clamshell
layouts.

## Termination and drive strength {#iface-odt}

At DRAM rates, a signal reflects at the end of a line that is not terminated. The DRAM therefore
terminates its own data pins with an *on-die termination* (ODT): a resistor switched on when the
ODT pin is high. The FPGA terminates its inputs in the same way when it receives read data.

DDR3 and DDR4 have two termination values: RTT_NOM, used when the chip is idle or another rank is
written, and RTT_WR, used while the chip itself is written (*dynamic ODT*). The driver strength of
the DRAM, RON, sets how hard it drives the read data. All three are set in the mode registers.

| Setting | DDR3 default | DDR4 default | Mode register |
|---------|--------------|--------------|---------------|
| RTT_NOM | 60 ohm | 40 ohm | MR1 |
| RTT_WR | 60 ohm | 120 ohm | MR2 |
| RON | 34 ohm | 34 ohm | MR1 |

In LiteDRAM, the defaults of the table are set by `litedram/init.py`; a PHY can override them
(`rtt_nom`, `rtt_wr`, `ron` in its settings). With the DRAM DLL off, a DDR3 mode for low
clock rates that the GW5A PHY offers (`dll_off`), both terminations are disabled.

The ODT pin is driven statically by default. With `with_dynamic_odt` (DDR3, single rank), the
controller raises ODT only around writes, so the DRAM terminations are off during reads
([Dynamic ODT](#ctrl-dynamic-odt)). The FPGA side termination is part of the I/O standards of the
platform file, not of LiteDRAM.

## ZQ calibration {#iface-zq}

The resistance of the drivers and terminations of a chip varies with the process, the voltage and
the temperature. DDR3 and later chips calibrate them against a precision resistor on their ZQ pin,
240 ohm to ground. ZQCL, the long calibration, runs once at initialization; ZQCS, the short one,
corrects the drift from time to time during operation.

In LiteDRAM, the initialization sequence ends with ZQCL ([Mode registers and
power-up](#primer-init)), and the refresher sends ZQCS once per second by default
([Refresh](#primer-refresh)). LPDDR4 has no ZQCS: it calibrates with two multi-purpose commands
(MPC), start and latch, which LiteDRAM sends at initialization only.

## Reference voltages {#iface-vref}

The data receivers compare each input to a reference voltage, VREF, set halfway between the high
and the low levels. On DDR3 the board provides VREF on dedicated pins. DDR4 terminates its data
pins to the supply (pseudo open drain), so the data swing sits near the top of the supply and the
right reference is not halfway. The DRAM generates its data VREF internally, programmed in MR6.

On the FPGA side, the receivers of the read data also need a VREF. Some FPGA I/O banks can set it
internally, in steps, instead of using a VREF pin.

In LiteDRAM, the DDR4 initialization writes MR6 with tCCD_L only and leaves its VREF field at
zero, the first value of range 1 (60% of VDDQ): the DRAM data VREF is not trained.

The UltraScale+ PHY can set the FPGA read VREF of its HP I/O banks (`with_hpio_vref`, register
`rd_vref`, codes 0 to 72). The BIOS does not scan it: the register keeps its build-time value
(`hpio_vref_tune`) unless software writes it. LiteX issue 2769 tracks the missing BIOS sweep.

## Clocks and the frequency ratio {#iface-clocking}

An FPGA fabric cannot run at the DRAM clock: a DDR3 at 800 MT/s has a 400 MHz clock and moves data
at 800 Mbps per pin. The PHY therefore uses the serializers and deserializers of the FPGA I/Os. The
controller runs at a fraction of the DRAM clock, and moves several clocks' worth of commands and
data per cycle.

This fraction is the *frequency ratio*. At 1:4, the controller runs at a quarter of the DRAM clock:
the Arty A7 bench target runs its controller at 125 MHz, its DRAM clock at 500 MHz, and its DDR3
at 1000 MT/s. For a DDR memory, the data rate is twice the DRAM clock: at 1:4, eight times the
controller clock.

An Artix-7 DDR3 target needs four clocks, generated by a PLL in the board's clock module
(`bench/arty.py`). The Kintex-7 and Virtex-7 targets need no `sys4x_dqs`: their output delays shift
DQS instead.

| Clock | Frequency | Use |
|-------------|---------------------|------------------------------------------------------|
| `sys` | controller clock | Controller, DFI, parallel side of the serializers |
| `sys4x` | 4 x `sys` | Serial side of the serializers: CK, commands, DQ |
| `sys4x_dqs` | 4 x `sys`, 90 degrees | Serial side of the DQS serializers (Artix-7) |
| `clk200` | 200 MHz | Reference of the input and output delays (`IDELAYCTRL`) |

Other families use their own clocking: the ECP5 PHY uses a 2x clock for its I/O gearing and a 4x
clock at 1:4, and the Gowin GW5A PHY selects 1:2 or 1:4 with its number of phases. [DDR PHYs](#phys)
gives the clocks of each family.

## DFI, the interface between the controller and the PHY {#iface-dfi}

The controller and the PHY meet at a *DFI* interface, named after the DDR PHY Interface
specification. It carries, for each DRAM clock of a controller cycle, one command slot and the
data of that clock. Each of these slots is a DFI *phase*. The figure below shows the phases at a
1:4 ratio.

![DFI phases at 1:4. Read the figure column by column: one controller clock (sys) spans four DRAM
clocks, and DFI phase N carries the command slot of DRAM clock N and two data beats. One burst of
8 fills one controller clock. The data of a command travel in a later controller clock, after the
read or write latency.](iface_dfi_phases.svg)

| DFI signal | Direction | Content |
|------------------|-----------------|-------------------------------------------------------|
| `address`, `bank` | To the PHY | Row or column address, bank (and bank group on DDR4) |
| `ras_n`, `cas_n`, `we_n`, `cs_n`, `act_n` | To the PHY | Command encoding |
| `cke`, `odt`, `reset_n` | To the PHY | Control pins |
| `wrdata`, `wrdata_mask` | To the PHY | Write data and byte masks, two beats per phase |
| `wrdata_en` | To the PHY | Write data valid, sent with the write latency |
| `rddata_en` | To the PHY | A read was issued on this phase |
| `rddata`, `rddata_valid` | To the controller | Read data and their valid flag |

Two latencies tie the commands to their data. The *write latency* is the number of controller
cycles between WR and the cycle where the controller presents the write data. The *read latency*
is the number of cycles between RD and the cycle where the read data come back valid. Both follow
from CL, CWL and the pipeline of the PHY.

The commands do not always start on phase 0. The PHY tells the controller on which phase to issue
reads and writes (`rdphase`, `wrphase`), so that the data of a burst fill whole controller cycles.

In LiteDRAM, the DFI interface is `Interface` of `litedram/phy/dfi.py`. It follows the structure of
the DFI specification, phases and signal names, without claiming a version of it.

Each PHY fills a `PhySettings` with its number of phases, its latencies in controller cycles, CL and CWL in DRAM
clocks, and its calibration capabilities. `DFIRateConverter` wraps a PHY to raise the ratio, with
more phases and narrower data per phase. See [Core architecture](#architecture).

## What each FPGA family provides {#iface-fpga}

Each PHY is built from the I/O primitives of its FPGA family. The table below summarizes what the
LiteDRAM PHYs use; [DDR PHYs](#phys) describes each one.

| Family | Serializers | Delay taps | Bitslips | Read capture |
|--------------------|--------------------------------|------------|------------|----------------------------|
| Xilinx 7-Series | OSERDESE2, ISERDESE2 | 32 | 8 | Fast clock, input delay per DQ |
| Xilinx UltraScale(+) | OSERDESE3, ISERDESE3 | 512 | 8 | Fast clock, input delay per DQ |
| Lattice ECP5 | ODDRX2DQA, IDDRX2DQA | 8 | 4 | DQSBUFM, burst detect |
| Lattice Nexus | ODDRX2DQ, IDDRX2DQ | 16 | 4 | DQSBUF, burst detect |
| Gowin GW2A | OSER4_MEM, IDES4_MEM | 256 | 4 | DQS block, burst detect |
| Gowin GW5A | OSER4_MEM, IDES4_MEM (1:2), OSER8_MEM, IDES8_MEM (1:4) | 256 | 4 or 8 | DQS block, burst detect |

The 7-Series input and output delays need a reference clock of 200 or 300 MHz, or 400 MHz on the
faster speed grades; their output delays exist only in the HP banks of Kintex-7 and Virtex-7. The UltraScale delays are set in time
units, and the FPGA compensates them for voltage and temperature while `en_vtc` is set.

Where to go next: [Initialization and calibration](#calibration) for the BIOS steps, [DDR
PHYs](#phys) for each family, [Debugging](#debugging) when a scan shows no window.
