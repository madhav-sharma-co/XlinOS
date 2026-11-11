"""XlinOS settings store and system actions shared by Settings, the control panel, the launcher and the shell.
Settings live in ~/.config/xlinos/settings.json. Nothing here draws anything."""
import json, os, subprocess, shutil

PATH = os.path.expanduser("~/.config/xlinos/settings.json")
DEFAULTS = {
    "accent": "#1e6bff", "theme": "dark", "text_scale": 1.0, "animations": "smooth", "transparency": 0.86,
    "bar_items": {"wifi": True, "bluetooth": True, "sound": True, "battery": True, "clock": True},
    "show_desktop_clock": True,
    "runbar_pins": None,            # None = all XlinOS apps; otherwise a list of app ids / desktop ids
    "launcher_pins": None, "desktop_icons": None, "widgets": [], "todo": [], "recent": [],
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

def run(cmd, timeout=2):
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
DEFAULT_DESKTOP = ["files", "settings"]
# the desktop list holds app ids (text) and app folders: {"folder": "Name", "items": [app ids]}
def desktop_icons():
    v = get("desktop_icons"); return list(DEFAULT_DESKTOP if v is None else v)
def desk_id(x): return x if isinstance(x, str) else "folder:" + x["folder"]
def _all_ids():
    out = set()
    for x in desktop_icons():
        if isinstance(x, str): out.add(x)
        else: out.update(x["items"])
    return out
def add_desktop_icon(i):
    if i in _all_ids(): return
    set("desktop_icons", desktop_icons() + [i])
def remove_desktop_icon(i):
    out = []
    for x in desktop_icons():
        if isinstance(x, str):
            if x != i: out.append(x)
        else:
            x = dict(x, items=[y for y in x["items"] if y != i])
            if len(x["items"]) > 1: out.append(x)
            else: out.extend(x["items"])            # a folder with one app left is dissolved
    set("desktop_icons", out)
def _unique_folder(base="Folder"):
    names = {x["folder"] for x in desktop_icons() if not isinstance(x, str)}
    n, k = base, 1
    while n in names: k += 1; n = "%s %d" % (base, k)
    return n
def desktop_drop(dragged, target):
    """Drop one app on another: they become a folder (like on a phone); drop on a folder: the app goes in."""
    if dragged == target or dragged.startswith("folder:"): return
    cur = desktop_icons(); out = []
    for x in cur:
        if isinstance(x, str) and x == dragged: continue
        if not isinstance(x, str): x = dict(x, items=[y for y in x["items"] if y != dragged])
        out.append(x)
    res = []
    for x in out:
        if desk_id(x) == target:
            if isinstance(x, str): x = {"folder": _unique_folder(), "items": [x, dragged]}
            else: x = dict(x, items=x["items"] + [dragged])
        res.append(x)
    # folders emptied down to one app turn back into that app
    fin = []
    for x in res:
        if not isinstance(x, str) and len(x["items"]) < 2: fin.extend(x["items"])
        else: fin.append(x)
    set("desktop_icons", fin)
def desktop_take_out(app_id): remove_desktop_icon(app_id); add_desktop_icon(app_id)
def desktop_rename_folder(old, new):
    new = (new or "").strip()
    if not new or new == old: return
    if any(not isinstance(x, str) and x["folder"] == new for x in desktop_icons()): new = _unique_folder(new)
    set("desktop_icons", [x if isinstance(x, str) or x["folder"] != old else dict(x, folder=new) for x in desktop_icons()])
def desktop_dissolve_folder(name):
    out = []
    for x in desktop_icons():
        if not isinstance(x, str) and x["folder"] == name: out.extend(x["items"])
        else: out.append(x)
    set("desktop_icons", out)

def toggle_pin(key, app_id):
    pins = get(key)
    if pins is None: pins = []
    pins = list(pins)
    if app_id in pins: pins.remove(app_id)
    else: pins.append(app_id)
    set(key, pins); return app_id in pins

# ---------------------------------------------------------------- look: accent and text size
import re as _re
_LIGHT_TEXT = _re.compile(r"(?<![\w-])color:\s*(?:#fff(?:fff)?|#e6eeff|#dbe6ff|#cdd9f5)\b", _re.I)
_LIGHT_FIX = """
button.primary, button.primary label, .go, .go label, .act:checked, .act:checked label, button:checked, button:checked label,
.tl, .apptile, .apptile image, .accent, .accent label, .acc, .acc label { color: #ffffff; }
"""
def light(css):
    """Turn the dark XlinOS palette into the light one (css is str or bytes) and return str."""
    s = css.decode() if isinstance(css, bytes) else css
    s = _re.sub(r"rgba\(\s*255\s*,\s*255\s*,\s*255\s*,\s*([0-9.]+)\s*\)", lambda m: "rgba(15,35,95,%.2f)" % min(1.0, float(m.group(1)) * 0.85), s)
    s = _re.sub(r"rgba\(\s*(?:8\s*,\s*14\s*,\s*44|10\s*,\s*18\s*,\s*52)\s*,", "rgba(246,248,255,", s)
    s = _LIGHT_TEXT.sub("color: #14203f", s)
    for a, b in (("#9db4e6", "#5b6c96"), ("#8fb0ff", "#2c5fd0"), ("#1c2a5c", "#dde5f8"), ("#3a4a8a", "#c3cde8"), ("#3a4a7a", "#b9c4e0")):
        s = s.replace(a, b)
    return s + _LIGHT_FIX

def is_light(): return get("theme") == "light"

def themed(css):
    """Swap the default blue for the chosen accent (css is str or bytes) and return bytes."""
    s = css.decode() if isinstance(css, bytes) else css
    a = get("accent")
    if a and a.lower() != "#1e6bff":
        s = s.replace("#1e6bff", a).replace("#3a80ff", a).replace("#1e4fd0", a)
    if is_light() and "/*nolight*/" not in s: s = light(s)
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
