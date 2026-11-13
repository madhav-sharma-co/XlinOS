# XlinOS installer

The live medium starts straight into the installer: it is the whole screen (own compositor settings in
`usr/share/xlinos/hypr/installer.lua`, selected by `xlinos-session` when `/run/archiso` exists). There is no bar, run bar,
wallpaper, desktop icons or window frame, and none of the desktop key bindings. The installed desktop is not changed.

## Screens
0. Loading (logo, spinner) - reads disks, keyboards and network, then moves on by itself.
1. Welcome - language (used for the installer texts where translated: English, Hindi, German, French, Spanish; legal texts stay English).
2. About XlinOS, installation agreement (draft placeholder + the repository licence, must be accepted), privacy and optional diagnostics (opt-in, off by default).
3. Language, region, keyboard - language, country, time zone (separate), keyboard layout + variant, a test field. The layout is applied to the running installer session.
4. Internet, disk and method - Wi-Fi / cable status, scan, connect with password, disconnect; disks with model, size, table, filesystems, other systems found, free space, flags; the three methods.
5. Review - every choice with Edit buttons, data-loss warning and a required tick box. "Install" asks once more in a dialog.
6. "Thanks for Choosing XlinOS" - real percentage, stage, current task, optional log, Cancel. Ends with "XlinOS is Ready!" and Restart.

Accounts are not created here: the first user is created on the first start (greeter).

## Methods
- **Alongside**: a new partition in free (unallocated) space of a GPT disk with an existing EFI partition. Nothing existing is changed; shrinking a partition of another system is not done by the installer.
- **Erase disk**: partitions the whole disk (512 MB EFI + system).
- **Manual (advanced)**: one existing unused partition is formatted and used, with the shared EFI partition. No partition editor is included.

## Safety (checked again by the engine, never only by the screen)
`xlinos_disks.py` finds the physical parent disk of any partition and refuses: the medium XlinOS runs from (including a loop-mounted ISO file and
disks labelled as install media), read-only devices, mounted or swap/RAID/LVM partitions, a too small target, an EFI partition as system partition,
an EFI partition on another disk, unknown devices, and a non-UEFI start. `xlinos-install-run` calls it before writing anything.

## Engine protocol
`xlinos-install-run TARGET options.json` prints `STEP <text>`, `PCT <n>`, `MODIFIED` (the disk has been changed), then `DONE`, `FAIL <reason>` or `CANCELLED clean|dirty`.
`PCT` comes from the package counters of the real install (pacman `(i/N)`), not from a timer. `xlinos-install-cancel` stops the whole process group;
partitioning and bootloader steps are marked critical and a cancel then waits until the step ends.

## Tests
- `tests/test-installer.py` - disk rules on a fake layout, progress parser.
- `tests/smoke/installer.py` - the screen flow (GTK stubbed).
- VM test (`scripts/ci/scenario.sh`) - real screenshots of the screens and a refusal of the VM's own disk.
- Installer test with `gui=1` (`scripts/ci/ai-gui.sh`) - drives the real installer on the ISO: review, start, cancel part way, install again.
- Boot test - the ISO boots into the full-screen installer.

## Not done / not tested
Windows and other-Linux dual boot on real hardware, real hardware in general, macOS (not supported), shrinking existing partitions, a partition editor, BIOS boot, offline install.
