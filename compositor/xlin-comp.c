// xlin-comp: the XlinOS window compositor (v0.2).
// Floating windows with snapping, virtual desktops, bars/dock (layer shell), screen lock, shortcuts and
// gestures from xlin.conf, a small control socket (xlinctl), clipboard, screenshots, HiDPI.
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <time.h>
#include <unistd.h>
#include <signal.h>
#include <fcntl.h>
#include <fnmatch.h>
#include <errno.h>
#include <sys/time.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <wayland-server-core.h>
#include <wlr/backend.h>
#include <wlr/backend/session.h>
#include <wlr/render/allocator.h>
#include <wlr/render/wlr_renderer.h>
#include <wlr/types/wlr_compositor.h>
#include <wlr/types/wlr_cursor.h>
#include <wlr/types/wlr_cursor_shape_v1.h>
#include <wlr/types/wlr_data_control_v1.h>
#include <wlr/types/wlr_data_device.h>
#include <wlr/types/wlr_fractional_scale_v1.h>
#include <wlr/types/wlr_idle_notify_v1.h>
#include <wlr/types/wlr_input_device.h>
#include <wlr/types/wlr_keyboard.h>
#include <wlr/types/wlr_layer_shell_v1.h>
#include <wlr/types/wlr_output.h>
#include <wlr/types/wlr_output_layout.h>
#include <wlr/types/wlr_pointer.h>
#include <wlr/types/wlr_primary_selection.h>
#include <wlr/types/wlr_primary_selection_v1.h>
#include <wlr/types/wlr_scene.h>
#include <wlr/types/wlr_screencopy_v1.h>
#include <wlr/types/wlr_seat.h>
#include <wlr/types/wlr_session_lock_v1.h>
#include <wlr/types/wlr_single_pixel_buffer_v1.h>
#include <wlr/types/wlr_subcompositor.h>
#include <wlr/types/wlr_viewporter.h>
#include <wlr/types/wlr_xcursor_manager.h>
#include <wlr/types/wlr_xdg_activation_v1.h>
#include <wlr/types/wlr_xdg_output_v1.h>
#include <wlr/types/wlr_xdg_shell.h>
#include <wlr/util/log.h>
#include <xkbcommon/xkbcommon.h>
#include <linux/input-event-codes.h>

#define VERSION "0.2"
enum grab { GRAB_NONE, GRAB_MOVE, GRAB_RESIZE };
enum snap { SN_NONE, SN_LEFT, SN_RIGHT, SN_MAX, SN_TL, SN_TR, SN_BL, SN_BR, SN_TOP, SN_BOTTOM, SN_CENTER };
enum act { A_EXEC, A_CLOSE, A_EXIT, A_NEXT, A_SNAP, A_FULL, A_WS, A_MOVEWS, A_MINIMIZE, A_SHOWDESKTOP, A_RELOAD, A_WSNEXT, A_WSPREV };

struct bind { uint32_t mods; xkb_keysym_t sym; enum act act; char *arg; };
struct gesture { int fingers; char dir; char *cmd; };
struct rule { char *cls; int ws; int w, h; int snap; };

struct output {
	struct wl_list link; struct wlr_output *wlr; struct wlr_scene_output *so;
	struct wlr_box usable;
	struct wl_listener frame, state, destroy;
};
struct toplevel {
	struct wl_list link; struct wlr_xdg_toplevel *xt; struct wlr_scene_tree *tree;
	unsigned id; int ws; bool hidden, full, mapped; enum snap snap; struct wlr_box restore; bool has_restore;
	struct wl_listener map, unmap, commit, destroy, req_move, req_resize, req_max, req_full, req_min;
};
struct popup { struct wlr_xdg_popup *xp; struct wl_listener commit, destroy; };
struct keyboard { struct wl_list link; struct wlr_keyboard *kb; struct wl_listener mod, key, destroy; };
struct layer_surface {
	struct wl_list link; struct wlr_scene_layer_surface_v1 *sl; struct wlr_layer_surface_v1 *ls;
	struct wl_listener map, unmap, commit, destroy;
};

enum { L_BG, L_BOTTOM, L_TOP, L_OVERLAY };
static struct {
	struct wl_display *display; struct wl_event_loop *loop;
	struct wlr_backend *backend; struct wlr_session *session;
	struct wlr_renderer *renderer; struct wlr_allocator *allocator;
	struct wlr_scene *scene; struct wlr_scene_output_layout *scene_layout;
	struct wlr_scene_tree *layer[4], *windows, *fs, *lock_tree;
	struct wlr_output_layout *out_layout;
	struct wlr_xdg_shell *xdg; struct wlr_layer_shell_v1 *layer_shell;
	struct wlr_cursor *cursor; struct wlr_xcursor_manager *xcur; struct wlr_seat *seat;
	struct wlr_idle_notifier_v1 *idle;
	struct wlr_session_lock_manager_v1 *lockmgr; struct wlr_session_lock_v1 *lock;
	struct wlr_cursor_shape_manager_v1 *shape;
	struct wlr_xdg_activation_v1 *activation;
	struct wl_list outputs, toplevels, keyboards, layers;
	struct wl_listener new_output, new_toplevel, new_popup, new_layer, new_input, new_lock, lock_surf, lock_unlock, lock_destroy;
	struct wl_listener cur_motion, cur_abs, cur_button, cur_axis, cur_frame, sw_begin, sw_update, sw_end;
	struct wl_listener req_cursor, req_sel, req_psel, req_shape, req_activate;
	enum grab grab; struct toplevel *grab_tl; double gx, gy; struct wlr_box gbox;
	struct bind *binds; int nbinds; struct gesture *gest; int ngest;
	struct rule *rules; int nrules; char **autostart; int nauto;
	char *hot[4];                         // hot corners: tl tr bl br
	bool corner_armed; double sw_dx, sw_dy; int sw_fingers;
	struct layer_surface *kb_layer;
	bool locked, lock_pending;
	int cur_ws, nws; unsigned next_id;
	int snap_edge, gap, repeat_rate, repeat_delay, cursor_size; float scale;
	char layout[64], variant[64];
	char sockpath[256];
} S;
static const char *main_conf, *user_conf;

// ---------------------------------------------------------------- small helpers
static void run(const char *cmd) {
	if (fork() == 0) { setsid(); execl("/bin/sh", "sh", "-c", cmd, (char *)NULL); _exit(1); }
}
static struct output *first_output(void) {
	struct output *o; wl_list_for_each(o, &S.outputs, link) return o; return NULL;
}
static struct output *output_at(double x, double y) {
	struct wlr_output *w = wlr_output_layout_output_at(S.out_layout, x, y);
	struct output *o; wl_list_for_each(o, &S.outputs, link) if (o->wlr == w) return o;
	return first_output();
}
static void geo(struct toplevel *t, struct wlr_box *b) {   // visible window box in layout coordinates
	struct wlr_box g = t->xt->base->geometry;
	b->x = t->tree->node.x + g.x; b->y = t->tree->node.y + g.y; b->width = g.width; b->height = g.height;
}
static bool visible(struct toplevel *t) { return t->mapped && !t->hidden && t->ws == S.cur_ws; }
static void update_vis(struct toplevel *t) { wlr_scene_node_set_enabled(&t->tree->node, visible(t)); }
static struct toplevel *by_id(unsigned id) {
	struct toplevel *t; wl_list_for_each(t, &S.toplevels, link) if (t->id == id) return t; return NULL;
}
static struct toplevel *top_visible(void) {
	struct toplevel *t; wl_list_for_each(t, &S.toplevels, link) if (visible(t)) return t; return NULL;
}
static struct toplevel *focused(void) {
	struct wlr_surface *s = S.seat->keyboard_state.focused_surface;
	if (!s) return NULL;
	struct wlr_xdg_toplevel *x = wlr_xdg_toplevel_try_from_wlr_surface(s);
	if (!x) return NULL;
	struct wlr_scene_tree *tr = x->base->data; return tr ? tr->node.data : NULL;
}
static void place(struct toplevel *t, struct wlr_box b) {   // put the visible box at b
	struct wlr_box g = t->xt->base->geometry;
	wlr_scene_node_set_position(&t->tree->node, b.x - g.x, b.y - g.y);
	wlr_xdg_toplevel_set_size(t->xt, b.width, b.height);
}

