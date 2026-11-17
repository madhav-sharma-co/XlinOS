#!/usr/bin/env bash
# Boot the XlinOS ISO in QEMU.   usage: scripts/test-qemu.sh [--uefi] [path/to/iso]
# --uefi needs OVMF (Arch: sudo pacman -S edk2-ovmf); set OVMF_CODE to override its path.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UEFI=0
[ "${1:-}" = "--uefi" ] && { UEFI=1; shift; }
ISO="${1:-$(ls -t "$ROOT"/out/xlinos-*.iso 2>/dev/null | head -n1 || true)}"
[ -n "$ISO" ] && [ -f "$ISO" ] || { echo "error: no ISO found" >&2; exit 1; }
command -v qemu-system-x86_64 >/dev/null || { echo "error: install qemu (Arch: pacman -S qemu-base)" >&2; exit 1; }

args=(-m 2G -smp 2 -cdrom "$ISO" -boot d -nic user,model=virtio-net-pci)
[ -w /dev/kvm ] && args+=(-enable-kvm -cpu host)

if [ "$UEFI" -eq 1 ]; then
	code="${OVMF_CODE:-}"
	if [ -z "$code" ]; then
		for c in /usr/share/edk2/x64/OVMF_CODE.4m.fd /usr/share/edk2-ovmf/x64/OVMF_CODE.fd /usr/share/OVMF/OVMF_CODE.fd; do
			[ -f "$c" ] && code="$c" && break
		done
	fi
	[ -n "$code" ] || { echo "error: OVMF not found; set OVMF_CODE" >&2; exit 1; }
	args+=(-drive "if=pflash,format=raw,readonly=on,file=$code")
fi

exec qemu-system-x86_64 "${args[@]}"
