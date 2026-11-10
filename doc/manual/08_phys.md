```{=latex}
\part{The PHYs and memories}
```

```{=html}
<h1 class="part">Part III. The PHYs and memories</h1>
```

# DDR PHYs {#phys}

The PHY is the only part of LiteDRAM that knows the FPGA: it turns the DFI phases of the
controller into DRAM pin signals, with the serializers, delays and clocks of one family. This
chapter describes every SDR, DDR2, DDR3 and DDR4 PHY and how each family differs; the concepts
are in [The DRAM interface and the PHY](#dram-interface).

The LPDDR4, LPDDR5 and RPC DRAM PHYs follow another design and have their own chapter,
[LPDDR4, LPDDR5 and RPC DRAM PHYs](#lpddr-phys).

## At a glance {#phys-glance}

| Class | FPGA | Memory | Ratio | Beats | Status |
|----------------------------------------------------------|-------------------------------|------------------|------------|-------------|---------------------|
| `GENSDRPHY` | Any | SDR | 1:1 | 1 | Validated |
| `HalfRateGENSDRPHY` | Any | SDR | 1:2 | 2 | Validated |
| `S6HalfRateDDRPHY` | Spartan-6 | DDR, LPDDR, DDR2, DDR3 | 1:2 | 4 | Not recorded |
| `S6QuarterRateDDRPHY` | Spartan-6 | DDR3 | 1:4 | 8 | Not recorded |
| `A7DDRPHY` | Artix-7, Spartan-7 | DDR2, DDR3 | 1:2, 1:4 | 4, 8 | Validated |
| `K7DDRPHY` | Kintex-7 | DDR2, DDR3 | 1:2, 1:4 | 4, 8 | Validated |
| `V7DDRPHY` | Virtex-7 | DDR2, DDR3 | 1:2, 1:4 | 4, 8 | Validated |
| `USDDRPHY` | Kintex/Virtex UltraScale | DDR3, DDR4 | 1:4 | 8 | Validated (DDR4) |
| `USPDDRPHY` | Kintex/Virtex UltraScale+ | DDR3, DDR4 | 1:4 | 8 | Validated (DDR4) |
| `ECP5DDRPHY` | Lattice ECP5 | DDR3 | 1:2, 1:4 | 8 | Validated |
| `NexusDDRPHY` | Lattice CrossLink-NX, Certus-NX | DDR3 | 1:2 | 8 | Validated |
| `GW2DDRPHY` | Gowin GW2A | DDR3 | 1:2 | 8 | Validated |
| `GW5DDRPHY` | Gowin GW5A | DDR3 | 1:2, 1:4 | 8 | Validated |

The ratio is the controller clock to the DRAM clock. *Beats* is the number of data words of the
DQ width that one controller cycle carries; the controller data width is the DQ width times this
number. At 1:4 on DDR3, one controller cycle carries a whole burst of 8.

The Lattice and Gowin PHYs also take a whole burst of 8 per DFI cycle at 1:2, with phases twice
as wide. They send it to the pins over two controller cycles. The module gives tCCD as 4 DRAM
clocks, two controller cycles at 1:2, so the controller never issues bursts closer than that.

*Validated* means run on hardware with the BIOS calibration and memory test. On UltraScale and
UltraScale+, the validated memory is DDR4; the classes also accept DDR3. *Not recorded* means that
the repository holds no hardware result, which is the case of the two Spartan-6 PHYs.

Spartan-7 devices have the same HR banks as Artix-7, without output delays, and use `A7DDRPHY`;
the PHY code itself does not name Spartan-7. Efinix and Intel FPGAs have no LiteDRAM DDR PHY and
use the generic SDR PHY ([Efinix](#phys-efinix)).

The 7-Series class also accepts DDR4 and then adds the DDR4 command multiplexer. Its file header
and the README list DDR2 and DDR3 only, and no DDR4 result on 7-Series is recorded. DDR5 is not
supported: the repository has no DDR5 code.

The file headers give the rates each PHY targets: DDR2 from 400 to 1066 MT/s and DDR3 from 800 to
1866 MT/s on 7-Series; DDR3 from 800 to 1600 MT/s and DDR4 from 1333 to 1866 MT/s on UltraScale;
DDR3 at 800 MT/s on ECP5, Nexus, GW2A and GW5A. These are design targets, not measurements.

In simulation, a DFI-level model replaces both the PHY and the DRAM (`SDRAMPHYModel`); it is
described in [Simulation and verification](#simulation).

## The PHY contract {#phys-contract}

Every PHY presents the same three things to the core, so that a design changes its PHY class and
nothing else ([Core architecture](#architecture)).

| Attribute | Content |
|-------------|------------------------------------------------------------------------|
| `dfi` | DFI interface: commands, write data and read data, one record per phase |
| `settings` | `PhySettings`: memory type, widths, phases, latencies, capabilities |
| Registers | Delay, bitslip and leveling controls for the BIOS ([Register reference](#registers)) |

The controller reads the settings to schedule its commands. The init code turns them into the
`sdram_phy.h` header of the BIOS ([Initialization and calibration](#calibration)). The table below
lists the fields that differ between PHYs.

| Field | Unit | Meaning |
|-----------------------------------------|-------------|------------------------------------------|
| `nphases` | Phases | DFI phases per controller cycle: the ratio |
| `dfi_databits` | Bits | Data bits per phase |
| `cl`, `cwl` | DRAM clocks | CAS read and write latencies of the DRAM |
| `rdphase`, `wrphase` | Phase | Phase on which the controller issues RD and WR |
| `read_latency` | Cycles | Controller cycles from `rddata_en` to `rddata_valid` |
| `write_latency` | Cycles | Controller cycles from WR to `wrdata` |
| `cmd_latency` | Cycles | Extra delay of the command path |
| `delays`, `bitslips` | Steps | Size of the delay and bitslip ranges per lane |
| `write_leveling` | Flag | The PHY can move DQS against CK |
| `write_dq_dqs_training` | Flag | The PHY can move DQ against DQS |
| `write_latency_calibration` | Flag | The PHY can shift write data by whole beats |
| `read_leveling` | Flag | The PHY can scan read delays and bitslips |

Each PHY derives its read and write phases from the CAS latencies and the ratio. With N phases
and a CAS latency CL, the PHY waits ceil(CL / N) controller cycles for the data. It issues RD
early by the difference, in phases, so that the data lands on a controller cycle boundary.

For example, DDR3 at 800 MT/s and 1:4 has CL 6: the PHY waits 2 controller cycles, 8 DRAM clocks,
and issues RD on phase 2. The same computation on CWL gives the write phase. The 7-Series,
UltraScale and LPDDR4 PHYs expose both phases as registers, so the BIOS can change them.

Two helpers adapt the pads before the PHY sees them. A pads reducer keeps only some byte lanes of
a board, for a test on part of the memory (`PHYPadsReducer`). A pads combiner merges DRAM chips
with separate command buses into one record, so that one controller drives them all
(`PHYPadsCombiner`).

## Common datapath {#phys-datapath}

The DDR PHYs share one structure. On the write path, each pin goes through a bitslip, a
serializer and an optional output delay; the read path does the same in reverse. The figure below
shows both directions for one DQ pin.

![Common datapath of the DDR PHYs: on writes, a bitslip, a serializer and an output delay per DQ
pin; on reads, an input delay, a deserializer and a bitslip. The blue path is the write
data.](phy_datapath.svg)

**Phases to bits.** The serializer runs at the DRAM rate. In each controller cycle it takes two
bits per phase, the words of the rising and falling edges of that phase. A 1:4 PHY therefore
feeds an 8:1 serializer and a 1:2 PHY a 4:1 one. The command pins use the same serializers, with
each phase held for both edges.

**Bitslip.** A bitslip shifts the serialized word by whole bit times. On writes it moves the data
by one or more beats against DQS. On reads it realigns the deserialized word so that the first
beat of the burst lands in phase 0. Calibration sets it per byte lane.

**Delays.** Input and output delays move one pin by a fraction of a bit time. They center the
capture inside the data eye and compensate the skew between lanes. Which delays exist depends on
the FPGA ([Delays per family](#phys-delays)).

**Strobes and enables.** DQS is serialized from a fixed toggling pattern; during write leveling it
becomes one pulse per register write. A delay line on the write enable drives the DQ and DQS
output enables at the write latency, with one cycle of preamble before and one of postamble after.

On the Lattice and Gowin PHYs, the DQS enable of these cycles acts per half cycle; the Xilinx PHYs
keep DQS toggling through both whole cycles ([Limitations](#phys-limitations)).

**Read valid.** The read enable of the controller enters a delay line of `read_latency` cycles.
Its output marks the cycle where the read data is valid on the DFI. The latency is fixed at build
time and covers the serializer, the CAS latency, the deserializer and the bitslip.

### Delays per family {#phys-delays}

The delays come from the IO primitives of the FPGA. Their step, their range and whether a pin has
an output delay at all decide which calibration steps a family supports
([Initialization and calibration](#calibration)).

| Family | Input delay | Output delay | Steps | Notes |
|------------------|----------------|----------------|-------|------------------------------------|
| Spartan-6 | None | None | 0 | Bitslips set at build time |
| 7-Series HP | `IDELAYE2` | `ODELAYE2` | 32 | Kintex-7 HP banks, Virtex-7 |
| 7-Series HR | `IDELAYE2` | None | 32 | Artix-7, Kintex-7 HR banks |
| UltraScale(+) | `IDELAYE3` | `ODELAYE3` | 512 | Time units, with compensation |
| ECP5 | DQS read clock | None | 8 | `DQSBUFM` read clock select |
| Nexus | DQS read clock | None | 16 | `DQSBUF` read clock select |
| GW2A, GW5A | DQS read delay | GW5A at 1:4 | 256 | `DQS` primitive, direction bit |

On 7-Series, the tap step depends on the `IDELAYCTRL` reference clock: 78 ps at 200 MHz, 52 ps
at 300 MHz and 39 ps at 400 MHz, the last on the -3 and -2/2E speed grades only. The PHY
computes the taps of a quarter DRAM clock, a 90 degree shift, into the `half_sys8x_taps`
register.

On UltraScale, the delays count in time units: the DQS output delay starts at a quarter of the
DRAM clock, in picoseconds. The PHY asserts a reference clock of at least 200 MHz on UltraScale
and 300 MHz on UltraScale+.

On the Lattice and Gowin PHYs, the read delay acts on the DQS clock that captures a byte lane, not
on each DQ pin. The CK and command pins have a static delay set at build time (`cmd_delay`).

### Rate conversion {#phys-rate-converter}

A PHY can run at a higher clock than the controller. The rate converter wraps a PHY and gives the
controller more phases with fewer bits each (`DFIRateConverter`). With a ratio of 2, a 1:2 PHY
appears to the controller as a 1:4 PHY at half its clock.

The converter serializes the commands of the extra phases onto successive PHY cycles and moves a
whole burst in one controller cycle. It recomputes the latencies of the wrapped PHY and
synchronizes its register strobes into the PHY clock domain. The 7-Series and ECP5 PHYs use it
for their higher ratios.

## Generic SDR {#phys-sdr}

The generic SDR PHY drives SDR SDRAM through the generic IO registers of LiteX, so it builds on
any FPGA that LiteX supports (`GENSDRPHY`). Each command pin goes through one output register and
each DQ pin through one tristate register. The README records it tested on Xilinx, Altera and
Lattice FPGAs.

| Parameter | Default | Role |
|----------------|---------------|----------------------------------------------|
| `sys_clk_freq` | 100 MHz | Controller clock, also the SDRAM clock |
| `cl` | From the rate | CAS latency: 2 up to 100 MHz, 3 above |
| `with_dfi_reg` | False | Half-rate only: register the DFI in `sys` |

The read latency is CL plus one cycle. The PHY has no delays and no bitslips: it relies on the
phase of the SDRAM clock, which the board design provides. That clock must be shifted from `sys`,
so that the read data meets the capture registers.

The half-rate variant runs the same PHY in `sys2x` and presents two DFI phases in `sys`
(`HalfRateGENSDRPHY`). It doubles the SDRAM clock for the same controller clock. Without
`with_dfi_reg`, the commands and write data have half a `sys` period to reach the `sys2x`
registers; with it, they are registered first and the read latency grows by one cycle.

**Clock phase.** The generator adds a PLL with a shifted SDRAM clock on ECP5 only, 90 degrees by
default (`sdram_clk_phase`); elsewhere the integrator provides that clock
([Integration](#integration)). When the SDRAM clock comes from a PLL with a run-time phase
stepper, the BIOS scans the phase over one clock and settles in the middle of the passing window.

An SDR PHY needs no leveling, so the BIOS goes from the init sequence straight to the memory test.
The capture below comes from a Trenz TEC0117 (Gowin GW1NR-9 with an embedded 16-bit SDR SDRAM) at
25 MT/s.

```console
SDRAM:		8192KiB 16-bit @ 25MT/s (CL-2 CWL-2)
[...]
Initializing SDRAM @0x40000000...
Switching SDRAM to software control.
Switching SDRAM to hardware control.
Memtest at 0x40000000 (2MiB)...
[...]
Memtest OK
```

## Spartan-6 {#phys-s6}

The Spartan-6 PHYs use the `OSERDES2` and `ISERDES2` serializers of the family, with `ODDR2` for
DQS. The half-rate PHY takes DDR, LPDDR, DDR2 and DDR3 at 1:2 (`S6HalfRateDDRPHY`). The
quarter-rate PHY runs it in `sys2x` behind a 1:2 adaptation, for DDR3 at 1:4
(`S6QuarterRateDDRPHY`).

These PHYs are not calibrated at run time. Three parameters set the alignment at build time, and
the file header warns that they may need adjusting for a board and a frequency.

| Parameter | Range | Role |
|-------------------------|------------|------------------------------------------------|
| `rd_bitslip` | 0 to 15 | `ISERDES2` bitslips applied after reset |
| `wr_bitslip` | 0 to 4 | Offset of write data and mask in the serializer |
| `dqs_ddr_alignment` | `C0`, `C1` | `ODDR2` alignment of the DQS outputs |

The CAS latency is fixed: CL 3 for DDR, LPDDR and DDR2, CL 5 and CWL 6 for DDR3. Read commands
go on phase 0 and write commands on phase 1. Besides `sys`, the CRG provides a half-rate clock for
the commands and DQS, and two full-rate clocks with their strobes for the write and read
serializers.

## Xilinx 7-Series {#phys-s7}

The 7-Series PHY serves the Artix-7, Kintex-7 and Virtex-7 devices with the `OSERDESE2` and
`ISERDESE2` serializers (`S7DDRPHY`). Three classes set whether the IO banks have output delays,
which decides the calibration steps available.

| Class | Output delays | Write calibration | Write latency calibration |
|--------------|-----------------------|----------------------------|--------------------------|
| `A7DDRPHY` | None | None | Off by default |
| `K7DDRPHY` | HP banks, or none | Leveling, DQ-DQS training | On with output delays |
| `V7DDRPHY` | All banks | Leveling, DQ-DQS training | On |

`K7DDRPHY` takes `with_odelay=False` for the HR banks, which have no output delays. DDR3 runs at
1:4 only; DDR2 runs at 1:2 or 1:4. On DDR2, the PHY turns off the write calibrations, so only
read leveling remains. Every variant reads with 32 delay taps and 8 bitslips per lane.

| Parameter | Default | Role |
|-----------------------------|---------------|----------------------------------------------|
| `memtype` | `DDR3` | `DDR2`, `DDR3`; `DDR4` accepted |
| `nphases` | 4 | 2 (DDR2 only) or 4 |
| `sys_clk_freq` | 100 MHz | Controller clock; the DRAM clock is `nphases` times it |
| `iodelay_clk_freq` | 200 MHz | `IDELAYCTRL` reference: 200, 300 or 400 MHz |
| `cl`, `cwl` | From the rate | CAS latencies |
| `cmd_latency` | 0 | Extra command delay, in controller cycles |
| `is_rdimm` | False | DDR4 registered DIMM settings |
| `with_ck_phase_shift` | False | Write leveling by CK phase |

On Artix-7 with DDR3, the read data must arrive one DRAM clock phase into the `ISERDESE2` word for
read leveling to work. The PHY moves its read phase by one instead of changing CL in the DRAM.

### Clocking {#phys-s7-clocking}

The CRG provides the controller clock, a fast clock at four times it (twice for DDR2 at 1:2) and
the reference clock of the `IDELAYCTRL`. The figure below shows these clocks for a PHY without
output delays.

![Clocking of the 7-Series PHY at 1:4 without output delays: the PLL or MMCM provides sys, sys4x,
sys4x_dqs shifted by 90 degrees for DQS, and the iodelay reference of the
IDELAYCTRL.](phy_s7_clocks.svg)

Without output delays, DQS is serialized on a copy of the fast clock shifted by 90 degrees, so
that it is centered on the data (`sys4x_dqs`). With output delays, DQS uses the fast clock, and
its output delay starts at a quarter of the DRAM clock. That gives the same 90 degrees, which
write leveling can then tune.

### CK phase shift {#phys-s7-ck-phase}

A design without output delays cannot level the writes per lane. With a fly-by command bus, a
single DQS phase then meets the DRAM timing on part of the lanes only. The CK phase shift option
moves CK against DQ and DQS instead (`with_ck_phase_shift`).

![CK phase shift on 7-Series: an MMCM of the PHY drives CK and the commands from fine phase shift
outputs, and DQ and DQS from static outputs; the CK phase registers step the
shift.](phy_ck_phase.svg)

The PHY then owns an MMCM, fed by `sys`, as the figure above shows. CK and the commands run on its
fine phase shift outputs; DQ, DQS and the read capture run on static outputs. One DRAM clock spans
112 fine steps at 1:4. The commands cross from `sys` through falling edge registers.

The option needs DDR3 at 1:4, x8 lanes and no output delays. The read side gains a per-bit
selection, so that read leveling can tune each DQ pin (`dq_dly_sel`). The BIOS scans the CK phase
over one DRAM clock with traffic and settles in the middle of the longest passing run
([Initialization and calibration](#calibration)).

The command crossing gets a clock uncertainty constraint before placement, and `mmcm_loc` can
place the MMCM. The clock domains of the PHY take its `name` as prefix, so two such PHYs in one
SoC need two names.

### Higher ratios {#phys-s7-ratio}

`s7ddrphy_with_ratio` wraps a 7-Series PHY in the rate converter. With a ratio of 2, the
controller runs at 1:8: the PHY logic runs in `sys2x` and the serializers in `sys8x`. No hardware
result at 1:8 is recorded.

## Xilinx UltraScale and UltraScale+ {#phys-us}

The UltraScale PHY drives DDR3 and DDR4 at 1:4 with `OSERDESE3`, `ISERDESE3` and their delays
(`USDDRPHY`). The UltraScale+ class is the same code for the newer devices (`USPDDRPHY`). Every
pin has a delay of 512 steps, and every lane 8 bitslips.

| Parameter | Default | Role |
|------------------------|---------------|------------------------------------------------|
| `memtype` | `DDR3` | `DDR3` or `DDR4` |
| `sys_clk_freq` | 100 MHz | Controller clock; the DRAM clock is four times it |
| `iodelay_clk_freq` | 200 MHz | Reference: 200 MHz or more, 300 MHz or more on UltraScale+ |
| `cl`, `cwl` | From the rate | CAS latencies |
| `is_rdimm` | False | DDR4 RDIMM: register clock driver settings |
| `is_clam_shell` | False | DDR4 chips on both sides of the board |
| `with_hpio_vref` | False | UltraScale+ DDR4: read VREF per byte |
| `hpio_vref_tune` | 31 | Read VREF code at reset, 0 to 72 |

**Delays and compensation.** The IO logic keeps the delays stable over voltage and temperature.
Calibration needs that compensation off while it moves the delays, so the BIOS clears the
`en_vtc` register under software control and sets it again afterwards.

**Write leveling.** The PHY can delay CK and the commands together, and DQS and DQ per lane. The
DQS output delay has no software reset: the PHY counts its increments, and the BIOS steps it
around to zero (`wdly_dqs_inc_count`). The BIOS reads the quarter clock in taps from the first
DQS delay (`half_sys8x_taps`).

**DDR4 commands.** The PHY inserts the DDR4 command multiplexer. It turns an ACT into the `act_n`
pin and moves RAS, CAS and WE onto address bits 16, 15 and 14. With x4 chips, each byte lane has
two DQS pairs.

**RDIMM.** `is_rdimm` programs the register clock driver of a DDR4 RDIMM with the drive settings
of an 8-chip load. The BIOS then skips the DDR4 MPR read leveling.

**Clam-shell.** On a clam-shell board, two DDR4 chips share each signal from opposite sides, with
mirrored address pins and two chip selects. The PHY reports half the ranks. The BIOS writes the
mode registers of each side with its chip select and the mirrored address bits.

**Read VREF.** On UltraScale+ with DDR4, `with_hpio_vref` drives the input reference of each byte
from an `HPIO_VREF` with a 7-bit code (`rd_vref`). Codes 15 to 72 give 58 + 0.5 x code percent of
VCCO. The bank `INTERNAL_VREF` must also be set, and x4 chips are refused.

The CRG provides `sys`, `sys4x` and the reference clock. The PHY resets from the `ic` domain of
the LiteX `IDELAYCTRL` wrapper. The generator CRG divides `sys` from `sys4x` with `BUFGCE_DIV`, so
that both stay aligned.

## Lattice ECP5 {#phys-ecp5}

The ECP5 PHY drives DDR3 at 1:2 with the DDR gearing primitives of the family: `ODDRX2F`,
`IDDRX2DQA` and the `DQSBUFM` DQS buffer of each byte (`ECP5DDRPHY`). Its edge clock runs at the
DRAM clock and its system clock at half of it. The photo below shows one board it runs on.

![Inside a Cam Link 4K: the Lattice ECP5 LFE5U-25F next to its DDR3L chip, one of the boards on
which the 1:4 ECP5 PHY was validated.](camlink_4k_inside.jpg)

| Parameter | Default | Role |
|------------------|---------------|------------------------------------------------------|
| `sys_clk_freq` | 100 MHz | PHY system clock; the DRAM clock is twice it |
| `cl`, `cwl` | From the rate | CAS latencies |
| `cmd_delay` | 0 | Static delay of CK and the commands, below 128 |
| `clk_polarity` | 0 | Inverts the CK pattern |
| `dm_remapping` | None | Maps the DM pins of a board to byte lanes |
| `with_dm` | True | False on boards without DM: writes are then full width |
| `io_rst_init` | False | Reset the IO gearing from the init sequence |
| `cmd_gearing` | `x2` | `x1` puts CK and the commands on `ODDRX1F` |

**Initialization.** The PHY runs its own sequence in an `init` clock domain. When the DLL of the
DQS buffers locks, it freezes the DLL, stops the edge clock and resets its domain. It then
releases both and pauses the DQS buffers while the DLL updates.

The CRG connects the stop and reset outputs of the PHY to its clock gate and divider, as the
figure below shows. The generator builds this clocking with `ECLKSYNCB` and `CLKDIVF`
([Integration](#integration)); the Gowin PHYs follow the same scheme with their own primitives.

![Clocking of the Lattice ECP5 and Gowin PHYs. Follow the two control lines of the PHY init
sequence: it stops the gate of the edge clock, which runs at the DRAM clock, and resets the divider
that makes sys, so that every IO starts on the same edge.](phy_lattice_clocks.svg)

**Read leveling.** Each byte has a 3-bit read clock select in its DQS buffer, so 8 delay steps,
and 4 bitslips. The DQS buffer also reports a burst detect: the PHY latches it in the
`burstdet_seen` register, and the BIOS counts a missing burst as an error.

**Command gearing.** The `x2` gearing uses the edge clock, which exists on the left and right banks
only. The `x1` gearing, marked experimental in the generator, also allows CK and the commands on
the top banks. CK then comes from a separate PLL output, `sys2x_ck`, shifted by 45 degrees by
default.

The generator records that 45 degrees worked from DDR3-300 to DDR3-600 on ECPIX-5, at 1:2 and
1:4, while 0 and 135 degrees or more failed at DDR3-600. The capture below shows the read leveling
of an ECPIX-5 with 16-bit DDR3 at 300 MT/s.

```console
SDRAM:		524288KiB 16-bit @ 300MT/s (CL-6 CWL-5)
[...]
Initializing SDRAM @0x40000000...
Switching SDRAM to software control.
Read leveling:
  m0, b00: |01110000| delays: 02+-01
  m0, b01: |00000000| delays: -
  m0, b02: |00000000| delays: -
  m0, b03: |00000000| delays: -
  best: m0, b00 delays: 02+-01
[...]
Switching SDRAM to hardware control.
Memtest at 0x40000000 (2.0MiB)...
[...]
Memtest OK
```

Each line is one bitslip (`b00` to `b03`) of one byte lane (`m0`), and each column one of the 8
delay steps. A `1` marks a step where the test pattern and the burst detect passed. Bitslip 0
passes on steps 1 to 3, so the BIOS sets the center, step 2.

### 1:4 on ECP5 {#phys-ecp5-ratio}

`ecp5ddrphy_with_ratio` wraps the PHY in the rate converter for 1:4. The controller runs in `sys`
with 4 phases, the PHY logic in `sys2x` and the edge clock in `sys4x`. Its docstring gives DDR3-800
with a controller near 100 MHz as the goal.

| Variant | Recorded validation |
|-------------------------|--------------------------------------------------------------|
| Default serializers | LFE5UM5G-85F, MT41K256M16, DDR3-600 (ECPIX-5) |
| `rate_crossing=True` | LFE5U-25F, MT41K64M16, DDR3-594 and DDR3-700 (Cam Link 4K) |

At 1:4 the IO gearing resets from the init sequence by default (`io_rst_init`). The docstring
reports the DRAM dead on about one placement in five with the `sys` reset.

The `rate_crossing` variant captures each word once per cycle, on a `sys2x` edge chosen at run
time, which makes it robust to the placement. Its `rate` register must be searched by the init
software, at every initialization, and the BIOS does not do it ([Limitations](#phys-limitations)).

## Lattice Nexus {#phys-nexus}

The Nexus PHY drives DDR3 at 1:2 on the CrossLink-NX and Certus-NX devices (`NexusDDRPHY`). It
follows the ECP5 design with the Nexus primitives `DDRDLL`, `DQSBUF`, `ODDRX2DQ` and `IDDRX2DQ`.
Its read clock select has 4 bits, so 16 delay steps, with 4 bitslips.

The write path of the Nexus IO comes out one DRAM clock late. The PHY starts it one controller
cycle early and uses fixed half-word bitslips to place DQ, DM and DQS at the CWL of the DRAM. A
code comment notes that the 8:1 IO of the family would allow 1:4; the PHY uses 1:2.

The generator does not support this PHY: a design instantiates it directly
([Integration](#integration)).

## Gowin {#phys-gowin}

The Gowin PHYs drive DDR3 with the `OSER4` and `IDES4_MEM` serializers and the `DQS` primitive of
the family. The GW2A PHY runs at 1:2 (`GW2DDRPHY`). The GW5A PHY runs at 1:2 or 1:4, with the 8:1
primitives at 1:4 (`GW5DDRPHY`). Both read with 256 delay steps and check burst detects as the
ECP5 PHY does.

| Parameter | Default | Role |
|----------------|---------|--------------------------------------------------------|
| `nphases` | 2 | GW5A only: 2 or 4 |
| `dll_off` | False | DDR3 DLL-off mode: CL 6, CWL 6, no ODT |
| `cmd_delay` | 0 | Static delay of CK and the commands, below 128 |
| `clk_polarity` | 0 | Inverts the CK pattern |
| `dm_remapping` | None | Maps the DM pins of a board to byte lanes |

**DLL-off mode.** With `dll_off`, the DRAM runs with its DLL disabled, which the generator
documents for DRAM clocks up to 125 MHz. The PHY forces CL and CWL to 6. The init sequence turns
off nominal and dynamic ODT, which the DRAM does not support with the DLL off.

**Read delay direction.** The read delay of the `DQS` primitive moves in both directions under a
direction bit (`rdly_dq_dir`). On GW5A it resets to the value of the DLL, so the BIOS walks it
down to zero before a scan.

**GW5A at 1:4.** With the DLL on, the PHY adds write delays per lane and declares write DQ-DQS
training, which the BIOS then runs. The burst detect pulses are short, so the CRG also provides
`sys4x_i`, the ungated fast clock, to capture them.

The clocking follows the figure of the ECP5 section. The PLL drives a `DHCEN` (GW2A) or `DHCE`
(GW5A) clock gate, a `CLKDIV` makes `sys`, and the PHY init sequence runs from the input clock.

## Efinix {#phys-efinix}

LiteDRAM has no PHY for Efinix devices. SDR SDRAM on Efinix uses the generic SDR PHY, through the
Efinix IO primitives that LiteX substitutes for its generic IO registers. The same mechanism
serves the Intel FPGAs.

DDR memory on Efinix goes through the hard DDR controller of the device, which LiteX wraps itself
for Trion, Titanium and Topaz (`litex/soc/cores/ram/efinix_ddr.py`). It exposes AXI ports and uses
none of the LiteDRAM controller, PHYs or calibration.

## Calibration hooks {#phys-calibration-hooks}

The BIOS runs one calibration code for every PHY. The capability defines of `sdram_phy.h` select
its steps, and a few steps test the PHY type for a family detail. The steps each PHY gets are
listed in [Per-family differences](#cal-families); on the 7-Series HR banks, the write latency
calibration runs only when the design enables it.

The family details in the BIOS are few. On ECP5, Nexus, GW2A and GW5A, it clears and checks
`burstdet_seen` around each read test. It also toggles every lane select after a step, which
pauses and restarts all DQS buffers together.

On UltraScale, the BIOS turns off the compensation during calibration and steps the DQS delay
back to zero. On GW5A, it walks the read delay down with the direction bit. The MPR read leveling
runs on DDR4 at 8 beats per cycle, except on RDIMMs and clam-shell boards.

Calibration passing does not prove the controller latencies, because the BIOS calibrates through
the DFI injector. The memory test through the controller does ([Debugging](#debugging)).

## Limitations {#phys-limitations}

- **Spartan-6.** No run-time calibration: the bitslips and the DQS alignment are build
  parameters, and no hardware result is recorded.
- **7-Series DDR4.** Accepted by the class, but not listed by the README or the file header, and
  not validated.
- **Xilinx DQS preamble.** On 7-Series and UltraScale, the preamble and postamble inputs of the
  DQS pattern are not connected (marked FIXME). DQS toggles through the cycle before and the
  cycle after each write instead of the JEDEC preamble and postamble shapes.
- **7-Series at 1:2.** The PHY builds its DFI with 4 phases while its settings declare 2; the
  controller drives the first two, and the other two are unused.
- **UltraScale+ read VREF.** The PHY generates the read VREF defines, but the LiteX BIOS does not
  scan the VREF: the code stays at `hpio_vref_tune` unless software writes `rd_vref`.
- **ECP5 rate crossing.** The BIOS does not search the `rate` register of `rate_crossing`, so that
  variant needs its own init software (LiteX issue #2770).
- **ECP5 command gearing.** The `x1` gearing is marked experimental in the generator.
- **Nexus.** 1:2 only, and not supported by the generator.
- **Efinix.** No LiteDRAM PHY: DDR on Efinix goes through the hard controller that LiteX wraps.

## In the code {#phys-code}

| File | Content |
|-------------------|------------------------------------------------------------------|
| `gensdrphy.py` | `GENSDRPHY`, `HalfRateGENSDRPHY` |
| `s6ddrphy.py` | `S6HalfRateDDRPHY`, `S6QuarterRateDDRPHY` |
| `s7ddrphy.py` | `S7DDRPHY`, its A7, K7 and V7 classes, CK phase shift, ratio wrapper |
| `usddrphy.py` | `USDDRPHY`, `USPDDRPHY` |
| `ecp5ddrphy.py` | `ECP5DDRPHY`, init sequence, rate crossing, ratio wrapper |
| `nxddrphy.py` | `NexusDDRPHY` and its init sequence |
| `gw2ddrphy.py` | `GW2DDRPHY` |
| `gw5ddrphy.py` | `GW5DDRPHY` |
| `dfi.py` | DFI interface, DDR4 command multiplexer, `DFIRateConverter` |
| `utils.py` | Bitslips, DQS pattern, serializers of the rate converter |

The files are in `litedram/phy/`; the pads and latency helpers are in `litedram/common.py`. The
unit tests are `test/test_<name>.py`, one per PHY file.

Where to go next: [LPDDR4, LPDDR5 and RPC DRAM PHYs](#lpddr-phys) for the other PHYs,
[Memory modules](#modules) for the timings a PHY runs with, [Supported FPGAs and boards](#boards)
for the boards of each family.
