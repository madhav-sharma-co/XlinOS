#!/usr/bin/env bash
# Builds the cached test system image: an installed-style XlinOS (same packages and post-install script as the
# installer) plus the CI hook (xlinos-ci.service). Runs in the archlinux container. usage: ci-vm-image.sh WORKDIR
set -euo pipefail
W="${1:?workdir}"; ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CFG="$ROOT/profile/airootfs/usr/share/xlinos/archinstall-config.json.in"
R=/var/tmp/vmimage-root   # outside the cached folder
rm -rf "$W" "$R"; mkdir -p "$W" "$R"
pacman-key --init && pacman-key --populate archlinux >/dev/null 2>&1 || true
pkgs="$(python3 -c 'import json,sys; print(" ".join(json.load(open(sys.argv[1]))["packages"]))' "$CFG")"
services="$(python3 -c 'import json,sys; print(" ".join(json.load(open(sys.argv[1]))["services"]))' "$CFG")"
mount --bind "$R" "$R"
pacstrap -K "$R" base linux mkinitcpio $pkgs 2>&1 | tail -n 5
arch-chroot "$R" systemctl enable $services
sed -e "s/@VERSION@/ci-test/g; s/@XLINOS_REF@//g" "$ROOT/profile/airootfs/usr/share/xlinos/post-install.sh" >"$R/post-install.sh"
arch-chroot "$R" bash /post-install.sh 2>&1 | tail -n 8
rm -f "$R/post-install.sh"
install -m 644 "$ROOT/scripts/ci/xlinos-ci.service" "$R/etc/systemd/system/xlinos-ci.service"
arch-chroot "$R" systemctl enable xlinos-ci.service
echo xlinos >"$R/etc/hostname"; echo "LANG=C.UTF-8" >"$R/etc/locale.conf"
echo "/dev/vda / ext4 defaults 0 1" >"$R/etc/fstab"
echo "root:root" | arch-chroot "$R" chpasswd
kver="$(ls "$R/usr/lib/modules" | head -1)"
arch-chroot "$R" mkinitcpio -k "$kver" -g /boot/initramfs-linux-fallback.img -S autodetect 2>&1 | tail -n 2
cp "$R/boot/vmlinuz-linux" "$R/boot/initramfs-linux-fallback.img" "$W/"
umount -l "$R" 2>/dev/null || true
truncate -s 9G "$W/disk.img"
mkfs.ext4 -q -F -d "$R" "$W/disk.img"
zstd -q -T0 --sparse -3 "$W/disk.img" -o "$W/disk.img.zst" && rm -f "$W/disk.img"
ls -la "$W"
