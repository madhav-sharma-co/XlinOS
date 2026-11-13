-- XlinOS compositor settings (Hyprland 0.57+, Lua). This is XlinOS's own file: windows float and overlap like on
-- Windows or macOS, and snap with the keyboard (xlinos-snap). Not related to Xlin-soft.

hl.env("XCURSOR_SIZE", "24")

-- keyboard chosen in the installer (written to /etc/xlinos-keyboard as "layout variant")
do
    local f = io.open("/etc/xlinos-keyboard", "r")
    if f then
        local line = f:read("*l") or ""; f:close()
        local layout, variant = line:match("^(%S+)%s*(%S*)")
        if layout then hl.config({ input = { kb_layout = layout, kb_variant = variant or "" } }) end
    end
end

hl.config({
    general = {
        gaps_in = 6,
        gaps_out = 12,
        border_size = 1,
        layout = "dwindle",
        resize_on_border = true,
        extend_border_grab_area = 14,
        col = { active_border = "rgba(4f93ffcc)", inactive_border = "rgba(ffffff1f)" },
    },
    decoration = {
        rounding = 14,
        fullscreen_opacity = 1.0,
        blur = { enabled = true, size = 8, passes = 3, vibrancy = 0.15 },
        shadow = { enabled = true, range = 30, render_power = 3, color = "rgba(00000066)" },
    },
    misc = {
        disable_hyprland_logo = true,
        disable_splash_rendering = true,
        force_default_wallpaper = -1,
    },
    ecosystem = { no_update_news = true, no_donation_nag = true },
    dwindle = { preserve_split = true },
})

-- every window floats (can overlap, be dragged and resized freely); apps open in the middle
hl.window_rule({ match = { class = ".*" }, float = true, center = true })

-- ---- keys ----------------------------------------------------------------------------------------
local function bind(keys, action, flags)
    hl.unbind(keys)
    hl.bind(keys, action, flags)
end
local function run(keys, cmd, flags)
    bind(keys, hl.dsp.exec_cmd(cmd), flags)
end

run("SUPER + Return", "xlinos-terminal")
run("SUPER + E", "xlinos-files")
run("SUPER + SPACE", "xlinos-launcher")
run("SUPER + L", "xlinos-lock")
run("Print", "xlinos-screenshot area")
run("SUPER + SHIFT + S", "xlinos-screenshot area")
run("SUPER + Print", "xlinos-screenshot full")
run("CTRL + SHIFT + Escape", "xlinos-monitor")
run("SUPER + A", "xlinos-quick")
run("SUPER + C", "xlinos-quick")
run("SUPER + P", "xlinos-quick")
run("SUPER + B", "xlinos-quick")
run("SUPER + S", "xlinos-settings")
run("SUPER + T", "xlinos-clock")
run("SUPER + M", "xlinos-monitor")
run("SUPER + N", "xlinos-notes")
run("SUPER + H", "xlinos unhide")
run("SUPER + SHIFT + D", "xlinos showdesktop")
run("SUPER + W", "xlinos wallpaper next")
run("SUPER + D", "xlinos theme toggle")
run("SUPER + V", "xlinos-clipboard")
run("SUPER + slash", "xlinos-keys")
run("SUPER + F1", "xlinos-help")
run("SHIFT + Print", "xlinos-screenshot full")
run("ALT + Print", "xlinos-screenshot window")
run("SUPER + CTRL + Up", "brightnessctl set 8%+")
run("SUPER + CTRL + Down", "brightnessctl set 8%-")
run("SUPER + CTRL + Right", "wpctl set-volume -l 1.0 @DEFAULT_AUDIO_SINK@ 5%+")
run("SUPER + CTRL + Left", "wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-")
run("XF86AudioRaiseVolume", "wpctl set-volume -l 1.0 @DEFAULT_AUDIO_SINK@ 5%+", { locked = true, repeating = true })
run("XF86AudioLowerVolume", "wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-", { locked = true, repeating = true })
run("XF86AudioMute", "wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle", { locked = true })
run("XF86MonBrightnessUp", "brightnessctl set 8%+", { locked = true, repeating = true })
run("XF86MonBrightnessDown", "brightnessctl set 8%-", { locked = true, repeating = true })
run("SUPER + Tab", "/usr/local/lib/xlinos/xlinos-overview")

