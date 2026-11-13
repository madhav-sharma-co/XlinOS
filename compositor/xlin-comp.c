// xlin-comp: the XlinOS window compositor.
// Floating windows, bars and docks (layer shell), shortcuts, clipboard, screenshots.
// Design follows the wlroots scene-graph approach. Phase 1 (see docs/COMPOSITOR.md).
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <time.h>
#include <unistd.h>
#include <signal.h>
#include <wayland-server-core.h>
#include <wlr/backend.h>
#include <wlr/render/allocator.h>
#include <wlr/render/wlr_renderer.h>
#include <wlr/types/wlr_compositor.h>
#include <wlr/types/wlr_cursor.h>
#include <wlr/types/wlr_data_control_v1.h>
#include <wlr/types/wlr_data_device.h>
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
#include <wlr/types/wlr_single_pixel_buffer_v1.h>
#include <wlr/types/wlr_subcompositor.h>
#include <wlr/types/wlr_viewporter.h>
#include <wlr/types/wlr_xcursor_manager.h>
#include <wlr/types/wlr_xdg_decoration_v1.h>
#include <wlr/types/wlr_xdg_output_v1.h>
#include <wlr/types/wlr_xdg_shell.h>
#include <wlr/util/log.h>
#include <xkbcommon/xkbcommon.h>
#include <linux/input-event-codes.h>

enum grab { GRAB_NONE, GRAB_MOVE, GRAB_RESIZE };
enum act { ACT_EXEC, ACT_CLOSE, ACT_EXIT, ACT_NEXT };

struct bind { uint32_t mods; xkb_keysym_t sym; enum act act; char *arg; };

struct server {
	struct wl_display *display;
	struct wlr_backend *backend;
	struct wlr_renderer *renderer;
	struct wlr_allocator *allocator;
	struct wlr_scene *scene;
	struct wlr_scene_output_layout *scene_layout;
	struct wlr_scene_tree *layer[4];   // background, bottom, [windows], top, overlay (see L_*)
	struct wlr_scene_tree *windows;
	struct wlr_output_layout *out_layout;
	struct wlr_xdg_shell *xdg;
	struct wlr_layer_shell_v1 *layer_shell;
	struct wlr_cursor *cursor;
	struct wlr_xcursor_manager *xcur;
	struct wlr_seat *seat;
	struct wl_list outputs, toplevels, keyboards, layers;
	struct wl_listener new_output, new_xdg_toplevel, new_xdg_popup, new_layer, new_input;
	struct wl_listener cur_motion, cur_abs, cur_button, cur_axis, cur_frame;
	struct wl_listener req_cursor, req_sel, req_psel, new_deco;
	struct wlr_xdg_decoration_manager_v1 *deco;
	enum grab grab; struct toplevel *grab_tl; double gx, gy; struct wlr_box gbox;
	struct bind *binds; int nbinds;
	struct layer_surface *kb_layer;    // layer surface that owns the keyboard (launcher)
};
static struct server S;
enum { L_BG = 0, L_BOTTOM = 1, L_TOP = 2, L_OVERLAY = 3 };

struct output {
	struct wl_list link; struct wlr_output *wlr; struct wlr_scene_output *so;
	struct wl_listener frame, state, destroy;
};
struct toplevel {
	struct wl_list link; struct wlr_xdg_toplevel *xt; struct wlr_scene_tree *tree;
	struct wl_listener map, unmap, commit, destroy, req_move, req_resize, req_max, req_full;
};
struct popup { struct wlr_xdg_popup *xp; struct wl_listener commit, destroy; };
struct keyboard {
	struct wl_list link; struct wlr_keyboard *kb;
	struct wl_listener mod, key, destroy;
};
struct layer_surface {
	struct wl_list link; struct wlr_scene_layer_surface_v1 *sl; struct wlr_layer_surface_v1 *ls;
	struct wl_listener map, unmap, commit, destroy;
};

