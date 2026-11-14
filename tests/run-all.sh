#!/usr/bin/env bash
# Runs every test that works without an Arch system. Account tests run in a private copy of /etc (needs root + unshare).
set -u
cd "$(dirname "$0")/.."
fail=0
for f in build.sh scripts/*.sh tests/*.sh profile/airootfs/usr/local/bin/* profile/airootfs/usr/share/xlinos/post-install.sh; do
  [[ -f "$f" ]] || continue
  if head -n1 "$f" | grep -q python; then
    python3 -I -c "import ast,sys;ast.parse(open(sys.argv[1]).read())" "$f" || { echo "SYNTAX: $f"; fail=1; }
  else
    bash -n "$f" || { echo "SYNTAX: $f"; fail=1; }
  fi
done
for f in profile/airootfs/usr/local/lib/xlinos/*; do
  [[ -f "$f" ]] || continue
  if [[ "$f" == *.py ]] || head -n1 "$f" | grep -q python; then
    python3 -I -c "import ast,sys;ast.parse(open(sys.argv[1]).read())" "$f" || { echo "SYNTAX: $f"; fail=1; }
  fi
done
sed "s|@POST_B64@|x|; s|@WLROOTS_PKG@|wlroots0.20|" profile/airootfs/usr/share/xlinos/archinstall-config.json.in | python3 -c 'import json,sys;json.load(sys.stdin)' || { echo "BAD archinstall json"; fail=1; }
python3 - <<'CHK' || fail=1
for path in ("profile/airootfs/usr/share/xlinos/xlin.conf", "profile/airootfs/usr/share/xlinos/installer.conf", "compositor/default.conf"):
    for ln, raw in enumerate(open(path), 1):
        s = raw.strip()
        if not s or s.startswith("#"): continue
        cmd = s.split()[0]
        if cmd not in ("set", "env", "exec-once", "bind", "unbind", "gesture", "rule"):
            raise SystemExit(f"BAD {path}:{ln}: unknown command {cmd}")
print("PASS xlin.conf syntax")
CHK
bash tests/test-snap.sh || fail=1
python3 tests/test-login.py || fail=1
python3 tests/test-installer.py >/tmp/ti.out 2>&1 && echo "PASS installer safety rules and progress" || { cat /tmp/ti.out; fail=1; }
out="$(SCEN=tests/smoke/installer.py XLINOS_SHARE=/tmp timeout 60 python3 tests/smoke/gtk_stub.py profile/airootfs/usr/local/lib/xlinos/xlinos-installer Installer 2>&1)"
grep -q "installer screens ok" <<<"$out" && echo "PASS installer screens" || { echo "FAIL installer screens"; echo "$out" | tail -8; fail=1; }
out="$(SCEN=tests/smoke/greeter.py timeout 60 python3 tests/smoke/gtk_stub.py profile/airootfs/usr/local/lib/xlinos/xlinos-greeter Greeter 2>&1)"
grep -q "scenario ok" <<<"$out" && echo "PASS greeter screens" || { echo "FAIL greeter screens"; echo "$out" | tail -8; fail=1; }
if [[ $EUID -eq 0 ]] && command -v unshare >/dev/null; then
  S="$(mktemp -d)"; cp -a /etc "$S/etc"
  sed -i -E '/^(ubuntu|xt[a-z]*):/d' "$S"/etc/passwd "$S"/etc/shadow "$S"/etc/group "$S"/etc/gshadow 2>/dev/null  # no human users may exist in the private copy
  awk -F: '$3>=1000 && $3<60000 && $7 !~ /(nologin|false)$/ {print $1}' "$S/etc/passwd" | cut -d: -f1 | while read -r u; do sed -i "/^$u:/d" "$S"/etc/passwd "$S"/etc/shadow; done
  unshare -m bash -c "mount --bind '$S/etc' /etc && bash tests/test-accounts.sh" || fail=1
else echo "skip: account tests need root and unshare"; fi
[[ $fail -eq 0 ]] && echo "ALL TESTS PASSED" || { echo "TESTS FAILED"; exit 1; }
