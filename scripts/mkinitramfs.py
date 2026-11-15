#!/usr/bin/env python3
"""XlinOS initramfs packer: writes a newc cpio archive (gzip) without needing cpio.

usage: mkinitramfs.py <rootdir> <output.cpio.gz>
Files in <rootdir> are packed as-is; /dev/console and /dev/null nodes are added.
"""
import gzip
import os
import stat
import sys

def entry(ino, name, mode, data=b"", rdev=(0, 0)):
    nlink = 2 if stat.S_ISDIR(mode) else 1
    hdr = "070701" + "".join(
        "%08X" % v
        for v in (ino, mode, 0, 0, nlink, 0, len(data), 0, 0, rdev[0], rdev[1],
                  len(name) + 1, 0)
    )
    out = hdr.encode() + name.encode() + b"\0"
    out += b"\0" * (-len(out) % 4)
    out += data + b"\0" * (-len(data) % 4)
    return out

def main():
    root, dest = sys.argv[1], sys.argv[2]
    blob, ino = b"", 1
    for dirpath, dirs, files in sorted(os.walk(root)):
        dirs.sort()
        rel = os.path.relpath(dirpath, root)
        if rel != ".":
            blob += entry(ino, rel, stat.S_IFDIR | 0o755)
            ino += 1
        for f in sorted(files):
            p = os.path.join(dirpath, f)
            name = os.path.relpath(p, root)
            mode = stat.S_IFREG | (0o755 if os.access(p, os.X_OK) else 0o644)
            with open(p, "rb") as fh:
                blob += entry(ino, name, mode, fh.read())
            ino += 1
    blob += entry(ino, "dev", stat.S_IFDIR | 0o755); ino += 1
    blob += entry(ino, "dev/console", stat.S_IFCHR | 0o600, rdev=(5, 1)); ino += 1
    blob += entry(ino, "dev/null", stat.S_IFCHR | 0o666, rdev=(1, 3)); ino += 1
    blob += entry(0, "TRAILER!!!", 0)
    with gzip.open(dest, "wb", 9) as out:
        out.write(blob)

if __name__ == "__main__":
    main()
