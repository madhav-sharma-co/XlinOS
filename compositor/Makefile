# XlinOS compositor. Needs: wlroots, wayland, xkbcommon, wayland-protocols, wlr-protocols.
WLR ?= $(shell pkg-config --list-all | awk '/^wlroots/{print $$1; exit}')
PKGS = wayland-server xkbcommon $(WLR)
CFLAGS += -O2 -g -Wall -Wno-unused-parameter -DWLR_USE_UNSTABLE $(shell pkg-config --cflags $(PKGS)) -I.
LIBS = $(shell pkg-config --libs $(PKGS))
XDG = $(shell pkg-config --variable=pkgdatadir wayland-protocols)/stable/xdg-shell/xdg-shell.xml
LAYER = /usr/share/wlr-protocols/unstable/wlr-layer-shell-unstable-v1.xml

xlin-comp: xlin-comp.c xdg-shell-protocol.h wlr-layer-shell-unstable-v1-protocol.h
	$(CC) $(CFLAGS) -o $@ xlin-comp.c $(LIBS)
xdg-shell-protocol.h:
	wayland-scanner server-header $(XDG) $@
wlr-layer-shell-unstable-v1-protocol.h:
	wayland-scanner server-header $(LAYER) $@
clean:
	rm -f xlin-comp *-protocol.h
