# Layers 2-4: kernel, services, base system

| Layer | What it is | XlinOS choice |
|---|---|---|
| 2 Kernel | Linux talks to the hardware | `linux` from Arch, unchanged (kernel choice: see decisions) |
| 3 Services | systemd starts background programs | NetworkManager, bluetooth, power-profiles-daemon, fstrim.timer. Boot no longer waits for the network (`NetworkManager-wait-online` off) |
| 4 Base | packages and pacman | Arch repos only. No `base-devel` (compilers) by default. The dock now comes from the official repo, so no AUR build is needed |

## Speed and memory defaults
- **zram swap** (compressed RAM, up to half of RAM, max 4 GB): smoother on small-memory devices, no disk wear.
- **sysctl** `vm.swappiness=100`, `vm.page-cluster=0`: tuned for zram.
- **journal** capped at 100 MB.
- **fstrim.timer**: keeps SSDs fast.

Files: `profile/airootfs/etc/` (live ISO) and `profile/airootfs/usr/share/xlinos/post-install.sh` (installed system).

## Decisions (CEO, 2026-11-05)
1. **Kernel:** `linux` only. Smallest and newest.
2. **Browser:** not bundled. `xlinos-browser` ("Get a Web Browser") installs Firefox, Chromium or Epiphany on request. Keeps the ISO small.
3. **Disk format:** `ext4`. Simple and fast. Note: with archinstall the filesystem is picked in its menu (choose ext4); Calamares will preset it later.
