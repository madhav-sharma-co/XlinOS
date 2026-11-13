-- XlinOS live installer session: the installer is the whole screen. No bar, no run bar, no wallpaper, no desktop icons, no window
-- borders or gaps, and none of the desktop key bindings. Only used when XlinOS is started from the install medium.
hl.env("XCURSOR_SIZE", "24")
hl.config({
    general = { gaps_in = 0, gaps_out = 0, border_size = 0, layout = "dwindle" },
    decoration = { rounding = 0, blur = { enabled = false }, shadow = { enabled = false } },
    animations = { enabled = false },
    misc = { disable_hyprland_logo = true, disable_splash_rendering = true, force_default_wallpaper = 0, background_color = "rgb(030a22)" },
    ecosystem = { no_update_news = true, no_donation_nag = true },
    input = { touchpad = { natural_scroll = false, tap_to_click = true } },
})
-- the installer window fills the screen; dialogs it opens float in the middle
hl.window_rule({ match = { class = "os.xlin.installer" }, fullscreen = true })
hl.on("hyprland.start", function()
    hl.dispatch(hl.dsp.exec_cmd("/usr/local/lib/xlinos/xlinos-installer"))
end)
