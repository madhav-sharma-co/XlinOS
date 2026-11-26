#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Axion Co.
# SPDX-License-Identifier: GPL-3.0-or-later
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

for file in README.md CONTRIBUTING.md docs/ARCHITECTURE.md docs/ROADMAP.md docs/LICENSING.md profiles/x86_64/README.md packaging/README.md scripts/README.md; do
  if [[ ! -s "$file" ]]; then
    printf 'FAIL: required file missing or empty: %s\n' "$file" >&2
    exit 1
  fi
done

grep -q 'madhav-sharma-co/Xlin' README.md
grep -q 'QEMU' docs/ARCHITECTURE.md
grep -q 'M3 — First XlinOS boot' docs/ROADMAP.md

printf 'PASS: XlinOS repository structure and project contracts are present.\n'
printf 'NOTE: this self-test does not build a kernel, root filesystem, or bootable image.\n'
