# XlinOS

**A clean, modern, smooth, fast, and professional desktop operating system.**

XlinOS is an Arch Linux-based desktop OS project focused on a coherent, polished user experience. The first milestone is a reproducible, bootable live image with a carefully selected desktop foundation—not a custom kernel.

## Product principles

- **Clarity:** purposeful layouts, readable typography, and minimal visual noise.
- **Responsiveness:** fast startup, low idle overhead, and fluid interactions.
- **Consistency:** one design language across the shell, settings, and system tools.
- **Reliability:** reproducible builds, tested updates, and safe defaults.
- **User control:** transparent settings, permissions, and system behavior.
- **AI-ready, not AI-dependent:** future intelligent features must be optional and respect user privacy.

## Initial technical direction

| Area | Direction |
| --- | --- |
| Base | Arch Linux |
| Image creation | archiso |
| Display protocol | Wayland |
| Desktop foundation | KDE Plasma initially, customized and evaluated against a future custom shell |
| UI technology | Qt 6 / QML for XlinOS-native experiences |
| Systems programming | Rust where it provides a clear safety or maintenance benefit |
| Packaging | Pacman and standard Arch packaging conventions |
| Build automation | Shell scripts and CI, with reproducible build steps |

The initial release will reuse mature Linux components. XlinOS will differentiate through integration, design, defaults, performance work, and its own applications over time.

## Repository status

This repository is at the foundation stage. The first engineering milestone is to document the product, establish build conventions, and produce a bootable Arch-based image.

See:
- [Architecture](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
- [Development guide](CONTRIBUTING.md)

## Non-goals for the first milestone

- Writing a new kernel.
- Replacing the Linux driver ecosystem.
- Building a package manager from scratch.
- Shipping always-on AI services.
- Claiming performance or security guarantees before they are measured.

## Project status

Early development. Interfaces, package choices, and implementation details may change as prototypes are tested.
