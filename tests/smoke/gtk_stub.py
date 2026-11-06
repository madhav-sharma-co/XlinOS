"""Smoke-run an Xlin-soft GTK app with a stubbed GTK (no display needed): catches NameError, AttributeError and
wrong-argument mistakes in our own code. Usage: SCEN=scenario.py gtk_stub.py <app file> <window class>"""
import sys, types, importlib.machinery, importlib.util, traceback, os
from unittest.mock import MagicMock

class Meta(type):
    def __getattr__(cls, name):
        if name.startswith('__'): raise AttributeError(name)
        if name.isupper() or (name.upper()==name): return 1
        return make(name)

class Base(metaclass=Meta):
    def __init__(self, *a, **k):
        self._d = {}
    def __getattr__(self, name):
        if name.startswith('__'): raise AttributeError(name)
        def f(*a, **k):
            if name in ('get_first_child','get_next_sibling','get_last_child','get_prev_sibling','get_parent','get_focus','get_visible_child'): return None
            if name == 'get_selection_bounds': return ()
            if name == 'compute_bounds': return (True, Fake())
            if name in ('get_y','get_x'): return 0
            if name.endswith(('_text','_label','_title','_name','_path','_filename','_uri')) and name.startswith('get_'): return ''
            if name.endswith(('_offset','_line','_line_count','_width','_height','_value','_selected','_position','_current_page','_n_pages','_page_size','_upper','_lower','_scale_factor')) and name.startswith('get_'): return 0
            if name.startswith(('has_','get_can_','get_has_')): return False
            return Fake()
        return f
    def __iter__(self): return iter(())
    def __int__(self): return 1
    def __bool__(self): return True
    def __lt__(self, o): return False
    __gt__ = __le__ = __ge__ = __lt__
    def __add__(self, o): return self
    __radd__ = __sub__ = __mul__ = __truediv__ = __rsub__ = __rmul__ = __add__
    def __getitem__(self, i): return Fake()
    def __len__(self): return 1
    def __index__(self): return 1
    def __and__(self, o): return 0
    __rand__ = __or__ = __ror__ = __and__
    def __float__(self): return 1.0

class Fake(Base): pass
_cache = {}
def make(name):
    if name not in _cache:
        _cache[name] = type(name, (Base,), {})
    return _cache[name]

class Mod(types.ModuleType):
    def __getattr__(self, name):
        if name.startswith('__'): raise AttributeError(name)
        if name.isupper(): return 1
        return make(name)

repo = types.ModuleType('gi.repository')
for n in ('Gtk','Gdk','Gio','GLib','Pango','GdkPixbuf','GtkSource','Gst','Poppler','Graphene','GObject','Vte','Adw'):
    m = Mod(n); setattr(repo, n, m); sys.modules['gi.repository.'+n] = m
gi = types.ModuleType('gi'); gi.require_version = lambda *a: None; gi.repository = repo
sys.modules['gi'] = gi; sys.modules['gi.repository'] = repo
sys.modules['cairo'] = Mod('cairo')

path, clsname = sys.argv[1], sys.argv[2]
sys.argv = [path]
loader = importlib.machinery.SourceFileLoader('app_mod', path)
spec = importlib.util.spec_from_loader('app_mod', loader)
mod = importlib.util.module_from_spec(spec)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib'))
spec.loader.exec_module(mod)
app = Fake()
try:
    try:
        win = getattr(mod, clsname)(app)
    except TypeError as e:
        if 'reload_css' in str(e): win = getattr(mod, clsname)(app, lambda: None)
        else: raise
    print('constructed', clsname)
    scen = os.environ.get('SCEN')
    if scen:
        exec(open(scen).read(), {'win': win, 'mod': mod, 'os': os, 'Fake': Fake})
        print('scenario ok')
except Exception:
    traceback.print_exc(); sys.exit(1)
