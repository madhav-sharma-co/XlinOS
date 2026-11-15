# Contributing to XlinOS

Thanks for helping build XlinOS. The project is early-stage; small, reviewable, well-documented changes are especially valuable.

## Before making changes

1. Read the [project overview](README.md), [architecture](docs/ARCHITECTURE.md), and [roadmap](docs/ROADMAP.md).
2. Search existing issues and discussions before starting a duplicate effort.
3. For a substantial architectural change, propose an Architecture Decision Record before implementation.

## Engineering principles

- Prefer upstream, maintained Linux components over unnecessary forks.
- Keep the initial system small and understandable.
- Avoid adding background services without a documented need.
- Keep AI and network-dependent features optional.
- Never commit secrets, private keys, tokens, personal data, or machine-specific configuration.
- Include reproducible test steps with code changes.
- Document hardware-specific behavior and known limitations.

## Changes and pull requests

- Make one logical change per pull request.
- Explain the problem, approach, alternatives, and user-visible impact.
- Include screenshots for visual changes where useful.
- Include build/test results and the environment used.
- Update documentation when behavior or setup steps change.

## Current development status

The project is in its foundation phase. A terminal-only archiso profile (milestone 0.1) and build scripts exist in `archiso/` and `scripts/`; CI builds the ISO and boot-tests its kernel, but the boot loaders and login flow are not yet tested. Do not assume an installable or production-ready operating system exists until the M1 acceptance criteria are met.
