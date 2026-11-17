#!/usr/bin/env bash
# Verify a built ISO.   usage: scripts/verify-iso.sh [path/to/iso]
# Checks: file exists and is non-empty, valid ISO 9660, XlinOS volume label,
# BIOS and UEFI boot entries; writes a .sha256 file next to it.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ISO="${1:-$(ls -t "$ROOT"/out/xlinos-*.iso 2>/dev/null | head -n1 || true)}"
fail() { echo "FAIL: $*" >&2; exit 1; }

[ -n "$ISO" ] && [ -f "$ISO" ] || fail "no ISO found (pass a path, or build first)"
[ -s "$ISO" ] || fail "ISO is empty: $ISO"
echo "ISO: $ISO ($(du -h "$ISO" | cut -f1))"

magic="$(dd if="$ISO" bs=1 skip=32769 count=5 2>/dev/null)"
[ "$magic" = "CD001" ] || fail "not an ISO 9660 image"
echo "ok: ISO 9660 signature"

if command -v xorriso >/dev/null; then
	info="$(xorriso -indev "$ISO" -report_el_torito plain 2>&1 || true)"
	label="$(grep -m1 'Volume id' <<<"$info" | sed "s/.*: *'\(.*\)'.*/\1/")"
	[[ $label == XLINOS_* ]] || fail "unexpected volume label: '${label:-none}'"
	echo "ok: volume label $label"
	grep -qi "BIOS" <<<"$info" || fail "no BIOS boot entry"
	grep -qi "UEFI" <<<"$info" || fail "no UEFI boot entry"
	echo "ok: BIOS and UEFI boot entries"
else
	echo "skipped: label and boot-entry checks (xorriso not installed)"
fi

(cd "$(dirname "$ISO")" && sha256sum "$(basename "$ISO")" | tee "$(basename "$ISO").sha256")
echo "VERIFIED (structure only). Boot it with scripts/test-qemu.sh to test it for real."
