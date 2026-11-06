#!/usr/bin/env bash
# Layer 1: the boot menus. Called by build.sh with the profile directory.
#  - the menus say XlinOS and syslinux shows the XlinOS splash picture
#  - the kernel is started quietly (no wall of text), which also helps boot speed
set -euo pipefail
P="${1:?usage: brand-boot.sh PROFILE_DIR}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 1. names
grep -rlE "Arch Linux" "$P"/syslinux "$P"/grub "$P"/efiboot 2>/dev/null | xargs -r sed -i 's/Arch Linux/XlinOS/g' || true
grep -rlE "install medium" "$P"/syslinux "$P"/grub "$P"/efiboot 2>/dev/null | xargs -r sed -i 's/install medium/live and installer/g' || true

# 2. splash picture for the BIOS (syslinux) menu: 640x480 PNG
if [[ -d "$P/syslinux" ]]; then
  cp "$HERE/assets/boot/splash.png" "$P/syslinux/splash.png"   # made by scripts/make-splash.py (needs Pillow, so it is committed)
fi

# 3. quiet kernel start: add the options in front of archisobasedir= on every boot entry (BIOS, GRUB, systemd-boot)
OPTS="quiet loglevel=3 systemd.show_status=auto rd.udev.log_level=3"
grep -rlE "archisobasedir=" "$P"/syslinux "$P"/grub "$P"/efiboot 2>/dev/null \
  | xargs -r sed -i -E "/ quiet( |$)/! s/archisobasedir=/$OPTS archisobasedir=/" || true
echo "boot menus: branded, splash set, quiet start"
