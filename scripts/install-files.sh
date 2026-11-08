#!/usr/bin/env bash
# Installs the XlinOS desktop files from a checkout of the repo into the system. Used by the installer and by system updates.
# usage: install-files.sh REPO_DIR            (run as root)
set -e
R="${1:?repo dir}"; A="$R/profile/airootfs"
install -d /usr/local/lib/xlinos /usr/local/bin
for f in "$A"/usr/local/lib/xlinos/*; do
  [[ -f "$f" ]] || continue
  case "$f" in *.py) m=644 ;; *) m=755 ;; esac
  install -m "$m" "$f" /usr/local/lib/xlinos/
done
for f in "$A"/usr/local/bin/*; do
  [[ -f "$f" ]] || continue
  [[ "$(basename "$f")" == xlinos-install ]] && continue
  install -m 755 "$f" /usr/local/bin/
done
install -m 644 "$A"/usr/share/applications/xlinos-browser.desktop /usr/share/applications/
install -D -m 644 "$A"/usr/share/xlinos/xlinos-mark.png /usr/share/xlinos/xlinos-mark.png
install -D -m 644 "$A"/usr/share/xlinos/hypr/hyprland.lua /usr/share/xlinos/hypr/hyprland.lua
install -D -m 644 "$A"/usr/share/xlinos/hyprlock.conf /usr/share/xlinos/hyprlock.conf
install -D -m 644 "$A"/usr/share/xlinos/wallpapers/xlin-dark.jpg /usr/share/xlinos/wallpapers/xlin-dark.jpg
install -d /etc/greetd
install -m 644 "$A"/usr/share/xlinos/greetd-config.toml /etc/greetd/config.toml
install -m 440 "$A"/usr/share/xlinos/sudoers-greeter /etc/sudoers.d/xlinos-greeter
chown root:root /usr/local/lib/xlinos/xlinos-accounts /usr/local/lib/xlinos/xlinos-update
chmod 755 /usr/local/lib/xlinos/xlinos-accounts /usr/local/lib/xlinos/xlinos-update
git -C "$R" rev-parse HEAD >/usr/share/xlinos/commit 2>/dev/null || echo unknown >/usr/share/xlinos/commit
