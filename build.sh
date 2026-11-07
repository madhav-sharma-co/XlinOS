#!/usr/bin/env bash
# Build the XlinOS live ISO. Run on Arch Linux (or in an Arch container) as root:  sudo ./build.sh [--aur]
# It starts from archiso's own "releng" profile and adds XlinOS on top, so the boot menus and the base stay current.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
ROOT="$PWD"
USE_AUR=0; [[ "${1:-}" == "--aur" ]] && USE_AUR=1   # the dock is in the official repo now; --aur only for AUR extras
XLIN_SOFT_REPO="${XLIN_SOFT_REPO:-https://github.com/madhav-sharma-co/XLIN-Soft.git}"
XLIN_SOFT_REF="${XLIN_SOFT_REF:-main}"
RELENG=/usr/share/archiso/configs/releng
WORK="$ROOT/work"; OUT="$ROOT/out"; PROFILE="$WORK/profile"

say() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
[[ -f /etc/arch-release ]] || { echo "Build on Arch Linux (or an Arch container)."; exit 1; }
[[ $EUID -eq 0 ]] || { echo "Run as root: sudo ./build.sh"; exit 1; }
[[ -d "$RELENG" ]] || { echo "Install archiso first: pacman -S archiso"; exit 1; }

version="$(cat "$ROOT/VERSION")"
say "Preparing the profile (XlinOS $version)"
mkdir -p "$WORK" "$OUT"
[[ -n "$WORK" && -d "$WORK" ]] && rm -rf "${WORK:?}/profile" "${WORK:?}/tmp" "${WORK:?}/xlin-soft"
cp -r "$RELENG" "$PROFILE"

# --- identity of the ISO
sed -i \
  -e 's|^iso_name=.*|iso_name="xlinos"|' \
  -e 's|^iso_label=.*|iso_label="XLINOS_$(date --date="@${SOURCE_DATE_EPOCH:-$(date +%s)}" +%Y%m)"|' \
  -e 's|^iso_publisher=.*|iso_publisher="XlinOS <https://github.com/madhav-sharma-co/XlinOS>"|' \
  -e 's|^iso_application=.*|iso_application="XlinOS live ISO"|' \
  -e "s|^iso_version=.*|iso_version=\"$version\"|" \
  -e 's|^install_dir=.*|install_dir="xlinos"|' \
  "$PROFILE/profiledef.sh"
# Layer 1: boot menus (names, splash picture, quiet start)
"$ROOT/scripts/brand-boot.sh" "$PROFILE"

# --- packages
say "Packages"
grep -vE '^\s*(#|$)' "$ROOT/profile/packages.extra" >>"$PROFILE/packages.x86_64"
sort -u -o "$PROFILE/packages.x86_64" "$PROFILE/packages.x86_64"

# --- the Xlin-soft source goes into the image
say "Xlin-soft ($XLIN_SOFT_REF)"
git clone --depth 1 --branch "$XLIN_SOFT_REF" "$XLIN_SOFT_REPO" "$WORK/xlin-soft"
rm -rf "$WORK/xlin-soft/.git"
mkdir -p "$PROFILE/airootfs/opt"
cp -r "$WORK/xlin-soft" "$PROFILE/airootfs/opt/xlin-soft"

# --- our files on top of releng's airootfs
cp -r "$ROOT/profile/airootfs/." "$PROFILE/airootfs/"
sed -i "s/@VERSION@/$version/g" "$PROFILE/airootfs/etc/os-release" "$PROFILE/airootfs/etc/issue" "$PROFILE/airootfs/etc/motd"
sed -i "s/@VERSION@/$version/g; s/@XLINOS_REF@/${XLINOS_REF:-}/g" "$PROFILE/airootfs/usr/share/xlinos/post-install.sh"
# archinstall config: embed the post-install script (base64 has no "|", so it is a safe sed delimiter)
x="$PROFILE/airootfs/usr/share/xlinos"
b64="$(base64 -w0 "$x/post-install.sh")"
sed "s|@POST_B64@|$b64|" "$x/archinstall-config.json.in" >"$x/archinstall-config.json"
rm -f "$x/archinstall-config.json.in"
python3 -c 'import json,sys; json.load(open(sys.argv[1]))' "$x/archinstall-config.json"

# --- the live user: uid 1000, no password, sudo without a password, autologin on tty1
if ! grep -q '^xlin:' "$PROFILE/airootfs/etc/passwd"; then
  echo 'xlin:x:1000:1000:XlinOS live user:/home/xlin:/bin/bash' >>"$PROFILE/airootfs/etc/passwd"
  echo 'xlin::14871::::::'                                      >>"$PROFILE/airootfs/etc/shadow"
  echo 'xlin:x:1000:'                                           >>"$PROFILE/airootfs/etc/group"
  echo 'xlin:!::'                                               >>"$PROFILE/airootfs/etc/gshadow"
  # also in the groups a desktop user needs (only where the group line exists)
  for g in wheel video audio input network storage optical; do
    sed -i -E "/^$g:/ { /:$/ s/\$/xlin/; /:$/! s/\$/,xlin/ }" "$PROFILE/airootfs/etc/group"
  done
fi
mkdir -p "$PROFILE/airootfs/home/xlin"
cp -a "$ROOT/profile/airootfs/etc/skel/." "$PROFILE/airootfs/home/xlin/"
cat >>"$PROFILE/profiledef.sh" <<'EOT'

# --- XlinOS
file_permissions+=(
  ["/etc/shadow"]="0:0:400"
  ["/etc/gshadow"]="0:0:400"
  ["/etc/sudoers.d/xlin-live"]="0:0:440"
  ["/home/xlin"]="1000:1000:750"
  ["/usr/local/bin/xlinos-session"]="0:0:755"
  ["/usr/local/bin/xlinos-install"]="0:0:755"
  ["/usr/local/bin/xlinos-browser"]="0:0:755"
  ["/usr/local/lib/xlinos/xlinos-accounts"]="0:0:755"
  ["/usr/local/lib/xlinos/xlinos-greeter"]="0:0:755"
  ["/usr/local/lib/xlinos/xlinos-shell"]="0:0:755"
  ["/usr/local/lib/xlinos/xlinos-snap"]="0:0:755"
  ["/usr/share/xlinos/post-install.sh"]="0:0:755"
)
EOT

# --- AUR-only packages (the Run Bar) go into a local repository that is used while building
if ((USE_AUR)); then
  say "AUR packages"
  "$ROOT/scripts/build-aur.sh" "$WORK/aur-repo"
  if [[ -f "$WORK/aur-repo/xlinos-aur.db.tar.gz" ]]; then
    printf '\n[xlinos-aur]\nSigLevel = Optional TrustAll\nServer = file://%s\n' "$WORK/aur-repo" >>"$PROFILE/pacman.conf"
    echo "nwg-dock-hyprland" >>"$PROFILE/packages.x86_64"
    sort -u -o "$PROFILE/packages.x86_64" "$PROFILE/packages.x86_64"
  fi
fi

say "Building the ISO (this takes a while)"
mkarchiso -v -w "$WORK/tmp" -o "$OUT" "$PROFILE"
say "Done: $(ls -1 "$OUT"/xlinos-*.iso | tail -1)"
