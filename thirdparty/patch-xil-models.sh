#!/bin/bash

set -e -u -o pipefail
shopt -s nullglob
shopt -s extglob

SELF_DIR="$(dirname $(readlink -f ${BASH_SOURCE[0]}))"
cd $SELF_DIR

SRC="$SELF_DIR/xil-models"
PATCHES="$SELF_DIR/patches/xil-models"

git submodule update --init --recursive
cd $SRC

if [[ -n "$(ls $PATCHES/)" ]]; then
	git am $PATCHES/*
fi
