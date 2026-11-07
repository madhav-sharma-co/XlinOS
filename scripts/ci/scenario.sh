#!/bin/bash
# What the VM test does: open windows, snap them, take screenshots. usage: scenario.sh OUTDIR
OUT="$1"
sleep 6; grim "$OUT/0-desktop.png"
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

echo "== launcher"; /usr/local/lib/xlinos/xlinos-launcher >"$OUT/launcher.log" 2>&1 &
sleep 5; shot 7-launcher; pkill -f xlinos-launcher
echo "== quick"; python3 /usr/local/lib/xlinos/xlinos-quick >"$OUT/quick.log" 2>&1 &
sleep 8; pgrep -fa xlinos-quick; shot 8-quick; pkill -f lib/xlinos/xlinos-quick
echo "== lock"; xlinos-lock >"$OUT/lock.log" 2>&1 &
sleep 8; shot 9-lock
echo "== terminal"; hyprctl dispatch exec xlinos-terminal >/dev/null; sleep 7
shot 10-terminal; hyprctl clients -j | jq -c '.[]|select(.class=="os.xlin.terminal")|{class,title,floating,at,size,workspace}'
addr=$(hyprctl clients -j | jq -r '.[]|select(.class=="os.xlin.terminal")|.address')
hyprctl eval "hl.dispatch(hl.dsp.window.move({ workspace = \"special:minimized\", follow = false, window = \"address:$addr\" }))"; sleep 1
echo "== after minimise"; hyprctl clients -j | jq -c '.[]|select(.class=="os.xlin.terminal")|{workspace,hidden}'; shot 11-minimised