// ---------------------------------------------------------------- helpers
static void run(const char *cmd) {
	if (fork() == 0) { setsid(); execl("/bin/sh", "sh", "-c", cmd, (char *)NULL); _exit(1); }
}
static struct toplevel *toplevel_at(double x, double y, struct wlr_surface **s, double *sx, double *sy) {
	struct wlr_scene_node *n = wlr_scene_node_at(&S.scene->tree.node, x, y, sx, sy);
	if (!n || n->type != WLR_SCENE_NODE_BUFFER) return NULL;
	struct wlr_scene_surface *ss = wlr_scene_surface_try_from_buffer(wlr_scene_buffer_from_node(n));
	if (!ss) return NULL;
	*s = ss->surface;
	struct wlr_scene_tree *t = n->parent;
	while (t && !t->node.data) t = t->node.parent;
	return t ? t->node.data : NULL;   // NULL for layer surfaces (their trees carry no toplevel)
}
static void focus_toplevel(struct toplevel *tl) {
	if (!tl) return;
	struct wlr_surface *prev = S.seat->keyboard_state.focused_surface;
	struct wlr_surface *surf = tl->xt->base->surface;
	if (prev == surf) return;
	if (prev) {
		struct wlr_xdg_toplevel *pt = wlr_xdg_toplevel_try_from_wlr_surface(prev);
		if (pt) wlr_xdg_toplevel_set_activated(pt, false);
	}
	wlr_scene_node_raise_to_top(&tl->tree->node);
	wl_list_remove(&tl->link); wl_list_insert(&S.toplevels, &tl->link);
	wlr_xdg_toplevel_set_activated(tl->xt, true);
	struct wlr_keyboard *kb = wlr_seat_get_keyboard(S.seat);
	if (kb) wlr_seat_keyboard_notify_enter(S.seat, surf, kb->keycodes, kb->num_keycodes, &kb->modifiers);
}
static void focus_layer(struct layer_surface *l) {
	S.kb_layer = l;
	struct wlr_keyboard *kb = wlr_seat_get_keyboard(S.seat);
	if (kb) wlr_seat_keyboard_notify_enter(S.seat, l->ls->surface, kb->keycodes, kb->num_keycodes, &kb->modifiers);
}
static void arrange_layers(struct output *o) {
	struct wlr_box full = {0}, usable;
	wlr_output_layout_get_box(S.out_layout, o->wlr, &full);
	usable = full;
	struct layer_surface *l;
	for (int pass = 0; pass < 2; pass++)   // exclusive-zone surfaces first
		wl_list_for_each(l, &S.layers, link)
			if (l->ls->output == o->wlr && (l->ls->current.exclusive_zone > 0) == (pass == 0))
				wlr_scene_layer_surface_v1_configure(l->sl, &full, &usable);
}

