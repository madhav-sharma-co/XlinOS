"""Shared XlinOS look for the shell: coloured app tiles used by the dock and the launcher."""
import shutil

# id, label, symbolic icon, gradient, command, window class (to show the running dot)
APPS = [
    ("files",    "Files",    "folder-symbolic",             ("#3b8bff", "#1e5bff"), "xlinos-files",   "thunar"),
    ("terminal", "Terminal", "utilities-terminal-symbolic", ("#1c2a5c", "#0f1838"), "kitty",          "kitty"),
    ("browser",  "Browser",  "web-browser-symbolic",        ("#19d2ff", "#0a74ff"), "xlinos-browser", ""),
]

def available():
    return [a for a in APPS if shutil.which(a[4].split()[0]) or shutil.which(a[4].split()[0], path="/usr/local/bin:/usr/bin")]

def css():
    out = [".apptile { border-radius: 16px; min-width: 52px; min-height: 52px; }",
           ".apptile image { color: #ffffff; -gtk-icon-size: 28px; }"]
    for a in APPS:
        out.append(".t-%s { background-image: linear-gradient(135deg, %s, %s); }" % (a[0], a[3][0], a[3][1]))
    out.append(".t-apps { background-image: linear-gradient(135deg, #2a3a7a, #16224f); }")
    out.append(".t-other { background-image: linear-gradient(135deg, #3a4a8a, #1c2a5c); }")
    return "\n".join(out)
