# XlinOS

An operating system built from scratch on the Linux kernel. Created by Madhav Sharma, presented by Axion Co.

## Layout

- `src/init/` – our own init (PID 1) with a built-in mini shell
- `scripts/` – kernel build, initramfs packer (no `cpio` needed), QEMU runner
- `build.sh` – builds everything into `build/`

## Build and run

Needs `gcc`, `make`, `bc`, `flex`, `bison`, `python3`, `qemu-system-x86_64`.

    ./build.sh kernel
    scripts/run-qemu.sh

## Rules for third-party code

- Use other projects' code only for things we cannot reasonably write ourselves.
- Before it ships, it is configured and patched so users see only Xlin names: no foreign
  product names, logos or branding in the UI, command names, paths, or messages.
- Legal notices stay: license texts and copyright headers are kept in the source tree
  (`third_party/`) because the licenses require it. Only user-visible branding is replaced.
- Track each import in `third_party/README.md` (origin, version, license, our changes).