// ---------------------------------------------------------------- layer shell (bars, dock, wallpaper, launcher)
static void layer_map(struct wl_listener *li, void *d) {
	struct layer_surface *l = wl_container_of(li, l, map);
	if (l->ls->current.keyboard_interactive == ZWLR_LAYER_SURFACE_V1_KEYBOARD_INTERACTIVITY_EXCLUSIVE) focus_layer(l);
}
static void layer_unmap(struct wl_listener *li, void *d) {
	struct layer_surface *l = wl_container_of(li, l, unmap);
	if (S.kb_layer == l) {
		S.kb_layer = NULL;
		wlr_seat_keyboard_notify_clear_focus(S.seat);
		if (!wl_list_empty(&S.toplevels)) {
			struct toplevel *t = wl_container_of(S.toplevels.next, t, link);
			wlr_seat_keyboard_notify_clear_focus(S.seat);
			struct wlr_keyboard *kb = wlr_seat_get_keyboard(S.seat);
			if (kb) wlr_seat_keyboard_notify_enter(S.seat, t->xt->base->surface, kb->keycodes, kb->num_keycodes, &kb->modifiers);
		}
	}
}
static void layer_commit(struct wl_listener *li, void *d) {
	struct layer_surface *l = wl_container_of(li, l, commit);
	if (!l->ls->initial_commit && !l->ls->surface->mapped && !l->ls->current.committed) return;
	struct output *o; wl_list_for_each(o, &S.outputs, link) if (o->wlr == l->ls->output) arrange_layers(o);
	if (l->ls->surface->mapped &&
	    l->ls->current.keyboard_interactive == ZWLR_LAYER_SURFACE_V1_KEYBOARD_INTERACTIVITY_EXCLUSIVE && S.kb_layer != l) focus_layer(l);
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
		struct output *o = wl_container_of(S.outputs.next, o, link);
		if (wl_list_empty(&S.outputs)) { wlr_layer_surface_v1_destroy(ls); return; }
		ls->output = o->wlr;
	}
	int idx = ls->pending.layer;   // background 0, bottom 1, top 2, overlay 3
	struct layer_surface *l = calloc(1, sizeof *l);
	l->ls = ls;
	l->sl = wlr_scene_layer_surface_v1_create(S.layer[idx], ls);
	wl_list_insert(&S.layers, &l->link);
	l->map.notify = layer_map; wl_signal_add(&ls->surface->events.map, &l->map);
	l->unmap.notify = layer_unmap; wl_signal_add(&ls->surface->events.unmap, &l->unmap);
	l->commit.notify = layer_commit; wl_signal_add(&ls->surface->events.commit, &l->commit);
	l->destroy.notify = layer_destroy; wl_signal_add(&ls->events.destroy, &l->destroy);
}

