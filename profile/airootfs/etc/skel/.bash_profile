# XlinOS: on the first text console, start the Xlin-soft desktop.
[[ -f ~/.bashrc ]] && . ~/.bashrc
if [[ -z "${WAYLAND_DISPLAY:-}" && -z "${DISPLAY:-}" && "$(tty)" == /dev/tty1 ]]; then
  exec /usr/local/bin/xlinos-session
fi
