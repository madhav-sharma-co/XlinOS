#!/bin/sh
# Runs as root in the test VM before the login manager: puts the repo's current XlinOS files in place and makes
# greetd start the test scenario (as user "t") instead of the login screen.
R=/mnt/repo
A=$R/profile/airootfs
id t >/dev/null 2>&1 || useradd -m -G video,input,render t 2>/dev/null || useradd -m t
cp -a $A/usr/local/lib/xlinos/. /usr/local/lib/xlinos/ 2>/dev/null
cp -a $A/usr/local/bin/. /usr/local/bin/ 2>/dev/null
cp -a $A/usr/share/xlinos/. /usr/share/xlinos/ 2>/dev/null
for f in $A/usr/share/applications/xlinos-*.desktop; do case $f in *xlinos-install.desktop) ;; *) cp $f /usr/share/applications/;; esac; done
cp $A/usr/share/xlinos/quickshell.bashrc /usr/share/xlinos/
cat >/etc/greetd/config.toml <<EOT
[terminal]
vt = 1
[default_session]
command = "$R/scripts/ci/vm-session.sh"
user = "t"
EOT
