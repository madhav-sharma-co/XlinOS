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
if [[ -f "$R/compositor/xlin-comp.c" ]] && command -v make >/dev/null && pkg-config --list-all 2>/dev/null | grep -q '^wlroots'; then
  make -C "$R/compositor" clean all
  install -m 755 "$R/compositor/xlin-comp" /usr/local/bin/xlin-comp
elif [[ -x "$R/compositor/xlin-comp" ]]; then
  install -m 755 "$R/compositor/xlin-comp" /usr/local/bin/xlin-comp
fi
for f in "$A"/usr/share/applications/xlinos-*.desktop; do [[ "$f" == *xlinos-install.desktop ]] && continue; install -m 644 "$f" /usr/share/applications/; done
install -D -m 644 "$A"/usr/local/share/applications/kitty.desktop /usr/local/share/applications/kitty.desktop
install -D -m 644 "$A"/usr/share/xlinos/xlinos-mark.png /usr/share/xlinos/xlinos-mark.png
install -D -m 644 "$A"/usr/share/xlinos/xlin.conf /usr/share/xlinos/xlin.conf
install -D -m 644 "$A"/usr/share/xlinos/installer.conf /usr/share/xlinos/installer.conf
install -D -m 644 "$A"/usr/share/xlinos/quickshell.bashrc /usr/share/xlinos/quickshell.bashrc
install -d /usr/share/xlinos/wallpapers; install -m 644 "$A"/usr/share/xlinos/wallpapers/*.jpg /usr/share/xlinos/wallpapers/
install -D -m 644 "$A"/usr/share/plymouth/themes/xlinos/xlinos.plymouth /usr/share/plymouth/themes/xlinos/xlinos.plymouth
for f in xlinos.script logo.png px.png; do install -m 644 "$A"/usr/share/plymouth/themes/xlinos/$f /usr/share/plymouth/themes/xlinos/; done
rm -f /usr/share/applications/xlinos-install.desktop /usr/local/bin/xlinos-install /usr/local/bin/xlinos-installer   # the installer is only for the live USB/ISO
rm -rf /usr/share/xlinos/hypr /usr/share/xlinos/hyprlock.conf /usr/share/xlinos/xlinos.lua
install -d /etc/greetd
install -m 644 "$A"/usr/share/xlinos/greetd-config.toml /etc/greetd/config.toml
install -m 440 "$A"/usr/share/xlinos/sudoers-greeter /etc/sudoers.d/xlinos-greeter
chown root:root /usr/local/lib/xlinos/xlinos-accounts /usr/local/lib/xlinos/xlinos-update
chmod 755 /usr/local/lib/xlinos/xlinos-accounts /usr/local/lib/xlinos/xlinos-update
git -C "$R" rev-parse HEAD >/usr/share/xlinos/commit 2>/dev/null || echo unknown >/usr/share/xlinos/commit

# the start-up menu says XlinOS (never the base system's name) and does not wait
for e in /boot/loader/entries/*.conf; do
  [[ -f "$e" ]] || continue
  sed -i -E 's/^title .*/title   XlinOS/' "$e"
done
if [[ -f /boot/loader/loader.conf ]]; then
  if grep -q '^timeout' /boot/loader/loader.conf; then sed -i -E 's/^timeout .*/timeout 0/' /boot/loader/loader.conf; else echo "timeout 0" >>/boot/loader/loader.conf; fi
fi
