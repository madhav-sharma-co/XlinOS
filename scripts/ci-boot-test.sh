#!/usr/bin/env bash
# Boot smoke test: starts the ISO's kernel and initramfs in QEMU with a serial console and checks
# that systemd reaches multi-user.target and shows the XlinOS identity. No graphical output needed.
# usage: scripts/ci-boot-test.sh path/to/iso     needs: qemu-system-x86_64, xorriso
set -euo pipefail

ISO="${1:?usage: $0 path/to/iso}"
TMP="$(mktemp -d)"
LOG="$TMP/serial.log"
trap 'kill "${QPID:-0}" 2>/dev/null || true' EXIT

xorriso -osirrox on -indev "$ISO" \
	-extract /xlinos/boot/x86_64/vmlinuz-linux "$TMP/vmlinuz" \
	-extract /xlinos/boot/x86_64/initramfs-linux.img "$TMP/initrd" >/dev/null 2>&1 \
	|| { echo "FAIL: could not extract kernel/initramfs from the ISO"; exit 1; }

accel=tcg
[ -w /dev/kvm ] && accel=kvm
echo "booting with accel=$accel"
qemu-system-x86_64 -accel "$accel" -m 2G -smp 2 -nographic -no-reboot \
	-kernel "$TMP/vmlinuz" -initrd "$TMP/initrd" -cdrom "$ISO" \
	-append "archisobasedir=xlinos archisolabel=XLINOS_0_1 console=ttyS0 systemd.show_status=1" \
	-nic user,model=virtio-net-pci >"$LOG" 2>&1 &
QPID=$!

deadline=$((SECONDS + ${BOOT_TIMEOUT:-420}))
while [ $SECONDS -lt $deadline ]; do
	grep -aq "Reached target.*Multi-User System" "$LOG" && break
	grep -aqi "kernel panic\|Cannot open root device\|Failed to mount" "$LOG" && break
	kill -0 "$QPID" 2>/dev/null || break
	sleep 3
done

echo "================ serial log (last 60 lines) ================"
tail -n 60 "$LOG"
echo "============================================================"

ok=1
check() { if grep -aqi "$2" "$LOG"; then echo "PASS: $1"; else echo "FAIL: $1"; ok=0; fi; }
check "kernel booted"                      "Linux version"
check "root image found (no initramfs error)" "Reached target.*Initrd Root File System\|Switching root\|Welcome to"
check "identity is XlinOS"                 "Welcome to XlinOS"
check "systemd reached multi-user.target"  "Reached target.*Multi-User System"
if grep -aqi "kernel panic\|emergency mode\|Cannot open root device" "$LOG"; then echo "FAIL: boot errors found"; ok=0; fi
if grep -aqi "Reached target.*Graphical Interface" "$LOG"; then echo "FAIL: graphical target reached"; ok=0; fi

[ "$ok" -eq 1 ] && echo "BOOT TEST PASSED" || { echo "BOOT TEST FAILED"; exit 1; }
