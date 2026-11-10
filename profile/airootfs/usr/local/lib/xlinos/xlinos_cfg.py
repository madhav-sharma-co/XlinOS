"""XlinOS settings store and system actions shared by Settings, the control panel, the launcher and the shell.
Settings live in ~/.config/xlinos/settings.json. Nothing here draws anything."""
import json, os, subprocess, shutil

PATH = os.path.expanduser("~/.config/xlinos/settings.json")
DEFAULTS = {
    "accent": "#1e6bff", "text_scale": 1.0, "animations": "smooth", "transparency": 0.86,
    "bar_items": {"wifi": True, "bluetooth": True, "sound": True, "battery": True, "clock": True},
    "show_desktop_clock": True,
    "runbar_pins": None,            # None = all XlinOS apps; otherwise a list of app ids / desktop ids
    "launcher_pins": None, "recent": [],
    "lock_minutes": 5, "sleep_minutes": 15,
    "natural_scroll": True, "tap_to_click": True, "pointer_speed": 0.0,
    "dnd": False, "night_light": False, "power_mode": "balanced", "airplane": False,
}
_cache = {"mtime": None, "data": None}

def load():
    try:
        m = os.path.getmtime(PATH)
        if _cache["mtime"] != m:
            _cache["data"] = json.load(open(PATH)); _cache["mtime"] = m
        return _cache["data"]
    except Exception:
        return {}

def get(key, default=None):
    d = load()
    if key in d: return d[key]
    return DEFAULTS.get(key, default) if default is None else default

def set(key, value):
    d = dict(load()); d[key] = value
    os.makedirs(os.path.dirname(PATH), exist_ok=True)
    tmp = PATH + ".tmp"; json.dump(d, open(tmp, "w"), indent=1); os.replace(tmp, PATH)
    _cache["mtime"] = None

def run(cmd, timeout=6):
    try:
        r = subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True, text=True, timeout=timeout); return r.stdout.strip()
    except Exception:
        return ""

def bg(cmd):
    subprocess.Popen(cmd, shell=isinstance(cmd, str), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)

def have(c): return shutil.which(c) is not None

# ---------------------------------------------------------------- Hyprland live settings (Lua config: hyprctl eval)
def hypr_eval(lua):
    bg(["hyprctl", "eval", lua])

def apply_animations():
    mode = get("animations")
    hypr_eval("hl.config({ animations = { enabled = %s } })" % ("false" if mode == "off" else "true"))

def apply_input():
    hypr_eval("hl.config({ input = { sensitivity = %s, touchpad = { natural_scroll = %s, tap_to_click = %s } } })" % (
        float(get("pointer_speed")), str(bool(get("natural_scroll"))).lower(), str(bool(get("tap_to_click"))).lower()))

def apply_all():
    apply_animations(); apply_input(); apply_idle()
    set_night_light(get("night_light")); power_mode(get("power_mode"))

# ---------------------------------------------------------------- lock and sleep (hypridle)
def apply_idle():
    lock, sleep = int(get("lock_minutes")), int(get("sleep_minutes"))
    d = os.path.expanduser("~/.config/hypr"); os.makedirs(d, exist_ok=True)
    txt = "general {\n    lock_cmd = xlinos-lock\n    before_sleep_cmd = xlinos-lock\n}\n"
    if lock > 0: txt += "listener {\n    timeout = %d\n    on-timeout = xlinos-lock\n}\n" % (lock * 60)
    if sleep > 0: txt += "listener {\n    timeout = %d\n    on-timeout = systemctl suspend\n}\n" % (sleep * 60)
    open(d + "/hypridle.conf", "w").write(txt)
    run("pkill hypridle")
    if have("hypridle"): bg("hypridle")

# ---------------------------------------------------------------- quick toggles
def wifi_on(): return "enabled" in run("nmcli radio wifi")
def bt_on(): return "Powered: yes" in run("bluetoothctl show")
def set_airplane(on):
    set("airplane", bool(on))
    bg("rfkill block all" if on else "rfkill unblock all")
    if not on: bg("nmcli radio wifi on")
def set_dnd(on): set("dnd", bool(on))
def set_night_light(on):
    set("night_light", bool(on)); run("pkill hyprsunset")
    if on and have("hyprsunset"): bg("hyprsunset -t 4000")
def power_modes():
    out = run("powerprofilesctl list")
    return [m for m in ("power-saver", "balanced", "performance") if m in out] if out else []
def power_mode(mode):
    if mode and have("powerprofilesctl"):
        set("power_mode", mode); bg(["powerprofilesctl", "set", mode])
def volume():
    out = run("wpctl get-volume @DEFAULT_AUDIO_SINK@")
    try: return int(float(out.split()[1]) * 100), "MUTED" in out
    except Exception: return 50, False
def set_volume(v): bg("wpctl set-volume -l 1.0 @DEFAULT_AUDIO_SINK@ %d%%" % v)
def toggle_mute(): run("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle")
def brightness():
    try: return int(run("brightnessctl -m").split(",")[3].rstrip("%"))
    except Exception: return None
def set_brightness(v): bg("brightnessctl set %d%%" % max(1, v))

# ---------------------------------------------------------------- pins and recent apps
def push_recent(app_id, limit=12):
    r = [a for a in get("recent") if a != app_id]; r.insert(0, app_id); set("recent", r[:limit])
def toggle_pin(key, app_id):
    pins = get(key)
    if pins is None: pins = []
    pins = list(pins)
    if app_id in pins: pins.remove(app_id)
    else: pins.append(app_id)
    set(key, pins); return app_id in pins

# ---------------------------------------------------------------- look: accent and text size
def themed(css):
    """Swap the default blue for the chosen accent (css is str or bytes) and return bytes."""
    s = css.decode() if isinstance(css, bytes) else css
    a = get("accent")
    if a and a.lower() != "#1e6bff":
        s = s.replace("#1e6bff", a).replace("#3a80ff", a).replace("#1e4fd0", a)
    return s.encode()

ACCENTS = [("Blue", "#1e6bff"), ("Violet", "#7b5cff"), ("Pink", "#e0407a"), ("Orange", "#ff7a1a"), ("Green", "#22b868"), ("Teal", "#12b5c8")]

# ---------------------------------------------------------------- default apps
DEFAULT_KINDS = [("Web browser", "x-scheme-handler/http", "browser"), ("Files", "inode/directory", "files"), ("Text", "text/plain", "edit"),
                 ("Images", "image/png", "photos"), ("Music and video", "video/mp4", "media"), ("PDF", "application/pdf", "pdf")]
def desktop_apps():
    from gi.repository import Gio
    return sorted([a for a in Gio.AppInfo.get_all() if a.should_show()], key=lambda a: a.get_name().lower())
def set_default(mime, desktop_id):
    run(["xdg-mime", "default", desktop_id, mime])
    if mime == "x-scheme-handler/http":
        run(["xdg-mime", "default", desktop_id, "x-scheme-handler/https"]); run(["xdg-settings", "set", "default-web-browser", desktop_id])
def get_default(mime): return run(["xdg-mime", "query", "default", mime])
