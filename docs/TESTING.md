# Testing XlinOS 0.1

## Test report (2026-11-15)

| Check | Result |
|---|---|
| Profile validation (`build-iso.sh --check`): files present, profile variables, packages, no graphical packages, symlinks | **Verified** |
| Shell scripts pass `bash -n` | **Verified** |
| ISO builds | **Not tested** (no Arch tools in the authoring environment) |
| ISO boots in a VM (BIOS and UEFI) | **Not tested** |
| Kernel loads, systemd reaches `multi-user.target` | **Not tested** |
| First-boot user creation and terminal login | **Not tested** |
| Networking (DHCP, DNS, Wi-Fi) | **Not tested** |
| System identifies itself as XlinOS | **Not tested** (configured in `os-release`, `issue`, `motd`, `hostname`) |
| No graphical session starts | **Not tested** (no graphical packages are installed) |

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
