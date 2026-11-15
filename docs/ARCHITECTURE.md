# XlinOS Architecture

## Architecture goals

XlinOS should feel like one coherent desktop while remaining maintainable and compatible with the Linux ecosystem. Prefer well-supported components over bespoke infrastructure until a real product requirement justifies replacing them.

## System layers

1. **Boot and image** — UEFI boot, kernel, initramfs, and an Archiso-built live image.
2. **Base operating system** — Arch Linux userspace, systemd, udev, NetworkManager, audio services, and standard Linux utilities.
3. **Graphics** — Wayland session and mature compositor/desktop components.
4. **Desktop experience** — begin with KDE Plasma as a stable foundation; customize defaults, theme, workflows, and applications. Evaluate a dedicated XlinOS shell only after usability prototypes establish requirements.
5. **XlinOS applications** — Qt 6 / QML applications and settings surfaces, introduced incrementally.
6. **Optional intelligence layer** — opt-in assistant and automation capabilities, isolated behind explicit permissions and clear privacy controls.

## Initial implementation choices

- **Distribution base:** Arch Linux.
- **Image tooling:** archiso, using a tracked profile in this repository.
- **Desktop baseline:** KDE Plasma on Wayland for the first prototype. This avoids taking on compositor, panel, window management, and accessibility engineering before the system can boot.
- **Native UI:** Qt 6 / QML for XlinOS-specific apps and later shell experiments.
- **Systems code:** Rust for new privileged services only where a narrowly scoped service is justified. Do not add daemons without a concrete need.
- **Packaging:** pacman and standard PKGBUILD conventions. Keep custom packages separate from upstream packages.

## Proposed repository layout

```text
.
├── README.md
├── CONTRIBUTING.md
├── docs/
│   ├── ARCHITECTURE.md
│   └── ROADMAP.md
├── packaging/
│   └── packages/          # future XlinOS PKGBUILDs
├── profiles/
│   └── xlinos/            # future archiso profile
├── scripts/               # reproducible developer/build helpers
└── .github/
    └── workflows/         # future validation and image-build CI
```

Directories should be added when their first real file is ready; avoid empty placeholder trees.

**Note:** the first tracked archiso profile (terminal-only milestone 0.1) lives in `archiso/`, with scripts in `scripts/`; see [ARCHITECTURE-0.1.md](ARCHITECTURE-0.1.md). It uses systemd-networkd and iwd instead of NetworkManager to stay minimal; the desktop milestones can revisit that.

## Design system direction

The visual identity is a hybrid of premium minimalism, restrained futurism, and professional productivity:

- calm surfaces and strong information hierarchy;
- consistent spacing, typography, iconography, and motion;
- dark and light themes with accessible contrast;
- restrained translucency only where it improves hierarchy;
- reduced-motion and high-contrast options;
- no animation that delays input or blocks work.

## Performance and quality principles

Measure before optimizing. Track boot-to-desktop time, idle memory, app launch time, frame pacing, battery behavior, and update reliability on documented hardware. Do not advertise numerical targets until they are tested on a defined reference device.

## Security principles

- keep the base close to upstream security updates;
- minimize privileged code and services;
- use signed packages and trusted repositories;
- do not run AI actions with elevated privileges by default;
- require explicit user approval for destructive or security-sensitive actions;
- document telemetry clearly and keep it opt-in.

## Architecture decision process

Record significant changes as short Architecture Decision Records (ADRs) under `docs/adr/`. Each ADR should include context, decision, alternatives, and consequences. Revisit choices when prototypes provide evidence, not merely because a newer technology is fashionable.
