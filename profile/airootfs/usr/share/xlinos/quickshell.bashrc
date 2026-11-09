# XlinOS Quickshell: friendly commands and a clean prompt on top of the normal shell.
[[ -f ~/.bashrc ]] && . ~/.bashrc
PS1='\[\e[1;36m\]\u\[\e[0m\]@\[\e[1;34m\]xlin\[\e[0m\] \[\e[1;33m\]\w\[\e[0m\] \[\e[1;36m\]›\[\e[0m\] '
alias ls='ls --color=auto -h --group-directories-first'
alias ll='ls -l'
alias grep='grep --color=auto'
help() {
  cat <<'EOT'
Quickshell, the XlinOS command line

  apps                 list the apps you can start
  open <file|folder>   open it in the right XlinOS app
  get <name>           install an app            (example: get firefox)
  remove <name>        remove an app
  search <word>        look for apps to install
  update               update XlinOS and the system
  about                show the XlinOS version
  lock                 lock the screen
  clear                clean the screen
EOT
}
apps()   { ls /usr/share/applications | sed -n 's/^xlinos-\(.*\)\.desktop$/\1/p'; }
about()  { . /etc/os-release; echo "$PRETTY_NAME"; echo "Build: $(cut -c1-8 /usr/share/xlinos/commit 2>/dev/null)"; }
get()    { sudo pacman -S --needed "$@"; }
remove() { sudo pacman -Rns "$@"; }
search() { pacman -Ss "$@" | head -40; }
update() { sudo /usr/local/lib/xlinos/xlinos-update apply; }
lock()   { xlinos-lock; }
open() {
  [[ -n "${1:-}" ]] || { echo "usage: open <file or folder>"; return 1; }
  if [[ -d "$1" ]]; then (xlinos-files "$1" >/dev/null 2>&1 &)
  else case "${1,,}" in
    *.png|*.jpg|*.jpeg|*.webp|*.gif|*.bmp) (xlinos-photos "$1" >/dev/null 2>&1 &);;
    *.mp3|*.ogg|*.flac|*.wav|*.mp4|*.mkv|*.webm|*.avi) (xlinos-media "$1" >/dev/null 2>&1 &);;
    *) (xlinos-notes "$1" >/dev/null 2>&1 &);;
  esac; fi
}
echo "Quickshell  -  type help to see what you can do"
