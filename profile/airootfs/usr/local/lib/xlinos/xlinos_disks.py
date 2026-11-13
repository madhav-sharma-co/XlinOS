#!/usr/bin/env python3
"""XlinOS installer: disk detection and safety checks. The graphical installer shows what this finds, and the install engine
(xlinos-install-run) asks it again before it touches anything, so the checks never depend on the screen.

  xlinos_disks.py scan                          JSON list of disks (run as root to also detect other systems)
  xlinos_disks.py validate MODE TARGET [EFI]    MODE: erase | freespace | partition. Exit 0 = allowed, 2 = refused (JSON with reasons)
  xlinos_disks.py gap DISK                      "START_SECTOR END_SECTOR" of the biggest free gap that is big enough
"""
import json, os, re, subprocess, sys, tempfile

ESP = "c12a7328-f81f-11d2-ba4b-00a0c93ec93b"
MS_DATA = "ebd0a0a2-b9e5-4433-87c0-68b6b72699c7"
MIN_INSTALL = 10 * 10**9      # smallest partition / free gap XlinOS is installed into
MIN_DISK = 16 * 10**9         # smallest disk that is erased
MEDIA_LABELS = ("XLINOS", "ARCH_", "ARCHISO")   # install media labels: never a target
SKIP = ("loop", "sr", "zram", "ram", "fd", "md")


def run(*cmd, timeout=15):
    try:
        return subprocess.run(list(cmd), capture_output=True, text=True, timeout=timeout)
    except Exception:
        return subprocess.CompletedProcess(cmd, 1, "", "")


def lsblk():
    r = run("lsblk", "-J", "-l", "-b", "-o", "NAME,PATH,PKNAME,TYPE,SIZE,MODEL,RM,RO,FSTYPE,LABEL,PARTTYPE,PTTYPE,MOUNTPOINTS,TRAN,UUID")
    try:
        return json.loads(r.stdout).get("blockdevices", [])
    except Exception:
        return []


def mounts_of(d):
    return [m for m in (d.get("mountpoints") or []) if m]


def swaps():
    try:
        return {l.split()[0] for l in open("/proc/swaps").read().splitlines()[1:] if l.strip()}
    except Exception:
        return set()


def by_path(devs):
    return {d["path"]: d for d in devs}


def parent_disk(path, devs):
    """The physical disk a partition lives on (follows partition -> disk, and device-mapper -> its disk)."""
    m = by_path(devs); seen = set()
    cur = m.get(path)
    while cur and cur["path"] not in seen:
        seen.add(cur["path"])
        if cur.get("type") == "disk": return cur["path"]
        pk = cur.get("pkname")
        cur = m.get("/dev/" + pk) if pk else None
    return None


def real_disks(devs):
    return [d for d in devs if d.get("type") == "disk" and not d["name"].startswith(SKIP)]


def loop_backing_devices(devs):
    """Block devices that hold a file the running system is loop-mounted from (an ISO started from a file on a disk)."""
    out = set()
    r = run("losetup", "-J", "-l")
    try:
        loops = json.loads(r.stdout).get("loopdevices", [])
    except Exception:
        loops = []
    for l in loops:
        f = (l.get("back-file") or "").replace(" (deleted)", "")
        if not f: continue
        s = run("findmnt", "-n", "-o", "SOURCE", "-T", f).stdout.strip()
        s = re.sub(r"\[.*\]$", "", s)
        if s.startswith("/dev/"): out.add(s)
    return out


def protected(devs):
    """{disk path: reason} for every disk the running installer depends on. These are never offered and never touched."""
    res = {}
    def add(path, why):
        d = parent_disk(path, devs)
        if d: res.setdefault(d, why)
    for d in devs:
        mps = mounts_of(d)
        if any(m == "/" or m.startswith("/run/archiso") or m.startswith("/run/xlinos-media") for m in mps):
            add(d["path"], "XlinOS is running from this device")
        lab = (d.get("label") or "").upper()
        if lab.startswith(MEDIA_LABELS):
            add(d["path"], "This is the XlinOS installation medium")
    for p in loop_backing_devices(devs):
        add(p, "The installer was started from a file on this disk")
    cmd = ""
    try: cmd = open("/proc/cmdline").read()
    except Exception: pass
    for key in ("archisodevice", "archisosearchuuid", "archisolabel"):
        mt = re.search(key + r"=(\S+)", cmd)
        if not mt: continue
        for d in devs:
            if mt.group(1) in (d.get("path"), d.get("uuid"), d.get("label")): add(d["path"], "This device supplied the installer")
    return res


