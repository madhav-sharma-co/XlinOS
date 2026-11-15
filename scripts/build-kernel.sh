#!/usr/bin/env bash
# Downloads and builds the Linux kernel for XlinOS into build/bzImage.
set -euo pipefail
cd "$(dirname "$0")/.."

KVER="${KVER:-6.12.60}"
SRC="build/linux-$KVER"
URL="https://cdn.kernel.org/pub/linux/kernel/v${KVER%%.*}.x/linux-$KVER.tar.xz"

mkdir -p build
if [ ! -d "$SRC" ]; then
	[ -f "build/linux-$KVER.tar.xz" ] || curl -fL "$URL" -o "build/linux-$KVER.tar.xz"
	tar -C build -xf "build/linux-$KVER.tar.xz"
fi

cd "$SRC"
make x86_64_defconfig
# XlinOS identity + what our init needs
./scripts/config \
	--set-str LOCALVERSION "-xlin" \
	--set-str DEFAULT_HOSTNAME "xlin" \
	-e BLK_DEV_INITRD -e DEVTMPFS -e DEVTMPFS_MOUNT -e TMPFS \
	-e PROC_FS -e SYSFS -e TTY -e SERIAL_8250 -e SERIAL_8250_CONSOLE
make olddefconfig
make -j"$(nproc)" bzImage
cp arch/x86/boot/bzImage ../bzImage
echo "kernel ready: build/bzImage"
