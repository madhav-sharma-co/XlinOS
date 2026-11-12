#!/usr/bin/env bash
# Runs INSIDE the live ISO (started by ci-archinstall.py with XL_GUI=1): drives the real full-screen installer through its test hook:
# review screen, start, CANCEL part way (must report it honestly), start again, wait for "XlinOS is Ready!". Then powers off.
exec > >(tee /r/out/install.log) 2>&1
OUT=/r/out; XI=/tmp/xi; mkdir -p $XI; chmod 777 $XI
UID_=$(id -u xlin); export XDG_RUNTIME_DIR=/run/user/$UID_
WL="$(basename "$(ls $XDG_RUNTIME_DIR/wayland-[0-9] | head -1)")"
SIG="$(ls -t $XDG_RUNTIME_DIR/hypr | head -1)"
echo "wayland=$WL sig=$SIG"; ps aux | grep -c "[x]linos-installer"
runuser -u xlin -- env XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR WAYLAND_DISPLAY=$WL HYPRLAND_INSTANCE_SIGNATURE=$SIG XLINOS_INSTALLER_TEST=$XI \
  /usr/local/lib/xlinos/xlinos-installer >$OUT/gui-app.log 2>&1 &
ic() { printf '%s\n' "$@" >$XI/cmd; chmod 666 $XI/cmd; sleep 2; }
st() { ic state; cat $XI/state.json; echo; }
ish() { ic "shot $XI/$1.png"; cp $XI/$1.png $OUT/ 2>/dev/null; }   # the app (user xlin) writes in /tmp, root copies to the shared folder
for _ in $(seq 1 60); do grep -q '"page"' $XI/state.json 2>/dev/null && break; ic state; done
sleep 3; st
ic "lang de_DE.UTF-8"; ish g1-welcome-german; ic "lang en_US.UTF-8"
ic "goto 2"; ic next; echo "agreement blocks:"; st; ic agree; ic next; ic "kb us"; ic next; sleep 3; ish g2-disk
ic "disk /dev/vda"; ic "method erase"; ic next; echo "review without loss box:"; st
ic loss; ic next; ic "goto 5"; ish g3-review; st
ic start; sleep 2; ish g4-installing-0
# wait for real progress, then cancel
for _ in $(seq 1 120); do sleep 5; ic state; p=$(python3 -c "import json;print(json.load(open('$XI/state.json'))['pct'].rstrip('%'))"); echo "pct=$p"; [ "${p:-0}" -ge 25 ] && break; done
ish g5-installing-25; st >>$OUT/gui-progress.txt
ic cancel; for _ in $(seq 1 60); do sleep 5; ic state; python3 -c "import json;print(json.load(open('$XI/state.json'))['title'])" | grep -q "cancelled" && break; done
ish g6-cancelled; echo "after cancel:"; st | tee -a $OUT/gui-progress.txt
mount | grep -c " /mnt" | tee -a $OUT/gui-progress.txt
# start again from the cancelled state: a full install
ic "goto 5"; ic loss; ic start
for _ in $(seq 1 240); do sleep 10; ic state; t=$(python3 -c "import json;d=json.load(open('$XI/state.json'));print(d['title'],'|',d['pct'],'|',d['stage'])"); echo "$t" >>$OUT/gui-progress.txt
  case "$t" in "XlinOS is Ready!"*|"The installation did not finish"*) break;; esac; done
ish g7-final; st | tee $OUT/gui-final.json
cp /var/log/xlinos-install.log $OUT/xlinos-install.log; tail -c 2000 /var/log/xlinos-install.log | tr '\r' '\n' | tail -20
echo INSTALL-FINISHED > $OUT/done
poweroff
