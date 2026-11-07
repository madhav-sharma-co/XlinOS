#!/usr/bin/env bash
# CI (archlinux container): headless Hyprland test of the XlinOS desktop. usage: ci-shell-test.sh OUTDIR
OUT="$(realpath -m "${1:?outdir}")"; REPO="$(cd "$(dirname "$0")/.." && pwd)"
install -d /usr/local/lib/xlinos
cp -a "$REPO"/profile/airootfs/usr/local/lib/xlinos/. /usr/local/lib/xlinos/
[[ -d "$REPO/profile/airootfs/usr/local/bin" ]] && cp -a "$REPO"/profile/airootfs/usr/local/bin/. /usr/local/bin/
mkdir -p /usr/share/xlinos && cp -a "$REPO"/profile/airootfs/usr/share/xlinos/. /usr/share/xlinos/
id t >/dev/null 2>&1 || useradd -m t
mkdir -p "$OUT"; chmod 777 "$OUT"
su t -c "bash '$REPO/scripts/ci-shell-run.sh' '$REPO' '$OUT'" 2>&1 | tee "$OUT/run.log"