-- windows: Super+arrows snap like Windows (Left/Right = halves, Up = maximize, Down = restore;
-- from a half, Up/Down make a quarter); Super+Shift+C centres
run("SUPER + Left",  "/usr/local/lib/xlinos/xlinos-snap left")
run("SUPER + Right", "/usr/local/lib/xlinos/xlinos-snap right")
run("SUPER + Up",    "/usr/local/lib/xlinos/xlinos-snap up")
run("SUPER + Down",  "/usr/local/lib/xlinos/xlinos-snap down")
run("SUPER + SHIFT + C", "/usr/local/lib/xlinos/xlinos-snap center")
bind("SUPER + Q", hl.dsp.window.close())
bind("SUPER + F", hl.dsp.window.fullscreen({ mode = "fullscreen", action = "toggle" }))
bind("ALT + Tab", function()
    hl.dispatch(hl.dsp.window.cycle_next())
    hl.dispatch(hl.dsp.window.alter_zorder({ mode = "top" }))
end)
bind("SUPER + SHIFT + Q", hl.dsp.exec_cmd("xlinos-logout"))
bind("SUPER + SHIFT + F", hl.dsp.window.float({ action = "toggle" }))
for _, d in ipairs({ "left", "right", "up", "down" }) do
    bind("SUPER + SHIFT + " .. d, hl.dsp.focus({ direction = d }))
end
local rz = { left = { -40, 0 }, right = { 40, 0 }, up = { 0, -40 }, down = { 0, 40 } }
for d, xy in pairs(rz) do
    bind("SUPER + CTRL + SHIFT + " .. d, hl.dsp.window.resize({ x = xy[1], y = xy[2], relative = true }), { repeating = true })
end
bind("SUPER + ALT + right", hl.dsp.focus({ workspace = "e+1" }))
bind("SUPER + ALT + left", hl.dsp.focus({ workspace = "e-1" }))
bind("SUPER + mouse_down", hl.dsp.focus({ workspace = "e+1" }))
bind("SUPER + mouse_up", hl.dsp.focus({ workspace = "e-1" }))
hl.gesture({ fingers = 3, direction = "horizontal", action = "workspace" })
hl.gesture({ fingers = 3, direction = "up", action = function() hl.exec_cmd("/usr/local/lib/xlinos/xlinos-launcher") end })
hl.gesture({ fingers = 3, direction = "down", action = function() hl.exec_cmd("xlinos showdesktop") end })

-- drag with Super + left button, resize with Super + right button
bind("SUPER + mouse:272", hl.dsp.window.drag(), { mouse = true })
bind("SUPER + mouse:273", hl.dsp.window.resize(), { mouse = true })

-- workspaces
for i = 1, 4 do
    bind("SUPER + " .. i, hl.dsp.focus({ workspace = i }))
    bind("SUPER + SHIFT + " .. i, hl.dsp.window.move({ workspace = i }))
end

hl.on("hyprland.start", function()
    hl.dispatch(hl.dsp.exec_cmd("/usr/local/lib/xlinos/xlinos-shell"))
    hl.dispatch(hl.dsp.exec_cmd("/usr/local/lib/xlinos/xlinos-notify"))
    hl.dispatch(hl.dsp.exec_cmd("/usr/local/lib/xlinos/xlinos-apply"))
    hl.dispatch(hl.dsp.exec_cmd("sh -c 'command -v cliphist >/dev/null && exec wl-paste --watch cliphist store'"))
end)

-- Drag a window to a screen edge to snap it (like Windows / macOS): remember the window on press, snap on release.
hl.bind("mouse:272", hl.dsp.exec_cmd("/usr/local/lib/xlinos/xlinos-snap press"), { non_consuming = true })
hl.bind("mouse:272", hl.dsp.exec_cmd("/usr/local/lib/xlinos/xlinos-snap drop"), { release = true, non_consuming = true })
