# Roadmap

## 0.1 alpha: boots and installs (now)
- [x] Repo, archiso profile, build script, CI workflow
- [ ] First CI build succeeds
- [ ] Boots in QEMU (BIOS and UEFI), live desktop starts
- [ ] `xlinos-install` completes in a VM; installed system boots to the desktop
- [ ] Release 0.1.0-alpha with the ISO (2 GB GitHub limit; use a split or a mirror if larger)

## 0.2 beta: feels like an OS
- [ ] Calamares graphical installer
- [ ] Graphical login (greetd or SDDM) and a welcome app on first boot
- [ ] Branding: wallpapers, boot splash, logo in boot menu
- [ ] Offline install of the base packages (no internet needed for the core)

## 0.3: own packaging
- [ ] PKGBUILD for `xlin-soft`, published in an own pacman repo (`xlinos-repo`)
- [ ] Automatic ISO builds on tags, checksums and signatures
- [ ] Updates: `pacman -Syu` brings Xlin-soft updates

## 1.0: public release
- [ ] Hardware testing (Intel/AMD/NVIDIA, laptops), UEFI + BIOS (+ Secure Boot decision)
- [ ] Website, docs, issue templates, mirror for downloads

## Later
- [ ] XlinOS Advanced edition (scope after 1.0)
- [ ] Performance budget checks in CI (ISO size, idle RAM, boot time)
- [ ] ARM build, if there is demand
