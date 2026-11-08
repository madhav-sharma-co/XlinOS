"""Shared XlinOS look for the shell: coloured app tiles used by the dock and the launcher."""
import shutil

# id, label, symbolic icon, gradient, command, window class (to show the running dot)
APPS = [
    ("files",    "Files",    "folder-symbolic",             ("#3b8bff", "#1e5bff"), "xlinos-files",   "os.xlin.files"),
    ("terminal", "Terminal", "utilities-terminal-symbolic", ("#1c2a5c", "#0f1838"), "xlinos-terminal", "os.xlin.terminal"),
    ("settings", "Settings", "emblem-system-symbolic",        ("#7b6dff", "#4b3fd6"), "xlinos-settings", "os.xlin.settings"),
    ("browser",  "Browser",  "applications-internet-symbolic",        ("#19d2ff", "#0a74ff"), "xlinos-browser", ""),
]

def available():
    return [a for a in APPS if shutil.which(a[4].split()[0], path="/usr/local/bin:/usr/bin")]

def css():
    out = [".apptile { border-radius: 16px; min-width: 52px; min-height: 52px; }",
           ".apptile image { color: #ffffff; -gtk-icon-size: 28px; }"]
    for a in APPS:
        out.append(".t-%s { background-image: linear-gradient(135deg, %s, %s); }" % (a[0], a[3][0], a[3][1]))
    out.append(".t-apps { background-image: linear-gradient(135deg, #2a3a7a, #16224f); }")
    out.append(".t-other { background-image: linear-gradient(135deg, #3a4a8a, #1c2a5c); }")
    return "\n".join(out)


# ---------------------------------------------------------------- window chrome for XlinOS apps
NAMES = {"os.xlin.terminal": "Terminal", "os.xlin.files": "Files", "os.xlin.store": "Store", "os.xlin.settings": "Settings"}

def friendly(cls):
    return NAMES.get(cls) or (cls.split(".")[-1].capitalize() if cls else "XlinOS")

def window_css():
    return """
.xwin { background: rgba(8,14,44,0.97); border-radius: 14px; border: 1px solid rgba(255,255,255,0.14); }
.xhead { padding: 0 12px; min-height: 40px; }
.xtitle { color: #dbe6ff; font-weight: 600; font-size: 13px; }
.tl { min-width: 13px; min-height: 13px; padding: 0; border-radius: 7px; border: none; box-shadow: none; background: #3a4a7a; }
.tl-close { background: #ff5f57; }
.tl-min:hover { background: #febc2e; }
.tl-max:hover { background: #28c840; }
"""

def make_window(app, title, width=900, height=560):
    """A frameless XlinOS window with close / minimise / maximise at the top-left. Returns (window, content_box)."""
    import subprocess, json
    from gi.repository import Gtk, Gdk
    win = Gtk.ApplicationWindow(application=app)
    win.set_decorated(False); win.set_default_size(width, height); win.set_title(title)
    root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); root.add_css_class("xwin")
    head = Gtk.CenterBox(); head.add_css_class("xhead")
    lights = Gtk.Box(spacing=8, valign=Gtk.Align.CENTER)

    def active_address():
        try:
            return json.loads(subprocess.run(["hyprctl", "-j", "activewindow"], capture_output=True, text=True, timeout=2).stdout)["address"]
        except Exception:
            return None

    def light(cls, tip, fn):
        b = Gtk.Button(); b.add_css_class("tl"); b.add_css_class(cls); b.set_tooltip_text(tip)
        b.set_valign(Gtk.Align.CENTER); b.connect("clicked", lambda _b: fn()); lights.append(b)

    def minimise():
        a = active_address()
        if a:
            subprocess.Popen(["hyprctl", "eval", 'hl.dispatch(hl.dsp.window.move({ workspace = "special:minimized", follow = false, window = "address:%s" }))' % a])
    light("tl-close", "Close", win.close)
    light("tl-min", "Minimise", minimise)
    light("tl-max", "Maximise", lambda: subprocess.Popen(["/usr/local/lib/xlinos/xlinos-snap", "max"]))
    head.set_start_widget(lights)
    t = Gtk.Label(label=title); t.add_css_class("xtitle"); head.set_center_widget(t)
    win.bind_property("title", t, "label")
    head.set_end_widget(Gtk.Box(width_request=60))

    drag = Gtk.GestureClick(button=1)
    def pressed(g, n, x, y):
        if n == 2:
            subprocess.Popen(["/usr/local/lib/xlinos/xlinos-snap", "max"]); return
        surf = win.get_native().get_surface()
        surf.begin_move(g.get_device(), 1, x, y, g.get_current_event_time())
    drag.connect("pressed", pressed); head.add_controller(drag)

    body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, vexpand=True)
    root.append(head); root.append(body); win.set_child(root)
    return win, body
