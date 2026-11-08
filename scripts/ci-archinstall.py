#!/usr/bin/env python3
"""Boots the real ISO, runs the real installer (archinstall + the XlinOS settings) onto a blank disk, then boots that disk (UEFI)
and checks the first-start screen. usage: ci-archinstall.py ISO REPO OUTDIR"""
import glob, os, shutil, socket, subprocess, sys, time
iso, repo, out = [os.path.abspath(a) for a in sys.argv[1:4]]
os.makedirs(out + "/shots", exist_ok=True); os.chmod(out, 0o777)
disk = out + "/disk.img"; subprocess.run(["truncate", "-s", "20G", disk], check=True)
code = sorted(glob.glob("/usr/share/OVMF/OVMF_CODE*.fd"))[0]
vars_dst = out + "/VARS.fd"; shutil.copy(code.replace("CODE", "VARS"), vars_dst)
mon = "/tmp/qemu-mon-ai"
def qemu(extra, name):
    if os.path.exists(mon): os.remove(mon)
    a = ["qemu-system-x86_64", "-m", "6144", "-smp", "2", "-vga", "std", "-display", "none", "-monitor", f"unix:{mon},server,nowait",
         "-serial", f"file:{out}/{name}-serial.log", "-device", "virtio-net-pci,netdev=n", "-netdev", "user,id=n",
         "-drive", f"file={disk},if=virtio,format=raw",
         "-drive", f"if=pflash,format=raw,unit=0,readonly=on,file={code}", "-drive", f"if=pflash,format=raw,unit=1,file={vars_dst}",
         "-virtfs", f"local,path={repo},mount_tag=repo,security_model=none,id=repo"] + extra
    a += ["-enable-kvm", "-cpu", "host"] if os.path.exists("/dev/kvm") else ["-cpu", "max"]
    p = subprocess.Popen(a)
    for _ in range(50):
        if os.path.exists(mon): break
        time.sleep(0.2)
    s = socket.socket(socket.AF_UNIX); s.connect(mon); s.settimeout(5)
    return p, s
def cmd(s, c):
    s.sendall((c + "\n").encode()); time.sleep(0.15)
    try: s.recv(65536)
    except Exception: pass
def shot(s, name):
    ppm = f"{out}/shots/{name}.ppm"; cmd(s, f"screendump {ppm}")
    try:
        from PIL import Image
        Image.open(ppm).save(f"{out}/shots/{name}.png"); os.remove(ppm)
    except Exception as e: print("convert failed", e)
    print("shot", name, flush=True)
KEYS = {" ": "spc", ".": "dot", "-": "minus", "/": "slash", ";": "semicolon", "=": "equal", "&": "shift-7", ",": "comma"}
def typ(s, text):
    for ch in text:
        if ch in KEYS: cmd(s, "sendkey " + KEYS[ch])
        elif ch.isupper(): cmd(s, "sendkey shift-" + ch.lower())
        else: cmd(s, "sendkey " + ch)
    cmd(s, "sendkey ret")
# ---- phase 1: install from the ISO
os.makedirs(repo + "/out", exist_ok=True); os.chmod(repo + "/out", 0o777)
p, s = qemu(["-cdrom", iso, "-boot", "d"], "phase1")
try:
    time.sleep(25); shot(s, "1-iso-menu"); cmd(s, "sendkey ret")
    time.sleep(90); shot(s, "2-iso-booted")
    cmd(s, "sendkey meta_l-ret"); time.sleep(6); shot(s, "2b-terminal")  # the live ISO starts the desktop: open XlinOS Terminal
    for line in ("id -u; sudo -n true; echo ok", "mkdir /r", "mount -t 9p -o trans=virtio repo /r", "bash /r/scripts/ci/ai.sh"):
        typ(s, line); time.sleep(2)
    shot(s, "2c-typed")
    t0 = time.time(); done = False
    while time.time() - t0 < 2400:
        time.sleep(30)
        if os.path.exists(repo + "/out/done"): done = True; break
        if int(time.time() - t0) % 300 < 30: shot(s, "3-installing")
    shot(s, "4-install-end")
    time.sleep(10)
finally:
    p.terminate(); p.wait()
shutil.copy(repo + "/out/install.log", out + "/install.log") if os.path.exists(repo + "/out/install.log") else None
if not done:
    print("FAILED: installer did not finish"); sys.exit(1)
# ---- phase 2: boot the installed disk
p, s = qemu([], "phase2")
fails = []
try:
    time.sleep(90); shot(s, "5-first-boot")
    from PIL import Image
    im = Image.open(f"{out}/shots/5-first-boot.png").convert("RGB").resize((64, 40))
    px = list(im.getdata()); lit = sum(1 for r, g, b in px if b > 40) / len(px)
    print("first boot lit=%.2f" % lit)
    if lit < 0.4: fails.append("first boot is not the graphical welcome screen")
finally:
    p.terminate()
if fails: print("FAILED:", fails); sys.exit(1)
