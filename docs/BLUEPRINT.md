# XlinOS Blueprint

## What XlinOS is
An Arch-based Linux distribution whose desktop is Xlin-soft (Hyprland). You boot a USB stick, try the desktop live, and install it to a disk. It is a rolling release that uses Arch's packages and Arch's package manager.

## Vision
**XlinOS: a clean, professional, lightweight, smooth, fast and useful OS that works on any device.**

Editions:
- **XlinOS**: the main edition for everyone. Sensible defaults, graphical installer, few choices to make.
- **XlinOS Advanced** (later): for advanced users, with developer tools, more control and less hand-holding. Scope to be decided after XlinOS 1.0.

What "any device" means, in steps:
1. x86_64 PCs and laptops, UEFI and BIOS (the first release target)
2. Virtual machines (QEMU/KVM, VirtualBox, VMware)
3. Later and only if there is demand: ARM boards and tablets (needs an ARM Arch port, so a separate build)

## Quality goals (measured, not just claimed)
- Lightweight: idle RAM under ~700 MB on the live desktop; ISO as small as possible (drop unneeded packages)
- Fast: boot to desktop in under 20 s on an SSD
- Smooth: no frame drops in the desktop animations on integrated graphics
- Clean: one look, one set of apps, no leftover Arch branding

## Principles
1. **Reuse, don't rebuild.** Arch provides kernel, packages and tools. XlinOS adds the desktop, installer, branding and defaults.
2. **Xlin-soft stays its own project.** XlinOS pulls it in; Xlin-soft still installs on plain Arch.
3. **Simple first.** Ship something that boots, then replace parts (installer, repo, login screen) one at a time.
4. **Honest status.** Every release says what is tested and what is not.

## Layers
| Layer | Source | Notes |
|---|---|---|
| Kernel, firmware, base | Arch (`linux`, `base`) | unchanged |
| Packages | Arch repos + a small AUR build (`nwg-dock-hyprland`) | later: own repo `xlinos-repo` |
| Desktop | Xlin-soft in `/opt/xlin-soft`, set up per user on first login | later: a `xlin-soft` package |
| Session start | `xlinos-session` (tty1 autologin on live, tty1 login on installs) | later: greetd/SDDM |
| Installer | `xlinos-install` = archinstall + preset | later: Calamares |
| Identity | `/etc/os-release` (ID=xlinos, ID_LIKE=arch), issue, motd, boot menu | keeps `/etc/arch-release` |
| ISO build | archiso `releng` profile + overlay, `build.sh`, GitHub Actions | |

## Repo map
- `build.sh`: builds the ISO. `scripts/`: AUR build, QEMU test.
- `profile/packages.extra`: extra packages. `profile/airootfs/`: files copied into the system.
- `docs/`: this blueprint, roadmap, testing.

## Install flow (today)
Boot ISO > live desktop (user `xlin`) > `sudo xlinos-install` > archinstall (disk, user, password) > post-install script (name, Xlin-soft source, session starter) > reboot > first login sets up Xlin-soft for that user.

## Known limits (alpha)
Untested on real hardware; needs internet to install; no Secure Boot; archinstall menus are text-based; Xlin-soft is fetched from GitHub at install time.

## Out of scope for now
Own kernel, own package manager, non-Arch base, ARM.
