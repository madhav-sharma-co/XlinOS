#!/usr/bin/env bash
# shellcheck disable=SC2034
# XlinOS archiso profile definition. Read by mkarchiso.

iso_name="xlinos"
iso_label="XLINOS_0_1"
iso_publisher="XlinOS <https://github.com/madhav-sharma-co/XlinOS>"
iso_application="XlinOS Live/Install ISO"
iso_version="0.1"
# Directory name inside the ISO (max 8 chars, a-z0-9). Internal only.
install_dir="xlinos"
buildmodes=('iso')
bootmodes=('bios.syslinux' 'uefi.systemd-boot')
arch="x86_64"
pacman_conf="pacman.conf"
airootfs_image_type="squashfs"
airootfs_image_tool_options=('-comp' 'xz' '-Xbcj' 'x86' '-b' '1M' '-Xdict-size' '1M')
bootstrap_tarball_compression=('zstd' '-c' '-T0' '--auto-threads=logical' '--long' '-19')
file_permissions=(
  ["/etc/shadow"]="0:0:400"
  ["/etc/sudoers.d/10-wheel"]="0:0:440"
  ["/usr/local/bin/xlin-firstboot"]="0:0:755"
  ["/usr/local/bin/xlin-login"]="0:0:755"
)
