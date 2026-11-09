#!/usr/bin/env bash
# Runs inside the new system at the end of the install (archinstall custom_commands).
# Needs the internet (it fetches the XlinOS desktop files from GitHub).
set -u
REF="@XLINOS_REF@"
# the XlinOS name (replaces the symlink that the Arch filesystem package installs)
rm -f /etc/os-release
cat >/etc/os-release <<'EOT'
NAME="XlinOS"
PRETTY_NAME="XlinOS @VERSION@"
ID=xlinos
ID_LIKE=arch
BUILD_ID=rolling
VERSION_ID=@VERSION@
ANSI_COLOR="38;2;23;147;209"
HOME_URL="https://github.com/madhav-sharma-co/XlinOS"
DOCUMENTATION_URL="https://github.com/madhav-sharma-co/XlinOS"
SUPPORT_URL="https://github.com/madhav-sharma-co/XlinOS/issues"
BUG_REPORT_URL="https://github.com/madhav-sharma-co/XlinOS/issues"
EOT
printf 'XlinOS @VERSION@ (\\l)\n\n' >/etc/issue

# boot menu: XlinOS name, quiet start, no waiting
for f in /boot/loader/entries/*.conf; do
  [[ -f "$f" ]] || continue
  sed -i -E 's/^title .*/title   XlinOS/' "$f"
  grep -q '^options.*quiet' "$f" || sed -i -E '/^options/ s/$/ quiet loglevel=3 systemd.show_status=auto/' "$f"
done
if [[ -f /boot/loader/loader.conf ]]; then
  sed -i -E '/^(timeout|editor|console-mode)/d' /boot/loader/loader.conf
  printf 'timeout 0\neditor no\nconsole-mode keep\n' >>/boot/loader/loader.conf
fi
printf 'XlinOS @VERSION@\n' >/etc/issue.net

# XlinOS login files (login screen, account helper, session starter, browser helper)
tmp="$(mktemp -d)"
if git clone --depth 1 ${REF:+--branch "$REF"} https://github.com/madhav-sharma-co/XlinOS.git "$tmp/x"; then
  bash "$tmp/x/scripts/install-files.sh" "$tmp/x"
  systemctl enable greetd.service
else
  echo "XlinOS: could not fetch the login files. Check the internet and run the installer again."
fi
rm -rf "$tmp"

# Layers 2-4: lean and fast defaults (zram swap, small journal, no boot wait for the network)
mkdir -p /etc/systemd/journald.conf.d /etc/sysctl.d
printf '[zram0]\nzram-size = min(ram / 2, 4096)\ncompression-algorithm = zstd\n' >/etc/systemd/zram-generator.conf
printf '[Journal]\nSystemMaxUse=100M\n' >/etc/systemd/journald.conf.d/xlinos.conf
printf 'vm.swappiness = 100\nvm.page-cluster = 0\n' >/etc/sysctl.d/99-xlinos.conf
ln -sf /dev/null /etc/systemd/system/NetworkManager-wait-online.service

# members of wheel may use sudo (with a password)
sed -i 's/^# %wheel ALL=(ALL:ALL) ALL/%wheel ALL=(ALL:ALL) ALL/' /etc/sudoers
exit 0