// ---------------------------------------------------------------- focus
static void kb_enter(struct wlr_surface *s) {
	struct wlr_keyboard *kb = wlr_seat_get_keyboard(S.seat);
	if (kb) wlr_seat_keyboard_notify_enter(S.seat, s, kb->keycodes, kb->num_keycodes, &kb->modifiers);
}
static void focus_toplevel(struct toplevel *t) {
	if (!t || S.locked) return;
	t->hidden = false;
	if (t->ws != S.cur_ws) {
		S.cur_ws = t->ws;
		struct toplevel *o; wl_list_for_each(o, &S.toplevels, link) update_vis(o);
	}
	update_vis(t);
	struct wlr_surface *prev = S.seat->keyboard_state.focused_surface, *surf = t->xt->base->surface;
	if (prev && prev != surf) {
		struct wlr_xdg_toplevel *pt = wlr_xdg_toplevel_try_from_wlr_surface(prev);
		if (pt) wlr_xdg_toplevel_set_activated(pt, false);
	}
	wlr_scene_node_raise_to_top(&t->tree->node);
	wl_list_remove(&t->link); wl_list_insert(&S.toplevels, &t->link);
	wlr_xdg_toplevel_set_activated(t->xt, true);
	if (prev != surf) kb_enter(surf);
}
static void focus_best(void) {
	struct toplevel *t = top_visible();
	if (t) focus_toplevel(t); else wlr_seat_keyboard_notify_clear_focus(S.seat);
}
static void switch_ws(int n) {
	if (n < 1 || n > S.nws || n == S.cur_ws) return;
	S.cur_ws = n;
	struct toplevel *t; wl_list_for_each(t, &S.toplevels, link) update_vis(t);
	struct wlr_surface *prev = S.seat->keyboard_state.focused_surface;
	if (prev) { struct wlr_xdg_toplevel *pt = wlr_xdg_toplevel_try_from_wlr_surface(prev); if (pt) wlr_xdg_toplevel_set_activated(pt, false); }
	wlr_seat_keyboard_notify_clear_focus(S.seat);
	focus_best();
}
static void focus_layer(struct layer_surface *l) {
	if (S.locked) return;
	S.kb_layer = l; kb_enter(l->ls->surface);
}

// ---------------------------------------------------------------- snapping
static struct wlr_box area_of(struct toplevel *t, bool full) {
	struct wlr_box b; geo(t, &b);
	struct output *o = output_at(b.x + b.width / 2.0, b.y + b.height / 2.0);
	struct wlr_box a = {0};
	if (!o) return (struct wlr_box){0, 0, 1280, 720};
	if (full) wlr_output_layout_get_box(S.out_layout, o->wlr, &a); else a = o->usable;
	return a;
}
static void snap_to(struct toplevel *t, enum snap m) {
	if (!t || !t->mapped) return;
	if (t->full) { t->full = false; wlr_xdg_toplevel_set_fullscreen(t->xt, false); wlr_scene_node_reparent(&t->tree->node, S.windows); }
	struct wlr_box cur; geo(t, &cur);
	if (m == SN_NONE) {
		if (t->has_restore) { place(t, t->restore); t->has_restore = false; }
		t->snap = SN_NONE; return;
	}
	if (t->snap == SN_NONE) { t->restore = cur; t->has_restore = true; }
	struct wlr_box a = area_of(t, false), b = a; int g = S.gap;
	int hw = a.width / 2, hh = a.height / 2;
	switch (m) {
	case SN_LEFT: b.width = hw; break;
	case SN_RIGHT: b.x = a.x + hw; b.width = a.width - hw; break;
	case SN_TOP: b.height = hh; break;
	case SN_BOTTOM: b.y = a.y + hh; b.height = a.height - hh; break;
	case SN_TL: b.width = hw; b.height = hh; break;
	case SN_TR: b.x = a.x + hw; b.width = a.width - hw; b.height = hh; break;
	case SN_BL: b.width = hw; b.y = a.y + hh; b.height = a.height - hh; break;
	case SN_BR: b.x = a.x + hw; b.width = a.width - hw; b.y = a.y + hh; b.height = a.height - hh; break;
	case SN_CENTER: b = cur; b.x = a.x + (a.width - cur.width) / 2; b.y = a.y + (a.height - cur.height) / 2;
		t->snap = SN_NONE; t->has_restore = false; place(t, b); return;
	default: break;
	}
	b.x += g; b.y += g; b.width -= 2 * g; b.height -= 2 * g;
	place(t, b); t->snap = m; wlr_scene_node_raise_to_top(&t->tree->node);
}
static void snap_dir(struct toplevel *t, const char *d) {   // arrows: Windows-style halves, quarters, maximize, restore
	enum snap c = t->snap, n = c;
	if (!strcmp(d, "left")) n = c == SN_RIGHT ? SN_NONE : c == SN_TR ? SN_TL : c == SN_BR ? SN_BL : SN_LEFT;
	else if (!strcmp(d, "right")) n = c == SN_LEFT ? SN_NONE : c == SN_TL ? SN_TR : c == SN_BL ? SN_BR : SN_RIGHT;
	else if (!strcmp(d, "up")) n = c == SN_NONE ? SN_MAX : c == SN_LEFT ? SN_TL : c == SN_RIGHT ? SN_TR : c == SN_BL ? SN_LEFT : c == SN_BR ? SN_RIGHT : c;
	else if (!strcmp(d, "down")) n = c == SN_MAX ? SN_NONE : c == SN_LEFT ? SN_BL : c == SN_RIGHT ? SN_BR : c == SN_TL ? SN_LEFT : c == SN_TR ? SN_RIGHT : c;
	else if (!strcmp(d, "max")) n = c == SN_MAX ? SN_NONE : SN_MAX;
	else if (!strcmp(d, "center")) n = SN_CENTER;
	else if (!strcmp(d, "restore")) n = SN_NONE;
	else if (!strcmp(d, "tl")) n = SN_TL; else if (!strcmp(d, "tr")) n = SN_TR;
	else if (!strcmp(d, "bl")) n = SN_BL; else if (!strcmp(d, "br")) n = SN_BR;
	else if (!strcmp(d, "top")) n = SN_TOP; else if (!strcmp(d, "bottom")) n = SN_BOTTOM;
	if (n != c || n == SN_CENTER) snap_to(t, n);
}
static void set_fullscreen(struct toplevel *t, bool on) {
	if (!t || t->full == on) return;
	if (on) {
		struct wlr_box cur; geo(t, &cur);
		if (t->snap == SN_NONE) { t->restore = cur; t->has_restore = true; }
		t->full = true;
		struct wlr_box a = area_of(t, true);
		wlr_scene_node_reparent(&t->tree->node, S.fs);
		wlr_xdg_toplevel_set_fullscreen(t->xt, true);
		place(t, a);
	} else {
		t->full = false;
		wlr_xdg_toplevel_set_fullscreen(t->xt, false);
		wlr_scene_node_reparent(&t->tree->node, S.windows);
		if (t->snap != SN_NONE) { enum snap s = t->snap; t->snap = SN_NONE; snap_to(t, s); }
		else if (t->has_restore) { place(t, t->restore); t->has_restore = false; }
	}
}
static void minimize(struct toplevel *t) {
	if (!t) return;
	t->hidden = true; update_vis(t);
	if (focused() == t) { wlr_seat_keyboard_notify_clear_focus(S.seat); focus_best(); }
}
static void show_desktop(void) {   // minimise everything here; run again to bring it back
	bool any = false; struct toplevel *t;
	wl_list_for_each(t, &S.toplevels, link) if (t->mapped && t->ws == S.cur_ws && !t->hidden) any = true;
	wl_list_for_each(t, &S.toplevels, link) if (t->mapped && t->ws == S.cur_ws) { t->hidden = any; update_vis(t); }
	if (any) wlr_seat_keyboard_notify_clear_focus(S.seat); else focus_best();
}

// ---------------------------------------------------------------- layer shell (bars, dock, wallpaper, launcher)
static void arrange_layers(struct output *o) {
	struct wlr_box full = {0}, usable;
	wlr_output_layout_get_box(S.out_layout, o->wlr, &full);
	usable = full;
	struct layer_surface *l;
	for (int pass = 0; pass < 2; pass++)
		wl_list_for_each(l, &S.layers, link)
			if (l->ls->output == o->wlr && (l->ls->current.exclusive_zone > 0) == (pass == 0))
				wlr_scene_layer_surface_v1_configure(l->sl, &full, &usable);
	o->usable = usable;
}
static void layer_map(struct wl_listener *li, void *d) {
	struct layer_surface *l = wl_container_of(li, l, map);
	if (l->ls->current.keyboard_interactive == ZWLR_LAYER_SURFACE_V1_KEYBOARD_INTERACTIVITY_EXCLUSIVE) focus_layer(l);
}
static void layer_unmap(struct wl_listener *li, void *d) {
	struct layer_surface *l = wl_container_of(li, l, unmap);
	if (S.kb_layer == l) { S.kb_layer = NULL; wlr_seat_keyboard_notify_clear_focus(S.seat); focus_best(); }
}
static void layer_commit(struct wl_listener *li, void *d) {
	struct layer_surface *l = wl_container_of(li, l, commit);
	if (!l->ls->initialized) return;
	struct output *o; wl_list_for_each(o, &S.outputs, link) if (o->wlr == l->ls->output) arrange_layers(o);
	if (l->ls->surface->mapped && l->ls->current.keyboard_interactive == ZWLR_LAYER_SURFACE_V1_KEYBOARD_INTERACTIVITY_EXCLUSIVE && S.kb_layer != l) focus_layer(l);
}
static void layer_destroy(struct wl_listener *li, void *d) {
	struct layer_surface *l = wl_container_of(li, l, destroy);
	if (S.kb_layer == l) S.kb_layer = NULL;
	wl_list_remove(&l->link); wl_list_remove(&l->map.link); wl_list_remove(&l->unmap.link);
	wl_list_remove(&l->commit.link); wl_list_remove(&l->destroy.link); free(l);
}
static void new_layer(struct wl_listener *li, void *d) {
	struct wlr_layer_surface_v1 *ls = d;
	if (!ls->output) {
		struct output *o = first_output();
		if (!o) { wlr_layer_surface_v1_destroy(ls); return; }
		ls->output = o->wlr;
	}
	struct layer_surface *l = calloc(1, sizeof *l); l->ls = ls;
	l->sl = wlr_scene_layer_surface_v1_create(S.layer[ls->pending.layer], ls);
	wl_list_insert(&S.layers, &l->link);
	l->map.notify = layer_map; wl_signal_add(&ls->surface->events.map, &l->map);
	l->unmap.notify = layer_unmap; wl_signal_add(&ls->surface->events.unmap, &l->unmap);
	l->commit.notify = layer_commit; wl_signal_add(&ls->surface->events.commit, &l->commit);
	l->destroy.notify = layer_destroy; wl_signal_add(&ls->events.destroy, &l->destroy);
}

