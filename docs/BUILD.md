# Building XlinOS

## Requirements

An Arch Linux machine (or Arch container) with about 10 GB free disk space and root access via `sudo`:

    sudo pacman -S archiso mtools libisoburn squashfs-tools

## Build

    ./scripts/build-iso.sh

What it does: validates the profile, checks tools, runs `mkarchiso` with work files in `build/work`, writes the ISO to `out/`, then runs `scripts/verify-iso.sh`.

Validate only (works on any Linux, no Arch tools needed):

    ./scripts/build-iso.sh --check

Clean generated files (only `build/` and `out/` inside this repo are touched):

    ./scripts/clean.sh

## Building without Arch (Docker or Podman)

    docker run --rm --privileged -v "$PWD":/xlinos -w /xlinos archlinux:latest bash -c \
      "pacman -Syu --noconfirm archiso mtools libisoburn squashfs-tools git && ./scripts/build-iso.sh"

`--privileged` is required because mkarchiso mounts filesystems inside the container.

## Reproducibility

- `SOURCE_DATE_EPOCH` is set to the latest commit time (override by exporting it).
- Packages come from the build host's pacman mirrors. For a pinned build, point `/etc/pacman.d/mirrorlist` at an Arch Linux Archive snapshot, for example `Server = https://archive.archlinux.org/repos/2026/11/01/$repo/os/$arch`, and record the date in the release notes.
