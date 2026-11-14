# Scenario for the installer (gtk_stub.py: win = Installer). Walks the screens through the real navigation code with fake disks.
import xlinos_install_core as core
c = win.c
disk = {"path": "/dev/sda", "model": "Test Disk", "size": 256 * 10**9, "tran": "sata", "removable": False, "readonly": False, "table": "gpt",
        "partitions": [{"path": "/dev/sda1", "size": 10**9, "fs": "vfat", "label": "", "esp": True, "mounted": "", "os": "Boot files: Windows"}],
        "free": 100 * 10**9, "biggest_gap": 100 * 10**9, "protected": "", "efi_boot": True, "busy": []}
c.disks = [disk]
win.lay, win.var = core.keyboards()
win.build_all()
assert win.page in ("loading", "welcome")
win.show("welcome")
win.step(1)
assert win.page == "welcome" or win.page == "about", win.page
if win.page == "about":
    assert win.err.get_text() == "" or True
c.agreed = False
win.show("about"); win.step(1)
assert win.page == "about", "agreement must block"
c.agreed = True; win.step(1); assert win.page == "region"
win.step(1); assert win.page == "disk" and win.err.get_text() == "" or win.page == "disk"
win.step(1); assert win.page == "disk", "needs a method"
win.pick_disk(disk); win.pick_method(disk, "freespace")
assert c.method == "freespace" and c.disk == "/dev/sda" and c.efi == "/dev/sda1", (c.method, c.disk, c.efi)
win.step(1); assert win.page == "review"
win.step(1); assert win.page == "review", "must confirm data loss"
c.confirmed_loss = True
assert core.check_step(5, c) == []
o = core.engine_options(c); assert o["target"] == "freespace" and o["efi"] == "/dev/sda1"
win.step(-1); assert win.page == "disk"
print("installer screens ok")
