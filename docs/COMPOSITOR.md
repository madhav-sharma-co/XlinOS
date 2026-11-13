# XlinOS compositor (xlin-comp)

The window compositor is XlinOS's own program, written in C on the wlroots library. It replaces the
third-party desktop engine step by step. The old engine stays as the fallback until this one has parity.

## Phase 1 (done, tested headless in CI)
Floating windows (move/resize with Super + mouse), focus, popups, bars/dock/wallpaper/launcher
(layer shell), shortcuts from a plain file (`compositor/default.conf`), clipboard, screenshots,
keyboard layouts, startup command (`-s`).

## Phase 2 (needed before it can replace the old engine)
Lock screen (ext-session-lock), idle/lock timer, fullscreen/maximize, snapping (halves, corners),
workspaces and overview, our own control socket + `xlinctl` (replaces `hyprctl`), multi-monitor
and scale, touchpad gestures, cursor shape, XWayland, notification/clipboard-manager protocols,
the greeter and session start script switch to it.

## Phase 3
Move shell settings (window rules, animations, blur) out of the old Lua config into one XlinOS
config, remove the old engine from the ISO, test on real hardware.

Build: `make -C compositor`. CI: `.github/workflows/compositor-test.yml`.