// ---------------------------------------------------------------- windows
static void apply_rules(struct toplevel *t) {
	const char *cls = t->xt->app_id ? t->xt->app_id : "";
	for (int i = 0; i < S.nrules; i++) {
		struct rule *r = &S.rules[i];
		if (fnmatch(r->cls, cls, FNM_CASEFOLD)) continue;
		if (r->ws > 0 && r->ws <= S.nws) t->ws = r->ws;
		if (r->snap) snap_to(t, r->snap);
		else if (r->w > 0) { struct wlr_box b; geo(t, &b); b.width = r->w; b.height = r->h; place(t, b); }
	}
}
static void tl_map(struct wl_listener *li, void *d) {
	struct toplevel *t = wl_container_of(li, t, map);
	t->mapped = true; t->ws = S.cur_ws;
	struct wlr_box g = t->xt->base->geometry;
	struct output *o = output_at(S.cursor->x, S.cursor->y);
	struct wlr_box a = o ? o->usable : (struct wlr_box){0, 0, 1280, 720};
	static int cascade; int off = (cascade++ % 5) * 28;
	int x = a.x + (a.width - g.width) / 2 + off, y = a.y + (a.height - g.height) / 2 + off;
	wlr_scene_node_set_position(&t->tree->node, (x < a.x ? a.x : x) - g.x, (y < a.y ? a.y : y) - g.y);
	apply_rules(t);
	update_vis(t);
	if (t->xt->requested.fullscreen) set_fullscreen(t, true);
	focus_toplevel(t);
}
static void tl_unmap(struct wl_listener *li, void *d) {
	struct toplevel *t = wl_container_of(li, t, unmap);
	if (S.grab_tl == t) { S.grab = GRAB_NONE; S.grab_tl = NULL; }
	bool had = focused() == t;
	t->mapped = false;
	if (had) { wlr_seat_keyboard_notify_clear_focus(S.seat); focus_best(); }
}
static void tl_commit(struct wl_listener *li, void *d) {
	struct toplevel *t = wl_container_of(li, t, commit);
	if (t->xt->base->initial_commit) wlr_xdg_toplevel_set_size(t->xt, 0, 0);
}
static void tl_destroy(struct wl_listener *li, void *d) {
	struct toplevel *t = wl_container_of(li, t, destroy);
	if (S.grab_tl == t) { S.grab = GRAB_NONE; S.grab_tl = NULL; }
	wl_list_remove(&t->map.link); wl_list_remove(&t->unmap.link); wl_list_remove(&t->commit.link);
	wl_list_remove(&t->destroy.link); wl_list_remove(&t->req_move.link); wl_list_remove(&t->req_resize.link);
	wl_list_remove(&t->req_max.link); wl_list_remove(&t->req_full.link); wl_list_remove(&t->req_min.link);
	wl_list_remove(&t->link); free(t);
}
static void begin_grab(struct toplevel *t, enum grab g) {
	if (S.locked || !t) return;
	if (g == GRAB_MOVE && t->snap != SN_NONE && t->has_restore) {   // dragging a snapped window gives it its old size back
		struct wlr_box cur; geo(t, &cur);
		double fx = (S.cursor->x - cur.x) / (double)(cur.width ? cur.width : 1);
		struct wlr_box r = t->restore;
		r.x = (int)(S.cursor->x - fx * r.width); r.y = (int)S.cursor->y - 14;
		t->snap = SN_NONE; t->has_restore = false; place(t, r);
	}
	S.grab = g; S.grab_tl = t; S.gx = S.cursor->x; S.gy = S.cursor->y;
	struct wlr_box b; geo(t, &b); S.gbox = b;
	wlr_cursor_set_xcursor(S.cursor, S.xcur, g == GRAB_MOVE ? "grabbing" : "se-resize");
}
static void tl_req_move(struct wl_listener *li, void *d) { struct toplevel *t = wl_container_of(li, t, req_move); begin_grab(t, GRAB_MOVE); }
static void tl_req_resize(struct wl_listener *li, void *d) { struct toplevel *t = wl_container_of(li, t, req_resize); begin_grab(t, GRAB_RESIZE); }
static void tl_req_max(struct wl_listener *li, void *d) {
	struct toplevel *t = wl_container_of(li, t, req_max);
	if (!t->xt->base->initialized) return;
	if (t->xt->requested.maximized) snap_to(t, SN_MAX); else snap_to(t, SN_NONE);
	wlr_xdg_toplevel_set_maximized(t->xt, t->xt->requested.maximized);
}
static void tl_req_full(struct wl_listener *li, void *d) {
	struct toplevel *t = wl_container_of(li, t, req_full);
	if (!t->xt->base->initialized) return;
	set_fullscreen(t, t->xt->requested.fullscreen);
}
static void tl_req_min(struct wl_listener *li, void *d) { struct toplevel *t = wl_container_of(li, t, req_min); minimize(t); }
static void new_toplevel(struct wl_listener *li, void *d) {
	struct wlr_xdg_toplevel *xt = d;
	struct toplevel *t = calloc(1, sizeof *t); t->xt = xt; t->id = ++S.next_id; t->ws = S.cur_ws;
	wl_list_insert(&S.toplevels, &t->link);
	t->tree = wlr_scene_xdg_surface_create(S.windows, xt->base);
	t->tree->node.data = t; xt->base->data = t->tree;
	wlr_scene_node_set_enabled(&t->tree->node, false);   // shown when mapped
	t->map.notify = tl_map; wl_signal_add(&xt->base->surface->events.map, &t->map);
	t->unmap.notify = tl_unmap; wl_signal_add(&xt->base->surface->events.unmap, &t->unmap);
	t->commit.notify = tl_commit; wl_signal_add(&xt->base->surface->events.commit, &t->commit);
	t->destroy.notify = tl_destroy; wl_signal_add(&xt->events.destroy, &t->destroy);
	t->req_move.notify = tl_req_move; wl_signal_add(&xt->events.request_move, &t->req_move);
	t->req_resize.notify = tl_req_resize; wl_signal_add(&xt->events.request_resize, &t->req_resize);
	t->req_max.notify = tl_req_max; wl_signal_add(&xt->events.request_maximize, &t->req_max);
	t->req_full.notify = tl_req_full; wl_signal_add(&xt->events.request_fullscreen, &t->req_full);
	t->req_min.notify = tl_req_min; wl_signal_add(&xt->events.request_minimize, &t->req_min);
}
static void popup_commit(struct wl_listener *li, void *d) {
	struct popup *p = wl_container_of(li, p, commit);
	if (p->xp->base->initial_commit) wlr_xdg_surface_schedule_configure(p->xp->base);
}
static void popup_destroy(struct wl_listener *li, void *d) {
	struct popup *p = wl_container_of(li, p, destroy);
	wl_list_remove(&p->commit.link); wl_list_remove(&p->destroy.link); free(p);
}
static void new_popup(struct wl_listener *li, void *d) {
	struct wlr_xdg_popup *xp = d;
	struct popup *p = calloc(1, sizeof *p); p->xp = xp;
	struct wlr_xdg_surface *parent = wlr_xdg_surface_try_from_wlr_surface(xp->parent);
	if (parent && parent->data) xp->base->data = wlr_scene_xdg_surface_create(parent->data, xp->base);
	p->commit.notify = popup_commit; wl_signal_add(&xp->base->surface->events.commit, &p->commit);
	p->destroy.notify = popup_destroy; wl_signal_add(&xp->events.destroy, &p->destroy);
}
static void req_activate(struct wl_listener *li, void *d) {
	struct wlr_xdg_activation_v1_request_activate_event *e = d;
	struct wlr_xdg_toplevel *x = wlr_xdg_toplevel_try_from_wlr_surface(e->surface);
	if (!x || !x->base->data) return;
	struct wlr_scene_tree *tr = x->base->data;
	if (tr->node.data) focus_toplevel(tr->node.data);
}

