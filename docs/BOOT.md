# How XlinOS boots (Layer 1)

## From power button to desktop
1. **Firmware** (UEFI on new PCs, BIOS on old ones) is built into the motherboard. It tests the hardware and looks for something to boot.
2. **Bootloader** is the first software we control. On the XlinOS ISO it is syslinux (BIOS) or GRUB / systemd-boot (UEFI). It shows the menu and loads the kernel and a small starter filesystem (initramfs) into memory.
3. **Kernel** (Linux) wakes up the hardware: CPU, memory, disks, graphics, network.
4. **initramfs** finds the real system (on the ISO, the compressed XlinOS image) and mounts it.
5. **systemd** starts the services: networking, sound, Bluetooth, login.
6. **Login and session**: `xlinos-session` starts the Xlin-soft desktop.

Layer 1 is steps 1 to 2. Everything below the bootloader is Arch's Linux, which we use as it is.

## What XlinOS changes in Layer 1
| Change | Where | Why |
|---|---|---|
| Menus say XlinOS ("XlinOS live and installer") | `scripts/brand-boot.sh` | identity; no Arch branding |
| XlinOS splash picture on the BIOS menu | `scripts/make-splash.py` > `syslinux/splash.png` | first impression |
| Quiet kernel start (`quiet loglevel=3 ...`) | `scripts/brand-boot.sh` | no wall of text; slightly faster |
| Both BIOS and UEFI entries | inherited from archiso `releng` | works on old and new PCs |

## Not done yet (and why)
- **Graphical boot animation (Plymouth):** it must be added to the initramfs, and a mistake there stops the system from booting. We add it after the first ISO boots in a VM, so we can test it safely.
- **GRUB and systemd-boot themes:** the UEFI menu is text-only for now. Boot-time themes come with the Calamares installer, which sets up the installed bootloader.
- **Boot-time measurement:** needs a running system (`systemd-analyze`).

## How to check it (after the first CI build)
Boot the ISO in QEMU in BIOS mode and in UEFI mode. You should see: the XlinOS menu, the splash picture (BIOS), and only a few quiet lines before the desktop. Send a screenshot of each.
