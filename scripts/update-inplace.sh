#!/usr/bin/env bash
# One-time test update of an installed XlinOS to the files in this checkout (no reinstall needed).
# usage: sudo bash scripts/update-inplace.sh [REPO_DIR]
# It builds the new compositor first, then backs up what it will replace, then installs. Restore with: sudo xlinos-restore
set -e
[[ $EUID -eq 0 ]] || { echo "Run with sudo."; exit 1; }
R="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
BK=/var/backups/xlinos-before-update.tar.gz

echo "1/4 Installing build tools (needs internet)..."
# wlroots has the version in its package name (for example wlroots0.20): pick the newest one
W=$(pacman -Ssq '^wlroots[0-9.]*$' | sort -V | tail -1)
[[ -n "$W" ]] || { echo "Could not find the wlroots package. Run: sudo pacman -Sy   and try again."; exit 1; }
echo "   using $W"
pacman -S --needed --noconfirm base-devel git "$W" wayland-protocols libinput pkgconf || { echo "Could not install the build tools. Nothing was changed. Send this output to Claude."; exit 1; }

echo "2/4 Building the new desktop (nothing is changed yet)..."
make -C "$R/compositor" clean all || { echo "Build failed. Nothing was changed. Send this output to Claude."; exit 1; }

echo "3/4 Saving a backup of the current desktop to $BK ..."
mkdir -p /var/backups
tar -czf "$BK" --ignore-failed-read /usr/local/bin /usr/local/lib/xlinos /usr/share/xlinos /usr/share/applications/xlinos-*.desktop /etc/greetd /etc/sudoers.d/xlinos-greeter 2>/dev/null || true
cat >/usr/local/bin/xlinos-restore <<'EOT'
#!/bin/sh
# Puts the desktop back the way it was before the test update.
[ "$(id -u)" = 0 ] || exec sudo "$0"
tar -xzf /var/backups/xlinos-before-update.tar.gz -C / && echo "Restored. Restart the laptop."
EOT
chmod 755 /usr/local/bin/xlinos-restore

echo "4/4 Installing the new desktop..."
bash "$R/scripts/install-files.sh" "$R"
systemctl enable greetd.service 2>/dev/null || true
echo
echo "Done. Save your work and RESTART the laptop to use the new desktop."
echo "If the screen does not come up: press Ctrl+Alt+F3, log in, and run: sudo xlinos-restore   then restart."
