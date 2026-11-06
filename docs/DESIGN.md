# XlinOS design

One look everywhere: the login screen, the desktop, the apps.

- **Colours:** deep navy background (`#03081c` to `#0a2060`), blue accent (`#1e6bff`, lighter `#4f93ff`), soft blue-grey text (`#9db4e6`), white headings.
- **Surfaces:** glass panels (translucent navy with blur and a thin light border), 12-18 px rounded corners.
- **Type:** Inter. Big thin clock (weight 200), semi-bold titles.
- **Layout:** slim glass status bar on top, a floating dock at the bottom, a large clock on the desktop, a launcher with a search field and an app grid, a quick-settings panel with the user's name, Lock, Log out and Shut down.
- **Names:** the user only sees "XlinOS" and Xlin-soft's app names. No Arch or Hyprland names in the interface, boot, login or text (rule since 2026-11-06).

Concept drawings: `assets/design/` (`1-desktop.png`, `2-launcher.png`, `3-quick-settings.png`, source `concept.html`).

## Status
| Part | How | State |
|---|---|---|
| Login screen | `xlinos-greeter` | done, seen on a real boot |
| Palette (desktop, bar, dock, panels, terminal, lock screen) | `usr/share/xlinos/themes/dark.sh` replaces Xlin-soft's dark theme at login | done, seen on a real boot |
| Wallpaper | `usr/share/xlinos/wallpapers/xlin-dark.jpg` (navy glow, large X mark), set with `awww` | done, seen on a real boot |
| No Hyprland update popup, no default wallpaper text | `usr/share/xlinos/xlinos.lua` loaded after the desktop config | done, seen on a real boot |
| Launcher grid, quick-settings panel with Log out, new dock icons | needs new UI code | decision pending: in XlinOS only, or in Xlin-soft as an "XlinOS edition" |
| Removing "Hyprland"/"Arch" wording in Xlin-soft's own texts | text patches or an edition switch | same decision |
| Boot animation (Plymouth) | after the above | planned |
