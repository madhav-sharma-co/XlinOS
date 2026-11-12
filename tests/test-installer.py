#!/usr/bin/env python3
"""Installer safety and progress tests that need no disks: the disk rules (with a fake disk layout) and the engine's progress parser."""
import os, re, subprocess, sys
LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "profile/airootfs/usr/local/lib/xlinos")
sys.path.insert(0, LIB)
import xlinos_disks as d
fails = []
def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond: fails.append(name)

def dev(name, typ, size, pk=None, **k):
    return dict({"name": name, "path": "/dev/" + name, "pkname": pk, "type": typ, "size": size, "model": "M", "rm": False, "ro": False, "fstype": None,
                 "label": None, "parttype": None, "pttype": "gpt" if typ == "disk" else None, "mountpoints": [None], "tran": "sata", "uuid": None}, **k)
G = 10**9
LAYOUT = [
    dev("sda", "disk", 500 * G), dev("sda1", "part", 512 * 10**6, "sda", parttype=d.ESP, fstype="vfat"),
    dev("sda2", "part", 100 * G, "sda", fstype="ntfs", parttype=d.MS_DATA), dev("sda3", "part", 30 * G, "sda", fstype="ext4"),
    dev("sda4", "part", 5 * G, "sda", fstype="ext4"),
    dev("sdb", "disk", 16 * G, rm=True, tran="usb"),
    dev("sdb1", "part", 16 * G, "sdb", fstype="iso9660", label="XLINOS_202611", mountpoints=["/run/archiso/bootmnt"]),
    dev("sdc", "disk", 64 * G), dev("sdc1", "part", 60 * G, "sdc", fstype="ext4", mountpoints=["/mnt/data"]),
    dev("sdd", "disk", 8 * G),
]
d.lsblk = lambda: LAYOUT
d.swaps = lambda: set()
d.loop_backing_devices = lambda devs: set()
d.gaps = lambda disk, min_bytes=d.MIN_INSTALL: [(2048, 99999999, 90 * G)] if disk == "/dev/sda" else []
os.path.isdir_real = os.path.isdir
_isdir = os.path.isdir
os.path.isdir = lambda p: True if p == "/sys/firmware/efi" else _isdir(p)

check("parent disk of a partition", d.parent_disk("/dev/sda3", LAYOUT) == "/dev/sda")
check("install USB is protected", "/dev/sdb" in d.protected(LAYOUT))
check("other disks are not protected", "/dev/sda" not in d.protected(LAYOUT))
check("erase a normal disk is allowed", d.validate("erase", "/dev/sda") == [])
check("erase the install USB is refused", d.validate("erase", "/dev/sdb") != [])
check("a partition on the install USB is refused", d.validate("partition", "/dev/sdb1", "/dev/sda1") != [])
check("erase with a mounted partition is refused", d.validate("erase", "/dev/sdc") != [])
check("erase of a too small disk is refused", d.validate("erase", "/dev/sdd") != [])
check("erase needs a whole disk", d.validate("erase", "/dev/sda3") != [])
check("unknown device is refused", d.validate("erase", "/dev/nope") != [])
check("unknown method is refused", d.validate("format-everything", "/dev/sda") != [])
check("partition install with shared EFI is allowed", d.validate("partition", "/dev/sda3", "/dev/sda1") == [])
check("partition install without EFI is refused", d.validate("partition", "/dev/sda3", "") != [])
check("EFI partition cannot be the system partition", d.validate("partition", "/dev/sda1", "/dev/sda1") != [])
check("too small partition is refused", d.validate("partition", "/dev/sda4", "/dev/sda1") != [])
check("non-EFI partition cannot be the shared start-up partition", d.validate("partition", "/dev/sda3", "/dev/sda2") != [])
check("free-space install is allowed on GPT with free space", d.validate("freespace", "/dev/sda", "/dev/sda1") == [])
check("free-space install without free space is refused", d.validate("freespace", "/dev/sdc", "/dev/sda1") != [])
check("EFI on another disk is refused", d.validate("partition", "/dev/sdc1", "/dev/sda1") != [])
_c = d.lsblk; LAYOUT[3]["mountpoints"] = ["/mnt/x"]
check("a mounted partition is refused", d.validate("partition", "/dev/sda3", "/dev/sda1") != [])
LAYOUT[3]["mountpoints"] = [None]

# progress parser: take watch_output out of the engine and feed it archinstall-style output
src = open(os.path.join(LIB, "xlinos-install-run")).read()
fn = src[src.index("watch_output() {"):]; fn = fn[:fn.index("\n}\n") + 3]
feed = "\n".join("(%d/156) installing pkg%d" % (i, i) for i in (1, 78, 156)) + "\r( 1/413) installing a\r(200/413) installing b\r(413/413) installing z\n" \
       "Running bootctl install\nrunning: echo x | base64 -d | bash\n"
script = "pct(){ echo PCT $1; }\nsay(){ echo \"$*\"; }\nsetstate(){ echo STATE $1; }\n" + fn + "\nprintf '%s' \"$XFEED\" | watch_output two | grep -E '^(PCT|STEP|STATE)'\n"
out = subprocess.run(["bash", "-c", script], capture_output=True, text=True, env=dict(os.environ, XFEED=feed)).stdout.split("\n")
pcts = [int(l.split()[1]) for l in out if l.startswith("PCT")]
steps = [l for l in out if l.startswith("STEP")]
check("progress rises with the package counter", pcts[:1] == [12 + 26 // 156] or (len(pcts) > 3 and pcts[0] < pcts[3]))
check("progress reaches the bootloader step", 86 in pcts and 90 in pcts)
check("stages follow the output", any("base system" in s for s in steps) and any("desktop and system" in s for s in steps) and any("bootloader" in s for s in steps) and any("Configuring" in s for s in steps))
check("bootloader step is marked critical, then cancellable again", "STATE critical" in out and out.index("STATE critical") < out.index("STATE cancellable"))
sys.exit(1 if fails else 0)
