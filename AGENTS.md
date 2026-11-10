# AGENTS.md: LiteDRAM

DRAM controller core for LiteX: SDR/DDR/DDR2/DDR3/DDR4/LPDDR4/LPDDR5/RPC PHYs, controller
(crossbar, refresh, ECC options), native/AXI/Wishbone/DMA frontends, standalone generator.

Read the LiteX agent page first: https://github.com/enjoy-digital/litex/wiki/LiteX-for-AI-Agents (framework map, conventions, how to
verify a change, contribute back). Index of the whole wiki for agents: https://github.com/enjoy-digital/litex/wiki/llms.txt.

## Where things are

- `litedram/phy/`: PHYs (`s7ddrphy.py`, `usddrphy.py`, `ecp5ddrphy.py`, `gw2ddrphy.py`, `gw5ddrphy.py`, `lpddr4/`, `lpddr5/`, `rpc/`...).
- `litedram/core/` (controller, crossbar, refresher), `litedram/frontend/` (AXI, Wishbone, DMA, BIST, FIFO, ECC).
- `litedram/modules.py`: DRAM chip/module timings; `litedram/init.py`: init sequences.
- `litedram/gen.py` (`litedram_gen examples/<board>.yml`): standalone Verilog core; `bench/`: hardware benches.
- Software side (calibration/leveling, memtest): LiteX `litex/soc/software/liblitedram/`.
- `doc/manual/`: the manual (Markdown chapters, pandoc PDF/HTML, `python3 doc/manual/build.py --check`);
  `doc/diagrams/`: its figures. Update the chapter with the code it describes (`doc/manual/STYLE.md`).

## Verify a change

```sh
python3 -m pytest test                                            # what CI runs
litedram_gen examples/arty.yml                                    # generator smoke test
python3 -m litex_boards.targets.digilent_arty --build --no-compile # elaborate a SoC with the PHY
```

- Calibration/leveling passing does not prove the controller latencies: the DFI injector is
  latency-insensitive; run a memtest through the controller.
- Resource claims on Xilinx: quote Vivado (out-of-context) numbers, not only Yosys.
- PHY changes need a build and a board for the targeted family; say which ones ran.

## Rules

- Style: https://github.com/enjoy-digital/litex/blob/master/doc/coding_style.md (match the
  surrounding file; `module: Description of the change.` commit titles; one change per commit).
- Never edit generated files (`build/`, `csr.h`, `csr.csv`, the Verilog): change the Python.
- One topic per pull request, from `master`, with what was tested and on which hardware; say
  that an agent wrote it and who supervised. Do not rename options or reformat unrelated code.
- Hardware: never flash a board or write its SPI flash unless the user asked; `--load` (volatile)
  is the default for experiments.

## Debug on hardware

Method: https://github.com/enjoy-digital/litex/wiki/Debug-A-SoC-On-Hardware (check the link and `--ident` first, registers before
traces, narrow LiteScope captures). `litex_mcp` gives the same loop as MCP tools (CSRs by name,
LiteScope captures, builds with parsed timing, simulation): https://github.com/enjoy-digital/litex/wiki/LiteX-for-AI-Agents#drive-a-soc-through-mcp.
