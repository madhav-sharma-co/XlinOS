#!/usr/bin/env bash
# Boots XlinOS in QEMU (serial console in this terminal). Exit: Ctrl-A then X.
set -euo pipefail
cd "$(dirname "$0")/.."
exec qemu-system-x86_64 -m 512 -nographic \
	-kernel build/bzImage -initrd build/initramfs.cpio.gz \
	-append "console=ttyS0 quiet" "$@"
