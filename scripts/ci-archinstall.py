#!/usr/bin/env python3
"""Boots the real ISO, runs the real installer (archinstall + the XlinOS settings) onto a blank disk, then boots that disk (UEFI)
and checks the first-start screen. usage: ci-archinstall.py ISO REPO OUTDIR"""
import glob, os, shutil, socket, subprocess, sys, time
iso, repo, out = [os.path.abspath(a) for a in sys.argv[1:4]]
os.makedirs(out + "/shots", exist_ok=True); os.chmod(out, 0o777)
DUALFLAG = os.environ.get("XL_DUAL") == "1"
os.makedirs(repo + "/out", exist_ok=True)
if DUALFLAG: open(repo + "/out/dual", "w").write("1")
disk = out + "/disk.img"; subprocess.run(["truncate", "-s", "20G", disk], check=True)
DUAL = os.environ.get("XL_DUAL") == "1"
if DUAL:   # pretend this disk already has another system: shared EFI partition (with a marker), a "host" partition (with a marker) and a free partition
    sh = lambda c: subprocess.run(c, shell=True, check=True)
    sh(f"sudo sgdisk -n1:0:+512M -t1:ef00 -n2:0:+3G -t2:8300 -n3:0:+10G -t3:8300 {disk}")
    sh(f"L=$(sudo losetup -fP --show {disk}); sudo mkfs.fat -F32 ${{L}}p1; sudo mkfs.ext4 -qF ${{L}}p2; sudo mkdir -p /mnt/xe /mnt/xh; "
       f"sudo mount ${{L}}p1 /mnt/xe; echo keep >/tmp/m; sudo cp /tmp/m /mnt/xe/HOST-ESP-MARKER; sudo umount /mnt/xe; "
       f"sudo mount ${{L}}p2 /mnt/xh; sudo cp /tmp/m /mnt/xh/HOST-ROOT-MARKER; sudo umount /mnt/xh; sudo losetup -d $L; sudo chmod 666 {disk}")
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
    REC["sock"] = s
    return p, s
import threading
LOCK = threading.RLock(); REC = {"on": False, "n": 0, "sock": None, "every": 2.0}
def cmd(s, c):
    with LOCK:
        s.sendall((c + "\n").encode()); time.sleep(0.15)
        try: s.recv(65536)
        except Exception: pass
def recorder():
    """Takes a picture of the virtual screen every few seconds; ffmpeg turns them into the video."""
    os.makedirs(out + "/frames", exist_ok=True)
    while REC["on"]:
        if REC["sock"] is not None:
            try: cmd(REC["sock"], f"screendump {out}/frames/{REC['n']:05d}.ppm"); REC["n"] += 1
            except Exception: pass
        time.sleep(REC["every"])
threading.Thread(target=recorder, daemon=True).start(); REC["on"] = True
def shot(s, name):
  try: _shot(s, name)
  except Exception as e: print("shot failed", name, e, flush=True)
def _shot(s, name):
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
    cmd(s, "sendkey ctrl-alt-f2"); time.sleep(4); shot(s, "2b-tty2")
    typ(s, "root"); time.sleep(2); cmd(s, "sendkey ret"); time.sleep(4); shot(s, "2b-login")
  # the live ISO starts the desktop: open XlinOS Terminal
    for line in ("mkdir /r", "mount -t 9p -o trans=virtio repo /r", "bash /r/scripts/ci/ai.sh"):
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
    REC["sock"] = None; p.terminate(); p.wait()
shutil.copy(repo + "/out/install.log", out + "/install.log") if os.path.exists(repo + "/out/install.log") else None
if not done:
    print("FAILED: installer did not finish"); sys.exit(1)
# ---- phase 2: boot the installed disk (UEFI), create the first user, log in, use the desktop
p, s = qemu([], "phase2")
fails = []
def lit(name):
    from PIL import Image
    im = Image.open(f"{out}/shots/{name}.png").convert("RGB").resize((64, 40))
    px = list(im.getdata()); v = sum(1 for r, g, b in px if b > 40) / len(px); print("check", name, "lit=%.2f" % v, flush=True)
    return v
def typ2(text):
    for ch in text:
        if ch in KEYS: cmd(s, "sendkey " + KEYS[ch])
        elif ch.isupper(): cmd(s, "sendkey shift-" + ch.lower())
        else: cmd(s, "sendkey " + ch)
try:
    time.sleep(90); shot(s, "5-first-boot")
    if lit("5-first-boot") < 0.4: fails.append("first boot is not the graphical welcome screen")
    typ2("Ann Lee"); cmd(s, "sendkey tab"); time.sleep(0.5)
    cmd(s, "sendkey tab"); typ2("Xlin2026pass"); cmd(s, "sendkey tab"); typ2("Xlin2026pass"); time.sleep(1); shot(s, "6-form-filled")
    cmd(s, "sendkey ret"); time.sleep(100); shot(s, "7-desktop")
    if lit("7-desktop") < 0.4: fails.append("no desktop after creating the user")
    for name, keys in (("8-launcher", "meta_l-spc"), ("9-closed", "esc"), ("10-terminal", "meta_l-ret"), ("11-quick", "meta_l-a")):
        cmd(s, "sendkey " + keys); time.sleep(6); shot(s, name)
    cmd(s, "sendkey esc"); time.sleep(2)
    cmd(s, "sendkey meta_l-l"); time.sleep(8); shot(s, "12-lock")
    time.sleep(5)
finally:
    time.sleep(3); REC["on"] = False; time.sleep(3); p.terminate()
subprocess.run(f"cd {out} && ffmpeg -y -loglevel error -framerate 6 -i frames/%05d.ppm -vf \"scale=1280:800:force_original_aspect_ratio=decrease,pad=1280:800:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1\" -c:v libx264 -preset veryfast -crf 29 -pix_fmt yuv420p xlinos-install.mp4", shell=True)
if fails: print("FAILED:", fails); sys.exit(1)
