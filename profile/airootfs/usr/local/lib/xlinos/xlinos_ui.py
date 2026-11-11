"""Shared XlinOS look for the shell: coloured app tiles used by the dock and the launcher."""
import shutil

def _install_theme_hook():
    """Every XlinOS window passes its style sheet through here, so accent colour and light/dark apply everywhere."""
    try:
        import gi
        gi.require_version("Gtk", "4.0")
        from gi.repository import Gtk
        import xlinos_cfg
        orig = Gtk.CssProvider.load_from_data
        def patched(self, data, *a):
            try:
                raw = data.decode() if isinstance(data, bytes) else data
                if "/*raw*/" not in raw: data = xlinos_cfg.themed(data)
            except Exception: pass
            return orig(self, data, *a)
        Gtk.CssProvider.load_from_data = patched
    except Exception:
        pass
_install_theme_hook()

# id, label, symbolic icon, gradient, command, window class (to show the running dot)
APPS = [
    ("files",    "Files",    "folder-symbolic",             ("#3b8bff", "#1e5bff"), "xlinos-files",   "os.xlin.files"),
    ("terminal", "Quickshell", "utilities-terminal-symbolic", ("#1c2a5c", "#0f1838"), "xlinos-terminal", "os.xlin.terminal"),
    ("store",    "Store",    "folder-download-symbolic",         ("#b06bff", "#7a3fe0"), "xlinos-store",    "os.xlin.store"),
    ("settings", "Settings", "emblem-system-symbolic",        ("#7b6dff", "#4b3fd6"), "xlinos-settings", "os.xlin.settings"),
    ("notes",    "Notes",    "document-edit-symbolic",         ("#19d2ff", "#1196e6"), "xlinos-notes",    "os.xlin.notes"),
    ("photos",   "Photos",   "image-x-generic-symbolic",       ("#ffb347", "#ff7a1a"), "xlinos-photos",   "os.xlin.photos"),
    ("calendar", "Calendar", "x-office-calendar-symbolic",     ("#ff6b6b", "#e03a4a"), "xlinos-calendar", "os.xlin.calendar"),
    ("media",    "Media",    "media-playback-start-symbolic", ("#ff7ab8", "#e0407a"), "xlinos-media",    "os.xlin.media"),
    ("calculator", "Calculator", "accessories-calculator-symbolic", ("#8a7bff", "#5a45e0"), "xlinos-calculator", "os.xlin.calculator"),
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
NAMES = {"os.xlin.terminal": "Quickshell", "os.xlin.files": "Files", "os.xlin.store": "Store", "os.xlin.settings": "Settings", "os.xlin.notes": "Notes", "os.xlin.calculator": "Calculator", "os.xlin.media": "Media", "os.xlin.photos": "Photos", "os.xlin.calendar": "Calendar", "os.xlin.edit": "Text Editor", "os.xlin.monitor": "System Monitor", "os.xlin.screenshot": "Screenshot", "os.xlin.clock": "Clock", "os.xlin.keys": "Shortcuts", "os.xlin.clipboard": "Clipboard"}

def friendly(cls):
    return NAMES.get(cls) or (cls.split(".")[-1].capitalize() if cls else "XlinOS")

BASE_CSS = """
button { background-image: none; background-color: rgba(255,255,255,0.09); color: #e6eeff; border: none; box-shadow: none; outline: none;
         border-radius: 12px; min-height: 20px; padding: 7px 16px; }
button:hover { background-color: rgba(255,255,255,0.16); }
button:disabled { opacity: 0.5; }
entry { background-image: none; background-color: rgba(255,255,255,0.07); color: #fff; border: 1px solid rgba(255,255,255,0.14);
        border-radius: 12px; min-height: 22px; padding: 6px 12px; box-shadow: none; outline: none; }
entry:focus-within { border-color: #4f93ff; }
scale trough { background: rgba(255,255,255,0.16); min-height: 6px; border-radius: 3px; border: none; box-shadow: none; }
scale highlight { background: #1e6bff; border-radius: 3px; border: none; }
scale slider { background: #fff; min-width: 18px; min-height: 18px; border-radius: 9px; border: none; box-shadow: 0 1px 4px rgba(0,0,0,0.35); margin: -6px; }
scale trough, scale highlight { background-image: none; outline: none; }
button.sec { background-image: none; background-color: rgba(255,255,255,0.10); color: #e6eeff; border: none; box-shadow: none; border-radius: 12px; min-height: 20px; padding: 8px 18px; }
button.sec:hover { background-color: rgba(255,255,255,0.18); }
button.primary { background-image: none; background-color: #1e6bff; color: #fff; border: none; box-shadow: none; border-radius: 12px; min-height: 20px; padding: 8px 18px; font-weight: 600; }
button.primary:hover { background-color: #3a80ff; }
switch { border-radius: 14px; border: none; box-shadow: none; background: rgba(255,255,255,0.16); }
switch slider { border-radius: 12px; margin: 2px; min-width: 22px; min-height: 22px; background: #fff; box-shadow: none; }
scrollbar slider { border-radius: 4px; min-width: 6px; background: rgba(255,255,255,0.22); }
"""

def window_css():
    return BASE_CSS + """
.xwin { background: rgba(8,14,44,1.0); border-radius: 14px; border: 1px solid rgba(255,255,255,0.14); overflow: hidden; }
.xhead { padding: 0 12px; min-height: 40px; }
.xtitle { color: #dbe6ff; font-weight: 600; font-size: 13px; }
.tl { min-width: 13px; min-height: 13px; padding: 0; border-radius: 7px; border: none; box-shadow: none; background-color: #3a4a7a; }
.tl-close { background-color: #ff5f57; }
.tl-min:hover { background-color: #febc2e; }
.tl-max:hover { background-color: #28c840; }
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
