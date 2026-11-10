# Controller {#controller}

This chapter describes the controller: the part of the core that turns requests into DRAM
commands, respects the timings of the module and keeps the DRAM refreshed. Read it to choose the
controller settings or to understand the bandwidth of a traffic pattern. Its commands and timings
are explained in [DRAM in a nutshell](#dram-primer).

## At a glance {#ctrl-glance}

| Item | Value |
|---------------------|---------------------------------------------------------------------------|
| Top-level class | `LiteDRAMController` (`litedram/core/controller.py`) |
| Parts | Bank machines, multiplexer, refresher, optional bandwidth monitor |
| Bank machines | One per bank and rank, or fewer shared by consecutive banks |
| Open rows | One per bank machine, closed by PRE or by auto-precharge |
| Commands per cycle | One RD or WR and one ACT or PRE per `sys` cycle on a multi-phase PHY |
| Read and write windows | 64 and 32 cycles by default, before turning the bus around |
| Refresh | REF every tREFI, up to 8 postponed, ZQCS once per second by default |
| Address mapping | `ROW_BANK_COL` |
| Settings | `ControllerSettings` |

## Overview {#ctrl-overview}

The controller has one bank machine per bank, a refresher and a multiplexer, as the figure below
shows. The bank machines receive the requests of their bank from the crossbar and turn them into
ACT, PRE, RD and WR commands. The refresher asks for refresh cycles. The multiplexer picks the
commands and places them on the DFI phases.

![Controller. Look at the two paths: commands go from the crossbar through the bank machines to the
multiplexer, while write and read data go straight from the crossbar to the multiplexer.](ctrl_overview.svg)

Commands and data travel separately. A bank machine never sees the data: when it issues a WR, the
crossbar presents the write data of that port; after a RD, the data comes back on the shared read
bus. The crossbar delays the handshake pulses of the ports by the PHY latencies to line them up
with the data.

## Bank machines {#ctrl-bank-machines}

A bank machine manages one bank. It remembers which row is open and inserts the ACT and PRE
commands that a request needs. A request to the open row is a row hit and goes out at once as RD or
WR; a request to another row first closes the open row and opens the new one.

Requests enter a command buffer of `cmd_buffer_depth` entries (8 by default), followed by a
single-entry stage that holds the current request. The buffer lets the bank machine look ahead:
when the next request targets another row, the current RD or WR carries the auto-precharge flag
and the row closes without a separate PRE command (`with_auto_precharge`).

The figure below shows the state machine of a bank machine. REGULAR issues RD and WR on row hits.
The other states open and close rows and wait for the timings between them.

![Bank machine state machine. Follow the loop of a row miss: PRECHARGE, wait tRP, ACTIVATE, wait
tRCD, back to REGULAR. With auto-precharge, the CAS itself closes the row and AUTOPRECHARGE only
waits.](ctrl_bankmachine.svg)

The bank machine enforces the timings that concern its own bank. It does not send a PRE before
tRAS after the ACT, tRTP after a RD, or the write recovery after a WR. That recovery counts the
write latency, tWR and tCCD. It also waits tRC between two ACTs, and tRP and tRCD through its wait
states.

On a refresh request, the bank machine enters REFRESH and grants the refresh once tRAS, tRTP and
the write recovery let its row close. The refresher then precharges all the banks itself.

A bank machine keeps a lock towards the crossbar while it holds requests. The crossbar does not
grant a locked port to another bank, so the requests of one port complete in order ([Native
port](#fe-native-port)).

### Shared bank machines {#ctrl-shared-bank-machines}

`nbankmachines` builds fewer bank machines than banks, each shared by consecutive banks. It must be
a power of 2 that divides the number of banks, and works with a single rank. A shared bank machine
arbitrates between its banks and keeps one row open at a time, so traffic that alternates between
its banks closes the row on each change.

The arbiter keeps the granted bank while it has requests, for at most 8 times `cmd_buffer_depth`
requests, so that runs of row hits survive. The generator documentation (`doc/gen.md`) records the
saving on a DDR3 controller and crossbar: about 1180 LUTs with 8 bank machines, about
470 with 2.

## Multiplexer {#ctrl-multiplexer}

The multiplexer picks the commands of the bank machines and of the refresher and drives the DFI.
Two round-robin choosers select among the bank machines: one for RD and WR, one for ACT and PRE.
The steerer places their choices on the DFI phases. On a PHY with one phase, a single chooser
handles every command.

The multiplexer serves reads and writes in turns, because each change of direction costs a bus
turnaround. The figure below shows its state machine. READ issues only reads and the commands that
prepare them; WRITE only writes; RTW and WTR are the turnarounds; REFRESH lets the refresher run.

![Multiplexer state machine. Look at the turnarounds: from READ to WRITE through RTW, from WRITE
to READ through WTR, and REFRESH from either direction once every bank machine has granted
it.](ctrl_multiplexer.svg)

READ moves to RTW when writes wait and either no read waits or the read window has run out. The
read window is `read_time` cycles, 64 by default; `write_time` bounds WRITE, 32 by default. Longer
windows give fewer turnarounds and more bandwidth on mixed traffic, but a longer wait for the
other direction.

The comments of `ControllerSettings` record the effect on a saturated read and write mix on
DDR3-1600 at 1:4, as the share of cycles with a RD or WR on the DFI:

| `read_time` / `write_time` | Cycles with a CAS |
|----------------------------|-------------------|
| 32 / 16 | 74% |
| 64 / 32 (default) | 85% |
| 128 / 64 | 92% |

### Turnarounds {#ctrl-turnarounds}

The read to write turnaround keeps the write data off the bus until the last read burst has left
it. In DRAM clocks it is RL + BL/2 + 2 - WL (JEDEC), plus one controller cycle of DQS preamble
driven by the PHYs, plus `nphases` - 1 for the worst phase alignment. `get_read_to_write_cycles`
rounds it up to `sys` cycles.

The write to read turnaround starts after the write data: WTR waits tWTR plus the write latency
(CWL in `sys` cycles) plus tCCD after the last WR, since tWTR counts from the end of the burst; a
module without tCCD leaves out only that term. After REFRESH, the multiplexer resumes in the direction of the waiting
requests, since a refresh lasts longer than any turnaround.

### Command scheduling {#ctrl-scheduling}

A controller cycle carries one command per DFI phase. The steerer puts the RD or WR on the read or
write phase of the PHY (`rdphase`, `wrphase`) and the ACT or PRE on the phase before it. A refresh
goes on phase 0 and selects every rank. One cycle therefore issues at most one CAS and one ACT
or PRE.

The read and write phases come from the PHY: they align the command so that the data reaches the
DFI at a fixed cycle. Some PHYs expose them as registers (`rdphase`, `wrphase`), which the BIOS
restores at boot and can force with `sdram_force_rdphase` and `sdram_force_wrphase`.

The multiplexer enforces the timings between banks. It holds an ACT until tRRD after the previous
ACT and while four ACTs fall in the last tFAW window. It holds a CAS until tCCD after the previous
one.

## Refresher {#ctrl-refresher}

DRAM cells lose their charge, so every row must be refreshed within the retention time. The
refresher asks for a refresh every tREFI and runs the refresh sequence once the bank machines have
closed their rows. The figure below shows its parts.

![Refresher. Look at the two sources of work: the tREFI timer through the postponer starts refresh
sequences, and the ZQCS timer adds a ZQ calibration after a refresh.](ctrl_refresh.svg)

The handshake goes through the multiplexer. The refresher raises its request; each bank machine
closes its row and grants; the multiplexer enters REFRESH once every bank machine has granted. The
sequencer then sends a PREA, waits tRP, sends a REF and waits tRFC.

The postponer groups refreshes (`refresh_postponing`, 1 by default, 8 at most). With N, it waits N
tREFI periods and then runs N refresh sequences back to back. Fewer interruptions help long
bursts of traffic, at the cost of a longer pause each time.

A ZQCS command recalibrates the output drivers and terminations of the DRAM. When the module
defines tZQCS, the refresher runs one at `refresh_zqcs_freq`, 1 Hz by default. The request waits
for the end of the next refresh sequence, then a PREA, tRP, the ZQCS and tZQCS follow.

The refresher needs a tREFI of at least 100 `sys` cycles and fails at elaboration otherwise.
`with_refresh=False` stops the refresh and ZQCS requests, for simulations that do not model the
retention time. The refresher is still built, so the tREFI check still applies.

## Timings {#ctrl-timings}

Every timing reaches the controller in `sys` cycles from the module ([Memory modules](#modules)).
The table below lists where each one is enforced.

| Timing | Between | Enforced by |
|------------|--------------------------------------------|--------------------------|
| tRCD | ACT and RD or WR of the bank | Bank machine (TRCD) |
| tRP | PRE and ACT of the bank | Bank machine (TRP), refresher |
| tRAS | ACT and PRE of the bank | Bank machine |
| tRC | Two ACTs of the bank | Bank machine |
| tRTP | RD and PRE of the bank | Bank machine |
| tWR | Write data and PRE of the bank | Bank machine, with the write latency and tCCD |
| tRRD | Two ACTs of any banks | Multiplexer |
| tFAW | A window of four ACTs of any banks | Multiplexer |
| tCCD | Two CAS commands | Multiplexer |
| tWTR | Write data and the next RD | Multiplexer (WTR) |
| tRFC | REF and the next command | Refresher |
| tREFI | Two refresh requests | Refresher |
| tZQCS | ZQCS and the next command | Refresher |

CL and CWL are not controller timings: they are programmed in the mode registers at
initialization, and the PHY latencies account for them.

## Dynamic ODT {#ctrl-dynamic-odt}

By default the controller asserts ODT all the time, on every rank. The DRAM termination is then on
during reads too, which the JEDEC rules forbid when RTT_NOM or RTT_WR are enabled. Dynamic ODT
(`with_dynamic_odt`) asserts ODT only with each WR and holds it for 6 DRAM clocks, as ODTH8
requires.

Dynamic ODT works with DDR3 on a single rank. The read to write and write to read turnarounds keep
the termination off from before the read preamble to after the read postamble.

## Bandwidth monitor {#ctrl-bandwidth}

`with_bandwidth` adds a monitor on the RD and WR commands of the multiplexer. It counts them over
periods of 2^24^ `sys` cycles; a write to `update` copies the counts of the last finished period to
`nreads` and `nwrites`. `data_width` gives the bits of one command.

The bandwidth in bits per second is the sum of the two counts times `data_width`, divided by the
period in seconds. The counts include every port, so the monitor shows the load of the DRAM, not
of one master.

## Settings {#ctrl-settings}

A `ControllerSettings` object holds the options of the controller. The generator takes all of them
but `refresh_cls` as YAML keys ([Build options](#build-options)). The table below lists them.

| Setting | Default | Meaning |
|------------------------------|----------------------|---------------------------------------|
| `cmd_buffer_depth` | `8` | Requests buffered per bank machine |
| `cmd_buffer_buffered` | `False` | Registered command buffers |
| `nbankmachines` | one per bank | Number of bank machines, shared when lower |
| `read_time` | `64` | Cycles of reads before turning to waiting writes |
| `write_time` | `32` | Cycles of writes before turning to waiting reads |
| `with_bandwidth` | `False` | Bandwidth monitor registers |
| `with_refresh` | `True` | Periodic refresh |
| `refresh_cls` | `Refresher` | Class of the refresher |
| `refresh_zqcs_freq` | `1e0` | ZQCS frequency in Hz |
| `refresh_postponing` | `1` | Refreshes grouped per request, 8 at most |
| `with_dynamic_odt` | `False` | ODT only around writes, DDR3 single rank |
| `with_auto_precharge` | `True` | Close the row with the CAS when the next request misses |
| `address_mapping` | `"ROW_BANK_COL"` | Address mapping, the only one |
| `bank_byte_alignment` | `0` | Minimum byte distance between bank changes |

The defaults suit most designs. A design with many masters on random addresses gains from
auto-precharge and a deep command buffer; a design with long streams in one direction gains from
longer read and write windows.

## In the code {#ctrl-code}

| Class | File and role |
|--------------------------|----------------------------------------------------------------|
| `ControllerSettings` | `litedram/core/controller.py`: settings |
| `LiteDRAMController` | `litedram/core/controller.py`: bank machines, multiplexer, refresher |
| `BankMachine` | `litedram/core/bankmachine.py`: row tracking and bank timings |
| `Multiplexer` | `litedram/core/multiplexer.py`: choosers, steerer, turnarounds |
| `Refresher` | `litedram/core/refresher.py`: timer, postponer, sequencer, ZQCS |
| `Bandwidth` | `litedram/core/bandwidth.py`: command counters |
| `tXXDController` | `litedram/common.py`: timing counters, with `tFAWController` |

Where to go next: [Ports and frontends](#frontends) for the user side of the crossbar, [Memory
modules](#modules) for the timings, [Performance and resources](#performance) for measured
figures.
