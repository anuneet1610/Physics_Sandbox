import math
import state


# ------------------------
# Ball vs Wall
# ------------------------

def ball_vs_wall(ball, wall):

    # --- Static check first (ball already overlapping) ---
    dx = ball.x - wall.x1
    dy = ball.y - wall.y1
    signed_dist = dx * wall.nx + dy * wall.ny

    t = dx * wall.tx + dy * wall.ty
    t = max(0.0, min(wall.length, t))
    closest_x = wall.x1 + t * wall.tx
    closest_y = wall.y1 + t * wall.ty
    cx = ball.x - closest_x
    cy = ball.y - closest_y
    dist = math.sqrt(cx * cx + cy * cy)

    if dist < ball.radius:
        # Already overlapping — resolve normally
        if dist < 1e-8:
            nx, ny = wall.nx, wall.ny
        else:
            nx = cx / dist
            ny = cy / dist

        vel_along_normal = ball.vx * nx + ball.vy * ny
        if vel_along_normal < 0:
            REST_THRESHOLD = 0.3
            restitution = 0.0 if abs(vel_along_normal) < REST_THRESHOLD else state.e
            j = -(1.0 + restitution) * vel_along_normal / (1.0 / ball.mass)
            ball.vx += j * nx / ball.mass
            ball.vy += j * ny / ball.mass

        overlap = ball.radius - dist
        ball.x += nx * overlap
        ball.y += ny * overlap
        return

    # --- Swept check: did ball cross the wall this frame? ---
    prev_x = ball.x - ball.vx * state.dt
    prev_y = ball.y - ball.vy * state.dt

    d_prev = (prev_x - wall.x1) * wall.nx + (prev_y - wall.y1) * wall.ny
    d_curr = signed_dist

    d_prev_surface = d_prev - ball.radius
    d_curr_surface = d_curr - ball.radius

    if d_prev_surface * d_curr_surface >= 0:
        return

    frac = d_prev_surface / (d_prev_surface - d_curr_surface)

    contact_x = prev_x + frac * (ball.x - prev_x)
    contact_y = prev_y + frac * (ball.y - prev_y)

    along = (contact_x - wall.x1) * wall.tx + (contact_y - wall.y1) * wall.ty
    if along < -ball.radius or along > wall.length + ball.radius:
        return

    nx, ny = wall.nx, wall.ny

    if d_prev < 0:
        nx, ny = -nx, -ny

    vel_along_normal = ball.vx * nx + ball.vy * ny
    if vel_along_normal >= 0:
        return

    REST_THRESHOLD = 0.3
    restitution = 0.0 if abs(vel_along_normal) < REST_THRESHOLD else state.e
    j = -(1.0 + restitution) * vel_along_normal / (1.0 / ball.mass)
    ball.vx += j * nx / ball.mass
    ball.vy += j * ny / ball.mass

    ball.x = contact_x + nx * ball.radius
    ball.y = contact_y + ny * ball.radius

