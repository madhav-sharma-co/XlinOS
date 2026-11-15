#!/usr/bin/env bash
# XlinOS build: ./build.sh [kernel]   (add "kernel" to also build the Linux kernel)
set -euo pipefail
cd "$(dirname "$0")"

mkdir -p build/rootfs/sbin
gcc -static -O2 -Wall -Wextra -o build/rootfs/init src/init/init.c
strip build/rootfs/init
python3 scripts/mkinitramfs.py build/rootfs build/initramfs.cpio.gz
echo "initramfs ready: build/initramfs.cpio.gz"

[ "${1:-}" = "kernel" ] && scripts/build-kernel.sh
echo "run it with: scripts/run-qemu.sh"
