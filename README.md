```
                                 __   _ __      ___  ___  ___   __  ___
                                / /  (_) /____ / _ \/ _ \/ _ | /  |/  /
                               / /__/ / __/ -_) // / , _/ __ |/ /|_/ /
                              /____/_/\__/\__/____/_/|_/_/ |_/_/  /_/

                                   Copyright 2015-2026 / EnjoyDigital
                               A small footprint and configurable DRAM core
                                        powered by Migen & LiteX
```

[![](https://github.com/enjoy-digital/litedram/workflows/ci/badge.svg)](https://github.com/enjoy-digital/litedram/actions) ![License](https://img.shields.io/badge/License-BSD%202--Clause-orange.svg) [![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/enjoy-digital/litedram)


[> Intro
--------
LiteDRAM provides a small footprint and configurable DRAM core.

LiteDRAM is part of LiteX libraries whose aims are to lower entry level of
complex FPGA cores by providing simple, elegant and efficient implementations
of components used in today's SoC such as Ethernet, SATA, PCIe, SDRAM Controller...

Using Migen to describe the HDL allows the core to be highly and easily configurable.

LiteDRAM can be used as LiteX library or can be integrated with your standard
design flow by generating the verilog rtl that you will use as a standard core.

[> Features
-----------
PHY:
  - Generic SDR PHY (vendor agnostic, tested on Xilinx, Altera, Lattice; 1:1 or 1:2 frequency ratio)
  - Xilinx Spartan6 DDR/LPDDR/DDR2/DDR3 PHY (1:2 or 1:4 frequency ratio)
  - Xilinx Spartan7/Artix7/Kintex7/Virtex7 DDR2/DDR3 PHY (1:2 or 1:4 frequency ratio)
  - Xilinx Artix7/Kintex7/Virtex7 LPDDR4 PHY and LPDDR5 PHY (each with a Verilator simulation PHY and DRAM model)
  - Xilinx Artix7 RPC DRAM (Etron Reduced Pin Count) PHY (with a Verilator simulation PHY)
  - Xilinx Kintex/Virtex Ultrascale (Plus) DDR3/DDR4 PHY (1:4 frequency ratio, optional read VREF scan on Ultrascale+ DDR4)
  - Altera Cyclone V native DDR3 PHY (1:4 frequency ratio). See [Cyclone V DDR3 support](doc/cyclone-v.md).
  - Lattice ECP5 DDR3 PHY (1:2 frequency ratio, or 1:4 with `ecp5ddrphy_with_ratio`)
  - Lattice Nexus DDR3 PHY (1:2 frequency ratio)
  - Gowin GW2A DDR3 PHY (1:2 frequency ratio)
  - Gowin GW5A DDR3 PHY (1:2 or 1:4 frequency ratio)
  - DFI-level SDRAM simulation PHY/model (SDR/DDR/LPDDR/DDR2/DDR3/DDR4) for Verilator (litex_sim, litedram_gen --sim)

Core:
  - Fully pipelined, high performance.
  - Configurable commands depth on bankmachines.
  - Auto-Precharge.
  - Periodic refresh/ZQ short calibration (up to 8 postponed refreshes).

Frontend:
  - Configurable crossbar (simply use crossbar.get_port() to add a new port!)
  - Ports arbitration transparent to the user.
  - Native, AXI-MM or Wishbone user interface.
  - DMA reader/writer.
  - BIST.
  - ECC (Error-correcting code)

[> FPGA Proven
---------------
LiteDRAM is already used in commercial and open-source designs:
- HDMI2USB: http://hdmi2usb.tv/home/
- NeTV2: https://www.crowdsupply.com/alphamax/netv2
- USBSniffer: http://blog.lambdaconcept.com/doku.php?id=products:usb_sniffer
- and others commercial designs...

[> Possible improvements
------------------------
- add Avalon-ST interface.
- add support for more Altera devices.
- ... See below Support and consulting :)

If you want to support these features, please contact us at florent [AT]
enjoy-digital.fr.

[> Documentation
----------------
The **DRAM Controller & PHYs manual** is the reference of the project, from the primers to the integration,
the examples, the debugging and the registers:

- Read it: [PDF](https://github.com/enjoy-digital/litedram/releases/download/manual-nightly/litedram_manual.pdf) or
  [HTML](https://github.com/enjoy-digital/litedram/releases/download/manual-nightly/litedram_manual.html) (rebuilt nightly).
- Sources and local build: [doc/manual](doc/manual/README.md).

[> Getting started
------------------
1. Install Python 3.6+ and FPGA vendor's development tools.
2. Install LiteX and the cores by following the LiteX's wiki [installation guide](https://github.com/enjoy-digital/litex/wiki/Installation).
3. You can find examples of integration of the core with LiteX in LiteX-Boards and in the examples directory.

[> Standalone core generation
-----------------------------
A standalone Verilog core (controller + PHY + init firmware, with native/Wishbone/Avalon/AXI/FIFO
user ports) can be generated from a YAML description:
```sh
$ litedram_gen examples/arty.yml
```
See [doc/gen.md](doc/gen.md) for the command line, the YAML keys, the native/Wishbone port protocols and the examples, and
the [Integration](doc/manual/13_integration.md) chapter of the manual.

[> Tests
--------
Unit tests are available in ./test/.
To run all the unit tests:
```sh
$ python3 -m pytest test
```

test_examples.py builds the LiteX BIOS (RISC-V GCC toolchain) and test_lpddr4.py/test_lpddr5.py
are long simulations: the CI runs them only in its full job (with `LITEDRAM_TEST_FULL=1` to enable
the slow configurations); skip them with:
```sh
$ python3 -m pytest test --ignore=test/test_examples.py --ignore=test/test_lpddr4.py --ignore=test/test_lpddr5.py
```

Tests can also be run individually:
```sh
$ python3 -m pytest test/test_name.py
```

[> License
----------
LiteDRAM is released under the very permissive two-clause BSD license. Under
the terms of this license, you are authorized to use LiteDRAM for closed-source
proprietary designs.
Even though we do not require you to do so, those things are awesome, so please
do them if possible:
 - tell us that you are using LiteDRAM
 - cite LiteDRAM in publications related to research it has helped
 - send us feedback and suggestions for improvements
 - send us bug reports when something goes wrong
 - send us the modifications and improvements you have done to LiteDRAM.

[> Support and consulting
-------------------------
We love open-source hardware and like sharing our designs with others.

LiteDRAM is developed and maintained by EnjoyDigital.

If you would like to know more about LiteDRAM or if you are already a happy
user and would like to extend it for your needs, EnjoyDigital can provide standard
commercial support as well as consulting services.

So feel free to contact us, we'd love to work with you! (and eventually shorten
the list of the possible improvements :)

[> Contact
----------
E-mail: florent [AT] enjoy-digital.fr