import pygame
import state
import config
from bodies import Rectangle, Ball

# ------------------------
# Fonts
# ------------------------

font_vel       = pygame.font.SysFont("monospace", 15, bold=True)
font_hud_title = pygame.font.SysFont("monospace", 13)
font_mode      = pygame.font.SysFont("monospace", 16, bold=True)
font_panel     = pygame.font.SysFont("monospace", 13, bold=True)

# ------------------------
# Gravity Slider
# ------------------------

SLIDER_X        = 900
SLIDER_Y_TOP    = 50
SLIDER_Y_BOTTOM = 850
SLIDER_WIDTH    = 20
G_MIN, G_MAX    = -20.0, 20.0
slider_dragging = False

def g_to_slider_y(g_val):
    t = (g_val - G_MIN) / (G_MAX - G_MIN)
    return SLIDER_Y_BOTTOM - t * (SLIDER_Y_BOTTOM - SLIDER_Y_TOP)

def slider_y_to_g(y):
    y = max(SLIDER_Y_TOP, min(SLIDER_Y_BOTTOM, y))
    t = (SLIDER_Y_BOTTOM - y) / (SLIDER_Y_BOTTOM - SLIDER_Y_TOP)
    return G_MIN + t * (G_MAX - G_MIN)

def point_on_slider_handle(mx, my):
    hy = g_to_slider_y(state.g)
    return (SLIDER_X - SLIDER_WIDTH <= mx <= SLIDER_X + SLIDER_WIDTH
            and hy - 10 <= my <= hy + 10)

def draw_slider(screen, g_val):
    pygame.draw.line(screen, (200, 200, 200), (SLIDER_X, SLIDER_Y_TOP), (SLIDER_X, SLIDER_Y_BOTTOM), 4)
    zy = g_to_slider_y(0)
    pygame.draw.line(screen, (120, 120, 120), (SLIDER_X - 12, zy), (SLIDER_X + 12, zy), 2)
    hy = g_to_slider_y(g_val)
    pygame.draw.circle(screen, (255, 200, 60), (SLIDER_X, int(hy)), 10)
    f = pygame.font.SysFont(None, 24)
    screen.blit(f.render(f"g = {g_val:.2f}", True, (255, 255, 255)), (SLIDER_X - 40, SLIDER_Y_TOP - 30))

# ------------------------
# Restitution Slider
# ------------------------

SLIDER2_X        = 950
SLIDER2_Y_TOP    = 50
SLIDER2_Y_BOTTOM = 850
SLIDER2_WIDTH    = 20
E_MIN, E_MAX     = 0.0, 1.0
slider2_dragging = False

def e_to_slider_y(e_val):
    t = (e_val - E_MIN) / (E_MAX - E_MIN)
    return SLIDER2_Y_BOTTOM - t * (SLIDER2_Y_BOTTOM - SLIDER2_Y_TOP)

def slider_y_to_e(y):
    y = max(SLIDER2_Y_TOP, min(SLIDER2_Y_BOTTOM, y))
    t = (SLIDER2_Y_BOTTOM - y) / (SLIDER2_Y_BOTTOM - SLIDER2_Y_TOP)
    return E_MIN + t * (E_MAX - E_MIN)

def point_on_slider2_handle(mx, my):
    hy = e_to_slider_y(state.e)
    return (SLIDER2_X - SLIDER2_WIDTH <= mx <= SLIDER2_X + SLIDER2_WIDTH
            and hy - 10 <= my <= hy + 10)

def draw_slider2(screen, e_val):
    pygame.draw.line(screen, (200, 200, 200), (SLIDER2_X, SLIDER2_Y_TOP), (SLIDER2_X, SLIDER2_Y_BOTTOM), 4)
    hy = e_to_slider_y(e_val)
    pygame.draw.circle(screen, (100, 220, 255), (SLIDER2_X, int(hy)), 10)
    f = pygame.font.SysFont(None, 24)
    screen.blit(f.render(f"e = {e_val:.2f}", True, (255, 255, 255)), (SLIDER2_X - 40, SLIDER2_Y_TOP - 30))

# ------------------------
# HUD
# ------------------------

HUD_Y_START = 843
HUD_LINE_H  = 18

# ------------------------
# Selected-Object Info Panel
# ------------------------

INFO_LINE_H  = 18

