#!/usr/bin/env bash
# Runs inside CI as a normal user: starts Hyprland headless with the XlinOS config, opens windows, drives xlinos-snap,
# takes screenshots with grim. usage: ci-shell-run.sh REPO OUTDIR
REPO="$1"; OUT="$2"; mkdir -p "$OUT"
export XDG_RUNTIME_DIR="/tmp/xdg-$(id -u)"; mkdir -p "$XDG_RUNTIME_DIR"; chmod 700 "$XDG_RUNTIME_DIR"
export AQ_BACKENDS=headless WLR_RENDERER_ALLOW_SOFTWARE=1 XLINOS_DEBUG=1 HOME="${HOME:-/home/t}"
CFG="$REPO/profile/airootfs/usr/share/xlinos/hypr/hyprland.lua"
mkdir -p "$HOME/.config/hypr"
Hyprland -c "$CFG" >"$OUT/hyprland.log" 2>&1 &
for _ in $(seq 1 40); do ls "$XDG_RUNTIME_DIR"/hypr/*/.socket.sock >/dev/null 2>&1 && break; sleep 0.5; done
export HYPRLAND_INSTANCE_SIGNATURE="$(ls -t "$XDG_RUNTIME_DIR/hypr" | head -1)"
sleep 2
echo "== monitors (before)"; hyprctl monitors -j | jq -c '.[] | {name,width,height}' 
[[ "$(hyprctl monitors -j | jq length)" == 0 ]] && { hyprctl output create headless; sleep 1; }
echo "== monitors"; hyprctl monitors -j | jq -c '.[] | {name,width,height,reserved}'
for _ in $(seq 1 20); do ls "$XDG_RUNTIME_DIR"/wayland-[0-9] >/dev/null 2>&1 && break; sleep 0.5; done
export WAYLAND_DISPLAY="$(basename "$(ls "$XDG_RUNTIME_DIR"/wayland-[0-9] | head -1)")"
echo "wayland: $WAYLAND_DISPLAY"
for t in A B C; do
  kitty --title "$t" bash -c "echo XlinOS terminal $t; sleep 900" >"$OUT/kitty-$t.log" 2>&1 &
  sleep 1.5
done
for _ in $(seq 1 30); do [[ "$(hyprctl clients -j | jq length)" -ge 3 ]] && break; sleep 1; done
sleep 2
geo() { hyprctl clients -j | jq -c '.[] | {t:.title,floating,at,size}'; }
shot() { grim "$OUT/$1.png" && echo "shot $1"; }
focus() { hyprctl eval "hl.dispatch(hl.dsp.focus({ window = \"title:$1\" }))" >/dev/null; sleep 0.4; }
snap() { focus "$1"; /usr/local/lib/xlinos/xlinos-snap "$2"; sleep 0.8; }
echo "== opened"; geo; shot 1-opened-overlapping
snap A left; snap B right; echo "== halves"; geo; shot 2-halves
snap C center; shot 3-third-window-over
snap C up; echo "== C max"; geo; shot 4-maximized
snap C down; echo "== C restored"; geo; shot 5-restored
snap A up; snap B down; echo "== quarters"; geo; shot 6-quarters
hyprctl eval 'hl.dispatch(hl.dsp.exit())' >/dev/null; sleep 1