def busy_reason(path, devs):
    """Why a partition must not be used right now (mounted, swap, or held by RAID/encryption/LVM), or ''."""
    d = by_path(devs).get(path) or {}
    mps = mounts_of(d)
    if mps: return "%s is in use (mounted at %s)" % (path, mps[0])
    if path in swaps(): return "%s is used as swap space" % path
    try:
        if os.listdir("/sys/class/block/%s/holders" % os.path.basename(path)): return "%s is used by another device (RAID, encryption or LVM)" % path
    except Exception: pass
    return ""


def part_disk_busy(disk, devs):
    """Mounted partitions on a disk, as text (empty when none)."""
    out = []
    for d in devs:
        if d.get("type") == "part" and parent_disk(d["path"], devs) == disk and mounts_of(d):
            out.append("%s (%s)" % (d["path"], mounts_of(d)[0]))
    return out


def gaps(disk, min_bytes=MIN_INSTALL):
    """Free gaps on a GPT/MBR disk as (start_sector, end_sector, bytes), biggest first."""
    r = run("sfdisk", "-J", disk)
    try:
        t = json.loads(r.stdout)["partitiontable"]
    except Exception:
        return []
    ss = int(t.get("sectorsize", 512)); first = int(t.get("firstlba", 2048)); last = int(t.get("lastlba", 0))
    if not last: return []
    cur, res = first, []
    for p in sorted(t.get("partitions", []), key=lambda p: p["start"]):
        if p["start"] > cur: res.append((cur, p["start"] - 1))
        cur = max(cur, p["start"] + p["size"])
    if cur <= last: res.append((cur, last))
    out = []
    for a, b in res:
        a = (a + 2047) // 2048 * 2048
        if b >= a and (b - a + 1) * ss >= min_bytes: out.append((a, b, (b - a + 1) * ss))
    return sorted(out, key=lambda g: -g[2])


# ---- other systems on the disks (read only)
KNOWN_EFI = {"microsoft": "Windows", "ubuntu": "Ubuntu", "fedora": "Fedora", "debian": "Debian", "arch": "Linux", "opensuse": "openSUSE",
             "mint": "Linux Mint", "pop": "Pop!_OS", "manjaro": "Manjaro", "endeavouros": "EndeavourOS", "boot": ""}


def probe(dev):
    """Mounts a partition read only for a moment and names the system on it. Returns a short name or ''."""
    fs = dev.get("fstype") or ""
    if not fs or os.geteuid() != 0: return ""
    mps = mounts_of(dev)
    tmp = None
    try:
        if mps: base = mps[0]
        else:
            tmp = tempfile.mkdtemp(prefix="xlprobe", dir="/run"); base = tmp
            types = {"ntfs": "ntfs3", "vfat": "vfat"}.get(fs, fs)
            if run("mount", "-o", "ro,nosuid,nodev,noexec", "-t", types, dev["path"], base, timeout=12).returncode != 0:
                return "Windows (probably)" if fs == "ntfs" else ""
        try:
            if (dev.get("parttype") or "").lower() == ESP or fs == "vfat":
                names = sorted({KNOWN_EFI.get(n.lower(), n) for n in os.listdir(os.path.join(base, "EFI"))} - {""})
                return "Boot files: " + ", ".join(names) if names else ""
        except Exception: pass
        if os.path.isdir(os.path.join(base, "Windows")): return "Windows"
        try:
            for l in open(os.path.join(base, "etc/os-release")):
                if l.startswith("PRETTY_NAME="): return l.split("=", 1)[1].strip().strip('"')
        except Exception: pass
        return ""
    finally:
        if tmp:
            run("umount", tmp);
            try: os.rmdir(tmp)
            except Exception: pass


