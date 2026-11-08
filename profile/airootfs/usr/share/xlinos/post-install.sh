#!/usr/bin/env bash
# Runs inside the new system at the end of the install (archinstall custom_commands).
# Needs the internet (it fetches Xlin-soft and the XlinOS login files from GitHub).
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

# Xlin-soft for everyone: source in /opt, programs in /usr/local (what its installer would do, done once as root)
git clone --depth 1 https://github.com/madhav-sharma-co/XLIN-Soft.git /opt/xlin-soft && rm -rf /opt/xlin-soft/.git
if [[ -f /opt/xlin-soft/scripts/files.sh ]]; then
  SRC=/opt/xlin-soft; . /opt/xlin-soft/scripts/files.sh
  for b in "${XLIN_BINS[@]}"; do install -m 755 "$SRC/bin/$b" "/usr/local/bin/$b"; done
  for l in "${XLIN_LIBS[@]}"; do install -D -m 644 "$SRC/lib/$l" "/usr/local/lib/xlin/$l"; done
fi

# XlinOS login files (login screen, account helper, session starter, browser helper)
tmp="$(mktemp -d)"
if git clone --depth 1 ${REF:+--branch "$REF"} https://github.com/madhav-sharma-co/XlinOS.git "$tmp/x"; then
  A="$tmp/x/profile/airootfs"
  install -d /usr/local/lib/xlinos
  install -m 755 "$A"/usr/local/lib/xlinos/xlinos-greeter "$A"/usr/local/lib/xlinos/xlinos-accounts "$A"/usr/local/lib/xlinos/xlinos-shell "$A"/usr/local/lib/xlinos/xlinos-focus "$A"/usr/local/lib/xlinos/xlinos-files "$A"/usr/local/lib/xlinos/xlinos-terminal "$A"/usr/local/lib/xlinos/xlinos_ui.py "$A"/usr/local/lib/xlinos/xlinos-lock "$A"/usr/local/lib/xlinos/xlinos-quick "$A"/usr/local/lib/xlinos/xlinos-launcher "$A"/usr/local/lib/xlinos/xlinos-snap /usr/local/lib/xlinos/
  install -m 644 "$A"/usr/local/lib/xlinos/xlinos_login.py /usr/local/lib/xlinos/
  install -m 755 "$A"/usr/local/bin/xlinos-session "$A"/usr/local/bin/xlinos-browser "$A"/usr/local/bin/xlinos-snap "$A"/usr/local/bin/xlinos-launcher "$A"/usr/local/bin/xlinos-lock "$A"/usr/local/bin/xlinos-terminal "$A"/usr/local/bin/xlinos-files "$A"/usr/local/bin/xlinos-quick /usr/local/bin/
  install -m 644 "$A"/usr/share/applications/xlinos-browser.desktop /usr/share/applications/
  install -D -m 644 "$A"/usr/share/xlinos/xlinos-mark.png /usr/share/xlinos/xlinos-mark.png
  install -D -m 644 "$A"/usr/share/xlinos/themes/dark.sh /usr/share/xlinos/themes/dark.sh
  install -D -m 644 "$A"/usr/share/xlinos/wallpapers/xlin-dark.jpg /usr/share/xlinos/wallpapers/xlin-dark.jpg
  install -D -m 644 "$A"/usr/share/xlinos/xlinos.lua /usr/share/xlinos/xlinos.lua
  install -d /etc/greetd
  install -m 644 "$A"/usr/share/xlinos/greetd-config.toml /etc/greetd/config.toml
  install -m 440 "$A"/usr/share/xlinos/sudoers-greeter /etc/sudoers.d/xlinos-greeter
  chown root:root /usr/local/lib/xlinos/xlinos-accounts && chmod 755 /usr/local/lib/xlinos/xlinos-accounts   # root-owned: the greeter may only run it
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