// ---------------------------------------------------------------- screen lock (ext-session-lock)
static bool in_lock(struct wlr_scene_node *n) {
	for (struct wlr_scene_tree *t = n->parent; t; t = t->node.parent) if (S.lock_tree && t == S.lock_tree) return true;
	return false;
}
static void lock_new_surface(struct wl_listener *li, void *d) {
	struct wlr_session_lock_surface_v1 *ls = d;
	struct output *o = NULL, *it;
	wl_list_for_each(it, &S.outputs, link) if (it->wlr == ls->output) o = it;
	if (!o || !S.lock_tree) return;
	struct wlr_box b = {0}; wlr_output_layout_get_box(S.out_layout, o->wlr, &b);
	struct wlr_scene_tree *t = wlr_scene_subsurface_tree_create(S.lock_tree, ls->surface);
	wlr_scene_node_set_position(&t->node, b.x, b.y);
	wlr_session_lock_surface_v1_configure(ls, b.width, b.height);
	kb_enter(ls->surface);
}
static void end_lock_tree(void) {
	if (S.lock_tree) { wlr_scene_node_destroy(&S.lock_tree->node); S.lock_tree = NULL; }
}
static void lock_unlock(struct wl_listener *li, void *d) {
	S.locked = false; end_lock_tree(); S.kb_layer = NULL;
	wlr_seat_keyboard_notify_clear_focus(S.seat); focus_best();
}
static void lock_destroy(struct wl_listener *li, void *d) {   // a lock client that dies leaves the screen locked
	wl_list_remove(&S.lock_surf.link); wl_list_remove(&S.lock_unlock.link); wl_list_remove(&S.lock_destroy.link);
	S.lock = NULL;
}
static void new_lock(struct wl_listener *li, void *d) {
	struct wlr_session_lock_v1 *lock = d;
	if (S.lock) { wlr_session_lock_v1_destroy(lock); return; }
	S.lock = lock; S.locked = true;
	end_lock_tree();
	S.lock_tree = wlr_scene_tree_create(&S.scene->tree);   // created last: above everything
	struct output *o;
	wl_list_for_each(o, &S.outputs, link) {
		struct wlr_box b = {0}; wlr_output_layout_get_box(S.out_layout, o->wlr, &b);
		float black[4] = {0, 0, 0, 1};
		struct wlr_scene_rect *r = wlr_scene_rect_create(S.lock_tree, b.width, b.height, black);
		wlr_scene_node_set_position(&r->node, b.x, b.y);
	}
	wlr_seat_keyboard_notify_clear_focus(S.seat); wlr_seat_pointer_notify_clear_focus(S.seat);
	S.kb_layer = NULL; S.grab = GRAB_NONE;
	S.lock_surf.notify = lock_new_surface; wl_signal_add(&lock->events.new_surface, &S.lock_surf);
	S.lock_unlock.notify = lock_unlock; wl_signal_add(&lock->events.unlock, &S.lock_unlock);
	S.lock_destroy.notify = lock_destroy; wl_signal_add(&lock->events.destroy, &S.lock_destroy);
	if (wl_list_empty(&S.outputs)) wlr_session_lock_v1_send_locked(lock); else S.lock_pending = true;
}

// ---------------------------------------------------------------- pointer, gestures
static void corner_check(void) {
	struct output *o = output_at(S.cursor->x, S.cursor->y); if (!o) return;
	struct wlr_box b = {0}; wlr_output_layout_get_box(S.out_layout, o->wlr, &b);
	double x = S.cursor->x - b.x, y = S.cursor->y - b.y; int c = -1;
	if (x < 2 && y < 2) c = 0; else if (x > b.width - 3 && y < 2) c = 1;
	else if (x < 2 && y > b.height - 3) c = 2; else if (x > b.width - 3 && y > b.height - 3) c = 3;
	if (c < 0) { S.corner_armed = true; return; }
	if (S.corner_armed && S.hot[c] && !S.locked) { S.corner_armed = false; run(S.hot[c]); }
}
static void pointer_motion(uint32_t time) {
	wlr_idle_notifier_v1_notify_activity(S.idle, S.seat);
	if (S.grab == GRAB_MOVE && S.grab_tl) {
		struct wlr_box g = S.grab_tl->xt->base->geometry;
		wlr_scene_node_set_position(&S.grab_tl->tree->node, S.gbox.x + (int)(S.cursor->x - S.gx) - g.x, S.gbox.y + (int)(S.cursor->y - S.gy) - g.y);
		return;
	}
	if (S.grab == GRAB_RESIZE && S.grab_tl) {
		int w = S.gbox.width + (int)(S.cursor->x - S.gx), h = S.gbox.height + (int)(S.cursor->y - S.gy);
		S.grab_tl->snap = SN_NONE;
		wlr_xdg_toplevel_set_size(S.grab_tl->xt, w < 160 ? 160 : w, h < 100 ? 100 : h);
		return;
	}
	corner_check();
	double sx, sy; struct wlr_surface *s = NULL;
	struct wlr_scene_node *n = wlr_scene_node_at(&S.scene->tree.node, S.cursor->x, S.cursor->y, &sx, &sy);
	if (n && n->type == WLR_SCENE_NODE_BUFFER && (!S.locked || in_lock(n))) {
		struct wlr_scene_surface *ss = wlr_scene_surface_try_from_buffer(wlr_scene_buffer_from_node(n));
		if (ss) s = ss->surface;
	}
	if (!s) { wlr_cursor_set_xcursor(S.cursor, S.xcur, "default"); wlr_seat_pointer_clear_focus(S.seat); return; }
	wlr_seat_pointer_notify_enter(S.seat, s, sx, sy);
	wlr_seat_pointer_notify_motion(S.seat, time, sx, sy);
}
static void cur_motion(struct wl_listener *li, void *d) {
	struct wlr_pointer_motion_event *e = d;
	wlr_cursor_move(S.cursor, &e->pointer->base, e->delta_x, e->delta_y); pointer_motion(e->time_msec);
}
static void cur_abs(struct wl_listener *li, void *d) {
	struct wlr_pointer_motion_absolute_event *e = d;
	wlr_cursor_warp_absolute(S.cursor, &e->pointer->base, e->x, e->y); pointer_motion(e->time_msec);
}
static struct toplevel *toplevel_under_cursor(void) {
	double sx, sy;
	struct wlr_scene_node *n = wlr_scene_node_at(&S.scene->tree.node, S.cursor->x, S.cursor->y, &sx, &sy);
	if (!n || n->type != WLR_SCENE_NODE_BUFFER) return NULL;
	struct wlr_scene_tree *t = n->parent;
	while (t && !t->node.data) t = t->node.parent;
	return t ? t->node.data : NULL;
}
static void drop_snap(void) {   // drag a window to a screen edge: halves, quarters, maximize
	struct toplevel *t = S.grab_tl; if (!t || S.snap_edge <= 0) return;
	struct output *o = output_at(S.cursor->x, S.cursor->y); if (!o) return;
	struct wlr_box b = {0}; wlr_output_layout_get_box(S.out_layout, o->wlr, &b);
	double x = S.cursor->x - b.x, y = S.cursor->y - b.y; int e = S.snap_edge, c = 90;
	bool L = x <= e, R = x >= b.width - 1 - e, T = y <= e;
	if (L && y <= c) snap_to(t, SN_TL); else if (R && y <= c) snap_to(t, SN_TR);
	else if (L && y >= b.height - c) snap_to(t, SN_BL); else if (R && y >= b.height - c) snap_to(t, SN_BR);
	else if (L) snap_to(t, SN_LEFT); else if (R) snap_to(t, SN_RIGHT); else if (T) snap_to(t, SN_MAX);
}
static void cur_button(struct wl_listener *li, void *d) {
	struct wlr_pointer_button_event *e = d;
	wlr_idle_notifier_v1_notify_activity(S.idle, S.seat);
	if (e->state == WL_POINTER_BUTTON_STATE_RELEASED) {
		if (S.grab != GRAB_NONE) {
			if (S.grab == GRAB_MOVE) drop_snap();
			S.grab = GRAB_NONE; wlr_cursor_set_xcursor(S.cursor, S.xcur, "default"); return;
		}
		wlr_seat_pointer_notify_button(S.seat, e->time_msec, e->button, e->state); return;
	}
	if (S.locked) { wlr_seat_pointer_notify_button(S.seat, e->time_msec, e->button, e->state); return; }
	struct toplevel *t = toplevel_under_cursor();
	struct wlr_keyboard *kb = wlr_seat_get_keyboard(S.seat);
	uint32_t mods = kb ? wlr_keyboard_get_modifiers(kb) : 0;
	if (t && (mods & WLR_MODIFIER_LOGO) && (e->button == BTN_LEFT || e->button == BTN_RIGHT)) {
		focus_toplevel(t); begin_grab(t, e->button == BTN_LEFT ? GRAB_MOVE : GRAB_RESIZE); return;
	}
	if (t) focus_toplevel(t);
	wlr_seat_pointer_notify_button(S.seat, e->time_msec, e->button, e->state);
}
static void cur_axis(struct wl_listener *li, void *d) {
	struct wlr_pointer_axis_event *e = d;
	wlr_idle_notifier_v1_notify_activity(S.idle, S.seat);
	struct wlr_keyboard *kb = wlr_seat_get_keyboard(S.seat);
	if (!S.locked && kb && (wlr_keyboard_get_modifiers(kb) & WLR_MODIFIER_LOGO) && e->orientation == WL_POINTER_AXIS_VERTICAL_SCROLL) {
		switch_ws(S.cur_ws + (e->delta > 0 ? 1 : -1)); return;   // Super + scroll changes desktop
	}
	wlr_seat_pointer_notify_axis(S.seat, e->time_msec, e->orientation, e->delta, e->delta_discrete, e->source, e->relative_direction);
}
static void cur_frame(struct wl_listener *li, void *d) { wlr_seat_pointer_notify_frame(S.seat); }
static void sw_begin(struct wl_listener *li, void *d) { struct wlr_pointer_swipe_begin_event *e = d; S.sw_dx = S.sw_dy = 0; S.sw_fingers = e->fingers; }
static void sw_update(struct wl_listener *li, void *d) { struct wlr_pointer_swipe_update_event *e = d; S.sw_dx += e->dx; S.sw_dy += e->dy; }
static void sw_end(struct wl_listener *li, void *d) {
	struct wlr_pointer_swipe_end_event *e = d;
	if (e->cancelled || S.locked) return;
	char dir; double ax = S.sw_dx < 0 ? -S.sw_dx : S.sw_dx, ay = S.sw_dy < 0 ? -S.sw_dy : S.sw_dy;
	if (ax < 60 && ay < 60) return;
	if (ax > ay) dir = S.sw_dx < 0 ? 'l' : 'r'; else dir = S.sw_dy < 0 ? 'u' : 'd';
	for (int i = 0; i < S.ngest; i++)
		if (S.gest[i].fingers == S.sw_fingers && S.gest[i].dir == dir) {
			if (!strncmp(S.gest[i].cmd, "@ws", 3)) switch_ws(S.cur_ws + (dir == 'l' ? 1 : -1));   // swipe left = next desktop
			else run(S.gest[i].cmd);
		}
}
static void req_cursor(struct wl_listener *li, void *d) {
	struct wlr_seat_pointer_request_set_cursor_event *e = d;
	if (S.seat->pointer_state.focused_client == e->seat_client && S.grab == GRAB_NONE)
		wlr_cursor_set_surface(S.cursor, e->surface, e->hotspot_x, e->hotspot_y);
}
static void req_shape(struct wl_listener *li, void *d) {
	struct wlr_cursor_shape_manager_v1_request_set_shape_event *e = d;
	if (S.seat->pointer_state.focused_client == e->seat_client && S.grab == GRAB_NONE)
		wlr_cursor_set_xcursor(S.cursor, S.xcur, wlr_cursor_shape_v1_name(e->shape));
}
static void req_sel(struct wl_listener *li, void *d) { struct wlr_seat_request_set_selection_event *e = d; wlr_seat_set_selection(S.seat, e->source, e->serial); }
static void req_psel(struct wl_listener *li, void *d) { struct wlr_seat_request_set_primary_selection_event *e = d; wlr_seat_set_primary_selection(S.seat, e->source, e->serial); }