def _format_label(obj, balls, rectangles):
    """Return e.g. 'Ball #2' or 'Rectangle #1' for the given object."""
    if isinstance(obj, Rectangle):
        idx = rectangles.index(obj) if obj in rectangles else -1
        return f"Rectangle #{idx + 1}"
    else:
        idx = balls.index(obj) if obj in balls else -1
        return f"Ball #{idx + 1}"
VAL_X        = 150   # px from panel left edge to start of value column
VAL_W_SINGLE = 90    # px wide for a single value cell
VAL_W_PAIR   = 80    # px wide for each of two side-by-side value cells
VAL_GAP      = 6     # gap between the two paired cells

# Populated every frame in draw_object_info_hud; used by info_field_at()
_info_field_rects = []   # list of (pygame.Rect, field_key)

# Fields the user is allowed to edit (momentum/KE/PE excluded)
_EDITABLE = {"mass", "radius", "length", "width", "x", "y", "vx", "vy", "omega"}


def _field_current_str(obj, field):
    """Return the live value of 'field' on obj as a compact string."""
    mapping = {
        "mass":   lambda o: o.mass,
        "radius": lambda o: o.radius,
        "length": lambda o: o.length,
        "width":  lambda o: o.width,
        "x":      lambda o: o.x,
        "y":      lambda o: o.y,
        "vx":     lambda o: o.vx,
        "vy":     lambda o: o.vy,
        "omega":  lambda o: getattr(o, "omega", 0.0),
    }
    val = mapping[field](obj)
    return f"{val:.5g}"


def _draw_value_cell(screen, px, py, val_str, field_key, cell_w):
    """
    Draw one value cell.  If field_key matches state.editing_field, show the
    text buffer + cursor and a yellow highlight box.
    Appends to _info_field_rects when field_key is editable.
    Returns the surface x of the rendered text (unused externally).
    """
    is_editing = (field_key is not None and state.editing_field == field_key)
    is_editable = field_key in _EDITABLE if field_key else False

    cell_rect = pygame.Rect(px - 2, py - 1, cell_w, INFO_LINE_H)

    if is_editing:
        pygame.draw.rect(screen, (45, 45, 18), cell_rect)
        pygame.draw.rect(screen, (200, 200, 70), cell_rect, 1)
        display = state.editing_text + "|"
        colour = (255, 255, 120)
    elif is_editable:
        display = val_str
        colour = (255, 210, 70)   # warm yellow → clickable
    else:
        display = val_str
        colour = (160, 160, 160)  # dimmed → read-only

    screen.blit(font_vel.render(display, True, colour), (px, py))

    if is_editable:
        _info_field_rects.append((cell_rect, field_key))


