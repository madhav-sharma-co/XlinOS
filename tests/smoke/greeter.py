# Scenario for the login screen (run by gtk_stub.py with `win` = Greeter). GTK is stubbed; accounts and greetd are fakes.
class E:  # a text box / drop-down / check box that really keeps its value
    def __init__(s, t=""): s.t = t; s.val = t; s.on = False
    def get_text(s): return s.t
    def set_text(s, t): s.t = t
    def grab_focus(s): pass
    def set_visible(s, v): pass
    def get_active(s): return s.on
    def set_active(s, v): s.on = v
    def set_model(s, m): pass
    def __getattr__(s, n): return lambda *a, **k: None

class FakeAcc:
    def __init__(s, users): s.u = users; s.calls = []
    def users(s): return s.u
    def create(s, name, full, pw, admin=False, auth=None):
        s.calls.append(("create", name, full, pw, admin, auth))
        if auth and auth.get("password") != "adminpw": return {"ok": False, "error": "auth_failed", "message": "Wrong password."}
        s.u.append({"name": name, "fullname": full or name, "admin": admin or not s.u, "uid": 1000 + len(s.u)})
        return {"ok": True, "name": name}
    def delete(s, name, auth, purge=False):
        s.calls.append(("delete", name, auth, purge))
        s.u[:] = [u for u in s.u if u["name"] != name]
        return {"ok": True, "name": name}

class FakeGreetd:
    def __init__(s): s.calls = []
    def login(s, user, pw, cmd=None, env=None):
        s.calls.append((user, pw)); return (pw == "good", "" if pw == "good" else "Wrong password.")

class FakeApp:
    quit_called = 0
    def quit(s): s.quit_called += 1

app_ = FakeApp()
win.get_application = lambda: app_
win.bg = lambda fn, done: done(fn())                # run background work at once
win.picked = lambda dd: getattr(dd, "val", "")
acc, gd = FakeAcc([]), FakeGreetd()
win.acc, win.greetd = acc, gd
for n in ("c_full", "c_name", "c_pw", "c_pw2", "c_auth_pw", "l_pass", "d_pw", "c_make_admin", "d_purge"):
    setattr(win, n, E())
for n in ("c_msg", "l_msg", "u_msg", "d_msg", "l_avatar", "l_name", "c_title", "c_sub"):
    setattr(win, n, E())
win.c_auth_user, win.d_user, win.d_auth = E(), E(), E()
win.save_last = lambda n: None; win.read_last = lambda: ""

# 1. first start: no users -> the welcome/create screen, then the new user is logged in at once
win.reload()
assert win.c_first is True, "no users must show the first-user screen"
win.c_full.t, win.c_name.t, win.c_pw.t, win.c_pw2.t = "Ann Lee", "ann", "good", "good"
win.do_create()
assert acc.calls[0][:5] == ("create", "ann", "Ann Lee", "good", False) and acc.calls[0][5] is None
assert gd.calls == [("ann", "good")], gd.calls
assert app_.quit_called == 1, "the greeter must exit after the session starts"

# 2. mismatching passwords never reach the helper
n = len(acc.calls)
win.c_pw.t, win.c_pw2.t = "a", "b"; win.show_create(first=False); win.c_name.t = "bob"; win.c_pw.t, win.c_pw2.t = "a", "b"
win.do_create(); assert len(acc.calls) == n and "match" in win.c_msg.t

# 3. second user needs an admin password
win.show_create(first=False)
win.c_full.t, win.c_name.t, win.c_pw.t, win.c_pw2.t = "Bob", "bob", "bobpw", "bobpw"
win.c_auth_user.val, win.c_auth_pw.t = "ann", "wrong"
win.do_create(); assert "Wrong" in win.c_msg.t and len(acc.u if hasattr(acc, "u") else []) == 1
win.c_auth_pw.t = "adminpw"; win.do_create()
assert [u["name"] for u in acc.u] == ["ann", "bob"]

# 4. login: wrong password shows a message, right one starts the session
win.current = "bob"; win.show_login()
win.l_pass.t = "bad"; win.do_login(); assert win.l_msg.t == "Wrong password." and app_.quit_called == 1
win.l_pass.t = "good"; win.do_login(); assert app_.quit_called == 2
win.l_pass.t = ""; win.do_login(); assert "Enter" in win.l_msg.t

# 5. screens that list and delete users
win.show_users()
win.show_delete(); win.d_user.val = "bob"; win.d_auth.val = "ann"; win.d_pw.t = "adminpw"; win.d_purge.on = True
win.do_delete()
assert acc.calls[-1] == ("delete", "bob", {"user": "ann", "password": "adminpw"}, True), acc.calls[-1]
assert [u["name"] for u in acc.u] == ["ann"]
