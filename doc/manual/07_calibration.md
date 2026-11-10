# Initialization and calibration {#calibration}

This chapter describes how a DRAM goes from power-up to a working memory: the JEDEC initialization
sequence, then the calibration that aligns the FPGA and DRAM signals. Read it to understand the
BIOS boot log, to bring up a board or to initialize a core without a CPU. Leveling itself is
explained in [The DRAM interface and the PHY](#dram-interface).

## At a glance {#cal-glance}

| Item | Value |
|---------------------|-------------------------------------------------------------------------|
| Gateware side | DFI injector, PHY delay and bitslip registers, PHY clock init blocks |
| Software side | LiteX BIOS, `liblitedram`: `sdram_init()` |
| Interface | `sdram_phy.h`, generated from the PHY settings and the module |
| Sequences | SDR, DDR, LPDDR, DDR2, DDR3, DDR4, RPC, LPDDR4, LPDDR5 (`litedram/init.py`) |
| Steps | Write leveling, MPR read leveling, write latency, DQ-DQS training, read leveling |
| Other levelings | CK phase leveling (7-Series HR banks), SDR clock phase leveling |
| Check | Memory test of 2 MiB through the controller, then a speed test |
| Result | `init_done`, and `init_error` on failure, in the generated core |

## Gateware and software {#cal-split}

Calibration is split between gateware and software. The gateware provides the means: the DFI
injector to send any command, and in each PHY the registers that move delays and bitslips. The
software decides: it writes test patterns, reads them back and chooses the settings. The same
algorithms then serve every PHY and every board.

The software is the LiteX BIOS and its `liblitedram`. It runs on the CPU of the SoC at boot, before
the DRAM holds any data, from the ROM and the SRAM. Its output on the console shows every scan, so
a failed calibration can be read from the boot log.

Some PHYs also have a small gateware init block for their clocks. The ECP5, Nexus and Gowin PHYs
lock a DLL and reset or pause their IO clocks in a fixed order after reset, in an `init` clock
domain. This prepares the PHY only; the DRAM itself is initialized by software.

Calibration works on the raw DFI, below the controller ([DFI injector](#arch-dfi-injector)). The
controller latencies take no part in it, so a passing calibration does not prove them. The memory
test at the end of the boot, through the controller, does.

## The generated header {#cal-header}

The BIOS learns everything about the PHY and the memory from `sdram_phy.h`. LiteDRAM generates it
from the PHY settings and the module (`get_sdram_phy_c_header`), and the LiteX builder writes it to
`generated/sdram_phy.h`. The table below lists its main content.

| Define or function | Content |
|---------------------------------------|-----------------------------------------------------|
| `SDRAM_PHY_<PHYTYPE>`, `SDRAM_PHY_<MEMTYPE>` | PHY class and memory type |
| `SDRAM_PHY_PHASES`, `SDRAM_PHY_XDR` | DFI phases; 1 for SDR, 2 for DDR |
| `SDRAM_PHY_DATABITS`, `SDRAM_PHY_MODULES` | DQ width and number of strobes |
| `SDRAM_PHY_CL`, `SDRAM_PHY_CWL` | CAS latency and write latency, DRAM clocks |
| `SDRAM_PHY_RDPHASE`, `SDRAM_PHY_WRPHASE` | Read and write phases at reset |
| `SDRAM_PHY_DELAYS`, `SDRAM_PHY_BITSLIPS` | Delay taps and bitslips of the PHY |
| Capability defines | Calibration steps the PHY supports |
| `SDRAM_PHY_CMD_DELAY` | Command delay forced at build time |
| `SDRAM_PHY_CKPHASE_STEPS` | CK phase steps per tCK, on CK phase PHYs |
| `init_sequence()` | The JEDEC sequence of the memory type |
| `command_p<n>()` | Issue a command on DFI phase n |

The capability defines select the calibration steps that the BIOS compiles in. They come from the
PHY settings: `write_leveling`, `write_latency_calibration`, `write_dq_dqs_training` and
`read_leveling`.

## Initialization sequence {#cal-init}

`sdram_init()` brings the DRAM from reset to normal operation, as the figure below shows. It takes
the DFI in software control, resets the PHY, sends the JEDEC sequence and runs the calibration. It
then gives the DFI back to the controller and tests the memory.

![DRAM initialization by the BIOS. Follow the steps from top left: the cyan leveling runs in
software control; the memory test runs through the controller and starts the leveling again on
failure when retries are enabled.](cal_flow.svg)

Before the sequence, `sdram_init()` clears the delays and bitslips forced from the console and
restores the read and write phases of the header. It pulses the PHY reset (`ddrphy_rst`) on the
PHYs that have one. On SDR PHYs with a clock phase stepper, the clock phase leveling runs right
after the JEDEC sequence.

The JEDEC sequence is `init_sequence()`, generated per memory type by `litedram/init.py`. It sends
the commands on DFI phase 0 through the injector, with the waits the standard asks for. The table
below shows the DDR3 sequence.

| Step | Command | Content |
|------------------------|------------|---------------------------------------------------------|
| Release reset | RESET_N | Control register, then a wait |
| Bring CKE high | CKE | Control register, then a wait |
| Load Mode Register 2 | MRS | CWL, RTT_WR |
| Load Mode Register 3 | MRS | 0 |
| Load Mode Register 1 | MRS | Output driver, RTT_NOM, DLL-off mode when used |
| Load Mode Register 0 | MRS | Burst length 8, CL, write recovery, DLL reset |
| ZQ Calibration | ZQCL | Then a wait |

The termination and driver values come from the PHY electrical settings. Without them, the DDR3
sequence uses 60 ohm for RTT_NOM and RTT_WR and 34 ohm for the output driver. The DDR4 sequence
programs MR0 to MR6, the LPDDR4 and LPDDR5 sequences their own mode registers
([LPDDR4, LPDDR5 and RPC DRAM PHYs](#lpddr-phys)).

## Calibration steps {#cal-steps}

`sdram_leveling()` resets every delay and bitslip, then runs the steps that the header enables, in
the order of the table below. Each step uses the results of the previous ones.

| Step | Enabled by | Sets |
|------------|-----------------------------------------------------------------------|-------------|
| Write leveling | `SDRAM_PHY_WRITE_LEVELING_CAPABLE` | Command delay, DQS and DQ delays |
| MPR read leveling | DDR4 with read leveling, 8 beats per cycle | First read settings |
| Write latency | `SDRAM_PHY_WRITE_LATENCY_CALIBRATION_CAPABLE` | Write bitslips |
| DQ-DQS training | `SDRAM_PHY_WRITE_DQ_DQS_TRAINING_CAPABLE` | Write DQ delays |
| Read leveling | `SDRAM_PHY_READ_LEVELING_CAPABLE` | Read bitslips and delays |
| CK phase leveling | `SDRAM_PHY_CKPHASE_STEPS`, replaces read leveling | CK phase, all lanes |

Most steps rely on one probe: write a burst of pseudo-random data to row 0 of bank 0 through the
injector, read it back and count the wrong bits of one byte lane. The BIOS output calls a byte lane
a module (`m0`, `m1`). A setting passes only when three patterns, from three seeds, read back
without error.

### Write leveling {#cal-write-leveling}

Write leveling aligns the DQS of each byte lane with the clock that reaches its chip. With a
fly-by layout the clock arrives later at each chip, so each lane needs its own DQS delay. The BIOS
sets MR1 bit 7, which makes the DRAM sample CK on each DQS edge and return the value on DQ.

For each lane, the BIOS moves the DQS and DQ write delays together, one tap at a time, and pulses
a DQS strobe (`wlevel_strobe`) at each tap. A tap where the DRAM returns 1 saw CK high.

The delay kept is the start of the longest run of 1s: the point where the DQS edge meets the CK
rising edge. A run that already starts at tap 0 gives a delay of 0 only when it is longer than a
quarter of a DRAM clock.

The scan covers the delay taps minus a quarter of a DRAM clock. A lane whose transition falls
outside the scan cannot be leveled, so the BIOS first moves the command and clock (`cdly`). It
tries delays up to half a DRAM clock and keeps the one that levels the most lanes with centred
data delays.

The capture below, from a KC705 (64-bit DDR3 SO-DIMM, 1 GiB, DDR3-1000), shows the effect of the
command delay. Before, lanes 4 to 7 start with CK high and their longest run of 1s at tap 0: they
get a delay of 0. After 12 taps of command delay, every lane shows its 0 to 1 transition.

```console
Before (delay = 0 taps):
Write leveling:
m0: |11000000000000011111111111| delay: 15
m1: |00000000000000111111111111| delay: 14
m2: |11110000000000000111111111| delay: 17
m3: |11110000000000000011111111| delay: 18
m4: |11111111110000000000000111| delay: 00
m5: |11111111110000000000000111| delay: 00
m6: |11111111111000000000000001| delay: 00
m7: |11111111111000000000000011| delay: 00

After (delay = 12 taps):
Write leveling:
m0: |11111111111111000000000000| delay: 00
m1: |11111111111100000000000001| delay: 00
m2: |00011111111111110000000000| delay: 03
m3: |00011111111111110000000000| delay: 03
m4: |00000000111111111111110000| delay: 08
m5: |00000000111111111111110000| delay: 08
m6: |00000000001111111111111000| delay: 10
m7: |00000000001111111111111000| delay: 10
```

The automatic scan of the command delay prints one block per delay when the BIOS is built with
`SDRAM_WRITE_LEVELING_CMD_DELAY_DEBUG`. The capture below is from the same board with that option.

The header gives the range 0-12, end excluded, so the blocks go from 0 to 11 taps. The BIOS keeps
11, where six lanes level and the mean delay is closest to the ideal, then runs the final
data scan. A dash means no
usable transition for that lane.

```console
Write leveling:
  tCK/4 taps: 6
  Cmd/Clk scan (0-12)
  |Cmd/Clk delay: 0
  m0: |11000000000000011111111111| delay: 15
[...]
Cmd/Clk delay: 11
  m0: |11111111111110000000000001| delay: -
  m1: |11111111111000000000000001| delay: -
  m2: |00111111111111100000000000| delay: 02
  m3: |00111111111111100000000000| delay: 02
  m4: |00000001111111111111100000| delay: 07
  m5: |00000000111111111111100000| delay: 08
  m6: |00000000011111111111110000| delay: 09
  m7: |00000000011111111111110000| delay: 09
Delay mean: 12, ideal: 13
| best: 11
  Setting Cmd/Clk delay to 11 taps.
  Data scan:
[...]
Write latency calibration:
m0:6 m1:6 m2:6 m3:6 m4:6 m5:6 m6:6 m7:6
```

The `tCK/4 taps` line is the PHY register `half_sys8x_taps`: delay taps in a quarter of a DRAM
clock. At 500 MHz with a 200 MHz IDELAY reference (78 ps taps), the 7-Series PHY computes 6.

The KC705 captures of this chapter come from older BIOS versions; a current BIOS prints the same
steps differently. The table below lists the differences, to read a recent log against them.

| Item | KC705 captures | Current BIOS |
|--------------------------|------------------------------|-----------------------------------------|
| DRAM clock in taps | `tCK/4 taps: 6` | `tCK equivalent taps: 24`, four times the register |
| Command delay scan | One block per delay | One pass digit per delay, blocks only with the debug option |
| Delay mean and ideal | In taps | In 1/256 of a tap (`/256`) |
| Run of 1s from tap 0 | Dash or 0, by version | 0 when longer than a quarter of a DRAM clock |
| Bitslip in read leveling | `b0` | `b00` |

With a current BIOS, lanes `m0` and `m1` of the final data scan above would get a delay of 0
instead of a dash.

### Write latency and DQ-DQS training {#cal-write-latency}

Write latency calibration chooses, per byte lane, when the write data leaves the PHY. The BIOS
tries the write bitslips by steps of 2, one DRAM clock each, and keeps the one whose written
pattern reads back with a read window. The line `m0:6 m1:6` above gives the bitslip of each lane.

Write DQ-DQS training centres the DQ of each lane on its DQS. The BIOS first finds a read bitslip
that works, moving the write data if needed. It then scans the write DQ delay and sets it in the
middle of the largest passing window.

### Read leveling {#cal-read-leveling}

Read leveling finds where to capture the read data of each byte lane. The PHY deserializes the
data with a bitslip, which shifts the word by one bit, and delays it with a tap delay. The BIOS
scans every bitslip and, for each one, every delay tap, as the figure below shows.

![Read leveling scan of one byte lane. Look at the cyan runs of passing taps: bitslip 4 has the
widest window, and the BIOS sets the delay at its centre, the green mark at tap 16.](cal_read_window.svg)

For each bitslip, the BIOS prints the passing taps, then the centre and half-width of the largest
window. It keeps the bitslip with the most passing taps; on a tie, the one with the fewest errors
on its failing taps, then the first one.

The BIOS then sets the delay to the middle of the window, which
opens on two consecutive passing taps, and checks it.

The capture below is the read leveling of the same KC705, for lane 1 (the figure) and the end of
the boot. One bitslip moves the window by one bit time, 1 ns at DDR3-1000, or about 13 taps of
78 ps; the widest window is on bitslip 4.

```console
Read leveling:
[...]
  m1, b0: |00000000000000000000000000000000| delays: -
  m1, b1: |00000000000000000000000000000000| delays: -
  m1, b2: |00000000000000000000000000000000| delays: -
  m1, b3: |11111111000000000000000000000000| delays: 04+-04
  m1, b4: |00000000000011111111100000000000| delays: 16+-04
  m1, b5: |00000000000000000000000000111111| delays: 29+-03
  m1, b6: |00000000000000000000000000000000| delays: -
  m1, b7: |00000000000000000000000000000000| delays: -
  best: m1, b04 delays: 16+-04
[...]
Switching SDRAM to hardware control.
Memtest at 0x40000000 (2MiB)...
  Write: 0x40000000-0x40200000 2MiB
   Read: 0x40000000-0x40200000 2MiB
Memtest OK
Memspeed at 0x40000000 (2MiB)...
  Write speed: 40MiB/s
   Read speed: 33MiB/s
```

On PHYs with more than 128 taps, the full scan would be slow. The BIOS then scans sparsely with one
seed to find candidate bitslips, and validates them with a full scan. It falls back to the full
scan when the candidates are ambiguous. The same fast path exists for the write latency
calibration and the final write leveling scan.

### MPR read leveling {#cal-mpr}

The write steps read back what they write, so they cannot tell a read error from a write error.
On DDR4, the BIOS first levels the reads on the predefined patterns of the DRAM multi-purpose
register (MPR), which need no write. Lanes where the final read leveling finds no window keep these
settings.

MPR read leveling runs on DDR4 PHYs with read leveling and 8 beats per controller cycle. It is
skipped on registered DIMMs and clam-shell layouts, and can be disabled with
`SDRAM_MPR_READ_LEVELING_DISABLE`.

## CL and CWL {#cal-cl-cwl}

CL and CWL are the read and write latencies of the DRAM, in DRAM clocks. The PHY picks them from
the data rate, with the slowest JEDEC bin that covers it (`get_default_cl_cwl`), unless its `cl`
and `cwl` parameters set them. The init sequence programs them, and the BIOS banner prints them.

The table below lists the DDR3 defaults. DDR2, DDR4 and SDR have their own tables in
`litedram/common.py`.

| DDR3 data rate up to | CL | CWL |
|----------------------|----|-----|
| 800 MT/s | 6 | 5 |
| 1066 MT/s | 7 | 6 |
| 1333 MT/s | 10 | 7 |
| 1600 MT/s | 11 | 8 |
| 1866 MT/s | 13 | 9 |

From CL and CWL, the PHY computes its read and write phases and latencies in controller cycles. A
wrong latency passes calibration, which runs on the raw DFI, and fails the memory test. The
`rdphase` and `wrphase` registers of the 7-Series and UltraScale PHYs let the BIOS console change
them without a rebuild (`sdram_force_rdphase`, `sdram_force_wrphase`).

On Artix-7 DDR3, the read data must arrive one DRAM clock later in the deserializer word for a
reliable read leveling. Older versions programmed CL + 1 in MR0 for this; the PHY now keeps CL and
shifts its own read schedule instead.

## Per-family differences {#cal-families}

Each PHY supports the steps its FPGA primitives allow. The table below lists them; [DDR PHYs](#phys)
describes the PHYs themselves.

| PHY | Steps | Delays | Bitslips |
|------------------------------|-------------------------------------------------|--------|----------|
| `GENSDRPHY` | None, or SDR clock phase leveling | none | none |
| `S6HalfRateDDRPHY` | None: settings fixed at build time | none | none |
| `A7DDRPHY` | Read leveling | 32 | 8 |
| `K7DDRPHY`, `V7DDRPHY`, DDR3 | Write leveling, write latency, DQ-DQS, read leveling | 32 | 8 |
| `K7DDRPHY`, `V7DDRPHY`, DDR2 | Read leveling | 32 | 8 |
| `S7DDRPHY`, CK phase shift | CK phase leveling | 32 | 8 |
| `USDDRPHY`, `USPDDRPHY` | Write leveling, write latency, read leveling, MPR on DDR4 | 512 | 8 |
| `ECP5DDRPHY` | Read leveling with burst detection | 8 | 4 |
| `NexusDDRPHY` | Read leveling with burst detection | 16 | 4 |
| `GW2DDRPHY` | Read leveling with burst detection | 256 | 4 |
| `GW5DDRPHY` | Read leveling with burst detection; DQ-DQS at 1:4 | 256 | 2 x phases |

The Artix-7 has no output delay, so its PHY cannot do write leveling. `K7DDRPHY` with
`with_odelay=False`, for Kintex-7 HR banks, behaves the same. `A7DDRPHY` also leaves the write
latency calibration off by default (`write_latency_calibration=False`).

Arty A7 boot logs from older LiteDRAM versions still show a `Write latency calibration:` line with `m0:0 m1:0`: they
predate this default, and a current Arty A7 log goes straight to the read leveling. The UltraScale PHYs turn their voltage and temperature
compensation off during calibration (`en_vtc`) and back on after it. The Gowin GW5A PHY adds the
write DQ-DQS training at 1:4 with the DRAM DLL on.

The Lattice and Gowin PHYs have a burst detector on each DQS group. The BIOS clears it before each
read check and counts an error when it saw no burst, which rejects settings that only pass by
chance. The capture below, from an ECPIX-5 (ECP5, 16-bit DDR3, 512 MiB, DDR3-300), shows their
short 8-tap scans.

```console
Read leveling:
  m0, b00: |01110000| delays: 02+-01
  m0, b01: |00000000| delays: -
  m0, b02: |00000000| delays: -
  m0, b03: |00000000| delays: -
  best: m0, b00 delays: 02+-01
  m1, b00: |01110000| delays: 02+-01
  m1, b01: |00000000| delays: -
  m1, b02: |00000000| delays: -
  m1, b03: |00000000| delays: -
  best: m1, b00 delays: 02+-01
Switching SDRAM to hardware control.
```

### CK phase leveling {#cal-ck-phase}

7-Series HR banks have no output delay, so with a fly-by layout a single DQS phase cannot meet
every lane. `S7DDRPHY` with `with_ck_phase_shift` moves CK and the commands instead, on a fine phase
shift output of the MMCM. It supports DDR3 at 1:4; the BIOS leveling expects 64-bit channels, or
72 bits with ECC lanes.

The BIOS scans the CK phase over one DRAM clock. At each step it runs the JEDEC sequence, picks a
write latency per lane and a read bitslip and delay per DQ bit, then checks with the DFI and with a
BIST run. It settles in the middle of the longest passing run of phases.

At the chosen phase, the BIOS refines the read delay of each bit under BIST traffic, since the eye
under traffic is narrower than under isolated bursts. The per-bit counters of the DFI ECC show
which bits fail when they exist ([DFI ECC](#arch-dfi-ecc)). The traffic checks use the LiteDRAM
BIST when the SoC has one (`add_sdram(with_bist=True)`).

### SDR clock phase leveling {#cal-sdr-phase}

An SDR PHY has no delays of its own. When the SDRAM clock comes from a PLL output with a run-time
phase shift (`sdram_clk_phase` registers), the BIOS scans that phase over one SDRAM clock. Each
step runs the JEDEC sequence and a write and read check of the first 1 MiB; the middle of the
longest passing run wins.

Without a phase stepper, an SDR memory needs no calibration at all. The capture below, from a
TEC0117 (Gowin GW1NR-9, 16-bit SDR SDRAM, 8 MiB, 25 MT/s), goes straight from software to hardware
control.

```console
Initializing SDRAM @0x40000000...
Switching SDRAM to software control.
Switching SDRAM to hardware control.
Memtest at 0x40000000 (2MiB)...
  Write: 0x40000000-0x40200000 2MiB
   Read: 0x40000000-0x40200000 2MiB
Memtest OK
Memspeed at 0x40000000 (2MiB)...
  Write speed: 5MiB/s
   Read speed: 6MiB/s
```

## Memory test and result {#cal-memtest}

After the calibration, the BIOS gives the DFI back to the controller and tests 2 MiB from the start
of the DRAM through the CPU bus. This test checks what calibration cannot: the latencies of the
controller and the whole path from the CPU.

When the test fails, the BIOS can run the leveling again. `SDRAM_LEVELING_RETRIES` sets the number
of attempts, 1 by default, so a default BIOS does not retry. After the last failure, it sets
`init_error` and `init_done` and stops.

On success, the BIOS measures the write and read speed and sets `init_done`. The speed test runs on
the CPU, so its result, printed in MiB/s, reflects the CPU and its bus more than the DRAM. The
`init_done` and `init_error` registers exist in the generated core (`ddrctrl` bank), where they
release the user ports.

## Initialization without a CPU {#cal-no-cpu}

A core generated with `cpu: None` has no BIOS. It exposes a `wb_ctrl` Wishbone slave on its
registers, and your logic or software runs the initialization. `init_sequence()` of `sdram_phy.h`
only sends the JEDEC commands; a complete initialization has seven steps:

1. Switch the DFI to software control (`sdram_dfii_control`).
2. Reset the PHY (`ddrphy_rst`), on the PHYs that have it.
3. Run `init_sequence()`.
4. Run the write and read leveling, on the PHYs that support it.
5. Switch the DFI back to hardware control.
6. Optionally run a memory test.
7. Write 1 to `ddrctrl_init_done`, and to `ddrctrl_init_error` on failure.

Step 7 is required with `block_until_ready`, the default of the generated ports: the ports do not
answer before `init_done` is set. This holds for a simulation core too. The register addresses of
`csr.csv` are byte addresses, while `wb_ctrl_adr` is a word address: shift them right by 2.

## Custom initialization {#cal-custom}

Some memories need board power sequencing or a training flow that the generated sequence cannot
express. With `CONFIG_SDRAM_CUSTOM_INIT`, `sdram_init()` calls `sdram_custom_init()`, provided by
the design, instead of the reset, the sequence and the leveling. The memory test and the result
registers stay the same.

## BIOS commands {#cal-commands}

The BIOS console gives access to each step, to repeat a calibration or force a setting. The table
below lists the commands; [Debugging](#debugging) shows how to use them.

| Command | Action |
|-----------------------------|----------------------------------------------------------|
| `sdram_init` | Initialization and calibration, as at boot |
| `sdram_cal` | Calibration only; the clock phase leveling on SDR PHYs |
| `sdram_test` | Memory test |
| `sdram_force_rdphase` | Force the read phase |
| `sdram_force_wrphase` | Force the write phase |
| `sdram_rst_cmd_delay` | Let the write leveling scan the command delay again |
| `sdram_force_cmd_delay` | Force the command delay |
| `sdram_rst_dat_delay` | Let the write leveling find the data delay of a lane |
| `sdram_force_dat_delay` | Force the data delay of a lane |
| `sdram_rst_bitslip` | Let the calibration find the write bitslip of a lane |
| `sdram_force_bitslip` | Force the write bitslip of a lane |
| `sdram_mr_write` | Write a mode register |
| `sdram_spd` | Read the SPD EEPROM of a module, compare it with the SPD memory of the build |
| `sdram_bist` | Run the BIST and print its throughput |
| `sdram_hw_test` | Memory test with the BIST |
| `sdram_debug` | Debug tests |

## Registers {#cal-registers}

The calibration registers are in the `ddrphy` bank, next to the injector registers of the `sdram`
bank. Their set depends on the PHY; the table below lists them, and [Register
reference](#registers) gives them per family.

| Register | Role | PHYs |
|-------------------------------------------|-------------------------------------------|------------------|
| `rst` | PHY reset at initialization | 7-Series, UltraScale |
| `dly_sel` | Byte lanes the delay registers act on | All with leveling |
| `half_sys8x_taps` | Delay taps in a quarter of a DRAM clock | 7-Series, UltraScale |
| `wlevel_en`, `wlevel_strobe` | Write leveling mode and DQS strobe | 7-Series, UltraScale |
| `cdly_rst`, `cdly_inc` | Command and clock delay | Kintex-7, Virtex-7, UltraScale |
| `wdly_dq_rst`, `wdly_dq_inc` | Write DQ delay | Kintex-7, Virtex-7, UltraScale |
| `wdly_dqs_rst`, `wdly_dqs_inc` | Write DQS delay | Kintex-7, Virtex-7, UltraScale |
| `wdly_dq_bitslip_rst`, `wdly_dq_bitslip` | Write bitslip | 7-Series, UltraScale |
| `rdly_dq_rst`, `rdly_dq_inc` | Read delay | All with leveling |
| `rdly_dq_bitslip_rst`, `rdly_dq_bitslip` | Read bitslip | All with leveling |
| `rdphase`, `wrphase` | Read and write phases | 7-Series, UltraScale |
| `en_vtc` | Voltage and temperature compensation | UltraScale |
| `burstdet_clr`, `burstdet_seen` | Burst detection | ECP5, Nexus, Gowin |
| `rdly_dq_dir` | Direction of the read delay steps | Gowin |

## In the code {#cal-code}

| Function or class | File and role |
|--------------------------------------|--------------------------------------------------|
| `get_sdram_phy_init_sequence` | `litedram/init.py`: JEDEC sequences |
| `get_sdram_phy_c_header` | `litedram/init.py`: `sdram_phy.h` |
| `get_default_cl_cwl` | `litedram/common.py`: default CL and CWL |
| `DFIInjector` | `litedram/dfii.py`: software access to the DFI |
| `sdram_init`, `sdram_leveling` | LiteX `liblitedram/sdram.c`: initialization and calibration |
| Delay accessors | LiteX `liblitedram/accessors.c`: delay and bitslip registers |

Where to go next: [DDR PHYs](#phys) for the PHY of each family, [Getting started](#getting-started)
to read a first boot log, [Debugging](#debugging) when a calibration fails.