// ---------------------------------------------------------------- keyboard and shortcuts
static void apply_keymap(struct wlr_keyboard *kb) {
	struct xkb_context *ctx = xkb_context_new(XKB_CONTEXT_NO_FLAGS);
	struct xkb_rule_names rn = { .layout = S.layout[0] ? S.layout : NULL, .variant = S.variant[0] ? S.variant : NULL };
	struct xkb_keymap *km = xkb_keymap_new_from_names(ctx, &rn, XKB_KEYMAP_COMPILE_NO_FLAGS);
	if (km) { wlr_keyboard_set_keymap(kb, km); xkb_keymap_unref(km); }
	xkb_context_unref(ctx);
}
static void set_layout(const char *l, const char *v) {
	snprintf(S.layout, sizeof S.layout, "%s", l ? l : ""); snprintf(S.variant, sizeof S.variant, "%s", v ? v : "");
	struct keyboard *k; wl_list_for_each(k, &S.keyboards, link) apply_keymap(k->kb);
}
static void reload_config(void);
static void do_act(enum act a, const char *arg) {
	struct toplevel *t = focused();
	switch (a) {
	case A_EXEC: run(arg); break;
	case A_CLOSE: if (t) wlr_xdg_toplevel_send_close(t->xt); break;
	case A_EXIT: wl_display_terminate(S.display); break;
	case A_NEXT: {   // bring the window at the back to the front
		struct toplevel *x, *last = NULL; wl_list_for_each(x, &S.toplevels, link) if (visible(x)) last = x;
		if (last && last != t) focus_toplevel(last); break; }
	case A_SNAP: if (t && arg) snap_dir(t, arg); break;
	case A_FULL: if (t) set_fullscreen(t, !t->full); break;
	case A_WS: if (arg) switch_ws(atoi(arg)); break;
	case A_WSNEXT: switch_ws(S.cur_ws + 1); break;
	case A_WSPREV: switch_ws(S.cur_ws - 1); break;
	case A_MOVEWS: if (t && arg) { int n = atoi(arg); if (n >= 1 && n <= S.nws) { t->ws = n; update_vis(t); focus_best(); } } break;
	case A_MINIMIZE: minimize(t); break;
	case A_SHOWDESKTOP: show_desktop(); break;
	case A_RELOAD: reload_config(); break;
	}
}
static bool handle_bind(uint32_t mods, xkb_keysym_t sym) {
	sym = xkb_keysym_to_lower(sym);
	mods &= WLR_MODIFIER_LOGO | WLR_MODIFIER_ALT | WLR_MODIFIER_CTRL | WLR_MODIFIER_SHIFT;
	for (int i = 0; i < S.nbinds; i++) {
		struct bind *b = &S.binds[i];
		if (b->mods != mods || b->sym != sym) continue;
		if (S.locked && sym < 0x1008FF00) continue;   // while locked only media keys work
		do_act(b->act, b->arg);
		return true;
	}
	return false;
}
static void kb_mod(struct wl_listener *li, void *d) {
	struct keyboard *k = wl_container_of(li, k, mod);
	wlr_seat_set_keyboard(S.seat, k->kb); wlr_seat_keyboard_notify_modifiers(S.seat, &k->kb->modifiers);
}
static void kb_key(struct wl_listener *li, void *d) {
	struct keyboard *k = wl_container_of(li, k, key);
	struct wlr_keyboard_key_event *e = d;
	wlr_idle_notifier_v1_notify_activity(S.idle, S.seat);
	const xkb_keysym_t *syms; int n = xkb_state_key_get_syms(k->kb->xkb_state, e->keycode + 8, &syms);
	bool handled = false;
	if (e->state == WL_KEYBOARD_KEY_STATE_PRESSED)
		for (int i = 0; i < n && !handled; i++) {
			if (syms[i] >= XKB_KEY_XF86Switch_VT_1 && syms[i] <= XKB_KEY_XF86Switch_VT_12 && S.session) {
				wlr_session_change_vt(S.session, syms[i] - XKB_KEY_XF86Switch_VT_1 + 1); handled = true; break;
			}
			handled = handle_bind(wlr_keyboard_get_modifiers(k->kb), syms[i]);
		}
	if (!handled) { wlr_seat_set_keyboard(S.seat, k->kb); wlr_seat_keyboard_notify_key(S.seat, e->time_msec, e->keycode, e->state); }
}
static void kb_destroy(struct wl_listener *li, void *d) {
	struct keyboard *k = wl_container_of(li, k, destroy);
	wl_list_remove(&k->mod.link); wl_list_remove(&k->key.link); wl_list_remove(&k->destroy.link); wl_list_remove(&k->link); free(k);
}
static void new_input(struct wl_listener *li, void *d) {
	struct wlr_input_device *dev = d;
	if (dev->type == WLR_INPUT_DEVICE_KEYBOARD) {
		struct wlr_keyboard *kb = wlr_keyboard_from_input_device(dev);
		struct keyboard *k = calloc(1, sizeof *k); k->kb = kb;
		apply_keymap(kb); wlr_keyboard_set_repeat_info(kb, S.repeat_rate, S.repeat_delay);
		k->mod.notify = kb_mod; wl_signal_add(&kb->events.modifiers, &k->mod);
		k->key.notify = kb_key; wl_signal_add(&kb->events.key, &k->key);
		k->destroy.notify = kb_destroy; wl_signal_add(&dev->events.destroy, &k->destroy);
		wlr_seat_set_keyboard(S.seat, kb); wl_list_insert(&S.keyboards, &k->link);
	} else if (dev->type == WLR_INPUT_DEVICE_POINTER) wlr_cursor_attach_input_device(S.cursor, dev);
	uint32_t caps = WL_SEAT_CAPABILITY_POINTER;
	if (!wl_list_empty(&S.keyboards)) caps |= WL_SEAT_CAPABILITY_KEYBOARD;
	wlr_seat_set_capabilities(S.seat, caps);
}

