```{=latex}
\frontmatter
```

# About this document {.unnumbered}

This manual is the reference of the LiteDRAM project: a DRAM controller for FPGAs, its PHYs for
the FPGA families it supports, its user ports and the software that calibrates the memory at boot.
It is written for FPGA engineers who need external memory in a design, and it teaches DRAM along
the way.

No prior knowledge of DRAM is assumed. Part I explains how a DRAM stores and moves data and what
the interface between the FPGA and the memory looks like, and points at the module that implements
each mechanism. Part II then describes the core: its architecture, the controller, the user ports
and the calibration.

Part III describes the PHYs and the memory modules. Part IV is the user guide: the supported boards,
the first build, the integration in a design, the examples, the simulation and the debugging. The
appendices hold the register reference, the build options, the glossary, the performance figures
and the maintenance notes of this manual.

| If you want to | Read |
|------------------------------------------|----------------------------------------------|
| Know what the project does and does not | [Introduction](#introduction) |
| Learn how a DRAM works | [DRAM in a nutshell](#dram-primer) |
| Understand DQS, leveling and DFI | [The DRAM interface and the PHY](#dram-interface) |
| Check that your FPGA or board is supported | [Supported FPGAs and boards](#boards) |
| Get a first memory test to pass | [Getting started](#getting-started) |
| Add DRAM to your own design | [Integration](#integration) |
| Understand a calibration that fails | [Debugging](#debugging) |

The manual follows the repository: every name, number and default is taken from the source code,
and the manual is generated from it on the date printed on the title page. When the code and the
manual disagree, the code is right and the manual has a bug.

## Conventions {.unnumbered}

- Numbers: `0x` prefix for hexadecimal, `0b` for binary.
- Rates: DRAM data rates in MT/s (millions of transfers per second on each data pin), clock
  frequencies in MHz. Bandwidths in MiB/s, as the memory test of the LiteX BIOS prints them. Sizes
  in bytes, KiB, MiB and GiB.
- Memory types are written SDR, DDR2, DDR3, DDR4, LPDDR4, LPDDR5 and RPC DRAM; DRAM commands in
  capitals (ACT, RD, WR, PRE, REF, MRS); timings in plain letters (tRCD, tRP, CL).
- The frequency ratio is written "1:4": one controller clock for four DRAM clocks. A DFI *phase*
  is one of the command slots carried in one controller clock.
- JEDEC standards are cited by their number, such as JESD79-3 for DDR3 and JESD79-4 for DDR4.
- *The core* is the DFI injector, the controller, the optional ECC and the crossbar; *the
  controller* is the bank machines, the multiplexer and the refresher; *the PHY* is the physical
  layer of one memory type on one FPGA family; *a port* is a user port of the crossbar; *a
  frontend* is a bridge or an engine on a port.
- *The module* is a class of `litedram/modules.py` that describes a memory chip or a DIMM; *the
  DRAM* is the physical memory on the board.
- *Calibration* is the whole tuning of the interface at boot; *leveling* is the write and read
  leveling procedures within it. *The BIOS* is the LiteX BIOS and its DRAM library,
  `liblitedram`.
- `<target>` stands for the name of a target script of `bench/` without its extension, such as
  `arty` or `kc705`.
- `<config>` stands for a YAML configuration file of the standalone generator `litedram_gen`, such
  as `examples/arty.yml`.
- Paths are relative to the repository root. Shell commands are given for a Linux host.
- When the text names a source file, it is the file to open to check or extend the fact.
