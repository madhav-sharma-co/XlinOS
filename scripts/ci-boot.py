#!/usr/bin/env python3
"""Boots an ISO in QEMU, takes screenshots at fixed times, and writes PNGs. Used by CI to look at what really boots.
usage: ci-boot.py ISO bios|uefi OUTDIR"""
import glob, os, shutil, socket, subprocess, sys, time
iso, mode, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
mon = f"/tmp/qemu-mon-{mode}"
args = ["qemu-system-x86_64", "-m", "4096", "-smp", "2", "-cdrom", iso, "-boot", "d", "-vga", "std",
        "-display", "none", "-monitor", f"unix:{mon},server,nowait", "-serial", f"file:{out}/{mode}-serial.log",
        "-device", "virtio-net-pci,netdev=n", "-netdev", "user,id=n"]
args += ["-enable-kvm", "-cpu", "host"] if os.path.exists("/dev/kvm") else ["-cpu", "max"]
if mode == "uefi":
    code = next(iter(sorted(glob.glob("/usr/share/OVMF/OVMF_CODE*.fd"))), None)
    if not code:
        sys.exit("no OVMF firmware found")
    vars_src = code.replace("CODE", "VARS")
    vars_dst = f"{out}/OVMF_VARS.fd"
    shutil.copy(vars_src, vars_dst)                      # UEFI needs its own writable variable store
    args += ["-drive", f"if=pflash,format=raw,unit=0,readonly=on,file={code}",
             "-drive", f"if=pflash,format=raw,unit=1,file={vars_dst}"]
print("KVM:", os.path.exists("/dev/kvm"), "cmd:", " ".join(args), flush=True)
p = subprocess.Popen(args)
for _ in range(50):
    if os.path.exists(mon): break
    time.sleep(0.2)
s = socket.socket(socket.AF_UNIX); s.connect(mon); s.settimeout(5)
def cmd(c):
    s.sendall((c + "\n").encode()); time.sleep(0.4)
    try: s.recv(65536)
    except Exception: pass
def shot(name):
    ppm = f"{out}/{mode}-{name}.ppm"
    cmd(f"screendump {ppm}")
    try:
        from PIL import Image
        Image.open(ppm).save(f"{out}/{mode}-{name}.png"); os.remove(ppm)
    except Exception as e:
        print("could not convert", name, e)
    print("shot", name, flush=True)
try:
    time.sleep(6); shot("0a-start")
    time.sleep(8); shot("0b-menu")
    time.sleep(8); shot("1-menu")
    cmd("sendkey ret")                       # boot the first entry
    for name, wait in (("2-booting", 30), ("3-after-70s", 30), ("4-after-2min", 50), ("5-after-3min", 60)):
        time.sleep(wait); shot(name)
finally:
    p.terminate()
    for f in glob.glob(f"{out}/*VARS*"): os.remove(f)