// ---------------------------------------------------------------- xlin.conf
static uint32_t mod_bit(const char *m) {
	if (!strcasecmp(m, "SUPER")) return WLR_MODIFIER_LOGO;
	if (!strcasecmp(m, "ALT")) return WLR_MODIFIER_ALT;
	if (!strcasecmp(m, "CTRL")) return WLR_MODIFIER_CTRL;
	if (!strcasecmp(m, "SHIFT")) return WLR_MODIFIER_SHIFT;
	return 0;
}
static bool parse_combo(char *combo, uint32_t *mods, xkb_keysym_t *sym) {
	char *save, *part, *last = NULL; *mods = 0;
	for (part = strtok_r(combo, "+", &save); part; part = strtok_r(NULL, "+", &save)) {
		uint32_t m = mod_bit(part); if (m) *mods |= m; else last = part;
	}
	if (!last) return false;
	*sym = xkb_keysym_to_lower(xkb_keysym_from_name(last, XKB_KEYSYM_CASE_INSENSITIVE));
	if (*sym == XKB_KEY_NoSymbol) { wlr_log(WLR_ERROR, "xlin.conf: unknown key %s", last); return false; }
	return true;
}
static int snap_by_name(const char *n) {
	static const char *names[] = {"", "left", "right", "max", "tl", "tr", "bl", "br", "top", "bottom", "center"};
	for (int i = 1; i < 11; i++) if (!strcmp(names[i], n)) return i;
	return 0;
}
static void add_bind(struct bind b) {
	for (int i = 0; i < S.nbinds; i++) if (S.binds[i].mods == b.mods && S.binds[i].sym == b.sym) { free(S.binds[i].arg); S.binds[i] = b; return; }
	S.binds = realloc(S.binds, sizeof(struct bind) * (S.nbinds + 1)); S.binds[S.nbinds++] = b;
}
static void cfg_set(const char *k, const char *v) {
	if (!strcmp(k, "snap_edge")) S.snap_edge = atoi(v);
	else if (!strcmp(k, "gap")) S.gap = atoi(v);
	else if (!strcmp(k, "workspaces")) { S.nws = atoi(v); if (S.nws < 1) S.nws = 1; if (S.nws > 9) S.nws = 9; }
	else if (!strcmp(k, "scale")) S.scale = (float)atof(v);
	else if (!strcmp(k, "cursor_size")) S.cursor_size = atoi(v);
	else if (!strcmp(k, "repeat_rate")) S.repeat_rate = atoi(v);
	else if (!strcmp(k, "repeat_delay")) S.repeat_delay = atoi(v);
	else if (!strcmp(k, "layout")) snprintf(S.layout, sizeof S.layout, "%s", v);
	else if (!strcmp(k, "variant")) snprintf(S.variant, sizeof S.variant, "%s", v);
	else if (!strncmp(k, "hotcorner_", 10)) {
		int c = !strcmp(k + 10, "tl") ? 0 : !strcmp(k + 10, "tr") ? 1 : !strcmp(k + 10, "bl") ? 2 : !strcmp(k + 10, "br") ? 3 : -1;
		if (c >= 0) { free(S.hot[c]); S.hot[c] = *v ? strdup(v) : NULL; }
	}
}
static void load_config(const char *path, bool first) {
	FILE *f = fopen(path, "r"); if (!f) return;
	char line[2048];
	while (fgets(line, sizeof line, f)) {
		line[strcspn(line, "\n")] = 0;
		char *p = line + strspn(line, " \t"); if (!*p || *p == '#') continue;
		char *cmd = strtok(p, " \t"), *rest = strtok(NULL, ""); if (!cmd) continue;
		if (rest) rest += strspn(rest, " \t");
		if (!strcmp(cmd, "set") && rest) { char *k = strtok(rest, " \t"), *v = strtok(NULL, ""); if (k) cfg_set(k, v ? v + strspn(v, " \t") : ""); }
		else if (!strcmp(cmd, "env") && rest) { char *k = strtok(rest, " \t"), *v = strtok(NULL, ""); if (k && v) setenv(k, v + strspn(v, " \t"), 1); }
		else if (!strcmp(cmd, "exec-once") && rest) { if (first) { S.autostart = realloc(S.autostart, sizeof(char *) * (S.nauto + 1)); S.autostart[S.nauto++] = strdup(rest); } }
		else if (!strcmp(cmd, "bind") && rest) {
			char *combo = strtok(rest, " \t"), *act = strtok(NULL, " \t"), *arg = strtok(NULL, "");
			if (!combo || !act) continue;
			if (arg) arg += strspn(arg, " \t");
			struct bind b = {0};
			if (!parse_combo(combo, &b.mods, &b.sym)) continue;
			if (!strcmp(act, "exec") && arg) { b.act = A_EXEC; b.arg = strdup(arg); }
			else if (!strcmp(act, "close")) b.act = A_CLOSE;
			else if (!strcmp(act, "exit")) b.act = A_EXIT;
			else if (!strcmp(act, "next")) b.act = A_NEXT;
			else if (!strcmp(act, "snap") && arg) { b.act = A_SNAP; b.arg = strdup(arg); }
			else if (!strcmp(act, "fullscreen")) b.act = A_FULL;
			else if (!strcmp(act, "workspace") && arg) { b.act = A_WS; b.arg = strdup(arg); }
			else if (!strcmp(act, "movetoworkspace") && arg) { b.act = A_MOVEWS; b.arg = strdup(arg); }
			else if (!strcmp(act, "workspace-next")) b.act = A_WSNEXT;
			else if (!strcmp(act, "workspace-prev")) b.act = A_WSPREV;
			else if (!strcmp(act, "minimize")) b.act = A_MINIMIZE;
			else if (!strcmp(act, "showdesktop")) b.act = A_SHOWDESKTOP;
			else if (!strcmp(act, "reload")) b.act = A_RELOAD;
			else continue;
			add_bind(b);
		}
		else if (!strcmp(cmd, "unbind") && rest) {
			uint32_t m; xkb_keysym_t s; if (!parse_combo(rest, &m, &s)) continue;
			for (int i = 0; i < S.nbinds; i++) if (S.binds[i].mods == m && S.binds[i].sym == s) { free(S.binds[i].arg); S.binds[i] = S.binds[--S.nbinds]; break; }
		}
		else if (!strcmp(cmd, "gesture") && rest) {   // gesture 3 left @ws   |   gesture 3 up xlinos-launcher
			char *fg = strtok(rest, " \t"), *dir = strtok(NULL, " \t"), *c = strtok(NULL, "");
			if (!fg || !dir || !c) continue;
			S.gest = realloc(S.gest, sizeof(struct gesture) * (S.ngest + 1));
			S.gest[S.ngest++] = (struct gesture){ atoi(fg), dir[0], strdup(c + strspn(c, " \t")) };
		}
		else if (!strcmp(cmd, "rule") && rest) {   // rule CLASS-GLOB [workspace=N] [size=WxH] [snap=MODE]
			char *cls = strtok(rest, " \t"); if (!cls) continue;
			struct rule r = { strdup(cls), 0, 0, 0, 0 }; char *o;
			while ((o = strtok(NULL, " \t"))) {
				if (!strncmp(o, "workspace=", 10)) r.ws = atoi(o + 10);
				else if (!strncmp(o, "size=", 5)) sscanf(o + 5, "%dx%d", &r.w, &r.h);
				else if (!strncmp(o, "snap=", 5)) r.snap = snap_by_name(o + 5);
			}
			S.rules = realloc(S.rules, sizeof(struct rule) * (S.nrules + 1)); S.rules[S.nrules++] = r;
		}
	}
	fclose(f);
}
static void clear_config(void) {
	for (int i = 0; i < S.nbinds; i++) free(S.binds[i].arg);
	S.nbinds = 0;
	for (int i = 0; i < S.ngest; i++) free(S.gest[i].cmd);
	S.ngest = 0;
	for (int i = 0; i < S.nrules; i++) free(S.rules[i].cls);
	S.nrules = 0;
	for (int i = 0; i < 4; i++) { free(S.hot[i]); S.hot[i] = NULL; }
}
static void reload_config(void) {
	clear_config();
	if (main_conf) load_config(main_conf, false);
	if (user_conf) load_config(user_conf, false);
	struct keyboard *k; wl_list_for_each(k, &S.keyboards, link) { apply_keymap(k->kb); wlr_keyboard_set_repeat_info(k->kb, S.repeat_rate, S.repeat_delay); }
	struct toplevel *t; wl_list_for_each(t, &S.toplevels, link) if (t->mapped && t->snap != SN_NONE && !t->full) { enum snap s = t->snap; t->snap = SN_NONE; t->has_restore = false; snap_to(t, s); }
	wlr_log(WLR_INFO, "xlin.conf reloaded: %d shortcuts", S.nbinds);
}

