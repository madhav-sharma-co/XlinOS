#!/bin/bash
# The test scenario, run as user t inside a real login session in the VM. Output goes to the shared folder.
R=/mnt/repo; OUT=$R/out; mkdir -p "$OUT"
exec >"$OUT/session.log" 2>&1
export XLINOS_DEBUG=1
export WLR_RENDERER_ALLOW_SOFTWARE=1 WLR_NO_HARDWARE_CURSORS=1
CFG=/usr/share/xlinos/xlin.conf
xlin-comp -c "$CFG" >"$OUT/xlin-comp.log" 2>&1 &
for _ in $(seq 1 40); do [ -S "$XDG_RUNTIME_DIR/xlin-comp.sock" ] && break; sleep 0.5; done
for _ in $(seq 1 20); do ls "$XDG_RUNTIME_DIR"/wayland-[0-9] >/dev/null 2>&1 && break; sleep 0.5; done
export WAYLAND_DISPLAY="$(basename "$(ls "$XDG_RUNTIME_DIR"/wayland-[0-9] | head -1)")"
export XLIN_COMP_SOCK="$XDG_RUNTIME_DIR/xlin-comp.sock"
sleep 3
echo "== monitors"; xlinctl monitors | jq -c '.[] | {name,width,height,refreshRate,reserved}'
if [[ -x /usr/local/lib/xlinos/xlinos-test-scenario ]]; then
  /usr/local/lib/xlinos/xlinos-test-scenario "$OUT"
else
  bash "$R/scripts/ci/scenario.sh" "$OUT"
fi
xlinctl exit >/dev/null 2>&1; sleep 1
echo ok >"$OUT/done"
sleep 600
