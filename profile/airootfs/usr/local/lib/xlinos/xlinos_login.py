"""XlinOS login logic: no GTK in here, so it can be tested without a screen.
  - Greetd: talks to the greetd login manager over its socket (length-prefixed JSON).
  - Accounts: calls the root helper (xlinos-accounts) through sudo.
"""
import json, os, socket, struct, subprocess

HELPER = ["/usr/bin/sudo", "-n", "/usr/local/lib/xlinos/xlinos-accounts"]
SESSION_CMD = ["/usr/local/bin/xlinos-session"]


class Greetd:
    def __init__(self, path=None):
        self.path = path or os.environ.get("GREETD_SOCK", "")

    def _send(self, s, obj):
        data = json.dumps(obj).encode()
        s.sendall(struct.pack("=I", len(data)) + data)

    def _recv(self, s):
        head = b""
        while len(head) < 4:
            c = s.recv(4 - len(head))
            if not c:
                raise ConnectionError("greetd closed the connection")
            head += c
        (n,) = struct.unpack("=I", head)
        buf = b""
        while len(buf) < n:
            c = s.recv(n - len(buf))
            if not c:
                raise ConnectionError("greetd closed the connection")
            buf += c
        return json.loads(buf)

    def login(self, user, password, cmd=None, env=None):
        """Returns (True, "") when the session was started, else (False, message for the screen)."""
        if not self.path:
            return False, "The login service is not running."
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            s.connect(self.path)
            self._send(s, {"type": "create_session", "username": user})
            answered = False
            while True:
                r = self._recv(s)
                t = r.get("type")
                if t == "auth_message":
                    kind = r.get("auth_message_type")
                    if kind in ("secret", "visible"):
                        if answered:  # asked twice: something else is needed that we cannot show
                            self._send(s, {"type": "cancel_session"}); self._recv(s)
                            return False, "Wrong password."
                        answered = True
                        self._send(s, {"type": "post_auth_message_response", "response": password})
                    else:  # info or error text: acknowledge
                        self._send(s, {"type": "post_auth_message_response", "response": None})
                elif t == "success":
                    self._send(s, {"type": "start_session", "cmd": cmd or SESSION_CMD, "env": env or []})
                    r2 = self._recv(s)
                    if r2.get("type") == "success":
                        return True, ""
                    return False, r2.get("description") or "Could not start the session."
                elif t == "error":
                    try:
                        self._send(s, {"type": "cancel_session"}); self._recv(s)
                    except Exception:
                        pass
                    if r.get("error_type") == "auth_error":
                        return False, "Wrong password."
                    return False, r.get("description") or "Login failed."
                else:
                    return False, "Unexpected answer from the login service."
        except (OSError, ConnectionError, ValueError) as e:
            return False, "Login service error: %s" % type(e).__name__
        finally:
            s.close()


class Accounts:
    def __init__(self, helper=None):
        self.helper = helper or (os.environ.get("XLINOS_HELPER", "").split() or HELPER)

    def call(self, req):
        try:
            r = subprocess.run(self.helper, input=json.dumps(req), capture_output=True, text=True, timeout=30)
            out = json.loads(r.stdout.strip().splitlines()[-1])
            return out if isinstance(out, dict) else {"ok": False, "error": "failed", "message": "Bad answer."}
        except Exception as e:
            return {"ok": False, "error": "failed", "message": "Could not reach the account service (%s)." % type(e).__name__}

    def users(self):
        r = self.call({"cmd": "list"})
        return r.get("users", []) if r.get("ok") else []

    def create(self, name, fullname, password, admin=False, auth=None):
        req = {"cmd": "create", "name": name, "fullname": fullname, "password": password, "admin": admin}
        if auth:
            req["auth"] = auth
        return self.call(req)

    def delete(self, name, auth, purge=False):
        return self.call({"cmd": "delete", "name": name, "purge": purge, "auth": auth})


def suggest_username(fullname):
    """'Ann Lee' -> 'ann'. Only letters and digits; starts with a letter."""
    first = (fullname.strip().split() or [""])[0].lower()
    name = "".join(c for c in first if c.isascii() and c.isalnum())
    while name and not name[0].isalpha():
        name = name[1:]
    return name[:31]
