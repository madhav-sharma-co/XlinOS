<!-- SPDX-FileCopyrightText: 2026 Axion Co. -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# XlinOS architecture

## System boundary

XlinOS is the operating-system integration project. Xlin owns kernel source management, kernel configuration, patches, compilation and kernel-level validation. XlinOS owns root-filesystem composition, OS configuration, image assembly, installation and end-to-end OS tests.

```text
UEFI firmware (OVMF for the first VM target)
        |
        v
Bootloader / boot entry
        |
        v
Xlin kernel + initramfs
        |
        v
PID 1 and early userspace
        |
        v
XlinOS base userspace
        +---- system services
        +---- networking
        +---- package and update management
        +---- system configuration
        +---- later: graphics session and desktop
```

This is the intended boot path. The Xlin repository currently documents a separate QEMU + OVMF kernel test that reaches a serial shell using a minimal test initramfs. That is not yet an XlinOS boot.

## First supported target

The first bring-up target is x86_64 in QEMU with OVMF UEFI firmware. The first acceptance interface is a serial console. Physical hardware, Secure Boot, graphics acceleration, laptops, ARM and other architectures are outside the first milestone.

## Kernel integration contract

XlinOS must consume a published or otherwise immutable Xlin kernel artifact. The integration record must capture:

- Xlin release or exact source commit.
- Linux upstream version and source commit inherited from Xlin.
- Kernel configuration/profile identifier.
- Artifact filename, architecture and cryptographic checksum.
- Required command-line parameters and initramfs expectations.
- Build provenance and licence notices.

Do not track a moving branch as a production kernel dependency. Until Xlin publishes a versioned artifact, local integration must be marked experimental and pin an exact commit.

## Userspace decision

The first userspace and init system are not yet frozen. systemd is the proposed init target, not an implemented dependency. Before implementation, record a decision covering base distribution and package source, package signing policy, init system, libc, filesystem layout, update/rollback/recovery strategy and licence obligations.

XlinOS is a downstream Linux-kernel-based operating system, not a Linux-independent kernel or userspace.

## Image pipeline

1. Resolve and verify pinned source/package inputs.
2. Obtain a compatible Xlin kernel artifact.
3. Assemble a minimal root filesystem.
4. Build an initramfs with required early-boot components.
5. Assemble a UEFI-bootable disk image.
6. Boot it in QEMU + OVMF.
7. Assert that the kernel reaches XlinOS userspace and PID 1 remains healthy.
8. Publish checksums, manifests, logs and build provenance.

Build steps must be repeatable and avoid privileged host modifications where practical.

## Security model

The initial VM is a development environment, not a hardened production platform. Before public release, define package-signature verification, update authenticity, default privilege policy, service exposure, filesystem permissions, secrets handling, vulnerability response and recovery. Never ship development credentials or disable verification to make a build pass.

## Non-goals for first boot

A custom kernel rewrite, custom bootloader, graphical desktop, app store, physical-hardware compatibility claims and Secure Boot certification are not first-boot goals.
