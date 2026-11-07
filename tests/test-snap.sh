#!/usr/bin/env bash
# xlinos-snap against a fake hyprctl: 1920x1080 screen, bar reserves 48 px at the top, scale 1.
set -u
cd "$(dirname "$0")/.."
D="$(mktemp -d)"; LOG="$D/log"
cat >"$D/hyprctl" <<'EOS'
#!/usr/bin/env bash
case "$*" in
  "activewindow -j") echo '{"address":"0xabc","floating":true,"monitor":0}' ;;
  "monitors -j") echo '[{"id":0,"x":0,"y":0,"width":1920,"height":1080,"scale":1.0,"reserved":[0,48,0,0]}]' ;;
  *) echo "$*" >>"$LOG_FILE" ;;
esac
EOS
chmod +x "$D/hyprctl"; export LOG_FILE="$LOG" PATH="$D:$PATH"
fail=0
chk() { : >"$LOG"; bash profile/airootfs/usr/local/bin/xlinos-snap "$1"; got="$(grep -o 'exact [0-9]* [0-9]*,address:0xabc ; dispatch movewindowpixel exact [0-9]* [0-9]*' "$LOG" | sed 's/,address:0xabc ; dispatch movewindowpixel//')"
  if [[ "$got" == "$2" ]]; then echo "PASS snap $1"; else echo "FAIL snap $1: got '$got' want '$2'"; fail=1; fi; }
# usable area: x 8..1912 (1904 wide), y 56..1072 (1016 high); half = (1904-8)/2 = 948, half height = 504
chk left   "exact 948 1016 exact 8 56"
chk right  "exact 948 1016 exact 964 56"
chk max    "exact 1904 1016 exact 8 56"
chk tl     "exact 948 504 exact 8 56"
chk br     "exact 948 504 exact 964 568"
chk top    "exact 1904 504 exact 8 56"
chk restore "exact 1180 711 exact 366 208"
exit $fail
