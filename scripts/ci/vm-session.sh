#!/bin/bash
# The test scenario, run as user t inside a real login session in the VM. Output goes to the shared folder.
R=/mnt/repo; OUT=$R/out; mkdir -p "$OUT"
exec >"$OUT/session.log" 2>&1
export XLINOS_DEBUG=1
export WLR_RENDERER_ALLOW_SOFTWARE=1 WLR_NO_HARDWARE_CURSORS=1
CFG=/usr/share/xlinos/hypr/hyprland.lua
Hyprland -c "$CFG" >"$OUT/hyprland.log" 2>&1 &
for _ in $(seq 1 40); do ls "$XDG_RUNTIME_DIR"/hypr/*/.socket.sock >/dev/null 2>&1 && break; sleep 0.5; done
export HYPRLAND_INSTANCE_SIGNATURE="$(ls -t "$XDG_RUNTIME_DIR/hypr" | head -1)"
for _ in $(seq 1 20); do ls "$XDG_RUNTIME_DIR"/wayland-[0-9] >/dev/null 2>&1 && break; sleep 0.5; done
export WAYLAND_DISPLAY="$(basename "$(ls "$XDG_RUNTIME_DIR"/wayland-[0-9] | head -1)")"
sleep 3
echo "== monitors"; hyprctl monitors -j | jq -c '.[] | {name,width,height,reserved}'
if [[ -x /usr/local/lib/xlinos/xlinos-test-scenario ]]; then
  /usr/local/lib/xlinos/xlinos-test-scenario "$OUT"
else
  bash "$R/scripts/ci/scenario.sh" "$OUT"
fi
hyprctl eval 'hl.dispatch(hl.dsp.exit())' >/dev/null 2>&1; sleep 1
echo ok >"$OUT/done"
sleep 600
