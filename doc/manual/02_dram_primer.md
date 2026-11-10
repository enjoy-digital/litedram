# DRAM in a nutshell {#dram-primer}

This chapter explains DRAM to an FPGA engineer who has never read a memory datasheet. It starts
from the storage cell, builds up the banks, rows and columns, then gives the commands, the timings
and the refresh that every controller must respect. It ends with the generations of DRAM and with
what makes a memory fast or slow.

Each section starts with the idea, then gives the mechanism, and ends with the part of LiteDRAM
that implements it. The next chapter, [The DRAM interface and the PHY](#dram-interface), covers
the pins and the signals.

The references are the JEDEC standards of each memory type: JESD79-2 for DDR2, JESD79-3 for DDR3,
JESD79-4 for DDR4, JESD209-4 for LPDDR4 and JESD209-5 for LPDDR5. This chapter uses DDR3 as its
example, because it is the most common memory on FPGA boards; [DRAM
generations](#primer-generations) lists what changes from one type to the next.

## The cell {#primer-cell}

A DRAM stores each bit as a charge on a tiny capacitor. One transistor connects the capacitor to a
*bit line* when its *word line* is selected. This one transistor, one capacitor cell is what makes
DRAM dense and cheap, and also what makes it slow and demanding. The figure below shows a cell.

![A DRAM cell. Selecting the word line connects the capacitor to the bit line; the sense amplifier
at the end of the bit line detects the small charge, amplifies it and writes it back into the
cell.](primer_cell.svg)

The charge is tiny compared to the bit line, so reading a cell only moves the bit line voltage a
little. A *sense amplifier* detects that change and drives the bit line to a full 0 or 1. Reading
drains the cell, so the sense amplifier writes the value back: a DRAM read is destructive, and it
restores the cell.

The capacitor also leaks. After some tens of milliseconds a cell can no longer be read reliably,
so every cell must be read and restored regularly: this is the *refresh*, described in
[Refresh](#primer-refresh).

In LiteDRAM, nothing models the cell: the controller only has to respect the timings that follow
from it, and to send the refreshes.

## Banks, rows and columns {#primer-organization}

A DRAM chip arranges its cells in a few independent arrays, the *banks*. Each bank is a matrix of
*rows* and *columns*. A row is opened as a whole: its word line connects all its cells to their
sense amplifiers, which then hold the entire row. The sense amplifiers act as a *row buffer*, as
the figure below shows.

![One bank of a DRAM chip. ACT opens one row (cyan) into the sense amplifiers, the row buffer; RD
and WR then select columns of that row and move one burst between the row buffer and the DQ pins.
A chip has several identical banks.](primer_organization.svg)

Reads and writes then work on the row buffer only: a column address selects which bits of the open
row go to or come from the data pins. Accesses to an open row are fast; accessing another row of
the same bank first requires closing the open one and opening the new one.

The banks are independent. Each one can have its own open row, and the controller can open a row
in one bank while another bank transfers data. This bank parallelism hides much of the cost of
opening rows.

The *width* of a chip is the number of data pins it has: x4, x8 or x16. The Micron MT41K128M16 of
the Arty A7, for example, is a DDR3 x16 chip with 8 banks, 16384 rows and 1024 columns: 8 x 16384 x
1024 x 16 bits, that is 2 Gbit or 256 MiB.

A wider memory is built from several chips side by side. They share the clock, command and address
pins and each drives its own data pins: eight x8 chips form a 64-bit memory, and nine form a
72-bit memory with room for ECC. Such a group of chips is a *rank*, and a DIMM carries one or
more ranks.

DDR4 groups its banks into *bank groups*: an x8 DDR4 chip such as the MT40A512M8 has 4 groups of 4
banks. Consecutive accesses to different bank groups can follow each other faster than accesses
within the same group.

In LiteDRAM, a module class of `litedram/modules.py` gives the geometry of a chip: `nbanks`,
`nrows` and `ncols`, plus `ngroups` and `ngroupbanks` for DDR4. The PHY counts the data pins and
the strobes, so the width of the memory comes from the board, not from the module. See [Memory
modules](#modules).

## Commands {#primer-commands}

The controller drives the DRAM with commands. On SDR to DDR3, a command is encoded on four pins
sampled at a clock edge, chip select (CS#), RAS#, CAS# and WE#, together with the bank and address
pins. The table below lists the commands a controller uses.

| Command | Name | Effect |
|---------|--------------------------|------------------------------------------------------------|
| ACT | Activate | Open a row of a bank into its row buffer |
| RD | Read | Read a burst from columns of the open row |
| WR | Write | Write a burst to columns of the open row |
| PRE | Precharge | Close the open row of a bank, restoring it to the cells |
| PREA | Precharge all | Close the open rows of every bank |
| REF | Refresh | Refresh the next rows of every bank, all banks closed |
| MRS | Mode register set | Write a mode register (latencies, burst length, drive, termination) |
| ZQCL, ZQCS | ZQ calibration long, short | Calibrate the output drivers and terminations against the ZQ resistor |
| NOP, DES | No operation, deselect | Nothing; fill the cycles between commands |

RD and WR can also close the row by themselves once the burst is done: this is
*auto-precharge*, selected by the address bit A10 of the command. It saves a PRE when the next
access goes to another row.

DDR4 adds an ACT_n pin and reuses the RAS#, CAS# and WE# pins as row address bits during ACT.
LPDDR4 and LPDDR5 replace the whole scheme with a narrow command and address bus on which each
command takes several clock edges.

In LiteDRAM, the controller produces DDR3-style commands on each DFI phase (`cas_n`, `ras_n`,
`we_n`, `cs_n`, address and bank). Each bank machine issues ACT, RD, WR and PRE for its bank, with
auto-precharge enabled by default (`with_auto_precharge`). The DDR4 PHYs convert ACT with a small
multiplexer (`DDR4DFIMux`); the LPDDR4 and LPDDR5 PHYs translate each command into their own
sequence.

## Bursts and prefetch {#primer-bursts}

A DRAM array is much slower than its pins. To keep the pins busy, each read fetches several
consecutive words at once from the row buffer and sends them one after the other: this is the
*prefetch*. A DDR3 chip fetches 8 words per access (8n prefetch) and sends them on 8 consecutive
clock edges, a *burst* of 8 (BL8).

Up to DDR3, each generation raised the pin rate by raising the prefetch, so the arrays could stay
at a similar speed; DDR4 kept the 8n prefetch and added bank groups instead. The burst length fixes the smallest amount of data one RD or WR moves: on a 16-bit DDR3
memory, 8 x 16 bits, that is 16 bytes. The table below gives the burst length LiteDRAM uses for
each type.

| Memory | SDR | DDR, LPDDR, DDR2 | DDR3, DDR4 | LPDDR4, LPDDR5, RPC DRAM |
|----------------|-----|------------------|------------|--------------------------|
| Burst length | 1 | 4 | 8 | 16 |

In LiteDRAM, the burst lengths are the `burst_lengths` table of `litedram/common.py`. The data
width of the controller is one full burst: a 16-bit DDR3 memory gives 128-bit controller data,
and a 64-bit DDR3 or DDR4 memory gives 512-bit data. Each access of the controller is one RD or
WR (see [Core architecture](#architecture)).

## Timings {#primer-timings}

A DRAM needs time between its commands: to open a row, to move the charge, to close it. The
datasheet gives these delays as *timings*, and the controller must never issue a command earlier
than they allow. The figure below shows a read to a closed row.

![One read to a closed row. ACT opens the row; RD can follow after tRCD; the burst appears on DQ
CL clocks after RD; PRE can close the row once tRAS has passed since ACT, and the next ACT to the
same bank waits tRP. The clock counts are an example.](primer_access.svg)

The first data arrive tRCD plus CL after ACT. When the row is already open, a read costs only CL,
and reads follow each other every tCCD. When another row of the same bank is open, the controller
must first close it. The figure below compares the two cases.

![A row hit and a row miss. Reads to the open row (top) follow each other and keep DQ busy. A read
to another row of the same bank (bottom) first waits tRP after PRE, then tRCD after ACT, before
its CL. The clock counts are an example.](primer_timings.svg)

The table below gives the main timings and the part of the LiteDRAM controller that enforces each
one. [Controller](#controller) describes these blocks.

| Timing | Between | Enforced by |
|-----------|-------------------------------------------------------|------------------|
| tRCD | ACT and RD or WR to the same bank | Bank machine |
| CL | RD and its first data (CAS latency) | PHY latency |
| CWL | WR and its first data (CAS write latency) | PHY latency |
| tRP | PRE and the next ACT to the same bank | Bank machine |
| tRAS | ACT and PRE to the same bank (minimum) | Bank machine |
| tRC | Two ACT to the same bank | Bank machine |
| tWR | End of the write data and PRE (write recovery) | Bank machine |
| tRTP | RD and PRE to the same bank | Bank machine |
| tRRD | Two ACT to different banks | Multiplexer |
| tFAW | Window holding at most four ACT | Multiplexer |
| tCCD | Two RD or two WR | Multiplexer |
| tWTR | End of the write data and the next RD | Multiplexer |
| tRFC | REF and the next command | Refresher |
| tREFI | Two REF (average interval) | Refresher |

A datasheet gives most timings in nanoseconds, some in clocks, and some as the larger of both,
such as "4 clocks or 7.5 ns". CL and CWL are counted in DRAM clocks and grow with the frequency:
LiteDRAM's default for DDR3-1600 is CL 11 and CWL 8.

In LiteDRAM, the module class lists the timings of each speed grade, and its constructor converts
them into controller clock cycles at the chosen frequency and ratio (`TimingSettings`), taking the
larger of the clock and nanosecond values. The default CL and CWL of each rate come from
`get_default_cl_cwl` of `litedram/common.py`. See [Memory modules](#modules).

## Refresh {#primer-refresh}

Every row must be refreshed within the retention time of the cells, 64 ms for DDR3 and DDR4 at
normal temperature. The controller does not refresh rows one by one: it sends REF, and the DRAM
refreshes the next rows of every bank by itself, using an internal counter.

Spreading 8192 REF over 64 ms gives one REF every 7.8 µs on average: this interval is tREFI.
Before REF, every bank must be closed, so the controller sends PREA first. The DRAM is then busy
for tRFC, from about one hundred to a few hundred nanoseconds depending on its density. The figure
below shows the sequence.

![Refresh. Every tREFI the controller closes all banks (PREA), sends REF and waits tRFC before
any other command. With postponing (bottom), the controller lets traffic run and then sends
several refreshes back to back.](primer_refresh.svg)

The standards allow a controller to postpone a few refreshes and catch up later, up to 8 for DDR3
and DDR4, as long as the average rate holds. Grouping refreshes leaves longer stretches of
uninterrupted traffic.

Refresh costs bandwidth: during tRFC, and while the banks reopen their rows afterwards, no data
moves. DDR4 can trade a shorter tRFC for more frequent refreshes with its *fine granularity
refresh* modes (1x, 2x and 4x).

The output drivers and terminations of the DRAM also drift with temperature and voltage. A ZQCS
command, sent from time to time, recalibrates them against an external precision resistor
([ZQ calibration](#iface-zq)).

In LiteDRAM, the refresher sends PREA, waits tRP, sends REF and waits tRFC every tREFI
(`Refresher` in `litedram/core/refresher.py`). It can postpone up to 8 refreshes
(`refresh_postponing`, default 1) and sends a ZQCS at `refresh_zqcs_freq`, once per second by
default, when the module gives a tZQCS. DDR4 module classes give tREFI and tRFC for each fine
granularity mode.

## Mode registers and power-up {#primer-init}

A DRAM is configured through its *mode registers*, written with MRS. They hold the burst length,
CL and CWL, the write recovery, the DLL enable, the output drive strength and the on-die
termination values. DDR3 has four mode registers, MR0 to MR3, and DDR4 seven, MR0 to MR6.

The standards define a power-up sequence that the controller must follow before any access. For
DDR3, LiteDRAM sends the following, in order:

1. Release RESET# and wait.
2. Bring CKE high and wait.
3. Write MR2 (CWL, dynamic termination), MR3, MR1 (drive strength, termination, DLL), then MR0
   (burst length, CL, write recovery, DLL reset).
4. Send ZQCL, the long ZQ calibration.

Memory modules on DIMMs also carry a small EEPROM, the *SPD* (Serial Presence Detect). It
describes the geometry and the timings of the module, so a controller can configure itself for the
DIMM it finds.

In LiteDRAM, `litedram/init.py` builds the initialization sequence of each memory type and writes
it into the C header the BIOS is built with. At boot, the BIOS replays it through the DFI injector,
before any calibration ([Initialization and calibration](#calibration)). Module classes can be
built from SPD data (`from_spd_data`), and the BIOS can read the SPD EEPROM of a DIMM.

## DRAM generations {#primer-generations}

Each generation lowered the supply voltage, raised the pin rate, and added mechanisms to keep the
faster signals readable. The table below summarizes the types LiteDRAM drives. The data rates are
the speed bins of the JEDEC standards cited at the top of this chapter; RPC DRAM is an Etron
product, outside JEDEC.

| Type | Supply | Prefetch | Data rates (MT/s) | Banks | New in this generation |
|----------|-------------|------------|-------------------|--------|------------------------------------|
| SDR | 3.3 V | 1n | up to about 200 | 2 or 4 | Synchronous interface, one transfer per clock |
| DDR | 2.5 V | 2n | 200 to 400 | 4 | Two transfers per clock, DQS strobe |
| DDR2 | 1.8 V | 4n | 400 to 1066 | 4 or 8 | On-die termination |
| DDR3 | 1.5 V, 1.35 V for DDR3L | 8n | 800 to 2133 | 8 | Fly-by topology, write leveling, ZQ calibration, dynamic termination, RESET# |
| DDR4 | 1.2 V | 8n | 1600 to 3200 | 8 or 16 | Bank groups, ACT_n, internal data VREF, data bus inversion |
| LPDDR4 | 1.1 V | 16n | up to 4266 | 8 | 16-bit channels, 6-bit command bus, multi-cycle commands |
| LPDDR5 | 1.05 V core, 0.5 V I/O | 16n | up to 6400 | 8 or 16 | Separate data clock (WCK), double data rate command bus |
| RPC DRAM | 1.5 V | Not given | DDR3 class | 4 | 16-bit memory on 22 or 24 pins, BL16, commands on the data pins |

LPDDR memories are low-power DRAMs for mobile devices, soldered next to the processor. RPC DRAM
(Reduced Pin Count) is an Etron DRAM that aims at the bandwidth of a 16-bit DDR3 with far fewer
pins. The DDR4 core supply is 1.2 V; the chip also needs a 2.5 V supply (VPP) for its word lines.

In LiteDRAM, the memory type of a design is the `memtype` of its module and PHY. SDR, DDR2, DDR3
and DDR4 share the same controller and calibration flow; LPDDR4, LPDDR5 and RPC DRAM add their own
PHYs, described in [LPDDR4, LPDDR5 and RPC DRAM PHYs](#lpddr-phys).

## Address mapping and bandwidth {#primer-mapping}

The peak bandwidth of a memory is its width times its data rate: a 16-bit DDR3 at 800 MT/s moves
1600 MB/s, about 1526 MiB/s, on its pins. A controller reaches it only when the data pins never wait. Three things
make them wait: row misses, refreshes and turnarounds between reads and writes.

Row misses depend on the *address mapping*: how the controller splits a user address into row,
bank and column. When consecutive addresses fall into the same row, sequential traffic is mostly
row hits. When the next rows fall into other banks, the controller can open them while the open
one transfers.

A *turnaround* is the dead time when the data bus changes direction. After a write, a read must
wait tWTR; before a write, a read must let its burst finish on the bus. A controller groups reads
together and writes together to pay fewer turnarounds.

In LiteDRAM, the address mapping is row, bank, column (`ROW_BANK_COL`): the column bits are the
lowest, then the bank, then the row. Sequential accesses walk through a row, then through the same
row of the next bank.

The multiplexer serves reads and writes in windows (`read_time`, `write_time`) to limit the
turnarounds. On a saturated mix of reads and writes at DDR3-1600 and 1:4, the controller source
records 74% to 92% of cycles with a read or a write, depending on these windows; the defaults give
85% ([Controller](#controller)).
