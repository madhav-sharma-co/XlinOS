# Testing the ISO

The ISO is built in GitHub Actions (Actions > Build ISO > Run workflow) or on an Arch machine with `./build.sh`.
Download the `xlinos-iso` artifact, then boot it in a VM:

    ./scripts/test-qemu.sh out/xlinos-*.iso

Check, in order:
1. The boot menu says XlinOS and the live session logs in as `xlin` and starts the desktop.
2. Wi-Fi/Ethernet, sound and Bluetooth menus work.
3. `sudo xlinos-install` installs to the VM disk (needs internet); reboot, log in, the desktop starts.
4. Try UEFI (`-bios OVMF`) and BIOS.

Report problems as issues with the step number and what you saw.
