# XlinOS Roadmap

This roadmap is milestone-based, not a promise of release dates. A milestone is complete only when its acceptance criteria are met and documented.

## M0 — Project foundation

- [x] Define product identity and principles.
- [x] Record the initial architecture direction.
- [x] Establish contribution and repository conventions.
- [ ] Confirm supported architecture and minimum hardware using test devices.
- [ ] Add a tracked archiso profile and reproducible build instructions.

**Exit criteria:** a new contributor can follow documented steps to build the same bootable image.

## M0.1 — Minimal Foundation (terminal only)

- [x] Tracked archiso profile in `archiso/` with build, clean, verify and QEMU scripts.
- [x] ISO builds successfully (GitHub Actions).
- [x] Kernel + initramfs from the ISO boot in QEMU to `multi-user.target` with XlinOS identity (CI smoke test).
- [ ] Boots in QEMU through the real boot loaders (BIOS and UEFI) to the XlinOS login after first-boot user creation.
- [ ] Networking, `multi-user.target` and identity checks pass (see `docs/TESTING.md`).

**Exit criteria:** the checklist in `docs/TESTING.md` is completed and recorded.

## M1 — Bootable prototype

- [ ] Produce an Archiso live image for x86_64 UEFI systems.
- [ ] Boot successfully in QEMU and on at least one physical test machine.
- [ ] Start a Wayland desktop session using the selected KDE Plasma baseline.
- [ ] Verify networking, audio, storage, graphics, suspend/resume where hardware supports it.
- [ ] Document known hardware limitations.

**Exit criteria:** a tester can boot the image, reach the desktop, and complete basic desktop tasks.

## M2 — XlinOS experience

- [ ] Establish typography, spacing, icon, color, and motion tokens.
- [ ] Create cohesive dark and light themes with accessible contrast.
- [ ] Configure panel, launcher, workspace, notifications, and default applications.
- [ ] Prototype one small XlinOS-native Qt/QML application.
- [ ] Test keyboard navigation, screen scaling, and reduced motion.

**Exit criteria:** the desktop feels coherent and remains usable with keyboard, mouse, and assistive settings.

## M3 — Reliability and performance

- [ ] Add automated profile/configuration validation.
- [ ] Record boot time, idle memory, launch latency, and frame pacing on reference hardware.
- [ ] Test update and rollback/recovery procedures.
- [ ] Review default services and remove unnecessary components.
- [ ] Publish a hardware compatibility matrix.

**Exit criteria:** repeatable tests and documented recovery procedures exist.

## M4 — Developer and application ecosystem

- [ ] Define XlinOS package naming and repository policy.
- [ ] Publish developer setup and packaging guides.
- [ ] Add signing and release verification procedures.
- [ ] Establish issue templates and release notes.

**Exit criteria:** an external contributor can build, package, and verify a sample XlinOS application.

## M5 — Optional intelligence features

- [ ] Specify threat model, data flows, and permission model first.
- [ ] Prototype an opt-in assistant with no default elevated privileges.
- [ ] Require confirmation for destructive actions.
- [ ] Document local vs remote processing and retention behavior.

**Exit criteria:** users can understand, control, disable, and audit assistant capabilities.

## Release discipline

Every release candidate must have a known base snapshot, build instructions, checksums, release notes, tested hardware, and a documented path to report issues. Never label an untested image stable.
