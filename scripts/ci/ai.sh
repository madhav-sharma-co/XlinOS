#!/usr/bin/env bash
# Runs INSIDE the live ISO (started by ci-archinstall.py): partitions /dev/vda, runs archinstall with the XlinOS config, powers off.
exec > >(tee /r/out/install.log) 2>&1
set -x
sgdisk -Z /dev/vda; sgdisk -n1:0:+512M -t1:ef00 -n2:0:0 -t2:8300 /dev/vda
mkfs.fat -F32 /dev/vda1; mkfs.ext4 -qF /dev/vda2
mount /dev/vda2 /mnt; mkdir -p /mnt/boot; mount /dev/vda1 /mnt/boot
python3 - <<'PY'
import json
c = json.load(open("/usr/share/xlinos/archinstall-config.json"))
c["bootloader"] = "systemd-boot"
c["disk_config"] = {"config_type": "pre_mounted_config", "mountpoint": "/mnt"}
json.dump(c, open("/tmp/c.json", "w"), indent=1)
PY
ping -c1 -W3 archlinux.org || echo "NO NETWORK"
archinstall --config /tmp/c.json --silent; echo "ARCHINSTALL EXIT $?"
sync; umount -R /mnt || true
echo INSTALL-FINISHED > /r/out/done
poweroff