// ---------------------------------------------------------------- windows
static void tl_map(struct wl_listener *li, void *d) {
	struct toplevel *t = wl_container_of(li, t, map);
	wl_list_insert(&S.toplevels, &t->link);
	struct wlr_box g = t->xt->base->geometry, area = {0};
	struct output *o = wl_list_empty(&S.outputs) ? NULL : wl_container_of(S.outputs.next, o, link);
	if (o) wlr_output_layout_get_box(S.out_layout, o->wlr, &area);
	int x = area.x + (area.width - g.width) / 2, y = area.y + (area.height - g.height) / 2;
	static int cascade; x += (cascade % 5) * 28; y += (cascade % 5) * 28; cascade++;
	wlr_scene_node_set_position(&t->tree->node, x < area.x ? area.x : x, y < area.y + 32 ? area.y + 32 : y);
	focus_toplevel(t);
}
static void tl_unmap(struct wl_listener *li, void *d) {
	struct toplevel *t = wl_container_of(li, t, unmap);
	if (S.grab_tl == t) S.grab = GRAB_NONE;
	bool had = S.seat->keyboard_state.focused_surface == t->xt->base->surface;
	wl_list_remove(&t->link);
	if (had) {
		wlr_seat_keyboard_notify_clear_focus(S.seat);
		if (!wl_list_empty(&S.toplevels)) { struct toplevel *n = wl_container_of(S.toplevels.next, n, link); focus_toplevel(n); }
	}
}
static void tl_commit(struct wl_listener *li, void *d) {
	struct toplevel *t = wl_container_of(li, t, commit);
	if (t->xt->base->initial_commit) wlr_xdg_toplevel_set_size(t->xt, 0, 0);
}
static void tl_destroy(struct wl_listener *li, void *d) {
	struct toplevel *t = wl_container_of(li, t, destroy);
	wl_list_remove(&t->map.link); wl_list_remove(&t->unmap.link); wl_list_remove(&t->commit.link);
	wl_list_remove(&t->destroy.link); wl_list_remove(&t->req_move.link); wl_list_remove(&t->req_resize.link);
	wl_list_remove(&t->req_max.link); wl_list_remove(&t->req_full.link); free(t);
}
static void begin_grab(struct toplevel *t, enum grab g);
static void tl_req_move(struct wl_listener *li, void *d) { struct toplevel *t = wl_container_of(li, t, req_move); begin_grab(t, GRAB_MOVE); }
static void tl_req_resize(struct wl_listener *li, void *d) { struct toplevel *t = wl_container_of(li, t, req_resize); begin_grab(t, GRAB_RESIZE); }
static void tl_req_max(struct wl_listener *li, void *d) {
	struct toplevel *t = wl_container_of(li, t, req_max);
	if (t->xt->base->initialized) wlr_xdg_surface_schedule_configure(t->xt->base);
}
static void tl_req_full(struct wl_listener *li, void *d) {
	struct toplevel *t = wl_container_of(li, t, req_full);
	if (t->xt->base->initialized) wlr_xdg_surface_schedule_configure(t->xt->base);
}
static void new_toplevel(struct wl_listener *li, void *d) {
	struct wlr_xdg_toplevel *xt = d;
	struct toplevel *t = calloc(1, sizeof *t);
	t->xt = xt;
	t->tree = wlr_scene_xdg_surface_create(S.windows, xt->base);
	t->tree->node.data = t;
	xt->base->data = t->tree;
	t->map.notify = tl_map; wl_signal_add(&xt->base->surface->events.map, &t->map);
	t->unmap.notify = tl_unmap; wl_signal_add(&xt->base->surface->events.unmap, &t->unmap);
	t->commit.notify = tl_commit; wl_signal_add(&xt->base->surface->events.commit, &t->commit);
	t->destroy.notify = tl_destroy; wl_signal_add(&xt->events.destroy, &t->destroy);
	t->req_move.notify = tl_req_move; wl_signal_add(&xt->events.request_move, &t->req_move);
	t->req_resize.notify = tl_req_resize; wl_signal_add(&xt->events.request_resize, &t->req_resize);
	t->req_max.notify = tl_req_max; wl_signal_add(&xt->events.request_maximize, &t->req_max);
	t->req_full.notify = tl_req_full; wl_signal_add(&xt->events.request_fullscreen, &t->req_full);
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
	if (parent) {
		struct wlr_scene_tree *pt = parent->data;
		xp->base->data = wlr_scene_xdg_surface_create(pt, xp->base);
	}
	p->commit.notify = popup_commit; wl_signal_add(&xp->base->surface->events.commit, &p->commit);
	p->destroy.notify = popup_destroy; wl_signal_add(&xp->events.destroy, &p->destroy);
}
static void new_deco(struct wl_listener *li, void *d) {   // windows draw their own title bars
	struct wlr_xdg_toplevel_decoration_v1 *dc = d;
	wlr_xdg_toplevel_decoration_v1_set_mode(dc, WLR_XDG_TOPLEVEL_DECORATION_V1_MODE_CLIENT_SIDE);
}

