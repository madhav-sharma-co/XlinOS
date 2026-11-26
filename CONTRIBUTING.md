<!-- SPDX-FileCopyrightText: 2026 Axion Co. -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Contributing to XlinOS

XlinOS is the operating system integration project built around the Xlin kernel.

## Project boundaries

- Kernel source, configuration, patches and kernel build logic belong in [Xlin](https://github.com/madhav-sharma-co/Xlin).
- Root filesystem, userspace, system configuration, image assembly, installer and OS-level tests belong in XlinOS.
- Changes crossing this boundary should update the integration contract in both projects.

## Before implementation

1. Read [the architecture](docs/ARCHITECTURE.md) and [roadmap](docs/ROADMAP.md).
2. Check whether the behavior is already owned by Xlin.
3. For a significant architectural choice, add a decision record under `docs/decisions/`.
4. Pin external inputs and document how they are verified.

## Engineering expectations

- Prefer small, reviewable changes.
- Do not claim a feature works unless it has been tested; include exact commands and environment.
- Keep build outputs, downloaded source trees and credentials out of Git.
- Do not disable signature or checksum verification as a workaround.
- Preserve upstream copyright and licence notices.
- Add tests for build scripts and image integration behavior.
- Keep documentation honest about target hardware and limitations.

## Validation

Run `bash tests/repository-selftest.sh`. More build and boot checks will be added as implementation lands.