def rect_vs_wall(rect, wall):
    # Corner offsets from rect centre (axis-aligned, no rotation)
    corner_offsets = [
        (-rect.length/2, -rect.width/2),
        (+rect.length/2, -rect.width/2),
        (-rect.length/2, +rect.width/2),
        (+rect.length/2, +rect.width/2),
    ]

    CORNER_RADIUS = 0.05

    for (ox, oy) in corner_offsets:
        cx = rect.x + ox
        cy = rect.y + oy
        dx = cx - wall.x1
        dy = cy - wall.y1

        # Signed distance from the infinite wall line (which side is the corner on?)
        signed_d = dx * wall.nx + dy * wall.ny

        # Closest point on the wall SEGMENT (for static proximity check)
        t = max(0.0, min(wall.length, dx * wall.tx + dy * wall.ty))
        closest_x = wall.x1 + t * wall.tx
        closest_y = wall.y1 + t * wall.ty
        pdx = cx - closest_x
        pdy = cy - closest_y
        dist = math.sqrt(pdx * pdx + pdy * pdy)

        # --- Static check: corner already within CORNER_RADIUS of wall ---
        if dist < CORNER_RADIUS:
            nx, ny = (wall.nx, wall.ny) if signed_d >= 0 else (-wall.nx, -wall.ny)
            vel_along = rect.vx * nx + rect.vy * ny
            if vel_along < 0:
                REST_THRESHOLD = 0.3
                restitution = 0.0 if abs(vel_along) < REST_THRESHOLD else state.e
                j = -(1.0 + restitution) * vel_along / (1.0 / rect.mass)
                rect.vx += j * nx / rect.mass
                rect.vy += j * ny / rect.mass
            overlap = CORNER_RADIUS - dist
            rect.x += nx * overlap
            rect.y += ny * overlap
            continue  # skip swept check for this corner

        # --- Swept check: did this corner cross the wall line this frame? ---
        # Previous corner position (before this frame's integrate)
        prev_cx = cx - rect.vx * state.dt
        prev_cy = cy - rect.vy * state.dt
        prev_signed_d = (prev_cx - wall.x1) * wall.nx + (prev_cy - wall.y1) * wall.ny

        # No crossing if both ends of the frame are on the same side
        if prev_signed_d * signed_d >= 0:
            continue

        # Fraction of the frame at which the corner hit the wall line
        frac = prev_signed_d / (prev_signed_d - signed_d)
        contact_cx = prev_cx + frac * (cx - prev_cx)
        contact_cy = prev_cy + frac * (cy - prev_cy)

        # Verify the contact point falls within the wall segment
        along = (contact_cx - wall.x1) * wall.tx + (contact_cy - wall.y1) * wall.ty
        if along < 0 or along > wall.length:
            continue

        # Normal points toward where the corner came from
        nx, ny = (wall.nx, wall.ny) if prev_signed_d >= 0 else (-wall.nx, -wall.ny)

        vel_along = rect.vx * nx + rect.vy * ny
        if vel_along >= 0:
            continue  # already separating

        REST_THRESHOLD = 0.3
        restitution = 0.0 if abs(vel_along) < REST_THRESHOLD else state.e
        j = -(1.0 + restitution) * vel_along / (1.0 / rect.mass)
        rect.vx += j * nx / rect.mass
        rect.vy += j * ny / rect.mass

        # Place rect so this corner sits exactly CORNER_RADIUS from the wall
        rect.x = contact_cx - ox + nx * CORNER_RADIUS
        rect.y = contact_cy - oy + ny * CORNER_RADIUS

def clamp_ball_to_world(ball):
    """Hard clamp: if a ball escapes the boundary box, snap it back and reflect velocity."""
    if not ball.can_move:
        return

    if ball.x - ball.radius < state.left_wall:
        ball.x = state.left_wall + ball.radius
        if ball.vx < 0:
            ball.vx = abs(ball.vx) * state.e

    if ball.x + ball.radius > state.right_wall:
        ball.x = state.right_wall - ball.radius
        if ball.vx > 0:
            ball.vx = -abs(ball.vx) * state.e

    if ball.y - ball.radius < state.ground:
        ball.y = state.ground + ball.radius
        if ball.vy < 0:
            ball.vy = abs(ball.vy) * state.e

    if ball.y + ball.radius > state.ceiling:
        ball.y = state.ceiling - ball.radius
        if ball.vy > 0:
            ball.vy = -abs(ball.vy) * state.e

def clamp_rect_to_world(rect):
    """Hard clamp: if a rectangle escapes the boundary box, snap it back and reflect velocity."""
    if not rect.can_move:
        return

    if rect.x - rect.length/2 < state.left_wall:
        rect.x = state.left_wall + rect.length/2
        if rect.vx < 0:
            rect.vx = abs(rect.vx) * state.e

    if rect.x + rect.length/2 > state.right_wall:
        rect.x = state.right_wall - rect.length/2
        if rect.vx > 0:
            rect.vx = -abs(rect.vx) * state.e

    if rect.y - rect.width/2 < state.ground:
        rect.y = state.ground + rect.width/2
        if rect.vy < 0:
            rect.vy = abs(rect.vy) * state.e

    if rect.y + rect.width/2 > state.ceiling:
        rect.y = state.ceiling - rect.width/2
        if rect.vy > 0:
            rect.vy = -abs(rect.vy) * state.e