// ---------------------------------------------------------------- control socket (xlinctl)
static void jstr(FILE *f, const char *s) {
	fputc('"', f);
	for (; s && *s; s++) { if (*s == '"' || *s == '\\') { fputc('\\', f); fputc(*s, f); } else if ((unsigned char)*s < 32) fputc(' ', f); else fputc(*s, f); }
	fputc('"', f);
}
static void jwin(FILE *f, struct toplevel *t) {
	struct wlr_box b; geo(t, &b);
	fprintf(f, "{\"address\":\"0x%x\",\"class\":", t->id); jstr(f, t->xt->app_id ? t->xt->app_id : "");
	fprintf(f, ",\"title\":"); jstr(f, t->xt->title ? t->xt->title : "");
	fprintf(f, ",\"workspace\":{\"id\":%d},\"at\":[%d,%d],\"size\":[%d,%d],\"floating\":true,\"hidden\":%s,\"fullscreen\":%s,\"snap\":%d,\"focus\":%s}",
		t->ws, b.x, b.y, b.width, b.height, t->hidden ? "true" : "false", t->full ? "true" : "false", t->snap, focused() == t ? "true" : "false");
}
static struct toplevel *parse_addr(const char *s) {
	if (!s || !*s) return focused();
	return by_id((unsigned)strtoul(s, NULL, 0));
}
static void ctl(char *line, FILE *o) {
	char *save, *c = strtok_r(line, " \t\r\n", &save), *a1 = strtok_r(NULL, " \t\r\n", &save), *a2 = strtok_r(NULL, " \t\r\n", &save), *a3 = strtok_r(NULL, " \t\r\n", &save);
	if (!c) { fputs("error: empty\n", o); return; }
	if (!strcmp(c, "version")) fprintf(o, "xlin-comp %s\n", VERSION);
	else if (!strcmp(c, "clients")) {
		fputc('[', o); bool first = true; struct toplevel *t;
		wl_list_for_each(t, &S.toplevels, link) if (t->mapped) { if (!first) fputc(',', o); first = false; jwin(o, t); }
		fputs("]\n", o);
	} else if (!strcmp(c, "activewindow")) { struct toplevel *t = focused(); if (t) jwin(o, t); else fputs("{}", o); fputc('\n', o); }
	else if (!strcmp(c, "monitors")) {
		fputc('[', o); bool first = true; struct output *m; int id = 0;
		wl_list_for_each(m, &S.outputs, link) {
			struct wlr_box b = {0}; wlr_output_layout_get_box(S.out_layout, m->wlr, &b);
			if (!first) fputc(',', o); first = false;
			fprintf(o, "{\"id\":%d,\"name\":", id++); jstr(o, m->wlr->name);
			fprintf(o, ",\"x\":%d,\"y\":%d,\"width\":%d,\"height\":%d,\"scale\":%.2f,\"usable\":[%d,%d,%d,%d]}",
				b.x, b.y, m->wlr->width, m->wlr->height, m->wlr->scale, m->usable.x, m->usable.y, m->usable.width, m->usable.height);
		}
		fputs("]\n", o);
	} else if (!strcmp(c, "workspaces")) {
		fputc('[', o);
		for (int i = 1; i <= S.nws; i++) {
			int n = 0; struct toplevel *t; wl_list_for_each(t, &S.toplevels, link) if (t->mapped && t->ws == i) n++;
			fprintf(o, "%s{\"id\":%d,\"windows\":%d,\"active\":%s}", i > 1 ? "," : "", i, n, i == S.cur_ws ? "true" : "false");
		}
		fputs("]\n", o);
	} else if (!strcmp(c, "activeworkspace")) fprintf(o, "{\"id\":%d}\n", S.cur_ws);
	else if (!strcmp(c, "cursor")) fprintf(o, "{\"x\":%d,\"y\":%d}\n", (int)S.cursor->x, (int)S.cursor->y);
	else if (!strcmp(c, "locked")) fprintf(o, "%s\n", S.locked ? "true" : "false");
	else if (!strcmp(c, "focus")) { struct toplevel *t = parse_addr(a1); if (t) { focus_toplevel(t); fputs("ok\n", o); } else fputs("error: no such window\n", o); }
	else if (!strcmp(c, "close")) { struct toplevel *t = parse_addr(a1); if (t) wlr_xdg_toplevel_send_close(t->xt); fputs("ok\n", o); }
	else if (!strcmp(c, "closeclass") && a1) { struct toplevel *t; wl_list_for_each(t, &S.toplevels, link) if (t->mapped && t->xt->app_id && !strcasecmp(t->xt->app_id, a1)) wlr_xdg_toplevel_send_close(t->xt); fputs("ok\n", o); }
	else if (!strcmp(c, "snap") && a1) { struct toplevel *t = parse_addr(a2); if (t) snap_dir(t, a1); fputs("ok\n", o); }
	else if (!strcmp(c, "move") && a1 && a2 && a3) { struct toplevel *t = by_id((unsigned)strtoul(a1, NULL, 0)); if (t) { struct wlr_box b; geo(t, &b); t->snap = SN_NONE; b.x = atoi(a2); b.y = atoi(a3); place(t, b); } fputs("ok\n", o); }
	else if (!strcmp(c, "size") && a1 && a2 && a3) { struct toplevel *t = by_id((unsigned)strtoul(a1, NULL, 0)); if (t) { struct wlr_box b; geo(t, &b); t->snap = SN_NONE; b.width = atoi(a2); b.height = atoi(a3); place(t, b); } fputs("ok\n", o); }
	else if (!strcmp(c, "minimize")) { minimize(parse_addr(a1)); fputs("ok\n", o); }
	else if (!strcmp(c, "fullscreen")) { struct toplevel *t = parse_addr(a1); if (t) set_fullscreen(t, !t->full); fputs("ok\n", o); }
	else if (!strcmp(c, "showdesktop")) { show_desktop(); fputs("ok\n", o); }
	else if (!strcmp(c, "workspace") && a1) { switch_ws(atoi(a1)); fputs("ok\n", o); }
	else if (!strcmp(c, "movetoworkspace") && a1) { struct toplevel *t = parse_addr(a2); int n = atoi(a1); if (t && n >= 1 && n <= S.nws) { t->ws = n; update_vis(t); focus_best(); } fputs("ok\n", o); }
	else if (!strcmp(c, "set") && a1) { cfg_set(a1, a2 ? a2 : ""); fputs("ok\n", o); }
	else if (!strcmp(c, "layout") && a1) { set_layout(a1, a2); fputs("ok\n", o); }
	else if (!strcmp(c, "reload")) { reload_config(); fputs("ok\n", o); }
	else if (!strcmp(c, "exit")) { fputs("ok\n", o); fflush(o); wl_display_terminate(S.display); }
	else fputs("error: unknown command\n", o);
}
static int ipc_ready(int fd, uint32_t mask, void *data) {
	int c = accept4(fd, NULL, NULL, SOCK_CLOEXEC); if (c < 0) return 0;
	struct timeval tv = {1, 0}; setsockopt(c, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof tv);
	char buf[1024]; ssize_t n = read(c, buf, sizeof buf - 1);
	if (n > 0) {
		buf[n] = 0; char *out = NULL; size_t sz = 0; FILE *f = open_memstream(&out, &sz);
		ctl(buf, f); fclose(f);
		if (out) { ssize_t w = write(c, out, sz); (void)w; free(out); }
	}
	close(c); return 0;
}
static void ipc_start(void) {
	const char *rt = getenv("XDG_RUNTIME_DIR");
	snprintf(S.sockpath, sizeof S.sockpath, "%s/xlin-comp.sock", rt ? rt : "/tmp");
	int fd = socket(AF_UNIX, SOCK_STREAM | SOCK_CLOEXEC, 0);
	struct sockaddr_un a = { .sun_family = AF_UNIX }; snprintf(a.sun_path, sizeof a.sun_path, "%s", S.sockpath);
	unlink(S.sockpath);
	if (bind(fd, (struct sockaddr *)&a, sizeof a) || listen(fd, 8)) { wlr_log(WLR_ERROR, "control socket failed: %s", strerror(errno)); return; }
	wl_event_loop_add_fd(S.loop, fd, WL_EVENT_READABLE, ipc_ready, NULL);
	setenv("XLIN_COMP_SOCK", S.sockpath, 1);
}

