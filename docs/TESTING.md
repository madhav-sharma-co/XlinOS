# Testing XlinOS 0.1

## Test report (2026-11-15)

Automated in GitHub Actions (workflow "Build ISO"), run 994746d:

| Check | Result |
|---|---|
| Profile validation (`build-iso.sh --check`) | **Verified** |
| ISO builds with `mkarchiso` (873 MB), valid ISO 9660, `XLINOS_0_1` label, BIOS and UEFI boot entries present | **Verified** (CI) |
| Kernel and initramfs from the ISO boot in QEMU (KVM) and find the root image | **Verified** (CI, serial log) |
| System identifies itself as XlinOS (`Welcome to XlinOS 0.1`, hostname `xlin`) | **Verified** (CI) |
| systemd reaches `multi-user.target`; no kernel panic or emergency mode | **Verified** (CI) |
| No graphical target reached | **Verified** (CI); no graphical packages are installed |
| syslinux (BIOS) and systemd-boot (UEFI) menus start the system | **Not tested** (CI boots the kernel directly with `-kernel`) |
| First-boot user creation and terminal login on tty1 | **Not tested** |
| Networking (DHCP, DNS, Wi-Fi) and time sync | **Not tested** |
| `systemctl --failed` and `journalctl -p err` reviewed | **Not tested** |
| Real hardware | **Not tested** |

Not claimed as complete until the untested rows are checked by a person (checklist below).

## How to verify (milestone checklist)

1. `./scripts/build-iso.sh` finishes and `scripts/verify-iso.sh` prints `VERIFIED`.
2. `./scripts/test-qemu.sh` and `./scripts/test-qemu.sh --uefi` both show the XlinOS boot menu.
3. In the VM, after boot: the first-boot screen asks for a username and password.
4. Log in. Run:
   - `cat /etc/os-release` shows `NAME="XlinOS"`
   - `hostnamectl` shows `xlin`
   - `systemctl get-default` prints `multi-user.target`
   - `systemctl --failed` lists nothing unexplained
   - `journalctl -b -p err` has no unexplained errors
   - `ip a`, `ping -c 3 1.1.1.1`, `ping -c 3 archlinux.org` (QEMU user networking)
   - `timedatectl` shows the clock synchronised
   - `sudo whoami` prints `root`; `su -` as root login is not possible (root is locked)
   - `pgrep -a Xorg` and `pgrep -a sway` print nothing
5. Wi-Fi on real hardware: `iwctl`, then `station wlan0 connect <SSID>`.

Record results here (date, ISO sha256, hardware or QEMU) before calling 0.1 complete.
