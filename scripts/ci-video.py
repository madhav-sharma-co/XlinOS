#!/usr/bin/env python3
"""Records the whole life of XlinOS as a video: power on the ISO, run the real installer, boot the installed disk, create the first
user, log in, use the desktop. Frames are taken from the virtual screen while it runs; ffmpeg joins them.
usage: ci-video.py ISO REPO OUTDIR"""
import glob, os, shutil, socket, subprocess, sys, threading, time
from PIL import Image, ImageDraw, ImageFont
iso, repo, out = [os.path.abspath(a) for a in sys.argv[1:4]]
fr = out + "/frames"; os.makedirs(fr, exist_ok=True); os.chmod(out, 0o777)
disk = out + "/disk.img"; subprocess.run(["truncate", "-s", "20G", disk], check=True)
code = sorted(glob.glob("/usr/share/OVMF/OVMF_CODE*.fd"))[0]
vars_dst = out + "/VARS.fd"; shutil.copy(code.replace("CODE", "VARS"), vars_dst)
mon = "/tmp/qemu-mon-vid"
lock = threading.Lock()
S = {"sock": None}
PHASE = {"cap": "", "every": 2.0, "speed": 1.0}
frames = []          # (file, time, speed)
stop = False
try: FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
except Exception: FONT = ImageFont.load_default()

def raw(c):
    with lock:
        s = S["sock"]
        if not s: return
        s.sendall((c + "\n").encode()); time.sleep(0.12)
        try: s.recv(65536)
        except Exception: pass

def grab():
    n = len(frames); ppm = f"{fr}/{n:05d}.ppm"
    raw(f"screendump {ppm}")
    try:
        im = Image.open(ppm).convert("RGB"); os.remove(ppm)
    except Exception:
        return
    im = im.resize((1280, 800))
    cap = PHASE["cap"]
    if cap:
        d = ImageDraw.Draw(im, "RGBA"); w = d.textlength(cap, font=FONT) + 40
        d.rounded_rectangle((20, 20, 20 + w, 74), radius=14, fill=(0, 0, 0, 170)); d.text((40, 30), cap, font=FONT, fill=(255, 255, 255, 255))
    f = f"{fr}/{n:05d}.jpg"; im.save(f, quality=85)
    frames.append((f, time.time(), PHASE["speed"]))

def recorder():
    while not stop:
        grab(); time.sleep(PHASE["every"])
threading.Thread(target=recorder, daemon=True).start()

def phase(cap, every=2.0, speed=1.0):
    PHASE.update(cap=cap, every=every, speed=speed)

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
    with lock: S["sock"] = s
    return p
KEYS = {" ": "spc", ".": "dot", "-": "minus", "/": "slash", ";": "semicolon", "=": "equal", "&": "shift-7", ",": "comma"}
def key(k): raw("sendkey " + k)
def typ(text, enter=True):
    for ch in text:
        key(KEYS[ch] if ch in KEYS else ("shift-" + ch.lower() if ch.isupper() else ch))
    if enter: key("ret")

os.makedirs(repo + "/out", exist_ok=True); os.chmod(repo + "/out", 0o777)
ok = False
try:
    phase("1  Power on: the XlinOS installer disc starts", 2.0)
    p = qemu(["-cdrom", iso, "-boot", "d"], "phase1")
    time.sleep(25); key("ret")
    phase("2  The live system starts", 2.0); time.sleep(85)
    phase("3  Installing XlinOS onto the disk (sped up)", 10.0, 12.0)
    key("ctrl-alt-f2"); time.sleep(4); typ("root"); time.sleep(2); key("ret"); time.sleep(4)
    for line in ("mkdir /r", "mount -t 9p -o trans=virtio repo /r", "bash /r/scripts/ci/ai.sh"):
        typ(line); time.sleep(2)
    t0 = time.time()
    while time.time() - t0 < 2400:
        time.sleep(15)
        if os.path.exists(repo + "/out/done"): ok = True; break
    time.sleep(8); p.terminate(); p.wait()
    if not ok: raise SystemExit("installer did not finish")
    phase("4  Restart: first boot of the installed XlinOS", 2.0)
    p = qemu([], "phase2"); time.sleep(70)
    phase("5  Welcome to XlinOS: create the first user", 2.0); time.sleep(6)
    typ("Ann Lee", enter=False); key("tab"); time.sleep(1); key("tab"); typ("Xlin2026pass", enter=False); key("tab"); typ("Xlin2026pass", enter=False); time.sleep(2)
    key("ret")
    phase("6  Account created: XlinOS signs you in", 2.0); time.sleep(40)
    phase("7  Desktop: status bar, run bar, clock", 2.0); time.sleep(25)
    phase("8  Launcher  (Super + Space)", 1.5); key("meta_l-spc"); time.sleep(6); key("esc"); time.sleep(2)
    phase("9  Files  (Super + E)", 1.5); key("meta_l-e"); time.sleep(8)
    key("meta_l-left"); time.sleep(3)
    phase("10  Terminal snapped beside it  (Super + Enter, Super + Right)", 1.5); key("meta_l-ret"); time.sleep(8)
    typ("echo Hello from XlinOS"); time.sleep(3); key("meta_l-right"); time.sleep(4)
    phase("11  Quick settings  (Super + A)", 1.5); key("meta_l-a"); time.sleep(6); key("esc"); time.sleep(2)
    phase("12  Lock screen  (Super + L)", 1.5); key("meta_l-l"); time.sleep(8)
    typ("Xlin2026pass"); phase("13  Unlocked: back on the desktop", 1.5); time.sleep(8)
    phase("14  Log out (Super + Shift + Q): back to the login screen", 2.0); key("meta_l-shift_l-q"); time.sleep(25)
    phase("15  Log in again", 2.0); typ("Xlin2026pass"); time.sleep(40)
finally:
    stop = True; time.sleep(3)
    try: p.terminate()
    except Exception: pass
# ---- join the frames
lst = []
for i, (f, t, sp) in enumerate(frames):
    nxt = frames[i + 1][1] if i + 1 < len(frames) else t + 2
    lst.append((f, max(0.04, min((nxt - t) / sp, 6.0))))
with open(out + "/list.txt", "w") as fh:
    for f, d in lst: fh.write("file '%s'\nduration %.3f\n" % (f, d))
    fh.write("file '%s'\n" % lst[-1][0])
subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", out + "/list.txt", "-vf", "fps=15,format=yuv420p", "-c:v", "libx264", "-crf", "26",
                "-preset", "veryfast", out + "/xlinos-demo.mp4"], check=True)
print("video done", len(frames), "frames", "install ok" if ok else "")
sys.exit(0 if ok else 1)
