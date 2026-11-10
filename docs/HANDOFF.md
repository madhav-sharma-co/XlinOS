# XlinOS handoff (for a new engineer or AI assistant)

XlinOS is a separate, real OS on an Arch/Linux base. Hyprland runs hidden under XlinOS's own shell. Vision: "A clean, professional, lightweight, smooth, fast and useful OS, compatible with any device". A later "XlinOS (advance)" edition is planned. Repo: github.com/madhav-sharma-co/XlinOS (branch main). Do NOT touch the separate Xlin-soft project.

## Rules from the owner
- No Arch or Hyprland branding or wording anywhere a user can see it (installer, login, boot, Store, Quickshell output).
- Own apps only for basics. The terminal app is called **Quickshell**; prompt is `user@xlin`; hostname `xlin`.
- Top bar = "status bar", dock = "run bar". Must not look like ML4W or other configs.
- Installer: archinstall-style settings menu in XlinOS's own look; the user account is created at first start.
- Work in big steps, show screenshots, no more videos. Ask for real decisions.
- Commit trailers: `Co-Authored-By: <assistant>` and the session link if the tool gives one. Never put the owner's email into the repo.

## Layout
- `profile/` archiso profile. `packages.extra` = packages added to releng. `airootfs/usr/local/lib/xlinos/` = all XlinOS apps (GTK4 + gtk4-layer-shell, Python): shell, launcher, quick, notify, overview, lock (GTK3), greeter (greetd+cage), settings, files, store, photos, calendar, media, terminal (Quickshell, VTE4), installer + `xlinos-install-run` (backend, root).
- `profile/airootfs/usr/share/xlinos/` configs: `hypr/hyprland.lua` (Hyprland 0.57 Lua), `archinstall-config.json.in`, `post-install.sh`, `quickshell.bashrc`.
- `scripts/` build and CI helpers, `.github/workflows/` build-iso.yml (builds the ISO), archinstall-test.yml (QEMU install + first boot, screenshots to `ci-shots-*` branches), etc.
- `docs/` DESIGN, BOOT, LOGIN, SYSTEM, ROADMAP, TESTING, BLUEPRINT.

## Build and test loop
1. Push to main, then `gh workflow run build-iso.yml --ref main` and wait.
2. `gh workflow run archinstall-test.yml --ref main -f run_id=<ISO build run id>` (add `-f dual=1` for the dual-boot test). Fetch results: `git fetch origin ci-shots-archinstall && git archive FETCH_HEAD | tar -x -C dir`.
3. ISO artifacts cannot be downloaded from the AI sandbox; the owner downloads them from the Actions page while logged in to GitHub. Publishing the ISO as a public release was not allowed without the owner saying yes.

## Installer
- GUI: `xlinos-installer` (settings menu: language, keyboard, time zone, install target, file system, computer name). Writes an options JSON and calls `xlinos-install-run <disk-or-partition> <opts.json>`.
- Whole-disk mode uses archinstall with `pre_mounted_config` + systemd-boot. Proven end to end in CI and on the owner's real laptop.
- Partition (dual-boot) mode: pacstrap + GRUB `XlinOS` entry, shares the existing EFI partition. Host files survive in CI, but the post-install step (branding, greetd) did not apply in the last dual-boot test and the cause was not found yet (see `/var/log/xlinos-post.log` in the target and CI `dual-check.txt`).
- Loopback/ISO-on-same-disk installs need `copytoram=y`; the backend now releases the loop mount and refuses without it.

## Known issues / roadmap
- Real-laptop issue seen: "Could not format the disk" on the first try (kernel kept old partition table); the owner got around it. Make `xlinos-install-run` call `partprobe`/`udevadm settle` after partitioning and retry mkfs, and log more clearly.
- Live ISO: NetworkManager now starts at boot (new build); older ISOs need iwctl or USB tethering.
- Unverified: real mouse drag/resize and snap restore, password unlock, Store install/remove, `xlinos-update apply`, btrfs path, overview card clicks.
- Remaining visible leaks: package names (hyprland etc.) in Store/Quickshell output; live ISO red systemd line.
- To do: status-bar menus (Wi-Fi, Bluetooth, volume), Plymouth boot animation, Mail and Camera apps, own package repo, slimmer ISO, XlinOS Advanced edition, update ROADMAP.

## First things to do in a new session
Clone the repo, read this file and `docs/ROADMAP.md`, run the build + install tests, then ask the owner what to do next.