def draw_object_info_hud(screen, selected_obj, balls, rectangles, g_val):
    global _info_field_rects
    _info_field_rects = []

    x, y = config.BOX_LEFT, HUD_Y_START

    if selected_obj is None:
        strip = pygame.Surface((config.BOX_RIGHT - config.BOX_LEFT, INFO_LINE_H + 10), pygame.SRCALPHA)
        strip.fill((0, 0, 0, 140))
        screen.blit(strip, (x, y - 4))
        screen.blit(font_hud_title.render(
            "  Select an object from the panel to see its info",
            True, (150, 150, 150)), (x + 6, y))
        return

    mass  = selected_obj.mass
    vx_   = selected_obj.vx
    vy_   = selected_obj.vy
    fx_   = getattr(selected_obj, "fx", 0.0)
    fy_   = getattr(selected_obj, "fy", 0.0)
    ax_   = fx_ / mass if mass else 0.0
    ay_   = fy_ / mass if mass else 0.0
    px_   = mass * vx_
    py_   = mass * vy_
    ke_   = 0.5 * mass * (vx_ * vx_ + vy_ * vy_)
    pe_   = mass * g_val * selected_obj.y
    omega = getattr(selected_obj, "omega", 0.0)

    # Each row: (label_str, [(display_str, field_key_or_None), ...])
    # field_key=None → read-only; field_key in _EDITABLE → editable
    if isinstance(selected_obj, Rectangle):
        size_row = ("Length / Width", [
            (f"{selected_obj.length:.4g}", "length"),
            (f"{selected_obj.width:.4g}",  "width"),
        ])
    else:
        size_row = ("Radius", [(f"{selected_obj.radius:.4g}", "radius")])

    rows = [
        ("Mass",         [(f"{mass:.4g}",  "mass")]),
        size_row,
        ("Position",     [(f"{selected_obj.x:+.4g}", "x"), (f"{selected_obj.y:+.4g}", "y")]),
        ("Velocity",     [(f"{vx_:+.4g}", "vx"),  (f"{vy_:+.4g}", "vy")]),
        ("Acceleration", [(f"{ax_:+.4g}", None),  (f"{ay_:+.4g}", None)]),
        ("Momentum",     [(f"{px_:+.4g}", None),  (f"{py_:+.4g}", None)]),
        ("KE",           [(f"{ke_:.4g}",  None)]),
        ("PE",           [(f"{pe_:.4g}",  None)]),
        ("Angular vel.", [(f"{omega:+.4g}", "omega")]),
    ]

    n_lines = len(rows) + 1   # +1 for title
    strip = pygame.Surface((config.BOX_RIGHT - config.BOX_LEFT, INFO_LINE_H * n_lines + 10),
                           pygame.SRCALPHA)
    strip.fill((0, 0, 0, 140))
    screen.blit(strip, (x, y - 4))

    # Title line
    obj_colour = getattr(selected_obj, "colour", (220, 220, 220))
    title = _format_label(selected_obj, balls, rectangles)
    screen.blit(font_hud_title.render(f"  {title}", True, obj_colour), (x + 6, y))
    y += INFO_LINE_H + 2

    # Data rows
    for label, values in rows:
        has_editable = any(fk in _EDITABLE for _, fk in values if fk)
        label_col = (220, 220, 220) if has_editable else (140, 140, 140)
        screen.blit(font_vel.render(f"  {label}", True, label_col), (x + 6, y))

        if len(values) == 1:
            val_str, fk = values[0]
            _draw_value_cell(screen, x + VAL_X, y, val_str, fk, VAL_W_SINGLE)
        else:
            for i, (val_str, fk) in enumerate(values):
                cell_x = x + VAL_X + i * (VAL_W_PAIR + VAL_GAP)
                _draw_value_cell(screen, cell_x, y, val_str, fk, VAL_W_PAIR)

        y += INFO_LINE_H


# ---- edit helpers ----

def info_field_at(mx, my):
    """Return field_key if (mx, my) is over an editable cell, else None."""
    for rect, fk in _info_field_rects:
        if rect.collidepoint(mx, my):
            return fk
    return None


def start_edit(obj, field_key):
    """Begin editing field_key; pre-populate buffer with current value."""
    state.editing_field = field_key
    state.editing_text  = _field_current_str(obj, field_key)


def commit_edit(obj):
    """Parse editing_text and write back to obj, then clear edit state."""
    if state.editing_field is None:
        return
    field = state.editing_field
    text  = state.editing_text
    state.editing_field = None
    state.editing_text  = ""
    if not text:
        return
    try:
        val = float(text)
    except ValueError:
        return
    if field in ("mass", "radius", "length", "width") and val <= 0:
        return  # reject non-positive sizes
    setattr_map = {
        "mass": "mass", "radius": "radius",
        "length": "length", "width": "width",
        "x": "x", "y": "y",
        "vx": "vx", "vy": "vy",
        "omega": "omega",
    }
    attr = setattr_map.get(field)
    if attr:
        setattr(obj, attr, val)


def handle_info_keydown(event, obj):
    """
    Route keyboard input while a field is being edited.
    Returns True to signal the event was consumed (skip mode-switch keys).
    """
    if state.editing_field is None:
        return False
    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        commit_edit(obj)
    elif event.key == pygame.K_ESCAPE:
        state.editing_field = None
        state.editing_text  = ""
    elif event.key == pygame.K_BACKSPACE:
        state.editing_text = state.editing_text[:-1]
    else:
        ch = event.unicode
        if ch in "0123456789.+-":
            state.editing_text += ch
    return True

def draw_mode_indicator(screen, mode):
    if mode == "WALL":
        colour = (255, 180, 50)
        text = "WALL MODE    [W] wall  [S] spring  [B] ball"
    elif mode == "SPRING":
        colour = (180, 255, 100)
        text = "SPRING MODE  [W] wall  [S] spring  [B] ball"
    else:
        colour = (100, 220, 255)
        text = "BALL MODE    [W] wall  [S] spring  [B] ball"
    screen.blit(font_mode.render(text, True, colour), (config.BOX_LEFT, config.BOX_TOP - 30))

