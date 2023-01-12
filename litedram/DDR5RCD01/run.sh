#
# This file is part of LiteDRAM.
#
# Copyright (c) 2023 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

#!/bin/bash

# This script runs all engineering tests.
# There are 3 possible outcomes:
# 1. The test builds, prints a log file and a waveform file
# 2. The test raises an error message "this test is to be done"
#    This means that the test has a known bug or its implementation is unfinished.
# 3. The test raises an error message "this test is not provided"
#    This means that explicit testing of this module is not in the validation plan.

all_py=( \
    "DDR5GlueRCDData.py" \
    "DDR5GlueRCD.py" \
    "DDR5RCD01Alert.py" \
    "DDR5RCD01BCOMSimulationPads.py" \
    "DDR5RCD01Channel.py" \
    "DDR5RCD01Chip.py" \
    "DDR5RCD01Common.py" \
    "DDR5RCD01ControlCenter.py" \
    "DDR5RCD01CoreEgressSimulationPads.py" \
    "DDR5RCD01CoreIngressSimulationPads.py" \
    "DDR5RCD01Core.py" \
    "DDR5RCD01DataBufferChip.py" \
    "DDR5RCD01DataBuffer.py" \
    "DDR5RCD01DataBufferShell.py" \
    "DDR5RCD01DataBufferSimulationPads.py" \
    "DDR5RCD01Error.py" \
    "DDR5RCD01FetchDecode.py" \
    "DDR5RCD01InputBuffer.py" \
    "DDR5RCD01LineBuffer.py" \
    "DDR5RCD01Loopback.py" \
    "DDR5RCD01OutputBuffer.py" \
    "DDR5RCD01Page.py" \
    "DDR5RCD01Pages.py" \
    "DDR5RCD01PLL.py" \
    "DDR5RCD01RegFile.py" \
    "DDR5RCD01Shell.py" \
    "DDR5RCD01SidebandSimulationPads.py" \
    "DDR5RCD01System.py" \
    "I2CSlave.py" \
    "I3CSlave.py" \
    "RCD_definitions.py" \
    "RCD_interfaces.py" \
    "RCD_utils.py" \
)

for test in ${all_py[@]}; do
    python $test
    read -p 'Next test?' user_continue
done

