#!/usr/bin/env bash
# Boot an XlinOS ISO in QEMU:  scripts/test-qemu.sh <iso> [--uefi]   (needs qemu; --uefi needs edk2-ovmf)
set -euo pipefail
iso="${1:?usage: test-qemu.sh <iso> [--uefi]}"
args=(-m 4G -smp 2 -enable-kvm -cpu host -device virtio-vga-gl -display gtk,gl=on -device intel-hda -device hda-duplex
      -nic user,model=virtio-net-pci -cdrom "$iso" -boot d)
[[ "${2:-}" == "--uefi" ]] && args+=(-bios /usr/share/edk2/x64/OVMF.4m.fd)
disk="${XLIN_TEST_DISK:-xlinos-test.qcow2}"
[[ -f "$disk" ]] || qemu-img create -f qcow2 "$disk" 30G >/dev/null
exec qemu-system-x86_64 "${args[@]}" -drive file="$disk",if=virtio
