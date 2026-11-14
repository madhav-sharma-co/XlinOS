#!/usr/bin/env bash
# xlinos-snap against a mock xlinctl: verifies all snap directions dispatch cleanly to xlin-comp.
set -u
cd "$(dirname "$0")/.."
D="$(mktemp -d)"; LOG="$D/log"
cat >"$D/xlinctl" <<'EOS'
#!/usr/bin/env bash
echo "$*" >>"$LOG_FILE"
EOS
chmod +x "$D/xlinctl"; export LOG_FILE="$LOG" PATH="$D:$PATH"
fail=0
chk() {
  : >"$LOG"
  bash profile/airootfs/usr/local/bin/xlinos-snap "$1"
  got="$(cat "$LOG")"
  if [[ "$got" == "$2" ]]; then echo "PASS snap $1"; else echo "FAIL snap $1: got '$got' want '$2'"; fail=1; fi
}
for dir in left right top bottom tl tr bl br max restore center; do
  chk "$dir" "snap $dir"
done
if bash profile/airootfs/usr/local/bin/xlinos-snap bogus 2>/dev/null; then
  echo "FAIL snap bogus should exit non-zero"; fail=1
else
  echo "PASS snap bogus rejected"
fi
exit $fail
