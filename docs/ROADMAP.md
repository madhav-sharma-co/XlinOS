# Roadmap

## 0.1 alpha: boots and installs (now)
- [x] Repo, archiso profile, build script, CI workflow
- [x] Layer 1 written: boot menu branding, splash picture, quiet start (untested)
- [x] First CI build succeeds (about 13 min, ISO 1.75 GB)
- [x] Boots in QEMU (BIOS and UEFI): XlinOS menu, quiet start, autologin, Xlin-soft desktop (seen in CI screenshots)
- [x] Installed-style system boots, creates the first user, shows the login and the desktop (CI install test)
- [ ] `xlinos-install` (archinstall) completes in a VM: still to test by hand
- [ ] Release 0.1.0-alpha with the ISO (2 GB GitHub limit; use a split or a mirror if larger)

## 0.2 beta: feels like an OS
- [ ] Calamares graphical installer
- [x] Login screen written: first-user welcome, lock-style login, switch/create/delete user (untested on a real boot; see docs/LOGIN.md)
- [ ] Boot logo (Plymouth), after the ISO boots
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
