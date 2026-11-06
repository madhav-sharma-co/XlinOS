#!/usr/bin/env bash
# Runs every test that works without an Arch system. Account tests run in a private copy of /etc (needs root + unshare).
set -u
cd "$(dirname "$0")/.."
fail=0
for f in build.sh scripts/*.sh tests/*.sh profile/airootfs/usr/local/bin/* profile/airootfs/usr/share/xlinos/post-install.sh; do bash -n "$f" || { echo "SYNTAX: $f"; fail=1; }; done
for f in profile/airootfs/usr/local/lib/xlinos/*; do case "$f" in *.py|*xlinos-greeter|*xlinos-accounts) python3 -I -c "import ast,sys;ast.parse(open(sys.argv[1]).read())" "$f" || { echo "SYNTAX: $f"; fail=1; };; esac; done
sed "s|@POST_B64@|x|" profile/airootfs/usr/share/xlinos/archinstall-config.json.in | python3 -c 'import json,sys;json.load(sys.stdin)' || { echo "BAD archinstall json"; fail=1; }
python3 tests/test-login.py || fail=1
out="$(SCEN=tests/smoke/greeter.py timeout 60 python3 tests/smoke/gtk_stub.py profile/airootfs/usr/local/lib/xlinos/xlinos-greeter Greeter 2>&1)"
grep -q "scenario ok" <<<"$out" && echo "PASS greeter screens" || { echo "FAIL greeter screens"; echo "$out" | tail -8; fail=1; }
if [[ $EUID -eq 0 ]] && command -v unshare >/dev/null; then
  S="$(mktemp -d)"; cp -a /etc "$S/etc"
  sed -i -E '/^(ubuntu|xt[a-z]*):/d' "$S"/etc/passwd "$S"/etc/shadow "$S"/etc/group "$S"/etc/gshadow 2>/dev/null
  # no human users may exist in the private copy
  awk -F: '$3>=1000 && $3<60000 && $7 !~ /(nologin|false)$/ {print $1}' "$S/etc/passwd" | cut -d: -f1 | while read -r u; do sed -i "/^$u:/d" "$S"/etc/passwd "$S"/etc/shadow; done
  unshare -m bash -c "mount --bind '$S/etc' /etc && bash tests/test-accounts.sh" || fail=1
else echo "skip: account tests need root and unshare"; fi
[[ $fail -eq 0 ]] && echo "ALL TESTS PASSED" || { echo "TESTS FAILED"; exit 1; }
