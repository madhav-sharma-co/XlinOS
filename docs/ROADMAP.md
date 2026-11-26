<!-- SPDX-FileCopyrightText: 2026 Axion Co. -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# XlinOS roadmap

A milestone is complete only when its exit criteria are met and evidence is recorded.

## M0 — Repository foundation
Status: in progress.

- [x] Establish repository and project boundary.
- [x] Document architecture and first platform target.
- [x] Define milestone exit criteria.
- [ ] Agree userspace, init system and package-source decision.
- [ ] Define kernel artifact hand-off with Xlin.

Exit: architecture decisions and ownership boundaries are clear; CI validates the repository skeleton.

## M1 — Kernel artifact integration
Status: not started.

- [ ] Select a versioned Xlin artifact or pin an experimental exact commit.
- [ ] Define artifact naming, metadata and checksum verification.
- [ ] Define kernel command line and initramfs compatibility requirements.
- [ ] Add integration manifest and validation tooling.

Exit: XlinOS verifies artifact architecture, version, source identity and checksum against its manifest.

## M2 — Minimal userspace
Status: not started.

- [ ] Record base-userspace and init-system decision.
- [ ] Define minimal package set and package trust policy.
- [ ] Assemble a root filesystem reproducibly.
- [ ] Configure users, groups, filesystem layout and essential services.
- [ ] Produce an SBOM/licence inventory.

Exit: a root filesystem is assembled from pinned inputs and passes structural checks.

## M3 — First XlinOS boot
Status: not started.

- [ ] Build initramfs integration that mounts and enters the root filesystem.
- [ ] Assemble a UEFI-bootable x86_64 disk image.
- [ ] Boot using QEMU + OVMF.
- [ ] Reach XlinOS userspace login or controlled serial shell.
- [ ] Verify PID 1, mounts and clean shutdown.

Exit: a fresh image reaches the documented userspace milestone in a VM, with logs retained by CI.

## M4 — Developer and system foundations
Status: not started.

- [ ] Add system identity and release metadata.
- [ ] Define package installation and update workflows.
- [ ] Add configuration and diagnostics tooling.
- [ ] Add recovery and image validation commands.
- [ ] Establish security update and vulnerability response processes.

Exit: a developer can install, inspect, update and recover a VM using documented procedures.

## M5 — Preview image
Status: not started.

- [ ] Publish reproducible VM images and checksums.
- [ ] Publish provenance, package manifest and licence notices.
- [ ] Document limitations and supported VM configuration.
- [ ] Add release smoke tests and rollback procedure.

Exit: another developer can verify, boot and smoke-test the image using published instructions.

## Later milestones

Graphics, desktop, installer, broader device support, ARM, Secure Boot and production update infrastructure are future milestones.
