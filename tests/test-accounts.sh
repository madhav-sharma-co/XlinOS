#!/usr/bin/env bash
# Tests the account helper with real useradd/userdel. Must run as root, in a throw-away container or VM.
set -u
H="$(cd "$(dirname "$0")/.." && pwd)/profile/airootfs/usr/local/lib/xlinos/xlinos-accounts"
[[ $EUID -eq 0 ]] || { echo "run as root in a disposable environment"; exit 2; }
getent group wheel >/dev/null || groupadd wheel
fail=0
LAST=''
run() { LAST="$(printf '%s' "$1" | python3 "$H")"; printf '%s' "$LAST"; }
ok()  { LAST="$(run "$1")"; printf '%s' "$LAST" | python3 -c 'import json,sys; d=json.load(sys.stdin); sys.exit(0 if d["ok"] else 1)'; }
err() { LAST="$(run "$1")"; printf '%s' "$LAST" | python3 -c 'import json,sys; d=json.load(sys.stdin); sys.exit(0 if (not d["ok"] and d["error"]==sys.argv[1]) else 1)' "$2"; }
t()   { if "$@"; then echo "PASS $T"; else echo "FAIL $T"; echo "     last answer: $LAST"; fail=1; fi; }
cleanup() { for u in xtadm xtstd xtthree; do userdel -r "$u" 2>/dev/null; done; }
cleanup
# the helper asks pgrep whether a user is logged in; a real process on this machine may own the test user's new id,
# so the tests use a stand-in pgrep: "nobody is logged in" (and a second one that says "yes" for one test)
SHIM="$(mktemp -d)"; printf '#!/bin/sh\nexit 1\n' >"$SHIM/pgrep"; printf '#!/bin/sh\nexit 0\n' >"$SHIM/pgrep-yes"; chmod +x "$SHIM"/pgrep*
export PATH="$SHIM:$PATH"
# precondition: no other human users, otherwise the first-user rule cannot be tested
n=$(python3 -c 'import pwd;print(sum(1 for p in pwd.getpwall() if 1000<=p.pw_uid<60000 and not p.pw_shell.endswith(("nologin","false"))))')
[[ $n -eq 0 ]] || { echo "SKIP: this system already has $n human user(s)"; exit 0; }

T="first user needs no auth, becomes admin";            t ok '{"cmd":"create","name":"xtadm","fullname":"Test Admin","password":"pass1234"}'
T="first user is in wheel";                              t bash -c 'id -nG xtadm | grep -qw wheel'
T="bad name rejected";                                   t err '{"cmd":"create","name":"Bad Name","password":"pass1234","auth":{"user":"xtadm","password":"pass1234"}}' bad_name
T="create without auth fails";                           t err '{"cmd":"create","name":"xtstd","password":"pass1234"}' auth_failed
T="create with wrong admin password fails";              t err '{"cmd":"create","name":"xtstd","password":"pass1234","auth":{"user":"xtadm","password":"nope"}}' auth_failed
T="short password rejected";                             t err '{"cmd":"create","name":"xtstd","password":"ab","auth":{"user":"xtadm","password":"pass1234"}}' bad_password
T="create standard user with admin password";            t ok '{"cmd":"create","name":"xtstd","fullname":"Test Std","password":"std-pass","auth":{"user":"xtadm","password":"pass1234"}}'
T="standard user is not in wheel";                       t bash -c '! id -nG xtstd | grep -qw wheel'
T="duplicate name rejected";                             t err '{"cmd":"create","name":"xtstd","password":"pass1234","auth":{"user":"xtadm","password":"pass1234"}}' exists
T="standard user cannot create users";                   t err '{"cmd":"create","name":"xtthree","password":"pass1234","auth":{"user":"xtstd","password":"std-pass"}}' not_admin
T="list shows both";                                     t bash -c "printf '{\"cmd\":\"list\"}' | python3 '$H' | grep -q xtstd"
T="delete needs a password";                             t err '{"cmd":"delete","name":"xtstd"}' auth_failed
T="another standard user's password is not enough";      t err '{"cmd":"delete","name":"xtadm","auth":{"user":"xtstd","password":"std-pass"}}' not_admin
T="last admin cannot be deleted";                        t err '{"cmd":"delete","name":"xtadm","auth":{"user":"xtadm","password":"pass1234"}}' last_admin
T="a logged-in user cannot be deleted"; t bash -c "cp $SHIM/pgrep-yes $SHIM/pgrep.yes; PATH=\"$SHIM/yes:\$PATH\"; mkdir -p $SHIM/yes; cp $SHIM/pgrep-yes $SHIM/yes/pgrep; printf '%s' '{\"cmd\":\"delete\",\"name\":\"xtstd\",\"auth\":{\"user\":\"xtstd\",\"password\":\"std-pass\"}}' | python3 '$H' | grep -q logged_in"
T="user can delete self with own password (keeps files)"; t ok '{"cmd":"delete","name":"xtstd","auth":{"user":"xtstd","password":"std-pass"}}'
T="files were kept";                                     t test -d /home/xtstd
T="admin can delete another user and purge files";       t bash -c "useradd -m xtthree && echo 'xtthree:abcd1234' | chpasswd && printf '%s' '{\"cmd\":\"delete\",\"name\":\"xtthree\",\"purge\":true,\"auth\":{\"user\":\"xtadm\",\"password\":\"pass1234\"}}' | python3 '$H' | grep -q '\"ok\": true' && [ ! -d /home/xtthree ]"
cleanup; rm -rf /home/xtstd
[[ $fail -eq 0 ]] && echo "all account tests passed" || { echo "account tests FAILED"; exit 1; }