# ------------------------
# Spring Panel
# ------------------------
# Sits between BOX_RIGHT (850) and SLIDER_X (900), full box height.
# Only drawn and interactive when mode == "SPRING".

PANEL_X     = config.BOX_RIGHT + 2   # left edge of panel
PANEL_W     = SLIDER_X - config.BOX_RIGHT - 4   # ~46px wide
PANEL_TOP   = config.BOX_TOP
PANEL_BOT   = config.BOX_BOTTOM
ROW_H       = 22   # px per ball row
SWATCH_R    = 6    # radius of colour swatch circle

def panel_row_rect(idx):
    """Return (x, y, w, h) for object row idx in the panel."""
    y = PANEL_TOP + idx * ROW_H
    return (PANEL_X, y, PANEL_W, ROW_H)

def panel_objects(balls, rectangles):
    """Combined, ordered list of springable objects with their panel labels."""
    items = []
    for idx, ball in enumerate(balls):
        items.append((ball, f"B{idx+1}"))
    for idx, rect in enumerate(rectangles):
        items.append((rect, f"R{idx+1}"))
    return items

def draw_spring_panel(screen, balls, rectangles, spring_selected_obj, springs, controlled_ball):
    # Background
    panel_surf = pygame.Surface((PANEL_W, PANEL_BOT - PANEL_TOP), pygame.SRCALPHA)
    panel_surf.fill((20, 20, 20, 200))
    screen.blit(panel_surf, (PANEL_X, PANEL_TOP))

    # Title
    title = font_panel.render("Objects", True, (180, 180, 180))
    screen.blit(title, (PANEL_X + 4, PANEL_TOP - 18))

    for idx, (obj, label_text) in enumerate(panel_objects(balls, rectangles)):
        rx, ry, rw, rh = panel_row_rect(idx)

        # Stop drawing if we've gone past the panel bottom
        if ry + rh > PANEL_BOT:
            break

        is_selected   = (obj is spring_selected_obj)
        is_controlled = (obj is controlled_ball)

        # Check if this object is connected to the already-selected object via a spring
        already_linked = False
        if spring_selected_obj is not None and obj is not spring_selected_obj:
            for sp in springs:
                if (sp.a is spring_selected_obj and sp.b is obj) or \
                   (sp.b is spring_selected_obj and sp.a is obj):
                    already_linked = True
                    break

        if is_controlled:
            pygame.draw.rect(screen, (20, 50, 20), (rx, ry, rw, rh))
        elif is_selected:
            pygame.draw.rect(screen, (60, 60, 20), (rx, ry, rw, rh))
        elif already_linked:
            pygame.draw.rect(screen, (50, 30, 10), (rx, ry, rw, rh))

        # Colour swatch — circle for balls, square for rectangles
        cx = rx + SWATCH_R + 4
        cy = ry + rh // 2
        if isinstance(obj, Rectangle):
            pygame.draw.rect(screen, obj.colour,
                              (cx - SWATCH_R, cy - SWATCH_R, SWATCH_R * 2, SWATCH_R * 2))
        else:
            pygame.draw.circle(screen, obj.colour, (cx, cy), SWATCH_R)

        # Gamepad icon on controlled object
        if is_controlled:
            pygame.draw.circle(screen, (80, 255, 80), (cx, cy), SWATCH_R + 2, 2)

        # Label, e.g. "B1" or "R1"
        label = font_panel.render(label_text, True, (220, 220, 220))
        screen.blit(label, (cx + SWATCH_R + 4, cy - label.get_height() // 2))

        # Row border
        pygame.draw.line(screen, (50, 50, 50), (rx, ry + rh - 1), (rx + rw, ry + rh - 1))

def panel_object_at(mx, my, balls, rectangles):
    """Return the object (ball or rectangle) whose panel row was clicked, or None."""
    if not (PANEL_X <= mx <= PANEL_X + PANEL_W):
        return None
    if not (PANEL_TOP <= my <= PANEL_BOT):
        return None
    idx = (my - PANEL_TOP) // ROW_H
    items = panel_objects(balls, rectangles)
    if 0 <= idx < len(items):
        # Make sure this row is actually drawn (not past panel bottom)
        _, ry, _, rh = panel_row_rect(idx)
        if ry + rh <= PANEL_BOT:
            return items[idx][0]
    return None