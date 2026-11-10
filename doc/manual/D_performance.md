# Performance and resources {#performance}

This appendix gathers the performance and resource figures of the project: the peak bandwidth of
the configurations, computed, the efficiency of the controller, the bandwidths measured on boards,
as recorded in the repositories, and the resource figures. Computed values are labelled as such;
every measured value names its source.

## Peak bandwidth {#perf-peak}

The peak bandwidth of a DRAM interface is its data rate times its width: one data word per transfer,
on every transfer. The data rate is the system clock times the number of DFI phases, times two for
the double data rate memories.

The table computes it, in MB/s (10^6 bytes per second), for the examples of `examples/` (plain
names) and for the bench targets, with the data rates of [At a glance](#ex-glance) and [Bench
targets](#ex-bench).

| Configuration | Memory | Data rate | Width | Computed peak |
|--------------------------------------------|--------------|--------------|------------|----------------|
| `ulx3s` | SDR | 50 MT/s | 16 bits | 100 MB/s |
| `versa_ecp5` | DDR3 | 200 MT/s | 16 bits | 400 MB/s |
| `tang_primer_20k` | DDR3 | 192 MT/s | 16 bits | 384 MB/s |
| `tang_mega_138k_pro` | DDR3 | 200 MT/s | 16 bits | 400 MB/s |
| `nexys4ddr` | DDR2 | 400 MT/s | 16 bits | 800 MB/s |
| `arty` | DDR3 | 800 MT/s | 16 bits | 1600 MB/s |
| `genesys2` | DDR3 | 800 MT/s | 32 bits | 3200 MB/s |
| `kcu105`, `xcu1525` examples | DDR4 | 1200 MT/s | 64 bits | 9600 MB/s |
| `arty` target | DDR3 | 1000 MT/s | 16 bits | 2000 MB/s |
| `genesys2` target | DDR3 | 1000 MT/s | 32 bits | 4000 MB/s |
| `kc705`, `kcu105`, `xcu1525` targets | DDR3, DDR4 | 1000 MT/s | 64 bits | 8000 MB/s |

The controller moves one burst per cycle at most: its data width is the DRAM width times the number
of DFI phases times two, 128 bits for a 16-bit DDR3 at 1:4. The peak is reached only when a column
command goes out on every cycle; the next section gives what the controller reaches.

## Efficiency of the controller {#perf-efficiency}

The controller loses cycles where no column command can go out: opening and closing rows, the
turnarounds between reads and writes, and the refreshes ([Controller](#controller)). The comments of
`ControllerSettings` record the effect of the read and write windows on a saturated mix of reads
and writes, for a DDR3-1600 at 1:4.

| `read_time` / `write_time` | Cycles with a column command (recorded) |
|----------------------------------------------------|--------------------------------------------------|
| 32 / 16 | 74% |
| 64 / 32 (default) | 85% |
| 128 / 64 | 92% |

Longer windows mean fewer turnarounds, at the cost of a longer worst-case wait for the other
direction. Traffic that stays in open rows and spreads over the banks comes closer to the peak;
random accesses in one bank are far from it.

## Measured bandwidths {#perf-measured}

No bandwidth figure is recorded in this repository by its own benches; the figures below come from
the commits that validated the PHYs, in LiteDRAM and LiteX-Boards.

**BIST on ECP5 at 1:4.** The commit that added the ECP5 PHY at 1:4 records host-driven BIST runs of
64 MB on a Cam Link 4K (ECP5 LFE5U-25F, DDR3 MT41K64M16, 16 bits), in MB/s as the commit writes
them.

| Data rate | sys_clk | Write | Read | Write and read |
|------------------|------------------------|---------------------|------------------|-----------------------|
| 594 MT/s | 74.25 MHz | 1027 MB/s | 1048 MB/s | 861 MB/s |
| 700 MT/s | 87.75 MHz | 1212 MB/s | 1233 MB/s | 1024 MB/s |

The computed peak of this 16-bit interface is 1188 MB/s at 594 MT/s and 1400 MB/s at 700 MT/s.
The same commit records that 796 MT/s found no read window with that read leveling.

**Memspeed.** The `memspeed` of the BIOS measures the CPU path: the CPU, its bus and the L2 cache
in front of the controller, in MiB/s as the BIOS prints them. It compares builds of one SoC; it is
not the bandwidth of the DRAM. The boot logs of the hardware captures used in this manual give:

| Board | Memory | Data rate | CPU | Write | Read |
|-----------------------------|---------------|-----------|-----------------------|-------------|-------------|
| KC705 | DDR3, 64 bits | 1000 MT/s | VexRiscv, 125 MHz | 40 MiB/s | 33 MiB/s |
| YPCB-00338-1P1 | DDR3, 32 bits | 1000 MT/s | VexRiscv, 125 MHz | 74.0 MiB/s | 78.0 MiB/s |
| Arty A7 | DDR3, 16 bits | 800 MT/s | Cortex-M1, 100 MHz | 16.5 MiB/s | 19.3 MiB/s |
| Arty A7 | DDR3, 16 bits | 800 MT/s | Microwatt, 100 MHz | 32 MiB/s | 54 MiB/s |
| Arty A7 | DDR3, 16 bits | 400 MT/s | Cortex-M3, 50 MHz | 9.7 MiB/s | 12.6 MiB/s |
| ECPIX-5 | DDR3, 16 bits | 300 MT/s | FireV, 75 MHz | 13.6 MiB/s | 23.4 MiB/s |
| ButterStick | DDR3, 16 bits | 300 MT/s | VexRiscv, 75 MHz | 13.6 MiB/s | 15.6 MiB/s |
| Tang Primer 20K | DDR3, 16 bits | 192 MT/s | VexRiscv SMP, 48 MHz | 11.7 MiB/s | 17.4 MiB/s |
| Analog Pocket | SDR, 16 bits | 50 MT/s | VexRiscv, 50 MHz | 15.6 MiB/s | 22.1 MiB/s |
| TEC0117 | SDR, 16 bits | 25 MT/s | VexRiscv Lite, 25 MHz | 5 MiB/s | 6 MiB/s |

The figures follow the CPU more than the memory: the 64-bit KC705 at 1000 MT/s is slower than the
32-bit YPCB-00338-1P1 at the same rate, and an Arty A7 at 800 MT/s doubles with another CPU.

The commit that brought the ECP5 targets of LiteX-Boards to 1:4 records the same effect for the
controller clock: on the ECPIX-5 at 600 MT/s, memspeed gives 24.3 MiB/s write and 35.1 MiB/s read at
1:4, against 17.5 MiB/s and 27.3 MiB/s at 1:2.

**Calibration time.** On the XCU1525, the fast scans of the BIOS for PHYs with more than 128 taps
bring the full DRAM calibration to about 25 seconds, against several minutes before, as recorded in
the history of LiteX.

## Resources {#perf-resources}

The repository records a few resource figures, all as comments next to the option they concern.

| Item | Figure (recorded) | Source |
|--------------------------|--------------------------|------------------------------------------------------------------|
| DDR3 controller and crossbar, 8 bank machines | about 1180 LUTs | `doc/gen.md` |
| Same with 2 shared bank machines | about 470 LUTs | `doc/gen.md` |
| WRAP burst support of an AXI port | about 180 LUTs | `litedram/gen.py` |
| Per-line ECC counters, 72 bits at 1:4 | about 4000 flip-flops | `litedram/core/__init__.py` |

Shared bank machines keep one open row per machine, so they cost efficiency when the accesses
alternate between the banks that share one. No resource table of the PHYs is recorded; a build of
the target gives them, and the `AGENTS.md` file asks for Vivado figures, not only Yosys ones, for
resource claims on Xilinx.

## Measuring {#perf-measuring}

Three tools measure the bandwidth of a design, from the most to the least representative of an
application:

- the bandwidth monitor of the controller (`with_bandwidth`): the read and write commands of the
  real traffic over 2^24 cycles; the bandwidth is `(nreads + nwrites) x data_width` bits per period;
- the BIST (`sdram_bist`): write and read speeds of one port in MiB/s, without the CPU;
- the benchmarks in simulation ([Benchmarks in simulation](#sim-benchmarks)): bandwidth and
  efficiency of access patterns, before any board.

Where to go next: [Controller](#controller) for the read and write windows, and
[Debugging](#debugging) for the BIST commands.
