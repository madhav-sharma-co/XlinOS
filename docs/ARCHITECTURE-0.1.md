# XlinOS 0.1 Architecture (terminal-only Minimal Foundation)

## Foundation

| Part | Choice |
|---|---|
| Base | Arch Linux packages (internal foundation, not the public identity) |
| Kernel | Official `linux` package |
| ISO tool | Archiso (`mkarchiso`) |
| Init | systemd |
| Shell | Bash |
| Package manager | pacman |
| Networking | systemd-networkd (DHCP), systemd-resolved (DNS), iwd (Wi-Fi) |
| Time | systemd-timesyncd |
| Boot loaders | syslinux (BIOS), systemd-boot (UEFI) |
| Installed filesystem | ext4 recommended (tools for Btrfs and XFS are included) |

## Boot process

1. Firmware starts the XlinOS boot menu (syslinux on BIOS, systemd-boot on UEFI).
2. The loader starts the Linux kernel and the initramfs.
3. The archiso initramfs hooks find the ISO by its label (`XLINOS_0_1`) and mount the compressed root image into RAM overlay.
4. systemd starts and reaches `multi-user.target` (set as default; no graphical target exists).
5. `getty@tty1` starts `agetty` with the XlinOS login wrapper (`/usr/local/bin/xlin-login`). If `/var/lib/xlin/setup-done` does not exist, the wrapper runs `xlin-firstboot`, which creates the first user (in `wheel`) and asks for a password. It runs inside the getty, after `multi-user.target`, so boot never waits for input.
6. The wrapper then starts the normal login prompt; after login the user gets Bash.

## Configuration decisions

- **systemd-firstboot is masked and the time zone is UTC:** otherwise systemd's own "Initial Setup" prompt blocks the boot on the console (found by the CI boot test). Users set the time zone with `timedatectl`.
- **No `mkinitcpio` preset in `airootfs`:** a preset passing `-c /etc/mkinitcpio.conf` stops mkinitcpio from reading `/etc/mkinitcpio.conf.d/archiso.conf`, so the live hooks were silently missing. Same layout as upstream archiso.
- **ISO-only pacman hooks are removed after the build** (`zzzz99-remove-iso-hooks.hook`) so `pacstrap` on the live system does not run them.

- **No default login:** root's password is locked (`!*` in `/etc/shadow`). No password is stored in the image. This differs from the stock Arch ISO, which logs in as root automatically.
- **os-release via a pacman hook:** archiso copies `airootfs` into the build root before installing packages, so shipping `/usr/lib/os-release` there makes pacman abort (the `filesystem` package owns it). The XlinOS file lives in `/usr/share/xlinos/os-release` and `etc/pacman.d/hooks/10-xlinos-identity.hook` installs it over `/usr/lib/os-release` after `filesystem` is installed or upgraded. `/etc/os-release` is a symlink to it in Arch's `filesystem` package.
- **`ID_LIKE=arch`:** states honestly what the system is derived from, which also helps tools that detect the distribution family.
- **`install_dir=xlinos`:** the directory inside the ISO; internal only.
- **iso_label `XLINOS_0_1`:** fixed (not date-based) so builds are reproducible.
- **Network:** systemd-networkd and iwd instead of NetworkManager, because they are smaller and ship with or beside systemd; fewer packages for a terminal-only system.
- **Locale `C.UTF-8`:** works without generating locales; a locale chooser can come later.
- **`packages.x86_64`:** every group is explained inside the file.

## Not included on purpose (0.1)

Desktop environment, display server, graphical installer, app store, custom package manager. These are later milestones.
