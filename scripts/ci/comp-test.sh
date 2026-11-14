#!/bin/bash
# Runs inside the headless compositor (started with -s). Writes results to $OUT/result.txt and shots to $OUT/*.png
OUT=${OUT:-/tmp/out}; mkdir -p "$OUT"; R="$OUT/result.txt"; : >"$R"
C="python3 $PWD/../profile/airootfs/usr/local/bin/xlinctl"
ok() { echo "PASS $1" >>"$R"; }; bad() { echo "FAIL $1" >>"$R"; }
chk() { if eval "$2"; then ok "$1"; else bad "$1"; fi; }
sleep 2
foot -e sh -c 'echo window ONE; sleep 120' & sleep 2
foot -e sh -c 'echo window TWO; sleep 120' & sleep 2
n=$($C clients | python3 -c 'import json,sys;print(len(json.load(sys.stdin)))')
chk "two windows listed ($n)" '[ "$n" = 2 ]'
chk "version" '$C version | grep -q xlin-comp'
$C snap left; sleep 1
sz=$($C activewindow | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d["at"][0],d["size"][0],d["snap"])')
echo "snap left -> $sz" >>"$R"
chk "snap left puts it at the left edge (gap allowed)" '[ "${sz%% *}" -le 16 ]'
grim "$OUT/1-snapped.png"
$C workspace 2; sleep 1
w=$($C workspaces | python3 -c 'import json,sys;d=json.load(sys.stdin);print([x["id"] for x in d if x["active"]][0])')
chk "workspace 2 active" '[ "$w" = 2 ]'
grim "$OUT/2-empty-desktop.png"
foot -e sh -c 'echo window on desktop TWO; sleep 120' & sleep 2
c2=$($C clients | python3 -c 'import json,sys;print(sum(1 for x in json.load(sys.stdin) if x["workspace"]["id"]==2))')
chk "new window opens on the current desktop" '[ "$c2" = 1 ]'
$C workspace 1; sleep 1
grim "$OUT/3-back.png"
$C snap max; sleep 1
mx=$($C activewindow | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d["size"][0])')
echo "max width $mx" >>"$R"
chk "maximise fills the width" '[ "$mx" -ge 1200 ]'
$C minimize; sleep 1
hid=$($C clients | python3 -c 'import json,sys;print(sum(1 for x in json.load(sys.stdin) if x["hidden"]))')
chk "minimise hides a window" '[ "$hid" = 1 ]'
$C unhide; sleep 1
hid2=$($C clients | python3 -c 'import json,sys;print(sum(1 for x in json.load(sys.stdin) if x["hidden"]))')
chk "unhide restores minimised window" '[ "$hid2" = 0 ]'
$C resize 40 20; sleep 1
chk "getoption layout works" '$C getoption workspaces | grep -q 4'
rr=$($C monitors | python3 -c 'import json,sys;m=json.load(sys.stdin);print(m[0]["refreshRate"])')
echo "refresh $rr" >>"$R"
chk "monitors reports a refresh rate" '[ -n "$rr" ]'
$C showdesktop; sleep 1; $C showdesktop; sleep 1
swaylock -c 224466 --indicator-idle-visible >/dev/null 2>&1 & sleep 4
chk "screen locks" '[ "$($C locked)" = true ]'
grim "$OUT/4-locked.png"
echo done >>"$R"
$C exit
