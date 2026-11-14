#!/usr/bin/env bash
# Runs INSIDE the live ISO (started by ci-archinstall.py): partitions /dev/vda, runs archinstall with the XlinOS config, powers off.
exec > >(tee /r/out/install.log) 2>&1
echo "== live compositor log"; cat /run/user/*/xlinos-compositor.log 2>&1 | head -120
echo "== compositor env"; tr '\0' '\n' </proc/$(pgrep -x xlin-comp | head -1)/environ 2>&1 | grep -E "WLR|XLIN|MESA|LIBGL" 
echo "== gpu"; ls /dev/dri; lspci 2>/dev/null | grep -i vga
set -x
if [ -f /r/out/dual ]; then
  echo '{"target":"partition","efi":"/dev/vda1","hostname":"xlin","fs":"ext4"}' >/tmp/o.json
  /usr/local/lib/xlinos/xlinos-install-run /dev/vda3 /tmp/o.json
  mkdir -p /m1 /m2; mount /dev/vda1 /m1; mount /dev/vda2 /m2
  mkdir -p /m3; mount /dev/vda3 /m3; { ls /m1 /m1/EFI /m2; cat /m3/etc/issue; cat /m3/var/log/xlinos-post.log | tail -30; ls /m3/usr/local/lib/xlinos | head -5; } 2>&1 | tee /r/out/dual-check.txt
else
/usr/local/lib/xlinos/xlinos-install-run /dev/vda; fi; echo "INSTALLER EXIT $?"
cp /var/log/xlinos-install.log /r/out/xlinos-install.log; tail -c 3000 /var/log/xlinos-install.log | tr '\r' '\n' | tail -40
echo INSTALL-FINISHED > /r/out/done
poweroff
