"""XlinOS system check: finds what is wrong and fixes what it can."""
import os, shutil, subprocess, json, time
import xlinos_cfg as cfg

def _run(cmd, t=4):
    try:
        r = subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True, text=True, timeout=t); return r.returncode, r.stdout.strip()
    except Exception:
        return 1, ""

def checks():
    """List of (id, title, ok, detail)."""
    out = []
    rc, o = _run("nmcli -t -f CONNECTIVITY general")
    out.append(("net", "Internet", o == "full", "Connected" if o == "full" else "Not connected. Open the Wi-Fi menu in the status bar."))
    out.append(("wifi", "Wi-Fi switched on", cfg.wifi_on(), "On" if cfg.wifi_on() else "Switched off"))
    rc, o = _run("systemctl is-active bluetooth")
    out.append(("bt", "Bluetooth service", o == "active", "Running" if o == "active" else "Not running"))
    rc, o = _run("wpctl status", 3)
    out.append(("sound", "Sound", rc == 0 and "Sinks" in o, "Working" if rc == 0 else "The sound system is not answering"))
    free = shutil.disk_usage("/").free / 1e9
    out.append(("disk", "Free disk space", free > 2, "%.1f GB free" % free if free > 2 else "Only %.1f GB free. Remove files you no longer need." % free))
    for pid, name, pat in (("shell", "Desktop (bars and icons)", "lib/xlinos/xlinos-shell"), ("notify", "Notifications", "lib/xlinos/xlinos-notify")):
        rc, o = _run(["pgrep", "-f", pat]); out.append((pid, name, rc == 0, "Running" if rc == 0 else "Not running"))
    try:
        json.load(open(os.path.expanduser("~/.config/xlinos/settings.json"))); good = True
    except FileNotFoundError: good = True
    except Exception: good = False
    out.append(("cfg", "Your settings file", good, "Fine" if good else "Damaged. Fix everything will reset it."))
    missing = [c for c in ("nmcli", "bluetoothctl", "wpctl", "brightnessctl", "grim", "slurp", "wl-copy", "powerprofilesctl") if shutil.which(c) is None]
    out.append(("tools", "System tools", not missing, "All present" if not missing else "Missing: " + ", ".join(missing) + ". Run an update."))
    return out

def fix(log=print):
    """Repairs what can be repaired without an administrator password. Returns True when finished."""
    def step(t): log(t)
    step("Switching Wi-Fi on")
    if not cfg.wifi_on(): _run("nmcli radio wifi on")
    step("Restarting sound")
    _run("systemctl --user restart pipewire pipewire-pulse wireplumber", 8)
    step("Switching Bluetooth on")
    rc, o = _run("systemctl is-active bluetooth")
    if o != "active": _run("sudo -n systemctl start bluetooth", 6)
    _run("bluetoothctl power on", 4)
    p = os.path.expanduser("~/.config/xlinos/settings.json")
    try: json.load(open(p))
    except FileNotFoundError: pass
    except Exception:
        step("Repairing your settings"); shutil.move(p, p + ".broken-%d" % time.time())
    step("Cleaning pictures cache")
    shutil.rmtree(os.path.expanduser("~/.cache/thumbnails"), ignore_errors=True)
    step("Restarting the desktop")
    subprocess.run(["pkill", "-f", "lib/xlinos/xlinos-notify"], capture_output=True)
    subprocess.Popen(["/usr/local/lib/xlinos/xlinos-notify"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    subprocess.run(["pkill", "-f", "lib/xlinos/xlinos-shell"], capture_output=True); time.sleep(0.5)
    subprocess.Popen(["/usr/local/lib/xlinos/xlinos-shell"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    time.sleep(2); step("Done")
    return True
