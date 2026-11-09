-- XlinOS compositor settings (Hyprland 0.57+, Lua). This is XlinOS's own file: windows float and overlap like on
-- Windows or macOS, and snap with the keyboard (xlinos-snap). Not related to Xlin-soft.

hl.env("XCURSOR_SIZE", "24")

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
run("SUPER + A", "xlinos-quick")
run("SUPER + Tab", "/usr/local/lib/xlinos/xlinos-overview")

-- windows: Super+arrows snap like Windows (Left/Right = halves, Up = maximize, Down = restore;
-- from a half, Up/Down make a quarter); Super+C centres
run("SUPER + Left",  "/usr/local/lib/xlinos/xlinos-snap left")
run("SUPER + Right", "/usr/local/lib/xlinos/xlinos-snap right")
run("SUPER + Up",    "/usr/local/lib/xlinos/xlinos-snap up")
run("SUPER + Down",  "/usr/local/lib/xlinos/xlinos-snap down")
run("SUPER + C",     "/usr/local/lib/xlinos/xlinos-snap center")
bind("SUPER + Q", hl.dsp.window.close())
bind("SUPER + F", hl.dsp.window.fullscreen({ mode = "fullscreen", action = "toggle" }))
bind("ALT + Tab", function()
    hl.dispatch(hl.dsp.window.cycle_next())
    hl.dispatch(hl.dsp.window.alter_zorder({ mode = "top" }))
end)
bind("SUPER + SHIFT + Q", hl.dsp.exit())

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
    -- Live USB / ISO session: open the installer welcome straight away
    hl.dispatch(hl.dsp.exec_cmd("sh -c '[ -d /run/archiso ] && sleep 2 && exec /usr/local/lib/xlinos/xlinos-installer'"))
end)

-- Drag a window to a screen edge to snap it (like Windows / macOS): remember the window on press, snap on release.
hl.bind("mouse:272", hl.dsp.exec_cmd("/usr/local/lib/xlinos/xlinos-snap press"), { non_consuming = true })
hl.bind("mouse:272", hl.dsp.exec_cmd("/usr/local/lib/xlinos/xlinos-snap drop"), { release = true, non_consuming = true })
