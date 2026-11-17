#!/usr/bin/env bash
# Build the XlinOS ISO.   usage: scripts/build-iso.sh [--check]
#   --check   only validate the archiso profile (works on any Linux, needs no Arch tools)
# Output: out/xlinos-<version>-x86_64.iso. Work files go to build/work (inside this repo only).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROFILE="$ROOT/archiso"
WORK="$ROOT/build/work"
OUT="$ROOT/out"

die() { echo "error: $*" >&2; exit 1; }

validate_profile() {
	echo "==> Validating archiso profile"
	local f
	for f in profiledef.sh packages.x86_64 pacman.conf syslinux/syslinux.cfg \
		efiboot/loader/loader.conf airootfs/usr/share/xlinos/os-release airootfs/etc/hostname; do
		[ -f "$PROFILE/$f" ] || die "missing profile file: archiso/$f"
	done
	bash -n "$PROFILE/profiledef.sh" || die "syntax error in profiledef.sh"
	bash -n "$PROFILE/airootfs/usr/local/bin/xlin-firstboot" || die "syntax error in xlin-firstboot"

	# Read the profile in a subshell so nothing leaks into this script.
	(
		declare -A file_permissions=()   # mkarchiso declares this before sourcing the profile
		# shellcheck source=/dev/null
		source "$PROFILE/profiledef.sh"
		[ -n "${iso_name:-}" ] || die "iso_name not set"
		[ "${#iso_label}" -le 32 ] || die "iso_label longer than 32 chars"
		[[ $install_dir =~ ^[a-z0-9]{1,8}$ ]] || die "install_dir must be 1-8 chars of a-z0-9"
		[ "${#bootmodes[@]}" -gt 0 ] || die "no bootmodes set"
		local p
		for p in "${!file_permissions[@]}"; do
			[ -e "$PROFILE/airootfs$p" ] || die "file_permissions entry has no file: $p"
		done
		grep -q "^ID=xlinos$" "$PROFILE/airootfs/usr/share/xlinos/os-release" || die "os-release ID is not xlinos"
	)

	# Packages: not empty, and no graphical stack in the 0.1 milestone.
	local pkgs
	pkgs="$(sed -e 's/#.*//' -e 's/[[:space:]]*$//' -e '/^$/d' "$PROFILE/packages.x86_64")"
	[ -n "$pkgs" ] || die "packages.x86_64 is empty"
	if grep -E '^(xorg.*|xwayland.*|plasma.*|kde-.*|gnome.*|sddm|gdm|lightdm|sway|hyprland|wayland|firefox|chromium)$' <<<"$pkgs"; then
		die "graphical packages are not allowed in XlinOS 0.1 (listed above)"
	fi
	grep -qx "base" <<<"$pkgs" && grep -qx "linux" <<<"$pkgs" || die "base and linux must be in packages.x86_64"

	# Dangling-symlink check (links to the target system's files are allowed: they start with /).
	local l
	while IFS= read -r l; do
		case "$(readlink "$l")" in /*) ;; *) [ -e "$l" ] || die "broken symlink: ${l#"$ROOT"/}" ;; esac
	done < <(find "$PROFILE/airootfs" -type l)
	echo "    profile OK"
}

check_deps() {
	echo "==> Checking build dependencies"
	local missing=() t
	for t in mkarchiso mksquashfs xorriso mformat; do
		command -v "$t" >/dev/null || missing+=("$t")
	done
	[ "${#missing[@]}" -eq 0 ] || die "missing tools: ${missing[*]}
Install on Arch with: sudo pacman -S archiso mtools libisoburn squashfs-tools"
	[ -r /etc/arch-release ] || echo "    warning: this is not Arch Linux; build in an Arch container (docs/BUILD.md)"
}

validate_profile
[ "${1:-}" = "--check" ] && exit 0
check_deps

# Fixed timestamp for reproducibility: the time of the latest commit if available.
SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-$(git -C "$ROOT" log -1 --format=%ct 2>/dev/null || date +%s)}"
export SOURCE_DATE_EPOCH

mkdir -p "$WORK" "$OUT"
echo "==> Building ISO (this takes a while)"
SUDO=""
[ "$(id -u)" -eq 0 ] || SUDO="sudo"
$SUDO mkarchiso -v -w "$WORK" -o "$OUT" "$PROFILE" || die "mkarchiso failed; see the output above"

ISO="$(ls -t "$OUT"/xlinos-*.iso 2>/dev/null | head -n1 || true)"
[ -n "$ISO" ] || die "build finished but no ISO found in $OUT"
"$ROOT/scripts/verify-iso.sh" "$ISO"
echo "==> Done: $ISO"
