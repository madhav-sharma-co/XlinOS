# XlinOS

**A clean, professional, lightweight, smooth, fast and useful operating system.**
Start it from a USB stick, try it live, and install it on your computer.

> **Status: 0.1 alpha.** New and not yet tested on many machines. Try it in a virtual machine first and report anything
> that breaks as a GitHub issue.

## What you get

| Part | What it does |
|------|--------------|
| Desktop | Its own look: status bar, run bar, launcher, quick settings, lock screen, floating windows with snapping |
| Apps | Terminal, Files, Store, Settings, Notes, Calculator, Photos, Media: all made for XlinOS |
| Installer | A graphical installer: choose a disk, confirm, wait. You create your user on the first start |
| Updates | Settings > About > Update System brings the newest XlinOS and system updates |

## Build the ISO

The ISO is built on a Linux machine (or container) with root. GitHub builds it for you too:
see [`.github/workflows/build-iso.yml`](.github/workflows/build-iso.yml). Locally: `sudo ./build.sh` (the ISO is written to `./out/`).

## Try it

    ./scripts/test-qemu.sh out/xlinos-*.iso            # needs qemu
    ./scripts/test-qemu.sh out/xlinos-*.iso --uefi     # UEFI boot (needs edk2-ovmf)

More in [docs/TESTING.md](docs/TESTING.md). What is planned is in [docs/ROADMAP.md](docs/ROADMAP.md).

## Layout

    build.sh              builds the ISO
    profile/              what XlinOS is made of: package list, desktop, apps, installer, branding
    scripts/              build helpers and tests
    docs/                 design, testing and roadmap

## Licence

XlinOS is MIT licensed (see [LICENSE](LICENSE)); the packages in the ISO keep their own licences.
