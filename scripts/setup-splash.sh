#!/usr/bin/env bash
# Turns on the XlinOS boot logo on an installed system (run as root). Safe to run again.
set -u
pacman -Q plymouth >/dev/null 2>&1 || pacman -S --noconfirm --needed plymouth || exit 1
install -d /etc/plymouth
printf '[Daemon]\nTheme=xlinos\nShowDelay=0\nDeviceTimeout=8\n' >/etc/plymouth/plymouthd.conf
# initramfs: add the plymouth hook right after udev (or systemd)
if [[ -f /etc/mkinitcpio.conf ]] && ! grep -qE '^HOOKS=.*plymouth' /etc/mkinitcpio.conf; then
  if grep -qE '^HOOKS=.*\bsystemd\b' /etc/mkinitcpio.conf; then
    sed -i -E '/^HOOKS=/ s/\bsystemd\b/systemd plymouth/' /etc/mkinitcpio.conf
  else
    sed -i -E '/^HOOKS=/ s/\budev\b/udev plymouth/' /etc/mkinitcpio.conf
  fi
fi
# the login screen waits for the logo to finish
install -d /etc/systemd/system/greetd.service.d
printf '[Unit]\nAfter=plymouth-quit.service\n' >/etc/systemd/system/greetd.service.d/plymouth.conf
# boot entries: quiet + splash, no cursor
for f in /boot/loader/entries/*.conf; do
  [[ -f "$f" ]] || continue
  grep -qE '^options.*\bsplash\b' "$f" || sed -i -E '/^options/ s/$/ splash vt.global_cursor_default=0/' "$f"
  grep -qE '^options.*\bquiet\b' "$f" || sed -i -E '/^options/ s/$/ quiet loglevel=3/' "$f"
done
if [[ -f /etc/default/grub ]] && ! grep -q 'splash' /etc/default/grub; then
  sed -i -E 's/^(GRUB_CMDLINE_LINUX_DEFAULT=")/\1splash vt.global_cursor_default=0 /' /etc/default/grub
  command -v grub-mkconfig >/dev/null && grub-mkconfig -o /boot/grub/grub.cfg 2>/dev/null || true
fi
mkinitcpio -P