def scan(with_probe=True):
    devs = lsblk()
    prot = protected(devs)
    efi_mode = os.path.isdir("/sys/firmware/efi")
    res = []
    for d in real_disks(devs):
        kids = [k for k in devs if k.get("type") == "part" and k.get("pkname") == d["name"]]
        parts = []
        for k in sorted(kids, key=lambda k: k["path"]):
            parts.append({"path": k["path"], "size": int(k.get("size") or 0), "fs": k.get("fstype") or "", "label": k.get("label") or "",
                          "esp": (k.get("parttype") or "").lower() == ESP, "mounted": (mounts_of(k) or [""])[0],
                          "os": probe(k) if with_probe and d["path"] not in prot else ""})
        size = int(d.get("size") or 0)
        g = gaps(d["path"])
        res.append({"path": d["path"], "model": (d.get("model") or "Disk").strip(), "size": size, "tran": d.get("tran") or "",
                    "removable": str(d.get("rm")) in ("1", "True", "true"), "readonly": str(d.get("ro")) in ("1", "True", "true"),
                    "table": d.get("pttype") or "none", "partitions": parts, "free": sum(x[2] for x in g) if g else 0,
                    "biggest_gap": g[0][2] if g else 0, "protected": prot.get(d["path"], ""), "efi_boot": efi_mode,
                    "busy": part_disk_busy(d["path"], devs)})
    return res


# ---- the rules
def validate(mode, target, efi=None):
    """Returns a list of reasons the install must NOT go ahead (empty = allowed). Never guesses: an unknown device is refused."""
    errs = []
    devs = lsblk(); m = by_path(devs); prot = protected(devs)
    if mode not in ("erase", "freespace", "partition"): return ["Unknown installation method."]
    if not target or target not in m: return ["The chosen disk or partition was not found."]
    t = m[target]
    if t["name"].startswith(SKIP): return ["That is not a disk XlinOS can be installed on."]
    if str(t.get("ro")) in ("1", "True", "true"): errs.append("That device is read only.")
    disk = parent_disk(target, devs)
    if not disk: return ["Could not tell which physical disk that is."]
    if disk in prot: errs.append("%s: %s. It can never be used as the target." % (disk, prot[disk]))
    if not os.path.isdir("/sys/firmware/efi"): errs.append("This computer did not start in UEFI mode. Turn UEFI on in the firmware settings.")
    if mode == "erase":
        if t.get("type") != "disk": errs.append("Erasing needs a whole disk, not a partition.")
        if int(t.get("size") or 0) < MIN_DISK: errs.append("The disk is too small (XlinOS needs at least 16 GB).")
        bz = part_disk_busy(target, devs)
        if bz: errs.append("Something on this disk is in use: " + ", ".join(bz))
    else:
        if mode == "freespace":
            if t.get("type") != "disk": errs.append("Free-space installation needs a disk.")
            elif not gaps(target): errs.append("There is no free space of at least 10 GB on this disk. Free some up first.")
            elif (t.get("pttype") or "") != "gpt": errs.append("Installing next to another system needs a GPT disk.")
        else:
            if t.get("type") != "part": errs.append("Choose a partition.")
            else:
                if int(t.get("size") or 0) < MIN_INSTALL: errs.append("The partition is too small (XlinOS needs at least 10 GB).")
                if (t.get("parttype") or "").lower() == ESP: errs.append("That is the start-up (EFI) partition. Choose a normal partition.")
                br = busy_reason(target, devs)
                if br: errs.append(br)
                if (t.get("label") or "").upper().startswith(MEDIA_LABELS): errs.append("That is the installation medium.")
        if not efi or efi not in m:
            errs.append("The existing start-up (EFI) partition was not found. XlinOS shares it so your other systems keep starting.")
        else:
            e = m[efi]
            if (e.get("parttype") or "").lower() != ESP: errs.append("The chosen start-up partition is not an EFI System Partition.")
            if parent_disk(efi, devs) in prot: errs.append("The start-up partition is on the installation medium.")
            if parent_disk(efi, devs) != disk: errs.append("The start-up partition must be on the same disk as XlinOS.")
            if efi == target: errs.append("The start-up partition cannot also be the system partition.")
    return errs


def main(a):
    if not a: print(__doc__); return 1
    if a[0] == "scan":
        print(json.dumps(scan(with_probe="--fast" not in a))); return 0
    if a[0] == "validate" and len(a) >= 3:
        errs = validate(a[1], a[2], a[3] if len(a) > 3 else None)
        print(json.dumps({"ok": not errs, "errors": errs})); return 0 if not errs else 2
    if a[0] == "gap" and len(a) == 2:
        g = gaps(a[1])
        if not g: return 2
        print(g[0][0], g[0][1]); return 0
    print(__doc__); return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
