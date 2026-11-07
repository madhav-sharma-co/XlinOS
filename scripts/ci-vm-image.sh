#!/usr/bin/env bash
# Builds the cached test system image: an installed-style XlinOS (same packages and post-install script as the
# installer) plus the CI hook (xlinos-ci.service). Runs in the archlinux container. usage: ci-vm-image.sh WORKDIR
set -euo pipefail
W="${1:?workdir}"; ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CFG="$ROOT/profile/airootfs/usr/share/xlinos/archinstall-config.json.in"
rm -rf "$W"; mkdir -p "$W/root"
pacman-key --init && pacman-key --populate archlinux >/dev/null 2>&1 || true
pkgs="$(python3 -c 'import json,sys; print(" ".join(json.load(open(sys.argv[1]))["packages"]))' "$CFG")"
services="$(python3 -c 'import json,sys; print(" ".join(json.load(open(sys.argv[1]))["services"]))' "$CFG")"
mount --bind "$W/root" "$W/root"
pacstrap -K "$W/root" base linux mkinitcpio $pkgs 2>&1 | tail -n 5
arch-chroot "$W/root" systemctl enable $services
sed -e "s/@VERSION@/ci-test/g; s/@XLINOS_REF@//g" "$ROOT/profile/airootfs/usr/share/xlinos/post-install.sh" >"$W/root/post-install.sh"
arch-chroot "$W/root" bash /post-install.sh 2>&1 | tail -n 8
rm -f "$W/root/post-install.sh"
install -m 644 "$ROOT/scripts/ci/xlinos-ci.service" "$W/root/etc/systemd/system/xlinos-ci.service"
arch-chroot "$W/root" systemctl enable xlinos-ci.service
echo xlinos >"$W/root/etc/hostname"; echo "LANG=C.UTF-8" >"$W/root/etc/locale.conf"
echo "/dev/vda / ext4 defaults 0 1" >"$W/root/etc/fstab"
echo "root:root" | arch-chroot "$W/root" chpasswd
kver="$(ls "$W/root/usr/lib/modules" | head -1)"
arch-chroot "$W/root" mkinitcpio -k "$kver" -g /boot/initramfs-linux-fallback.img -S autodetect 2>&1 | tail -n 2
cp "$W/root/boot/vmlinuz-linux" "$W/root/boot/initramfs-linux-fallback.img" "$W/"
umount "$W/root" 2>/dev/null || true
truncate -s 9G "$W/disk.img"
mkfs.ext4 -q -F -d "$W/root" "$W/disk.img"
rm -rf "$W/root"
zstd -q -T0 --sparse -3 "$W/disk.img" -o "$W/disk.img.zst" && rm -f "$W/disk.img"
ls -la "$W"
