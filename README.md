<!--
SPDX-FileCopyrightText: 2026 Axion Co.
SPDX-License-Identifier: CC-BY-4.0
-->

# XlinOS

**XlinOS is the operating system built around the Xlin kernel.** It is an Axion Co. project, developed alongside the [Xlin kernel](https://github.com/madhav-sharma-co/Xlin).

The first engineering target is a reproducible **x86_64 UEFI virtual-machine image** that boots the Xlin kernel into a minimal, maintainable userspace. The initial milestone is a reliable serial-console system; a graphical desktop is a later milestone.

> **Development status: architecture and repository bootstrap.** This repository is newly initialized. No XlinOS image, installer, desktop, or end-to-end boot integration is available yet. The Xlin kernel currently documents a successful QEMU + OVMF boot to a serial shell using its own minimal test initramfs. That is a kernel test, not an XlinOS boot.

## Relationship to Xlin

- **Xlin** owns the downstream kernel source pin, kernel configuration, patches, build and kernel-level boot validation.
- **XlinOS** owns the operating-system integration: root filesystem, initramfs integration, system services, system configuration, image assembly, installation and OS-level testing.
- XlinOS consumes versioned Xlin kernel artifacts. It must not silently duplicate or fork kernel build logic.

Kernel repository: [madhav-sharma-co/Xlin](https://github.com/madhav-sharma-co/Xlin)

## Initial platform

| Area | Initial decision |
|---|---|
| Architecture | x86_64 |
| Firmware | UEFI, tested with OVMF |
| First environment | QEMU virtual machine |
| Kernel | Xlin kernel; exact supported version is tracked in the integration manifest |
| First interface | Serial console |
| Userspace | Minimal Linux userspace, selected and documented before image implementation |
| Init | systemd is the proposed first target; integration is not yet implemented |
| Desktop | Out of scope for the first boot milestone |

These are initial development targets, not claims of completed support. See [Architecture](docs/ARCHITECTURE.md) and [Roadmap](docs/ROADMAP.md).

## Project structure

```text
XlinOS/
├── docs/                 # Architecture, decisions and development guides
├── profiles/x86_64/      # Platform-specific OS profile
├── packaging/            # OS package and image integration
├── scripts/              # Reproducible build and developer tooling
├── tests/                # Image and VM integration tests
└── .github/workflows/    # Continuous integration
```

## Development principles

1. **Kernel boundary:** kernel development belongs in Xlin; OS integration belongs here.
2. **Reproducibility:** pin inputs, record versions and make image builds repeatable.
3. **Traceability:** every shipped kernel must identify its exact Xlin release and upstream base.
4. **Security:** minimize the base system, avoid running services unnecessarily and document trust boundaries.
5. **Honest status:** distinguish design, implemented, tested and hardware-validated features.
6. **Upstream respect:** preserve Linux kernel licensing, notices and attribution in the Xlin project and its distributed artifacts.

## Roadmap

1. Repository and architecture foundation.
2. Define the Xlin kernel artifact contract and supported userspace.
3. Build a minimal root filesystem and initramfs integration.
4. Assemble a bootable UEFI disk image.
5. Boot XlinOS in QEMU + OVMF and add repeatable smoke tests.
6. Add package management, system configuration and installation.
7. Evaluate graphics, desktop, networking and broader hardware support.

See [ROADMAP.md](docs/ROADMAP.md) for exit criteria.

## Contributing

Start with [CONTRIBUTING.md](CONTRIBUTING.md). Architecture changes should be recorded as short decision documents under `docs/decisions/`.

## Licensing

Licensing for each component and distributed image must be documented before redistribution. XlinOS must preserve the licences and notices of Xlin, Linux and every userspace component it ships. See [LICENSING.md](docs/LICENSING.md).
