#!/bin/bash

set -e -u -o pipefail
shopt -s nullglob
shopt -s extglob

SELF_DIR="$(dirname $(readlink -f ${BASH_SOURCE[0]}))"
cd $SELF_DIR

SRC="$SELF_DIR/micron"
PATCHES="$SELF_DIR/patches/micron"


if [[ ! -e "$SRC/ddr3.v" ]]; then
	cat <<-EOF
Micron memory model not found. Please download "DDR3 SDRAM Verilog Model" from:

  https://www.micron.com/products/dram/ddr3-sdram/part-catalog/mt41k512m16ha-125

and unpack it in the following directory:

  $SRC

EOF
	mkdir -p $SRC
	exit 1
fi

cd $SRC
git init .
git add \
	1024Mb_ddr3_parameters.vh \
	2048Mb_ddr3_parameters.vh \
	4096Mb_ddr3_parameters.vh \
	8192Mb_ddr3_parameters.vh \
	ddr3.v \
	ddr3_dimm.v \
	ddr3_mcp.v \
	ddr3_module.v \
	readme.txt \
	subtest.vh \
	tb.v
git commit -m 'Initial commit'

if [[ -n "$(ls $PATCHES/)" ]]; then
	git am $PATCHES/*
fi
