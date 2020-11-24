```
                                 __   _ __      ___  ___  ___   __  ___
                                / /  (_) /____ / _ \/ _ \/ _ | /  |/  /
                               / /__/ / __/ -_) // / , _/ __ |/ /|_/ /
                              /____/_/\__/\__/____/_/|_/_/ |_/_/  /_/

                                   Copyright 2015-2020 / EnjoyDigital
                               A small footprint and configurable DRAM core
                                        powered by Migen & LiteX
```

[![](https://github.com/enjoy-digital/litedram/workflows/ci/badge.svg)](https://github.com/enjoy-digital/litedram/actions) ![License](https://img.shields.io/badge/License-BSD%202--Clause-orange.svg)


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
  - Generic SDRAM PHY (vendor agnostic, tested on Xilinx, Altera, Lattice)
  - Spartan6 DDR/LPDDR/DDR2/DDR3 PHY (1:2 or 1:4 frequency ratio)
  - Spartan7/Artix7/Kintex7/Virtex7 DDR2/DDR3 PHY (1:2 or 1:4 frequency ratio)
  - Kintex/Virtex Ultrascale (Plus) DDR3/DDR4 PHY (1:4 frequency ratio)
  - ECP5 DDR3 PHY (1:2 frequency ratio)

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
- add support for Altera devices.
- add more documentation
- ... See below Support and consulting :)

If you want to support these features, please contact us at florent [AT]
enjoy-digital.fr.

[> Getting started
------------------
1. Install Python 3.6+ and FPGA vendor's development tools.
2. Install LiteX and the cores by following the LiteX's wiki [installation guide](https://github.com/enjoy-digital/litex/wiki/Installation).
3. You can find examples of integration of the core with LiteX in LiteX-Boards and in the examples directory.

[> Tests
--------
Unit tests are available in ./test/.
To run all the unit tests:
```sh
$ ./setup.py test
```

Tests can also be run individually:
```sh
$ python3 -m unittest test.test_name
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