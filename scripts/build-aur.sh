#!/usr/bin/env bash
# Build the AUR-only packages into a local pacman repository:  build-aur.sh <repo dir>   (run as root)
# makepkg refuses to run as root, so the build runs as a throw-away user.
set -euo pipefail
REPO="$(realpath -m "${1:-./aur-repo}")"
PKGS=(nwg-dock-hyprland)
mkdir -p "$REPO"
id -u xlinbuild >/dev/null 2>&1 || useradd -m xlinbuild
echo 'xlinbuild ALL=(ALL) NOPASSWD: ALL' >/etc/sudoers.d/xlinbuild; chmod 440 /etc/sudoers.d/xlinbuild
chown xlinbuild "$REPO"
for p in "${PKGS[@]}"; do
  if pacman -Si "$p" >/dev/null 2>&1; then echo "$p: in the official repositories"; continue; fi
  if sudo -u xlinbuild bash -c "d=\$(mktemp -d) && cd \$d && git clone --depth 1 https://aur.archlinux.org/$p.git && cd $p && makepkg -sf --noconfirm --needed && cp *.pkg.tar.* '$REPO/'"; then
    echo "$p: built"
  else
    echo "$p: could not be built, the ISO will not contain it" >&2
  fi
done
shopt -s nullglob
pk=("$REPO"/*.pkg.tar.*)
((${#pk[@]})) && repo-add "$REPO/xlinos-aur.db.tar.gz" "${pk[@]}" >/dev/null
rm -f /etc/sudoers.d/xlinbuild
exit 0
