#!/usr/bin/env python3
"""Tests the login logic against a fake greetd socket and a fake account helper. No GTK, no root."""
import json, os, socket, struct, sys, tempfile, threading
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "profile/airootfs/usr/local/lib/xlinos"))
import xlinos_login as L

def send(c, o): d = json.dumps(o).encode(); c.sendall(struct.pack("=I", len(d)) + d)
def recv(c):
    n = struct.unpack("=I", c.recv(4))[0]; b = b""
    while len(b) < n: b += c.recv(n - len(b))
    return json.loads(b)

def serve(path, good, log, extra_prompt=False):
    srv = socket.socket(socket.AF_UNIX); srv.bind(path); srv.listen(1)
    def run():
        c, _ = srv.accept()
        try:
            m = recv(c); log.append(m)
            send(c, {"type": "auth_message", "auth_message_type": "secret", "auth_message": "Password:"})
            m = recv(c); log.append(m)
            if m["response"] == good:
                send(c, {"type": "success"}); m = recv(c); log.append(m); send(c, {"type": "success"})
            elif extra_prompt:
                send(c, {"type": "auth_message", "auth_message_type": "secret", "auth_message": "Again:"})
                log.append(recv(c)); send(c, {"type": "success"})
            else:
                send(c, {"type": "error", "error_type": "auth_error", "description": "x"}); log.append(recv(c)); send(c, {"type": "success"})
        finally:
            c.close(); srv.close()
    t = threading.Thread(target=run, daemon=True); t.start(); return t

d = tempfile.mkdtemp(); fail = 0
def check(name, cond):
    global fail
    print(("PASS " if cond else "FAIL ") + name); fail |= (not cond)

p = os.path.join(d, "a.sock"); log = []; t = serve(p, "right", log)
ok, msg = L.Greetd(p).login("ann", "right"); t.join(2)
check("right password starts the session", ok and log[-1]["type"] == "start_session" and log[-1]["cmd"] == L.SESSION_CMD)
check("user name sent", log[0] == {"type": "create_session", "username": "ann"})

p = os.path.join(d, "b.sock"); log = []; t = serve(p, "right", log)
ok, msg = L.Greetd(p).login("ann", "wrong"); t.join(2)
check("wrong password is refused with a message", (not ok) and msg == "Wrong password." and log[-1]["type"] == "cancel_session")

p = os.path.join(d, "c.sock"); log = []; t = serve(p, "right", log, extra_prompt=True)
ok, msg = L.Greetd(p).login("ann", "wrong"); t.join(2)
check("a second prompt is not answered", (not ok) and log[-1]["type"] == "cancel_session")

ok, msg = L.Greetd(os.path.join(d, "none.sock")).login("ann", "x")
check("missing socket gives a message, not a crash", (not ok) and "error" in msg.lower())
ok, msg = L.Greetd("").login("ann", "x")
check("no GREETD_SOCK gives a message", (not ok) and "not running" in msg)

h = os.path.join(d, "helper"); open(h, "w").write('#!/bin/sh\ncat >/dev/null\necho \'{"ok": true, "users": [{"name": "ann", "fullname": "Ann", "admin": true, "uid": 1000}]}\'\n'); os.chmod(h, 0o755)
check("accounts: list through the helper", L.Accounts([h]).users()[0]["name"] == "ann")
r = L.Accounts(["/nonexistent/helper"]).call({"cmd": "list"})
check("accounts: missing helper gives an error answer", r["ok"] is False and "account service" in r["message"])
check("suggest_username", [L.suggest_username(x) for x in ("Ann Lee", "  José K", "1bob", "")] == ["ann", "jos", "bob", ""])
sys.exit(fail)
