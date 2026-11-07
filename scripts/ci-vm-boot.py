#!/usr/bin/env python3
"""Boots the cached test image with the repo shared into it (9p) and waits for the scenario to finish.
usage: ci-vm-boot.py WORKDIR REPO   (results appear in REPO/out)"""
import os, subprocess, sys, time
W, REPO = sys.argv[1:3]
out = os.path.join(REPO, "out"); os.makedirs(out, exist_ok=True); os.chmod(out, 0o777)
for f in os.listdir(out):
    try: os.remove(os.path.join(out, f))
    except OSError: pass
a = ["qemu-system-x86_64", "-m", "4096", "-smp", "2", "-kernel", f"{W}/vmlinuz-linux", "-initrd", f"{W}/initramfs-linux-fallback.img",
     "-append", "root=/dev/vda rw console=ttyS0 loglevel=4 xlinos.ci", "-drive", f"file={W}/disk.img,if=virtio,format=raw",
     "-virtfs", f"local,path={REPO},mount_tag=repo,security_model=none,id=repo",
     "-vga", "std", "-display", "none", "-serial", f"file:{out}/serial.log"]
a += ["-enable-kvm", "-cpu", "host"] if os.path.exists("/dev/kvm") else ["-cpu", "max"]
p = subprocess.Popen(a)
start = time.time()
while time.time() - start < 420:
    if os.path.exists(f"{out}/done") or p.poll() is not None: break
    time.sleep(3)
print("finished after", int(time.time() - start), "s; done:", os.path.exists(f"{out}/done"), flush=True)
time.sleep(2); p.terminate()
