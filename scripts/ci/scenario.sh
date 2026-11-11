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
echo "== terminal"; xlinos-terminal >"$OUT/terminal.log" 2>&1 &
sleep 8
shot 10-terminal; hyprctl clients -j | jq -c '.[]|select(.class=="os.xlin.terminal")|{class,title,floating,at,size,workspace}'
addr=$(hyprctl clients -j | jq -r '.[]|select(.class=="os.xlin.terminal")|.address')
hyprctl eval "hl.dispatch(hl.dsp.window.move({ workspace = \"special:minimized\", follow = false, window = \"address:$addr\" }))"; sleep 1
echo "== after minimise"; hyprctl clients -j | jq -c '.[]|select(.class=="os.xlin.terminal")|{workspace,hidden}'; shot 11-minimised
mkdir -p ~/Documents ~/Downloads ~/Pictures ~/Music ~/Videos ~/Projects; echo hi > ~/notes.txt
xlinos-files >"$OUT/files.log" 2>&1 &
sleep 8; shot 12-files
echo "== edge snap"; focus A
/usr/local/lib/xlinos/xlinos-snap press
hyprctl eval 'hl.dispatch(hl.dsp.window.move({ x = 300, y = 300 }))' >/dev/null; sleep 0.5
echo "cursor move:"; hyprctl eval 'hl.dispatch(hl.dsp.cursor.move({ x = 2, y = 400 }))'
sleep 1.5; hyprctl cursorpos; shot 13a-snap-preview; pgrep -fa "xlinos-(preview|snap)"; cat ${XDG_RUNTIME_DIR:-/tmp}/xlinos-snap-watch.log; cat ${XDG_RUNTIME_DIR:-/tmp}/xlinos-snap-watch.pid
XLINOS_DEBUG=1 /usr/local/lib/xlinos/xlinos-snap drop; sleep 0.8; geo; shot 13-edge-snap
echo "== config errors"; hyprctl configerrors
echo "== restore minimised terminal"; /usr/local/lib/xlinos/xlinos-focus os.xlin.terminal xlinos-terminal; sleep 1
hyprctl clients -j | jq -c '.[]|select(.class=="os.xlin.terminal")|{workspace:.workspace.name,at}'; shot 14-restored-terminal
xlinos-settings about >"$OUT/settings.log" 2>&1 &
sleep 8; shot 15-settings
xlinos-store >"$OUT/store.log" 2>&1 &
sleep 8; shot 16-store
xlinos-calculator >"$OUT/calc.log" 2>&1 &
xlinos-notes >"$OUT/notes.log" 2>&1 &
sleep 9; shot 17-calc-notes
xlinos-media >"$OUT/media.log" 2>&1 &
sleep 8; shot 18-media
mkdir -p ~/Pictures; cp /usr/share/xlinos/wallpapers/xlin-dark.jpg ~/Pictures/XlinOS-wallpaper.jpg
xlinos-photos >"$OUT/photos.log" 2>&1 &
sleep 8; shot 19-photos
xlinos-calendar >"$OUT/calendar.log" 2>&1 &
sleep 8; shot 20-calendar
notify-send -a Calendar "Team call at 5 pm" "Starts in 10 minutes" >"$OUT/notify-send.log" 2>&1; sleep 2; shot 21-notification
/usr/local/lib/xlinos/xlinos-overview >"$OUT/overview.log" 2>&1 &
sleep 5; shot 22-overview; pkill -f xlinos-overview
for k in wifi bluetooth sound; do XLINOS_MENU_PIN=1 /usr/local/lib/xlinos/xlinos-menu $k >"$OUT/menu-$k.log" 2>&1 & sleep 12; shot 23-menu-$k; pkill -f "xlinos-menu $k"; done
printf 'hello XlinOS\n' >/tmp/demo.txt; xlinos-edit /tmp/demo.txt >"$OUT/edit.log" 2>&1 &
sleep 6; shot 26-editor
xlinos-monitor >"$OUT/monitor.log" 2>&1 &
sleep 7; shot 27-monitor
xlinos-clock >"$OUT/clock.log" 2>&1 &
sleep 5; shot 28-clock
xlinos-screenshot >"$OUT/screenshot.log" 2>&1 &
sleep 5; shot 29-screenshot-app
xlinos-screenshot full; ls -la ~/Pictures/Screenshots | tee "$OUT/screenshots.txt"
xlinos-settings general >"$OUT/settings-general.log" 2>&1 &
sleep 6; shot 30-settings-general; pkill -f xlinos-settings
for pg in personalisation desktop; do xlinos-settings $pg >"$OUT/settings-$pg.log" 2>&1 & sleep 6; shot 31-settings-$pg; pkill -f xlinos-settings; done
python3 /usr/local/lib/xlinos/xlinos-quick >"$OUT/quick2.log" 2>&1 &
sleep 14; shot 32-control-panel; pkill -f lib/xlinos/xlinos-quick
python3 /usr/local/lib/xlinos/xlinos-launcher >"$OUT/launcher2.log" 2>&1 &
sleep 6; shot 33-launcher; pkill -f lib/xlinos/xlinos-launcher
echo "== pin test"
python3 - <<'PY' >"$OUT/pin.log" 2>&1
import sys, subprocess, time
sys.path.insert(0, "/usr/local/lib/xlinos")
import xlinos_cfg as c, xlinos_ui
ids = [a[0] for a in xlinos_ui.available()] + ["kitty"]
c.set("runbar_pins", ids)
subprocess.run(["pkill", "-f", "lib/xlinos/xlinos-shell"]); time.sleep(0.5)
subprocess.Popen(["/usr/local/lib/xlinos/xlinos-shell"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
PY
sleep 8; pgrep -fa xlinos-shell | tee "$OUT/pin-shell.txt"; shot 34-pinned-kitty
echo "== keys + cli"
hyprctl configerrors >"$OUT/configerrors.txt" 2>&1; cat "$OUT/configerrors.txt"
xlinos status >"$OUT/xlinos-status.txt" 2>&1; xlinos doctor >>"$OUT/xlinos-status.txt" 2>&1; cat "$OUT/xlinos-status.txt"
xlinos-keys >"$OUT/keys.log" 2>&1 &
sleep 5; shot 35-keys; pkill -f lib/xlinos/xlinos-keys
echo "== desktop icons"
mkdir -p ~/Desktop/Projects; echo hi >~/Desktop/hello.txt
python3 -c "import sys; sys.path.insert(0,'/usr/local/lib/xlinos'); import xlinos_cfg as c; c.add_desktop_icon('kitty.desktop'); c.add_desktop_icon('calendar')"
sleep 4; xlinos showdesktop; sleep 4; shot 38-desktop-icons
python3 -c "import sys; sys.path.insert(0,'/usr/local/lib/xlinos'); import xlinos_cfg as c; c.desktop_drop('calendar','settings'); c.desktop_drop('kitty.desktop','folder:Folder')" >"$OUT/folder.log" 2>&1
sleep 4; shot 39-desktop-folder; cat ~/.config/xlinos/settings.json | tr -d '\n' | cut -c1-400 >"$OUT/folder-json.txt"; xlinos showdesktop; sleep 2
echo "== light theme"
xlinos theme light; sleep 6
xlinos-settings personalisation >"$OUT/light-settings.log" 2>&1 &
xlinos-files >"$OUT/light-files.log" 2>&1 &
sleep 8; shot 36-light-settings-files
pkill -f lib/xlinos/xlinos-settings; pkill -f lib/xlinos/xlinos-files
xlinos-notes >"$OUT/light-notes.log" 2>&1 &
python3 /usr/local/lib/xlinos/xlinos-launcher >"$OUT/light-launcher.log" 2>&1 &
sleep 8; shot 37-light-launcher-notes; pkill -f lib/xlinos/xlinos-launcher; pkill -f lib/xlinos/xlinos-notes
xlinos theme dark; sleep 4
echo "== lock"; xlinos-lock >"$OUT/lock.log" 2>&1 &
sleep 8; shot 9-lock