// ---------------------------------------------------------------- pointer
static void begin_grab(struct toplevel *t, enum grab g) {
	S.grab = g; S.grab_tl = t;
	S.gx = S.cursor->x; S.gy = S.cursor->y;
	S.gbox.x = t->tree->node.x; S.gbox.y = t->tree->node.y;
	S.gbox.width = t->xt->base->geometry.width; S.gbox.height = t->xt->base->geometry.height;
	wlr_cursor_set_xcursor(S.cursor, S.xcur, g == GRAB_MOVE ? "grabbing" : "se-resize");
}
static void pointer_motion(uint32_t time) {
	if (S.grab == GRAB_MOVE) {
		wlr_scene_node_set_position(&S.grab_tl->tree->node, S.gbox.x + (int)(S.cursor->x - S.gx), S.gbox.y + (int)(S.cursor->y - S.gy));
		return;
	}
	if (S.grab == GRAB_RESIZE) {
		int w = S.gbox.width + (int)(S.cursor->x - S.gx), h = S.gbox.height + (int)(S.cursor->y - S.gy);
		wlr_xdg_toplevel_set_size(S.grab_tl->xt, w < 160 ? 160 : w, h < 100 ? 100 : h);
		return;
	}
	double sx, sy; struct wlr_surface *s = NULL;
	struct wlr_scene_node *n = wlr_scene_node_at(&S.scene->tree.node, S.cursor->x, S.cursor->y, &sx, &sy);
	if (n && n->type == WLR_SCENE_NODE_BUFFER) {
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
static void cur_button(struct wl_listener *li, void *d) {
	struct wlr_pointer_button_event *e = d;
	if (e->state == WL_POINTER_BUTTON_STATE_RELEASED) {
		if (S.grab != GRAB_NONE) { S.grab = GRAB_NONE; wlr_cursor_set_xcursor(S.cursor, S.xcur, "default"); return; }
		wlr_seat_pointer_notify_button(S.seat, e->time_msec, e->button, e->state); return;
	}
	struct wlr_surface *s = NULL; double sx, sy;
	struct toplevel *t = toplevel_at(S.cursor->x, S.cursor->y, &s, &sx, &sy);
	struct wlr_keyboard *kb = wlr_seat_get_keyboard(S.seat);
	uint32_t mods = kb ? wlr_keyboard_get_modifiers(kb) : 0;
	if (t && (mods & WLR_MODIFIER_LOGO) && (e->button == BTN_LEFT || e->button == BTN_RIGHT)) {
		focus_toplevel(t); begin_grab(t, e->button == BTN_LEFT ? GRAB_MOVE : GRAB_RESIZE); return;
	}
	if (t) focus_toplevel(t);
	else if (S.kb_layer && s != S.kb_layer->ls->surface) {   // click outside the launcher: it closes itself
	}
	wlr_seat_pointer_notify_button(S.seat, e->time_msec, e->button, e->state);
}
static void cur_axis(struct wl_listener *li, void *d) {
	struct wlr_pointer_axis_event *e = d;
	wlr_seat_pointer_notify_axis(S.seat, e->time_msec, e->orientation, e->delta, e->delta_discrete, e->source, e->relative_direction);
}
static void cur_frame(struct wl_listener *li, void *d) { wlr_seat_pointer_notify_frame(S.seat); }

// ---------------------------------------------------------------- keyboard and shortcuts
static bool handle_bind(uint32_t mods, xkb_keysym_t sym) {
	sym = xkb_keysym_to_lower(sym);
	mods &= WLR_MODIFIER_LOGO | WLR_MODIFIER_ALT | WLR_MODIFIER_CTRL | WLR_MODIFIER_SHIFT;
	for (int i = 0; i < S.nbinds; i++) {
		struct bind *b = &S.binds[i];
		if (b->mods != mods || b->sym != sym) continue;
		switch (b->act) {
		case ACT_EXEC: run(b->arg); break;
		case ACT_CLOSE: if (!wl_list_empty(&S.toplevels)) { struct toplevel *t = wl_container_of(S.toplevels.next, t, link); wlr_xdg_toplevel_send_close(t->xt); } break;
		case ACT_EXIT: wl_display_terminate(S.display); break;
		case ACT_NEXT: if (S.toplevels.next != S.toplevels.prev) {
			struct toplevel *last = wl_container_of(S.toplevels.prev, last, link); focus_toplevel(last); } break;
		}
		return true;
	}
	return false;
}
static void kb_mod(struct wl_listener *li, void *d) {
	struct keyboard *k = wl_container_of(li, k, mod);
	wlr_seat_set_keyboard(S.seat, k->kb);
	wlr_seat_keyboard_notify_modifiers(S.seat, &k->kb->modifiers);
}
static void kb_key(struct wl_listener *li, void *d) {
	struct keyboard *k = wl_container_of(li, k, key);
	struct wlr_keyboard_key_event *e = d;
	const xkb_keysym_t *syms; int n = xkb_state_key_get_syms(k->kb->xkb_state, e->keycode + 8, &syms);
	bool handled = false;
	if (e->state == WL_KEYBOARD_KEY_STATE_PRESSED)
		for (int i = 0; i < n && !handled; i++) handled = handle_bind(wlr_keyboard_get_modifiers(k->kb), syms[i]);
	if (!handled) {
		wlr_seat_set_keyboard(S.seat, k->kb);
		wlr_seat_keyboard_notify_key(S.seat, e->time_msec, e->keycode, e->state);
	}
}
static void kb_destroy(struct wl_listener *li, void *d) {
	struct keyboard *k = wl_container_of(li, k, destroy);
	wl_list_remove(&k->mod.link); wl_list_remove(&k->key.link); wl_list_remove(&k->destroy.link); wl_list_remove(&k->link); free(k);
}
static void add_keyboard(struct wlr_input_device *dev) {
	struct wlr_keyboard *kb = wlr_keyboard_from_input_device(dev);
	struct keyboard *k = calloc(1, sizeof *k); k->kb = kb;
	struct xkb_context *ctx = xkb_context_new(XKB_CONTEXT_NO_FLAGS);
	struct xkb_rule_names rn = { .layout = getenv("XKB_DEFAULT_LAYOUT"), .variant = getenv("XKB_DEFAULT_VARIANT") };
	struct xkb_keymap *km = xkb_keymap_new_from_names(ctx, &rn, XKB_KEYMAP_COMPILE_NO_FLAGS);
	wlr_keyboard_set_keymap(kb, km); xkb_keymap_unref(km); xkb_context_unref(ctx);
	wlr_keyboard_set_repeat_info(kb, 25, 600);
	k->mod.notify = kb_mod; wl_signal_add(&kb->events.modifiers, &k->mod);
	k->key.notify = kb_key; wl_signal_add(&kb->events.key, &k->key);
	k->destroy.notify = kb_destroy; wl_signal_add(&dev->events.destroy, &k->destroy);
	wlr_seat_set_keyboard(S.seat, kb);
	wl_list_insert(&S.keyboards, &k->link);
}
static void new_input(struct wl_listener *li, void *d) {
	struct wlr_input_device *dev = d;
	if (dev->type == WLR_INPUT_DEVICE_KEYBOARD) add_keyboard(dev);
	else if (dev->type == WLR_INPUT_DEVICE_POINTER) wlr_cursor_attach_input_device(S.cursor, dev);
	uint32_t caps = WL_SEAT_CAPABILITY_POINTER;
	if (!wl_list_empty(&S.keyboards)) caps |= WL_SEAT_CAPABILITY_KEYBOARD;
	wlr_seat_set_capabilities(S.seat, caps);
}
static void req_cursor(struct wl_listener *li, void *d) {
	struct wlr_seat_pointer_request_set_cursor_event *e = d;
	if (S.seat->pointer_state.focused_client == e->seat_client && S.grab == GRAB_NONE)
		wlr_cursor_set_surface(S.cursor, e->surface, e->hotspot_x, e->hotspot_y);
}
static void req_sel(struct wl_listener *li, void *d) { struct wlr_seat_request_set_selection_event *e = d; wlr_seat_set_selection(S.seat, e->source, e->serial); }
static void req_psel(struct wl_listener *li, void *d) { struct wlr_seat_request_set_primary_selection_event *e = d; wlr_seat_set_primary_selection(S.seat, e->source, e->serial); }

// shortcuts: lines "SUPER+SHIFT+Q exec command" / "close" / "exit" / "next"
static uint32_t mod_bit(const char *m) {
	if (!strcasecmp(m, "SUPER")) return WLR_MODIFIER_LOGO;
	if (!strcasecmp(m, "ALT")) return WLR_MODIFIER_ALT;
	if (!strcasecmp(m, "CTRL")) return WLR_MODIFIER_CTRL;
	if (!strcasecmp(m, "SHIFT")) return WLR_MODIFIER_SHIFT;
	return 0;
}
static void load_binds(const char *path) {
	FILE *f = fopen(path, "r"); if (!f) { wlr_log(WLR_INFO, "no shortcut file %s", path); return; }
	char line[1024];
	while (fgets(line, sizeof line, f)) {
		line[strcspn(line, "\n")] = 0;
		if (!*line || *line == '#') continue;
		char *combo = strtok(line, " \t"), *act = strtok(NULL, " \t"), *arg = strtok(NULL, "");
		if (!combo || !act) continue;
		struct bind b = {0};
		char *save, *part, *last = NULL;
		for (part = strtok_r(combo, "+", &save); part; part = strtok_r(NULL, "+", &save)) {
			uint32_t m = mod_bit(part);
			if (m) b.mods |= m; else last = part;
		}
		if (!last) continue;
		b.sym = xkb_keysym_to_lower(xkb_keysym_from_name(last, XKB_KEYSYM_CASE_INSENSITIVE));
		if (b.sym == XKB_KEY_NoSymbol) { wlr_log(WLR_ERROR, "unknown key %s", last); continue; }
		if (!strcmp(act, "exec") && arg) { b.act = ACT_EXEC; b.arg = strdup(arg + strspn(arg, " \t")); }
		else if (!strcmp(act, "close")) b.act = ACT_CLOSE;
		else if (!strcmp(act, "exit")) b.act = ACT_EXIT;
		else if (!strcmp(act, "next")) b.act = ACT_NEXT;
		else continue;
		S.binds = realloc(S.binds, sizeof(struct bind) * (S.nbinds + 1)); S.binds[S.nbinds++] = b;
	}
	fclose(f);
	wlr_log(WLR_INFO, "%d shortcuts loaded", S.nbinds);
}

// ---------------------------------------------------------------- outputs
static void out_frame(struct wl_listener *li, void *d) {
	struct output *o = wl_container_of(li, o, frame);
	wlr_scene_output_commit(o->so, NULL);
	struct timespec now; clock_gettime(CLOCK_MONOTONIC, &now);
	wlr_scene_output_send_frame_done(o->so, &now);
}
static void out_state(struct wl_listener *li, void *d) {
	struct output *o = wl_container_of(li, o, state); arrange_layers(o);
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
	wlr_output_commit_state(wo, &st); wlr_output_state_finish(&st);
	struct output *o = calloc(1, sizeof *o); o->wlr = wo;
	o->frame.notify = out_frame; wl_signal_add(&wo->events.frame, &o->frame);
	o->state.notify = out_state; wl_signal_add(&wo->events.request_state, &o->state);
	o->destroy.notify = out_destroy; wl_signal_add(&wo->events.destroy, &o->destroy);
	wl_list_insert(&S.outputs, &o->link);
	struct wlr_output_layout_output *lo = wlr_output_layout_add_auto(S.out_layout, wo);
	o->so = wlr_scene_output_create(S.scene, wo);
	wlr_scene_output_layout_add_output(S.scene_layout, lo, o->so);
	wlr_log(WLR_INFO, "output %s %dx%d", wo->name, wo->width, wo->height);
}

// ---------------------------------------------------------------- main
int main(int argc, char **argv) {
	wlr_log_init(WLR_INFO, NULL);
	char *startup = NULL, *conf = getenv("XLIN_COMP_CONF");
	for (int i = 1; i < argc; i++) {
		if (!strcmp(argv[i], "-s") && i + 1 < argc) startup = argv[++i];
		else if (!strcmp(argv[i], "-c") && i + 1 < argc) conf = argv[++i];
		else if (!strcmp(argv[i], "-v")) { puts("xlin-comp 0.1"); return 0; }
	}
	wl_list_init(&S.outputs); wl_list_init(&S.toplevels); wl_list_init(&S.keyboards); wl_list_init(&S.layers);
	S.display = wl_display_create();
	S.backend = wlr_backend_autocreate(wl_display_get_event_loop(S.display), NULL);
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
	S.out_layout = wlr_output_layout_create(S.display);
	wlr_xdg_output_manager_v1_create(S.display, S.out_layout);
	S.scene = wlr_scene_create();
	S.scene_layout = wlr_scene_attach_output_layout(S.scene, S.out_layout);
	S.layer[L_BG] = wlr_scene_tree_create(&S.scene->tree);
	S.layer[L_BOTTOM] = wlr_scene_tree_create(&S.scene->tree);
	S.windows = wlr_scene_tree_create(&S.scene->tree);
	S.layer[L_TOP] = wlr_scene_tree_create(&S.scene->tree);
	S.layer[L_OVERLAY] = wlr_scene_tree_create(&S.scene->tree);
	S.new_output.notify = new_output; wl_signal_add(&S.backend->events.new_output, &S.new_output);
	S.xdg = wlr_xdg_shell_create(S.display, 3);
	S.new_xdg_toplevel.notify = new_toplevel; wl_signal_add(&S.xdg->events.new_toplevel, &S.new_xdg_toplevel);
	S.new_xdg_popup.notify = new_popup; wl_signal_add(&S.xdg->events.new_popup, &S.new_xdg_popup);
	S.layer_shell = wlr_layer_shell_v1_create(S.display, 4);
	S.new_layer.notify = new_layer; wl_signal_add(&S.layer_shell->events.new_surface, &S.new_layer);
	S.deco = wlr_xdg_decoration_manager_v1_create(S.display);
	S.new_deco.notify = new_deco; wl_signal_add(&S.deco->events.new_toplevel_decoration, &S.new_deco);
	S.cursor = wlr_cursor_create(); wlr_cursor_attach_output_layout(S.cursor, S.out_layout);
	S.xcur = wlr_xcursor_manager_create(NULL, 24);
	S.cur_motion.notify = cur_motion; wl_signal_add(&S.cursor->events.motion, &S.cur_motion);
	S.cur_abs.notify = cur_abs; wl_signal_add(&S.cursor->events.motion_absolute, &S.cur_abs);
	S.cur_button.notify = cur_button; wl_signal_add(&S.cursor->events.button, &S.cur_button);
	S.cur_axis.notify = cur_axis; wl_signal_add(&S.cursor->events.axis, &S.cur_axis);
	S.cur_frame.notify = cur_frame; wl_signal_add(&S.cursor->events.frame, &S.cur_frame);
	S.seat = wlr_seat_create(S.display, "seat0");
	S.new_input.notify = new_input; wl_signal_add(&S.backend->events.new_input, &S.new_input);
	S.req_cursor.notify = req_cursor; wl_signal_add(&S.seat->events.request_set_cursor, &S.req_cursor);
	S.req_sel.notify = req_sel; wl_signal_add(&S.seat->events.request_set_selection, &S.req_sel);
	S.req_psel.notify = req_psel; wl_signal_add(&S.seat->events.request_set_primary_selection, &S.req_psel);

	if (conf) load_binds(conf);
	const char *sock = wl_display_add_socket_auto(S.display);
	if (!sock) { wlr_backend_destroy(S.backend); return 1; }
	if (!wlr_backend_start(S.backend)) { wlr_backend_destroy(S.backend); wl_display_destroy(S.display); return 1; }
	setenv("WAYLAND_DISPLAY", sock, 1);
	setenv("XDG_CURRENT_DESKTOP", "XlinOS", 1);
	signal(SIGCHLD, SIG_IGN);
	if (startup) run(startup);
	wlr_log(WLR_INFO, "XlinOS compositor running on %s", sock);
	wl_display_run(S.display);
	wl_display_destroy_clients(S.display);
	wlr_scene_node_destroy(&S.scene->tree.node);
	wlr_xcursor_manager_destroy(S.xcur);
	wlr_output_layout_destroy(S.out_layout);
	wl_display_destroy(S.display);
	return 0;
}
