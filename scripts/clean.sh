#!/usr/bin/env bash
# Remove generated build files (build/ and out/ inside this repo only).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[ -f "$ROOT/archiso/profiledef.sh" ] || { echo "error: $ROOT is not the XlinOS repo" >&2; exit 1; }

# Never delete while something is still mounted under build/ (mkarchiso may leave mounts behind).
if grep -q " $ROOT/build" /proc/mounts; then
	echo "error: something is still mounted under $ROOT/build; unmount it first" >&2
	exit 1
fi

for d in build out; do
	if [ -d "$ROOT/$d" ]; then
		echo "removing $ROOT/$d"
		if [ -w "$ROOT/$d" ] && ! find "$ROOT/$d" ! -user "$(id -un)" -print -quit | grep -q .; then
			rm -rf -- "${ROOT:?}/$d"
		else
			sudo rm -rf -- "${ROOT:?}/$d"
		fi
	fi
done
echo "clean"
