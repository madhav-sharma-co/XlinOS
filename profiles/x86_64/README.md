<!-- SPDX-FileCopyrightText: 2026 Axion Co. -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# x86_64 platform profile

Initial bring-up target: x86_64 UEFI virtual machines using QEMU + OVMF.

## Target assumptions

- 64-bit x86 CPU supported by the selected Xlin kernel configuration.
- UEFI firmware; legacy BIOS is outside the first milestone.
- Virtio devices where practical for virtual storage and networking.
- Serial console enabled for deterministic CI diagnostics.
- Virtual disk image assembled by the XlinOS image pipeline.

CPU minimum, RAM/disk minimums, partition layout, filesystem, bootloader, kernel command line, graphics device and supported QEMU versions must be decided and tested before the first image release. A successful QEMU boot does not establish physical PC compatibility.
