#!/usr/bin/env bash
# Builds an installed-style XlinOS system image the way the installer would (same package list, same post-install script),
# then boots it in QEMU and drives the first start. Runs in the archlinux container in CI (privileged).
# usage: ci-install-test.sh OUTDIR
set -euo pipefail
OUT="${1:?outdir}"; mkdir -p "$OUT"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CFG="$ROOT/profile/airootfs/usr/share/xlinos/archinstall-config.json.in"
W=/var/tmp/xlinos-install; rm -rf "$W"; mkdir -p "$W/root"
pacman-key --init && pacman-key --populate archlinux >/dev/null 2>&1 || true
pkgs="$(python3 -c 'import json,sys; c=json.load(open(sys.argv[1])); print(" ".join(p for p in c["packages"]))' "$CFG")"
services="$(python3 -c 'import json,sys; c=json.load(open(sys.argv[1])); print(" ".join(c["services"]))' "$CFG")"
mount --bind "$W/root" "$W/root"
pacstrap -K "$W/root" base linux mkinitcpio $pkgs 2>&1 | tail -n 15
# the installer's own steps
arch-chroot "$W/root" systemctl enable $services
sed -e "s/@VERSION@/ci-test/g; s/@XLINOS_REF@//g" "$ROOT/profile/airootfs/usr/share/xlinos/post-install.sh" >"$W/root/post-install.sh"
arch-chroot "$W/root" bash /post-install.sh 2>&1 | tail -n 20
rm -f "$W/root/post-install.sh"
echo xlinos >"$W/root/etc/hostname"; echo "LANG=C.UTF-8" >"$W/root/etc/locale.conf"
echo "/dev/vda / ext4 defaults 0 1" >"$W/root/etc/fstab"
echo "root:root" | arch-chroot "$W/root" chpasswd
ls -la "$W/root/boot" | head
# a start-up image with all drivers (the default one is trimmed to the build machine and would miss the virtual disk)
kver="$(ls "$W/root/usr/lib/modules" | head -1)"
arch-chroot "$W/root" mkinitcpio -k "$kver" -g /boot/initramfs-linux-fallback.img -S autodetect 2>&1 | tail -n 3
cp "$W/root/boot/vmlinuz-linux" "$W/root/boot/initramfs-linux-fallback.img" "$W/"
umount "$W/root" 2>/dev/null || true
truncate -s 9G "$W/disk.img"
mkfs.ext4 -q -F -d "$W/root" "$W/disk.img"
du -sh "$W/root" | tail -1
python3 "$ROOT/scripts/ci-install-boot.py" "$W" "$OUT"
