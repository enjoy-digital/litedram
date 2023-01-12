# LiteDRAM DDR5 RCD01 Simulation Model

The model provides a simplified view of the RCD chip used
on Registered Dual-Inline Memory Modules (RDIMM) for the DDR5 technology. The model is meant for simulation only. The model is
validated with the migen simulator tool.

## Table of contents
* [This directory](#this-directory)
* [Implementation](#the-implementation)
* [TODO](#TODO)
* [Setup](#setup)
* [License](#license)


## Scope
    
    1. implementation of the DDR5 RCD01 model
    2. unit tests in 'unittests/'

    3. integration tests in 'tests/'

    4. run engineering tests with:
        $> bash run.sh
    Logs and waveform are produced in 'eng_test/' dir

## The implementation
    1. DDR5 RCD01 Core
        - meant to meet the JESD82-511 specification
        - top-level implementation of the RCD physical functions
        - integrates DDR5RCD01xxx blocks (channel A, B and common part)
        - RCD definitons, utils and interfaces contain configuration
        information about the RCD Core (bus widths, register file size, etc.)
    2. DDR5 RCD01 System is a wrapper to enable integration with
    existing LiteDRAM implementations. The System encapsulates:
        - RCD Chip
            - Core
            - IXC slaves
        - Data Buffer Chip:
            - Data Buffer
    
    Data Buffers are wrappers for possible future LRDIMM applications.
    
    Files *SimulationPads* are interfaces meant for litedram integration
    
    IXC slaves are empty wrapper meant as placeholders for possible implementation of the SMBus

## Setup
    - setup as in rowhammer

## TODO
        [x] Initial implementation
        [ ] Full implementation
        [x] Engineering tests
        [ ] Unit tests
        [ ] Integration test

## License

This file is part of LiteDRAM.

Copyright (c) 2023 Antmicro <www.antmicro.com>

SPDX-License-Identifier: BSD-2-Clause
