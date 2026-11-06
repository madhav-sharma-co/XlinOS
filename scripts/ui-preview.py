#!/usr/bin/env python3
"""Renders the real login screen (xlinos-greeter) with fake users and saves a PNG of every screen. Run under xvfb-run in CI.
usage: ui-preview.py OUTDIR"""
import importlib.machinery, importlib.util, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = f"{ROOT}/profile/airootfs/usr/local/lib/xlinos"
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
os.environ.setdefault("GSK_RENDERER", "cairo")
os.environ["XLINOS_SHARE"] = f"{ROOT}/profile/airootfs/usr/share/xlinos"
sys.path.insert(0, LIB)
import gi
gi.require_version("Gtk", "4.0"); gi.require_version("Graphene", "1.0")
from gi.repository import Gdk, GLib, Graphene, Gtk
import xlinos_login

USERS = [{"name": "ann", "fullname": "Ann Lee", "admin": True, "uid": 1000},
         {"name": "bob", "fullname": "Bob Carter", "admin": False, "uid": 1001}]
class FakeAcc:
    def __init__(self): self.u = []
    def users(self): return list(self.u)
    def create(self, *a, **k): return {"ok": True}
    def delete(self, *a, **k): return {"ok": True}
class FakeGreetd:
    def login(self, *a, **k): return False, "Wrong password."
xlinos_login.Accounts, xlinos_login.Greetd = FakeAcc, FakeGreetd

loader = importlib.machinery.SourceFileLoader("greeter", f"{LIB}/xlinos-greeter")
spec = importlib.util.spec_from_loader("greeter", loader); G = importlib.util.module_from_spec(spec); loader.exec_module(G)

def shot(win, name):
    w, h = win.get_width(), win.get_height()
    snap = Gtk.Snapshot(); Gtk.WidgetPaintable.new(win).snapshot(snap, w, h)
    tex = win.get_native().get_renderer().render_texture(snap.to_node(), Graphene.Rect().init(0, 0, w, h))
    tex.save_to_png(f"{out}/{name}.png"); print("saved", name, w, h, flush=True)

class App(Gtk.Application):
    def do_activate(self):
        prov = Gtk.CssProvider(); prov.load_from_string(G.CSS.decode())
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        win = G.Greeter(self); win.unfullscreen(); win.set_default_size(1280, 800); win.present()
        acc = win.acc
        def scene(i=[0]):
            n = i[0]; i[0] += 1
            if n == 0:   acc.u = []; win.reload()                                   # first start
            elif n == 1: shot(win, "1-welcome-create-first-user")
            elif n == 2: acc.u = list(USERS); win.reload()
            elif n == 3: shot(win, "2-login")
            elif n == 4: win.l_msg.set_text("Wrong password."); win.l_pass.set_text("secret")
            elif n == 5: shot(win, "3-login-wrong-password")
            elif n == 6: win.show_users()
            elif n == 7: shot(win, "4-switch-user")
            elif n == 8: win.show_create(first=False)
            elif n == 9: shot(win, "5-new-user")
            elif n == 10: win.show_delete()
            elif n == 11: shot(win, "6-delete-user")
            else: self.quit(); return False
            return True
        GLib.timeout_add(900, scene)
App().run(None)
