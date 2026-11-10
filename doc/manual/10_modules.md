# Memory modules {#modules}

The module is a Python class that describes one DRAM chip or DIMM: its organization and its
datasheet timings, which the controller uses. This chapter explains what a module class defines,
how its timings become controller cycles and how to add one. It is for the designers who port
LiteDRAM to a board.

The DRAM concepts behind the fields (banks, rows, refresh, the timing names) are explained in
[DRAM in a nutshell](#dram-primer).

## At a glance {#mod-glance}

| Attribute | Content |
|----------------------------|--------------------------------------------------------------------|
| Base class | Memory type: `SDRModule`, `DDR2Module`, `DDR3Module`, `DDR4Module` and others |
| `nbanks` | Banks per chip |
| `nrows`, `ncols` | Rows per bank, columns per row |
| `ngroups`, `ngroupbanks` | DDR4: bank groups, banks per group |
| `technology_timings` | Timings common to every speed grade: tREFI, tWTR, tCCD, tRRD, tZQCS, tRTP |
| `speedgrade_timings` | Timings per speed grade: tRP, tRCD, tWR, tRFC, tFAW, tRAS |

A design creates the module with the controller clock and the ratio, and passes it to the SoC
with the PHY ([Integration](#integration)). The example below is the module of an Arty A7 target,
whose PHY runs at 1:4.

```python
module = MT41K128M16(sys_clk_freq, "1:4")
```

The instance computes two settings objects. The geometry settings give the address widths of the
controller; the timing settings give each timing in controller cycles ([Core architecture](#architecture)).
Both are fixed at build time.

## Geometry {#mod-geometry}

The geometry is that of one chip, or of one rank of a DIMM: the banks, the rows and the columns.
The class turns each count into a number of address bits, so each must be a power of two. The
controller address width is the larger of the row and column widths.

The data width comes from the PHY, not from the module: it is the number of DQ pins. A board
with two x16 chips uses the module of one chip and a 32-bit PHY. The memory size is 2 to the
power of the bank, row and column bits, times the ranks and the data width in bytes.

For example, the MT41K128M16 has 8 banks, 16384 rows and 1024 columns: 3, 14 and 10 address
bits. On a 16-bit bus, that gives 2^27 x 2 bytes, 256 MiB. On DDR4, the banks are split into bank
groups, and the bank group bits go to the `bg` pins of the PHY.

## Timings {#mod-timings}

Each timing is written in the unit of the datasheet, in one of three forms. A plain number is in
nanoseconds. A pair is a number of DRAM clocks and a number of nanoseconds, and the larger of the
two applies; either can be `None`. A dictionary gives one value per DDR4 fine refresh mode.

| Form | Example | Meaning |
|------------------|------------------------------------------------|----------------------------------------|
| Number | `tRP=13.75` | 13.75 ns |
| Pair | `tWTR=(4, 7.5)` | 4 DRAM clocks or 7.5 ns, the larger |
| Pair | `tRFC=(None, 260)` | 260 ns |
| Dictionary | `tRFC=trfc` | `trfc` keyed by mode: `1x`, `2x`, `4x` |

**Technology timings** do not change with the speed grade: tREFI, tWTR, tCCD, tRRD, tZQCS and
tRTP. Without a tRTP, the class applies the JEDEC default of the type: the larger of 7.5 ns and
2 clocks on DDR2, 4 clocks on DDR3 and DDR4, or 8 clocks on LPDDR4.

**Speed grade timings** change with the speed bin of the chip: tRP, tRCD, tWR, tRFC, tFAW and
tRAS. A speed grade can also override tCCD and tRRD, and give the CL and CWL of the bin. tRC is
not written: the class computes it as tRP plus tRAS.

### Conversion to controller cycles {#mod-conversion}

The controller counts in controller cycles, so each timing is converted with the clock and the
ratio given to the module. The figure below shows the conversion of one timing.

![Conversion of a module timing: the nanoseconds become cycles with a phase margin, the DRAM clocks
become cycles divided by the ratio, and the larger value goes into the timing settings of the
controller.](mod_timing_conversion.svg)

**Nanoseconds.** The time is divided by the controller period and rounded up, after adding a
margin. The margin covers a command issued on the last phase of a cycle: it is the controller
period times (1 - 1/N), N being the ratio. At 1:4 the margin is three quarters of a controller
period.

**DRAM clocks.** The clock count is divided by the ratio and rounded up. The larger of the two
results becomes the timing in the settings.

Two timings skip the margin. tREFI is a maximum, not a minimum, so it is converted without it.
tCCD is exact, because two commands of the same type go out on the same phase. The class also
computes tWR and tCCD in DRAM clocks, without the margin, for the mode registers.

For example, the MT41K128M16 at a 100 MHz controller and 1:4 has a margin of 7.5 ns. Its tRP of
13.75 ns becomes ceil((13.75 + 7.5) / 10), 3 cycles, and its tREFI of 7.8125 µs becomes
782 cycles. These values are computed by the class; `test/test_modules.py` checks the conversions
of several modules.

### Speed grades and CAS latencies {#mod-speedgrades}

The speed grade selects a column of the datasheet, and the default speed grade is the one the
module marks as `default`. It names the bin of the chip, not the rate it runs at: a DDR3-1600
chip run at 800 MT/s keeps its 1600 timings, converted with the actual clock.

```python
module = MT40A1G8(sys_clk_freq, "1:4", speedgrade="2666")
```

The PHY sets the CAS latencies. By default, it picks CL and CWL from the JEDEC bin of its DRAM
clock, for example CL 6 and CWL 5 up to DDR3-800. A speed grade can give its own; the generator
passes them to the PHY, and a SoC passes `cl` and `cwl` to the PHY constructor.

### Fine refresh mode {#mod-fine-refresh}

DDR4 can refresh in finer steps: in 2x and 4x modes, refreshes come two or four times more often
and each takes less time. A DDR4 module gives tREFI and tRFC per mode, and the mode is chosen at
instantiation, 1x by default.

```python
module = MT40A512M8(sys_clk_freq, "1:4", fine_refresh_mode="2x")
```

The init sequence writes the mode into the MR3 register of the DRAM. Other memory types refuse
the parameter.

## Registered modules {#mod-registered}

The registered DIMM classes derive from a registered base class, which sets the `registered`
flag. The flag documents the module; it does not configure anything. The PHY must be built with
`is_rdimm` so that the init sequence programs the register clock driver of the DIMM
([UltraScale and UltraScale+](#phys-us)).

## The database {#mod-database}

`litedram/modules.py` holds the module classes. The table below counts them by memory type.

| Type | Classes | Examples |
|-----------------|---------|-------------------------------------------------------------|
| SDR | 22 | `MT48LC16M16`, `IS42S16160`, `W9825G6KH6`, `AS4C32M16` |
| DDR | 1 | `MT46V32M16` |
| LPDDR | 4 | `MT46H32M16`, `MT46H128M16` |
| DDR2 | 5 | `MT47H64M16`, `MT47H128M8`, `P3R1GE4JGF` |
| DDR3 chips | 21 | `MT41K128M16`, `MT41K256M16`, `IS43TR16256A`, `K4B2G1646F` |
| DDR3 DIMMs | 4 | `MT8JTF12864`, `MT8KTF51264`, `MT16KTF1G64HZ`, `MT18KSF1G72HZ` |
| DDR4 | 9 | `MT40A512M8`, `MT40A1G8`, `EDY4016A`, `MTA4ATF51264HZ` |
| DDR4 registered | 6 | `MTA18ASF2G72PZ`, `M393A4K40DB3`, `HMA84GR7DJR4N` |
| LPDDR4 | 1 | `MT53E256M16D1` |
| RPC | 1 | `EM6GA16L` |

Some classes derive from another with no change, such as a DDR3L chip from its DDR3 version.
`MT18KSF1G72HZ` is a 72-bit DIMM, for the DFI ECC of [Controller](#controller). The LPDDR5 simulation uses an example module defined in its
simulation SoC; the database has no LPDDR5 class.

## Adding a module {#mod-adding}

A new chip needs a class with its geometry and timings, taken from its datasheet. The class below
is the MT41J128M16 of the database, whose DDR3L twin `MT41K128M16` derives from it.

```python
class MT41J128M16(DDR3Module):
    # geometry
    nbanks = 8
    nrows  = 16384
    ncols  = 1024
    # timings
    technology_timings = _TechnologyTimings(
        tREFI=64e6/8192, tWTR=(4, 7.5), tCCD=(4, None), tRRD=(6, 10),
        tZQCS=(64, 80))
    speedgrade_timings = {
        "800": _SpeedgradeTimings(
            tRP=13.1, tRCD=13.1, tWR=13.1, tRFC=(64, None),
            tFAW=(None, 50), tRAS=37.5),
        "1600": _SpeedgradeTimings(
            tRP=13.75, tRCD=13.75, tWR=13.75, tRFC=(128, None),
            tFAW=(None, 40), tRAS=35),
    }
    speedgrade_timings["default"] = speedgrade_timings["1600"]
```

The class above is shortened to two of its four speed grades and reformatted. The steps below build a new class
the same way.

1. Derive from the base class of the memory type, or from the registered one for an RDIMM.
2. Read the addressing table of the datasheet: the bank count, the row count (2 to the power of
   the row address bits) and the column count. On DDR4, set the bank groups and banks per group.
3. Write the technology timings. tREFI is the refresh period over the number of refreshes, for
   example 64 ms over 8192, written in ns as `64e6/8192`.
4. Write one entry per speed grade, with each minimum in the form of the datasheet: a pair when it
   reads "max(n nCK, t ns)".
5. Mark one speed grade as `default`: it applies when the design names none.

Check the new class with the module tests, which instantiate every class of the database with
every speed grade.

```sh
python3 -m pytest -v test/test_modules.py
```

## SPD {#mod-spd}

DDR3 and DDR4 DIMMs carry their parameters in an SPD EEPROM, read over I2C. LiteDRAM can build a
module from an SPD dump instead of a class (`SDRAMModule.from_spd_data`). It decodes the geometry
and the minimum timings, and finds the speed grade from the minimum clock period.

On a SoC with I2C, the BIOS reads the EEPROM of a DIMM with its `sdram_spd` command, given the
3-bit address of the EEPROM. `parse_spd_hexdump` reads that dump back into a list of bytes. `litex_sim` takes the same
dump to simulate a DIMM (`--sdram-from-spd-dump`).

```python
from litedram.modules import SDRAMModule, parse_spd_hexdump

spd_data = parse_spd_hexdump("spd_dump.txt")
module   = SDRAMModule.from_spd_data(spd_data, sys_clk_freq)
```

A module built from SPD data keeps that data. LiteX `add_sdram` then adds it to the SoC as a
read-only memory named `sdram_spd`, so that software can compare the EEPROM of the board with the
data the bitstream was built for. The BIOS command has that comparison, but does not compile it
in ([Limitations](#mod-limitations)).

`test/spd_data/` holds ten SPD dumps of Micron DDR3 and DDR4 modules, used by the tests.

## Limitations {#mod-limitations}

- **SPD ratio.** A module built from SPD data assumes 1:4 for DDR3 and DDR4, whatever the ratio
  of the PHY. On a 1:2 PHY (ECP5, Nexus, Gowin), its DRAM clock counts are divided by 4 instead
  of 2: tCCD, 4 DRAM clocks, becomes one controller cycle instead of two. Use a module class on
  these PHYs.
- **SPD check.** The `sdram_spd` command of the BIOS compares the EEPROM with a `SPD_BASE` region
  that no generated header defines, since the read-only memory is `SDRAM_SPD_BASE`; the
  comparison is never compiled.
- **SPD types.** Only DDR3 and DDR4 SPD data is decoded.
- **Registered flag.** The `registered` flag of a class is not used by the code; the PHY setting
  decides.
- **LPDDR4.** tZQCS is not set, since the ZQ calibration runs only at initialization, and tCCD is
  always that of the masked write ([LPDDR4, LPDDR5 and RPC DRAM PHYs](#lpddr-phys)).
- **RPC.** The timings of `EM6GA16L` carry a note that they may need further verification.

## In the code {#mod-code}

| Name | Content |
|----------------------------|------------------------------------------------------------------|
| `SDRAMModule` | Base class: geometry and timing settings, conversion, SPD loader |
| `_TechnologyTimings` | Timings common to every speed grade |
| `_SpeedgradeTimings` | Timings of one speed grade, optional CL and CWL |
| `DDR3SPDData` | SPD decoder of DDR3; `DDR4SPDData` derives from it |
| `parse_spd_hexdump` | Reader of an SPD dump printed by the BIOS |

All of them are in `litedram/modules.py`; the timing settings class is in `litedram/common.py`,
and the tests in `test/test_modules.py`.

Where to go next: [Controller](#controller) for how the timings are enforced,
[DDR PHYs](#phys) for the PHY that runs the module, [Integration](#integration) to put both in a
SoC.
