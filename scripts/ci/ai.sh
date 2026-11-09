#!/usr/bin/env bash
# Runs INSIDE the live ISO (started by ci-archinstall.py): partitions /dev/vda, runs archinstall with the XlinOS config, powers off.
exec > >(tee /r/out/install.log) 2>&1
set -x
/usr/local/lib/xlinos/xlinos-install-run /dev/vda; echo "INSTALLER EXIT $?"
cat /var/log/xlinos-install.log
echo INSTALL-FINISHED > /r/out/done
poweroff
