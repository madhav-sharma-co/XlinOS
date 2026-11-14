# XlinOS compositor (xlin-comp)

The window compositor is XlinOS's own C program on wlroots (`compositor/xlin-comp.c`).
XlinOS now runs directly on `xlin-comp` and `/usr/share/xlinos/xlin.conf` (with `~/.config/xlin/xlin.conf`
for user overrides) — no third-party window manager or Lua engine is used.

## Features (v0.3)
- Floating windows with cascade placement, Super + mouse move/resize, and live edge/corner snap preview
- Windows/KDE-style quick tiling (`snap left|right|top|bottom|tl|tr|bl|br|max|restore|center`), directional focus, relative resize
- macOS-style shortcuts, hot corners (`hotcorner_tl|tr|bl|br`), 3-finger trackpad gestures, natural scroll & tap-to-click
- Virtual desktops (`workspaces`), window overview (`xlinos-overview`), Show Desktop (`showdesktop`) and `unhide`
- Window rules (`rule CLASS-GLOB [workspace=N] [size=WxH] [snap=MODE] [center] [fullscreen] [maximize]`)
- Built-in idle lock & sleep timer (`idle_lock_minutes`, `idle_sleep_minutes`)
- Screen lock (`ext-session-lock-v1`), clipboard (`wl-clipboard` + `cliphist`), screenshots (`grim` + `slurp`), Night Light (`wlsunset` via `wlr-gamma-control-v1`)
- Unix control socket & CLI (`xlinctl`) for shell, settings, installer keyboard preview, and live config reload (`xlinctl reload`)

Build: `make -C compositor`. CI: `.github/workflows/compositor-test.yml`.