// ---------------------------------------------------------------- outputs
static void out_frame(struct wl_listener *li, void *d) {
	struct output *o = wl_container_of(li, o, frame);
	wlr_scene_output_commit(o->so, NULL);
	struct timespec now; clock_gettime(CLOCK_MONOTONIC, &now);
	wlr_scene_output_send_frame_done(o->so, &now);
	if (S.lock_pending && S.lock) { S.lock_pending = false; wlr_session_lock_v1_send_locked(S.lock); }
}
static void out_state(struct wl_listener *li, void *d) {
	struct output *o = wl_container_of(li, o, state);
	const struct wlr_output_event_request_state *e = d;
	wlr_output_commit_state(o->wlr, e->state); arrange_layers(o);
}
static void out_destroy(struct wl_listener *li, void *d) {
	struct output *o = wl_container_of(li, o, destroy);
	wl_list_remove(&o->frame.link); wl_list_remove(&o->state.link); wl_list_remove(&o->destroy.link); wl_list_remove(&o->link); free(o);
}
static void new_output(struct wl_listener *li, void *d) {
	struct wlr_output *wo = d;
	wlr_output_init_render(wo, S.allocator, S.renderer);
	struct wlr_output_state st; wlr_output_state_init(&st);
	wlr_output_state_set_enabled(&st, true);
	struct wlr_output_mode *m = wlr_output_preferred_mode(wo);
	if (m) wlr_output_state_set_mode(&st, m);
	if (S.scale > 0) wlr_output_state_set_scale(&st, S.scale);
	wlr_output_commit_state(wo, &st); wlr_output_state_finish(&st);
	struct output *o = calloc(1, sizeof *o); o->wlr = wo;
	o->frame.notify = out_frame; wl_signal_add(&wo->events.frame, &o->frame);
	o->state.notify = out_state; wl_signal_add(&wo->events.request_state, &o->state);
	o->destroy.notify = out_destroy; wl_signal_add(&wo->events.destroy, &o->destroy);
	wl_list_insert(&S.outputs, &o->link);
	struct wlr_output_layout_output *lo = wlr_output_layout_add_auto(S.out_layout, wo);
	o->so = wlr_scene_output_create(S.scene, wo);
	wlr_scene_output_layout_add_output(S.scene_layout, lo, o->so);
	arrange_layers(o);
	wlr_log(WLR_INFO, "output %s %dx%d scale %.2f", wo->name, wo->width, wo->height, wo->scale);
}

// ---------------------------------------------------------------- main
int main(int argc, char **argv) {
	wlr_log_init(WLR_INFO, NULL);
	char *startup = NULL;
	main_conf = getenv("XLIN_COMP_CONF");
	for (int i = 1; i < argc; i++) {
		if (!strcmp(argv[i], "-s") && i + 1 < argc) startup = argv[++i];
		else if (!strcmp(argv[i], "-c") && i + 1 < argc) main_conf = argv[++i];
		else if (!strcmp(argv[i], "-v")) { puts("xlin-comp " VERSION); return 0; }
	}
	S.cur_ws = 1; S.nws = 4; S.snap_edge = 24; S.repeat_rate = 25; S.repeat_delay = 600; S.cursor_size = 24; S.corner_armed = true;
	if (!main_conf) main_conf = "/usr/share/xlinos/xlin.conf";
	static char upath[512]; const char *h = getenv("HOME");
	if (h) { snprintf(upath, sizeof upath, "%s/.config/xlin/xlin.conf", h); user_conf = upath; }
	wl_list_init(&S.outputs); wl_list_init(&S.toplevels); wl_list_init(&S.keyboards); wl_list_init(&S.layers);
	load_config(main_conf, true);
	if (user_conf) load_config(user_conf, true);
	char sz[16]; snprintf(sz, sizeof sz, "%d", S.cursor_size); setenv("XCURSOR_SIZE", sz, 0);

	S.display = wl_display_create(); S.loop = wl_display_get_event_loop(S.display);
	S.backend = wlr_backend_autocreate(S.loop, &S.session);
	if (!S.backend) { wlr_log(WLR_ERROR, "no display backend"); return 1; }
	S.renderer = wlr_renderer_autocreate(S.backend);
	wlr_renderer_init_wl_display(S.renderer, S.display);
	S.allocator = wlr_allocator_autocreate(S.backend, S.renderer);
	wlr_compositor_create(S.display, 5, S.renderer);
	wlr_subcompositor_create(S.display);
	wlr_data_device_manager_create(S.display);
	wlr_primary_selection_v1_device_manager_create(S.display);
	wlr_data_control_manager_v1_create(S.display);
	wlr_viewporter_create(S.display);
	wlr_single_pixel_buffer_manager_v1_create(S.display);
	wlr_screencopy_manager_v1_create(S.display);
	wlr_fractional_scale_manager_v1_create(S.display, 1);
	S.idle = wlr_idle_notifier_v1_create(S.display);
	S.out_layout = wlr_output_layout_create(S.display);
	wlr_xdg_output_manager_v1_create(S.display, S.out_layout);
	S.scene = wlr_scene_create();
	S.scene_layout = wlr_scene_attach_output_layout(S.scene, S.out_layout);
	S.layer[L_BG] = wlr_scene_tree_create(&S.scene->tree);
	S.layer[L_BOTTOM] = wlr_scene_tree_create(&S.scene->tree);
	S.windows = wlr_scene_tree_create(&S.scene->tree);
	S.layer[L_TOP] = wlr_scene_tree_create(&S.scene->tree);
	S.fs = wlr_scene_tree_create(&S.scene->tree);
	S.layer[L_OVERLAY] = wlr_scene_tree_create(&S.scene->tree);
	S.new_output.notify = new_output; wl_signal_add(&S.backend->events.new_output, &S.new_output);
	S.xdg = wlr_xdg_shell_create(S.display, 3);
	S.new_toplevel.notify = new_toplevel; wl_signal_add(&S.xdg->events.new_toplevel, &S.new_toplevel);
	S.new_popup.notify = new_popup; wl_signal_add(&S.xdg->events.new_popup, &S.new_popup);
	S.layer_shell = wlr_layer_shell_v1_create(S.display, 4);
	S.new_layer.notify = new_layer; wl_signal_add(&S.layer_shell->events.new_surface, &S.new_layer);
	S.lockmgr = wlr_session_lock_manager_v1_create(S.display);
	S.new_lock.notify = new_lock; wl_signal_add(&S.lockmgr->events.new_lock, &S.new_lock);
	S.activation = wlr_xdg_activation_v1_create(S.display);
	S.req_activate.notify = req_activate; wl_signal_add(&S.activation->events.request_activate, &S.req_activate);
	S.cursor = wlr_cursor_create(); wlr_cursor_attach_output_layout(S.cursor, S.out_layout);
	S.xcur = wlr_xcursor_manager_create(NULL, S.cursor_size);
	S.cur_motion.notify = cur_motion; wl_signal_add(&S.cursor->events.motion, &S.cur_motion);
	S.cur_abs.notify = cur_abs; wl_signal_add(&S.cursor->events.motion_absolute, &S.cur_abs);
	S.cur_button.notify = cur_button; wl_signal_add(&S.cursor->events.button, &S.cur_button);
	S.cur_axis.notify = cur_axis; wl_signal_add(&S.cursor->events.axis, &S.cur_axis);
	S.cur_frame.notify = cur_frame; wl_signal_add(&S.cursor->events.frame, &S.cur_frame);
	S.sw_begin.notify = sw_begin; wl_signal_add(&S.cursor->events.swipe_begin, &S.sw_begin);
	S.sw_update.notify = sw_update; wl_signal_add(&S.cursor->events.swipe_update, &S.sw_update);
	S.sw_end.notify = sw_end; wl_signal_add(&S.cursor->events.swipe_end, &S.sw_end);
	S.seat = wlr_seat_create(S.display, "seat0");
	S.shape = wlr_cursor_shape_manager_v1_create(S.display, 1);
	S.req_shape.notify = req_shape; wl_signal_add(&S.shape->events.request_set_shape, &S.req_shape);
	S.new_input.notify = new_input; wl_signal_add(&S.backend->events.new_input, &S.new_input);
	S.req_cursor.notify = req_cursor; wl_signal_add(&S.seat->events.request_set_cursor, &S.req_cursor);
	S.req_sel.notify = req_sel; wl_signal_add(&S.seat->events.request_set_selection, &S.req_sel);
	S.req_psel.notify = req_psel; wl_signal_add(&S.seat->events.request_set_primary_selection, &S.req_psel);

	const char *sock = wl_display_add_socket_auto(S.display);
	if (!sock) { wlr_backend_destroy(S.backend); return 1; }
	if (!wlr_backend_start(S.backend)) { wlr_backend_destroy(S.backend); wl_display_destroy(S.display); return 1; }
	setenv("WAYLAND_DISPLAY", sock, 1);
	setenv("XDG_CURRENT_DESKTOP", "XlinOS", 1);
	setenv("XDG_SESSION_TYPE", "wayland", 1);
	ipc_start();
	signal(SIGCHLD, SIG_IGN); signal(SIGPIPE, SIG_IGN);
	for (int i = 0; i < S.nauto; i++) run(S.autostart[i]);
	if (startup) run(startup);
	wlr_log(WLR_INFO, "XlinOS compositor %s running on %s (%d shortcuts)", VERSION, sock, S.nbinds);
	wl_display_run(S.display);
	unlink(S.sockpath);
	wl_display_destroy_clients(S.display);
	wlr_scene_node_destroy(&S.scene->tree.node);
	wlr_xcursor_manager_destroy(S.xcur);
	wlr_output_layout_destroy(S.out_layout);
	wl_display_destroy(S.display);
	return 0;
}
