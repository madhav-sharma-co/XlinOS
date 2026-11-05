# XlinOS

**An Arch Linux based distribution with the [Xlin-soft](https://github.com/madhav-sharma-co/XLIN-Soft) desktop.**
Boot the live ISO, try the calm, clean Xlin-soft desktop, and install it to a disk.

> **Status: 0.1 alpha.** The ISO build and the installer are new and have not been tested on many machines.
> Try it in a virtual machine first, and please report anything that breaks as a GitHub issue.

## What it is

| Part | What it does |
|------|--------------|
| Live ISO | Built with `archiso`. Boots straight into the Xlin-soft desktop (Hyprland) as a live user |
| Installer | `sudo xlinos-install` (also "Install XlinOS" in the Launcher) runs `archinstall` with XlinOS settings, then sets up Xlin-soft for your user |
| Xlin-soft | Kept in `/opt/xlin-soft` and set up for each user on first login |
| Branding | The XlinOS name in `/etc/os-release`, the login message and the installer |

XlinOS is Arch Linux with a different default desktop. Updates come from the normal Arch repositories (`pacman -Syu`),
and `xlin update` updates Xlin-soft.

## Build the ISO

You need an Arch Linux machine (or an Arch container) and root:

    sudo pacman -S --needed archiso git base-devel
    sudo ./build.sh                 # the ISO is written to ./out/
    sudo ./build.sh --aur          # also build AUR packages into a local repo (not needed by default)

Build with a given Xlin-soft tag or branch (default `main`): `sudo XLIN_SOFT_REF=v0.1.1 ./build.sh`

GitHub can build it for you: see [`.github/workflows/build-iso.yml`](.github/workflows/build-iso.yml).

## Try it

    ./scripts/test-qemu.sh out/xlinos-*.iso            # needs qemu
    ./scripts/test-qemu.sh out/xlinos-*.iso --uefi     # UEFI boot (needs edk2-ovmf)

More in [docs/TESTING.md](docs/TESTING.md). What is planned is in [docs/ROADMAP.md](docs/ROADMAP.md).

## Layout

    build.sh              builds the ISO (starts from archiso's own "releng" profile, then adds XlinOS)
    profile/              what XlinOS adds: package list, live user, autologin, installer, branding
    scripts/              build helpers (AUR packages, QEMU test)
    docs/                 testing and roadmap

## Names and licences

XlinOS is built on Arch Linux. "Arch Linux" and its logo belong to Arch Linux; XlinOS does not use them as its own
brand. XlinOS and Xlin-soft are MIT licensed (see [LICENSE](LICENSE)); the packages in the ISO keep their own licences.
