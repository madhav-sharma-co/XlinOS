#!/usr/bin/env bash
# Runs inside the new system at the end of the install (archinstall custom_commands).
set -u
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
# Xlin-soft source, and the session starter for every user created from now on
git clone --depth 1 https://github.com/madhav-sharma-co/XLIN-Soft.git /opt/xlin-soft && rm -rf /opt/xlin-soft/.git
cat >/usr/local/bin/xlinos-session <<'EOT'
#!/usr/bin/env bash
if [[ ! -f "$HOME/.config/xlin/state/source" && -d /opt/xlin-soft ]]; then
  echo "XlinOS: setting up the desktop for $USER (first start, about a minute; you may be asked for your password)..."
  src="$HOME/.Xlin-soft"
  [[ -d "$src" ]] || cp -r /opt/xlin-soft "$src"
  ( cd "$src" && XLIN_NO_UPGRADE=1 bash install.sh </dev/null ) || echo "(setup had a problem: run 'xlin doctor' inside the desktop)"
  mkdir -p "$HOME/.config/xlin/state"; echo "$src" >"$HOME/.config/xlin/state/source"
fi
export XDG_CURRENT_DESKTOP=Hyprland XDG_SESSION_TYPE=wayland XDG_SESSION_DESKTOP=Hyprland
exec Hyprland
EOT
chmod 755 /usr/local/bin/xlinos-session
cat >/etc/skel/.bash_profile <<'EOT'
[[ -f ~/.bashrc ]] && . ~/.bashrc
if [[ -z "${WAYLAND_DISPLAY:-}" && -z "${DISPLAY:-}" && "$(tty)" == /dev/tty1 ]]; then
  exec /usr/local/bin/xlinos-session
fi
EOT
# Layers 2-4: lean and fast defaults (zram swap, small journal, no boot wait for the network)
mkdir -p /etc/systemd/journald.conf.d /etc/sysctl.d
printf '[zram0]\nzram-size = min(ram / 2, 4096)\ncompression-algorithm = zstd\n' >/etc/systemd/zram-generator.conf
printf '[Journal]\nSystemMaxUse=100M\n' >/etc/systemd/journald.conf.d/xlinos.conf
printf 'vm.swappiness = 100\nvm.page-cluster = 0\n' >/etc/sysctl.d/99-xlinos.conf
ln -sf /dev/null /etc/systemd/system/NetworkManager-wait-online.service
# members of wheel may use sudo (with a password)
sed -i 's/^# %wheel ALL=(ALL:ALL) ALL/%wheel ALL=(ALL:ALL) ALL/' /etc/sudoers
for u in $(awk -F: '$3>=1000 && $3<60000 {print $1}' /etc/passwd); do
  h="$(getent passwd "$u" | cut -d: -f6)"
  [[ -d "$h" && ! -f "$h/.bash_profile" ]] && { cp /etc/skel/.bash_profile "$h/.bash_profile"; chown "$u": "$h/.bash_profile"; }
done
exit 0
