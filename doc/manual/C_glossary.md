# Glossary {#glossary}

The terms of DRAM and of LiteDRAM used in this manual, in alphabetical order. Each entry points to
the section that explains it.

| Term | Meaning |
|------------------|----------------------------------------------------------------------------------|
| ACT | Activate: opens a row of a bank into its row buffer. See [Commands](#primer-commands) |
| AL | Additive latency: extra delay a DDR3 or DDR4 chip adds to CL and CWL; LiteDRAM leaves it at 0. See [Timings](#primer-timings) |
| Auto-precharge | RD or WR that closes the row by itself after the burst. See [Commands](#primer-commands) |
| Bank | Independent array of a DRAM chip, with its own open row. See [Banks, rows and columns](#primer-organization) |
| Bank group | Group of banks of a DDR4 chip; accesses to different groups follow each other faster. See [Banks, rows and columns](#primer-organization) |
| Bank machine | Block of the controller that manages the open row of one bank. See [Controller](#controller) |
| BIOS | The LiteX BIOS and its DRAM library, `liblitedram`, which initializes and calibrates the DRAM. See [Initialization and calibration](#calibration) |
| BIST | Built-in self test: hardware generator and checker of DRAM traffic. See [Ports and frontends](#frontends) |
| Bitslip | Shift of the deserialized data by whole bits, the coarse setting of leveling. See [Read leveling](#iface-read-leveling) |
| BL | Burst length: number of transfers of one RD or WR. See [Bursts and prefetch](#primer-bursts) |
| Burst detect | Flag of the Lattice and Gowin DQS blocks: a read burst was seen. See [Read leveling](#iface-read-leveling) |
| Calibration | Whole tuning of the interface at boot, leveling included. See [Initialization and calibration](#calibration) |
| CK | Differential clock sent to the DRAM. See [The signals](#iface-signals) |
| CKE | Clock enable pin of the DRAM. See [The signals](#iface-signals) |
| CL | CAS latency: DRAM clocks between RD and its first data. See [Timings](#primer-timings) |
| Column | Position within a row; RD and WR select columns. See [Banks, rows and columns](#primer-organization) |
| CWL | CAS write latency: DRAM clocks between WR and its first data. See [Timings](#primer-timings) |
| DBI | Data bus inversion: DDR4 option that inverts a byte to reduce the zeros on the bus. See [DRAM generations](#primer-generations) |
| DFI | Interface between the controller and the PHY, after the DDR PHY Interface specification. See [DFI, the interface between the controller and the PHY](#iface-dfi) |
| DFI injector | Block between the controller and the PHY that gives software access to the DRAM. See [Core architecture](#architecture) |
| DIMM | Module carrying one or more ranks of DRAM chips. See [Banks, rows and columns](#primer-organization) |
| DM | Data mask: masks bytes during a write. See [The signals](#iface-signals) |
| DQ | Data pins. See [The signals](#iface-signals) |
| DQS | Data strobe, sent with the data by the side that sends them. See [Double data rate and the strobe](#iface-dqs) |
| ECC | Error-correcting code; LiteDRAM uses SECDED. See [Controller](#controller) |
| Fly-by | Routing of clock, command and address past the chips in turn. See [Fly-by topology and write leveling](#iface-flyby) |
| Frequency ratio | Controller clock to DRAM clock, written 1:2 or 1:4. See [Clocks and the frequency ratio](#iface-clocking) |
| Leveling | Write leveling and read leveling procedures. See [Fly-by topology and write leveling](#iface-flyby) |
| MPC | Multi-purpose command of LPDDR4 and LPDDR5, used for ZQ calibration. See [ZQ calibration](#iface-zq) |
| MPR | Multi-purpose register of DDR3 and DDR4: a fixed read pattern for read leveling. See [Read leveling](#iface-read-leveling) |
| MRS | Mode register set: writes a mode register. See [Mode registers and power-up](#primer-init) |
| ODT | On-die termination of the DRAM data pins, and the pin that turns it on. See [Termination and drive strength](#iface-odt) |
| Phase | One command slot of a DFI cycle, one per DRAM clock. See [DFI, the interface between the controller and the PHY](#iface-dfi) |
| PHY | Physical layer of one memory type on one FPGA family. See [DDR PHYs](#phys) |
| Port | User port of the crossbar. See [Ports and frontends](#frontends) |
| PRE, PREA | Precharge: closes the open row of one bank, or of all banks. See [Commands](#primer-commands) |
| Prefetch | Number of words a DRAM fetches from its array per access. See [Bursts and prefetch](#primer-bursts) |
| Rank | Group of chips sharing the command bus and selected together. See [Banks, rows and columns](#primer-organization) |
| RD, WR | Read and write commands. See [Commands](#primer-commands) |
| RDIMM | Registered DIMM: a register chip buffers command and address. See [Memory modules](#modules) |
| REF | Refresh command. See [Refresh](#primer-refresh) |
| RON | Output driver impedance of the DRAM. See [Termination and drive strength](#iface-odt) |
| Row | Line of cells opened as a whole by ACT. See [Banks, rows and columns](#primer-organization) |
| Row buffer | Sense amplifiers holding the open row of a bank. See [Banks, rows and columns](#primer-organization) |
| RTT_NOM, RTT_WR | Nominal and write values of the on-die termination. See [Termination and drive strength](#iface-odt) |
| SECDED | Single error correction, double error detection. See [Controller](#controller) |
| SPD | Serial presence detect: EEPROM of a DIMM describing it. See [Mode registers and power-up](#primer-init) |
| tCCD | Minimum time between two RD or two WR. See [Timings](#primer-timings) |
| tFAW | Window in which at most four ACT may be issued. See [Timings](#primer-timings) |
| tRAS | Minimum time between ACT and PRE of a bank. See [Timings](#primer-timings) |
| tRC | Minimum time between two ACT of a bank. See [Timings](#primer-timings) |
| tRCD | Minimum time between ACT and RD or WR. See [Timings](#primer-timings) |
| tREFI | Average interval between two REF. See [Refresh](#primer-refresh) |
| tRFC | Time the DRAM is busy after REF. See [Refresh](#primer-refresh) |
| tRP | Minimum time between PRE and the next ACT of a bank. See [Timings](#primer-timings) |
| tRRD | Minimum time between two ACT to different banks. See [Timings](#primer-timings) |
| tRTP | Minimum time between RD and PRE of a bank. See [Timings](#primer-timings) |
| tWR | Write recovery: end of the write data to PRE. See [Timings](#primer-timings) |
| tWTR | End of the write data to the next RD. See [Timings](#primer-timings) |
| VREF | Reference voltage of the receivers. See [Reference voltages](#iface-vref) |
| WCK | Data clock of LPDDR5, two or four times CK. See [DRAM generations](#primer-generations) |
| Write leveling | Alignment of DQS with CK at each chip. See [Fly-by topology and write leveling](#iface-flyby) |
| ZQCL, ZQCS | Long and short ZQ calibration commands. See [ZQ calibration](#iface-zq) |
