-- XlinOS settings on top of the desktop config (loaded after it).

-- no Hyprland update notice, no default wallpaper text
hl.config({
    ecosystem = { no_update_news = true, no_donation_nag = true },
    misc = { force_default_wallpaper = -1 },
})

-- ---- windows: free floating windows, like a normal desktop ---------------------------------
-- every window floats (move it with Super+drag or by its title, resize at its edges);
-- tiling is still there: Super+Shift+F turns a window back into a tile
hl.window_rule({ match = { class = ".*" }, float = true })

-- ---- snapping: halves, corners, full size ----------------------------------------------------
local function bind(keys, cmd)
    hl.unbind(keys)
    hl.bind(keys, hl.dsp.exec_cmd(cmd))
end
bind("SUPER + Left",  "xlinos-snap left")       -- left half
bind("SUPER + Right", "xlinos-snap right")      -- right half
bind("SUPER + Up",    "xlinos-snap max")        -- full size
bind("SUPER + Down",  "xlinos-snap restore")    -- normal size, centred
bind("SUPER + ALT + U", "xlinos-snap tl")       -- corners: U I
bind("SUPER + ALT + I", "xlinos-snap tr")       --          J K
bind("SUPER + ALT + J", "xlinos-snap bl")
bind("SUPER + ALT + K", "xlinos-snap br")
bind("SUPER + ALT + Up",   "xlinos-snap top")   -- top / bottom half
bind("SUPER + ALT + Down", "xlinos-snap bottom")
-- window list (Alt+Tab goes to the next window)
bind("SUPER + Tab", "rofi -show window")
