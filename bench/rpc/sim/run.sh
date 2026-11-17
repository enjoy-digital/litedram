#!/bin/sh
# Simulate NXRPCPHY with Lattice's primitive models (QuestaSim from Radiant) and a RPC DRAM model.
#
# Usage: ./gen.py top.v && ./run.sh [+STB=n +DQS=n +DB=n +RD_EN=n +RD_PH=n +RDLY=n +MON=n ...]
# RADIANT: Radiant install directory (default /opt/radiant); the QuestaSim license comes from the
# environment (SALT_LICENSE_SERVER).
RADIANT=${RADIANT:-/opt/radiant}
Q=$RADIANT/questasim/linux_x86_64
L=$RADIANT/cae_library/simulation/libs
cd "$(dirname "$0")"
if [ ! -d work ] || [ top.v -nt work/_info ] || [ tb.sv -nt work/_info ] || [ rpc_dram.sv -nt work/_info ]; then
    rm -rf work; $Q/vlib work > /dev/null
    $Q/vlog -quiet -sv top.v rpc_dram.sv tb.sv || exit 1
fi
$Q/vsim -c -quiet -t 1ps -L $L/lfcpnx -L $L/pmi_work tb "$@" -do "run -all; quit -f" 2>&1 | grep "^# \\["
