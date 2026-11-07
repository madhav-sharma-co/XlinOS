#!/bin/bash
# What the VM test does: open windows, snap them, take screenshots. usage: scenario.sh OUTDIR
OUT="$1"
for t in A B C; do
  kitty --title "$t" bash -c "echo XlinOS terminal $t; sleep 900" >"$OUT/kitty-$t.log" 2>&1 &
  sleep 2
done
for _ in $(seq 1 30); do [[ "$(hyprctl clients -j | jq length)" -ge 3 ]] && break; sleep 1; done
sleep 6
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
