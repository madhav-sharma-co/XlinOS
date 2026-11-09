#!/usr/bin/env bash
# Runs INSIDE the live ISO (started by ci-archinstall.py): partitions /dev/vda, runs archinstall with the XlinOS config, powers off.
exec > >(tee /r/out/install.log) 2>&1
set -x
if [ -f /r/out/dual ]; then
  echo '{"target":"partition","efi":"/dev/vda1","hostname":"xlin","fs":"ext4"}' >/tmp/o.json
  /usr/local/lib/xlinos/xlinos-install-run /dev/vda3 /tmp/o.json
  mkdir -p /m1 /m2; mount /dev/vda1 /m1; mount /dev/vda2 /m2
  ls /m1 /m1/EFI /m2 | tee /r/out/dual-check.txt
else
/usr/local/lib/xlinos/xlinos-install-run /dev/vda; fi; echo "INSTALLER EXIT $?"
cat /var/log/xlinos-install.log
echo INSTALL-FINISHED > /r/out/done
poweroff
