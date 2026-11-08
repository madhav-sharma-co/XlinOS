#!/usr/bin/env python3
"""Boots the test system image and drives the first start by typing into the login screen. usage: ci-install-boot.py WORKDIR OUTDIR"""
import sys, os, socket, subprocess, sys, time
W, OUT = sys.argv[1:3]
mon = "/tmp/qemu-mon-install"
def start():
    if os.path.exists(mon): os.remove(mon)
    a = ["qemu-system-x86_64", "-m", "4096", "-smp", "2", "-kernel", f"{W}/vmlinuz-linux", "-initrd", f"{W}/initramfs-linux-fallback.img",
         "-append", "root=/dev/vda rw console=ttyS0 quiet loglevel=3", "-drive", f"file={W}/disk.img,if=virtio,format=raw",
         "-vga", "std", "-display", "none", "-monitor", f"unix:{mon},server,nowait", "-serial", f"file:{OUT}/serial.log",
         "-device", "virtio-net-pci,netdev=n", "-netdev", "user,id=n"]
    a += ["-enable-kvm", "-cpu", "host"] if os.path.exists("/dev/kvm") else ["-cpu", "max"]
    p = subprocess.Popen(a)
    for _ in range(50):
        if os.path.exists(mon): break
        time.sleep(0.2)
    s = socket.socket(socket.AF_UNIX); s.connect(mon); s.settimeout(5)
    return p, s
p, s = start()
def cmd(c):
    s.sendall((c + "\n").encode()); time.sleep(0.3)
    try: s.recv(65536)
    except Exception: pass
def shot(name):
    ppm = f"{OUT}/{name}.ppm"; cmd(f"screendump {ppm}")
    try:
        from PIL import Image
        Image.open(ppm).save(f"{OUT}/{name}.png"); os.remove(ppm)
    except Exception as e: print("convert failed", name, e)
    print("shot", name, flush=True)
FAILS = []
def expect_graphic(name):
    """The picture must be a graphical screen (blue desktop or login), not a black text console."""
    try:
        from PIL import Image
        im = Image.open(f"{OUT}/{name}.png").convert("RGB").resize((64, 40))
        px = list(im.getdata()); lit = sum(1 for r, g, b in px if b > 40) / len(px)
        print("check", name, "lit=%.2f" % lit, flush=True)
        if lit < 0.4: FAILS.append(name)
    except Exception as e:
        print("check failed", name, e); FAILS.append(name)
KEYS = {" ": "spc", ".": "dot", "-": "minus"}
def typ(text):
    for ch in text:
        if ch in KEYS: cmd("sendkey " + KEYS[ch])
        elif ch.isupper(): cmd("sendkey shift-" + ch.lower())
        else: cmd("sendkey " + ch)
try:
    time.sleep(75); shot("1-first-start"); expect_graphic("1-first-start")
    typ("Ann Lee"); cmd("sendkey tab"); time.sleep(0.5); shot("2-name-typed")
    cmd("sendkey tab"); typ("Xlin2026pass"); cmd("sendkey tab"); typ("Xlin2026pass"); time.sleep(0.5); shot("3-form-filled")
    cmd("sendkey ret")
    time.sleep(25); shot("4-after-create")
    time.sleep(70); shot("5-desktop-first-login"); expect_graphic("5-desktop-first-login")
    cmd("system_powerdown"); time.sleep(25)
    p.terminate(); p.wait(); time.sleep(2)
    p, s = start()
    time.sleep(60); shot("6-login-screen"); expect_graphic("6-login-screen")
    typ("wrongpass"); cmd("sendkey ret"); time.sleep(4); shot("7-wrong-password")
    cmd("sendkey ctrl-a"); cmd("sendkey backspace"); typ("Xlin2026pass"); cmd("sendkey ret")
    time.sleep(45); shot("8-desktop-after-login"); expect_graphic("8-desktop-after-login")
finally:
    p.terminate()
if FAILS:
    print("FAILED: not a graphical screen:", FAILS); sys.exit(1)
