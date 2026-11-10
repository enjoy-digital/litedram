# Vocabulary of the LiteDRAM manual

Project-specific writing rules, completing the generic `STYLE.md` of the manual kit.

## Names of the parts

- *the core* is `LiteDRAMCore`: DFI injector, controller, optional ECC and crossbar; *the
  controller* is the bank machines, the multiplexer and the refresher; *the PHY* is the physical
  layer of one memory type and FPGA family; *a port* is a user port of the crossbar; *a frontend* is
  a bridge or engine on a port (AXI, Wishbone, DMA, BIST, FIFO, ECC).
- *the module* is a class of `litedram/modules.py` that describes a memory chip or DIMM; *the DRAM*
  is the physical memory on the board.
- *calibration* is the whole tuning of the interface at boot; *leveling* is the JEDEC write and read
  leveling procedures within it.
- *the BIOS* is the LiteX BIOS and its `liblitedram`; *the generator* is `litedram_gen`; *target* is
  a script of `bench/`; *example* is a YAML file of `examples/`.

## Protocol names

- Memory types as SDR, DDR2, DDR3, DDR4, LPDDR4, LPDDR5, RPC DRAM, HBM2.
- Commands in capitals: ACT, PRE, PREA, RD, WR, REF, ZQCS, ZQCL, MRS.
- Timings as tRCD, tRP, tRAS, tRFC, tREFI, tWR, tWTR, tCCD, tFAW, CL, CWL, without italics.
- The frequency ratio written "1:2" or "1:4" (controller clock to DRAM clock); DFI *phase* for one
  of the commands carried in a controller cycle.
- Data rates in MT/s; clock frequencies in MHz. Cite JEDEC standards by number (JESD79-3F) and
  section, only when sure.

## Placeholders

- `<target>` is a target script name of `bench/` without `.py`; `<config>` is a generator YAML file.
  Both are defined once in the Conventions of the front matter.

## Hardware names

- FPGA families: Spartan-6, Artix-7, Kintex-7, Virtex-7, Kintex UltraScale, Kintex/Virtex
  UltraScale+, Lattice ECP5, Lattice CrossLink-NX/Certus-NX (Nexus), Gowin GW1N/GW2A/GW5A, Efinix
  Titanium/Trion.
- Boards as LiteX-Boards names them (Arty A7, KC705, Genesys2, ECPIX-5, Tang Primer 20K, XCU1525).
