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
    # Previous position (before this frame's integrate)
    prev_x = ball.x - ball.vx * state.dt
    prev_y = ball.y - ball.vy * state.dt

    # Signed distances at start and end of frame
    d_prev = (prev_x - wall.x1) * wall.nx + (prev_y - wall.y1) * wall.ny
    d_curr = signed_dist

    # Crossed the infinite line if signs differ and the crossing is within radius band
    # More precisely: the ball surface (offset by radius) crossed the wall
    d_prev_surface = d_prev - ball.radius
    d_curr_surface = d_curr - ball.radius

    if d_prev_surface * d_curr_surface >= 0:
        return  # didn't cross

    # Fraction of the frame at which the ball surface hit the wall line
    frac = d_prev_surface / (d_prev_surface - d_curr_surface)

    # Position at moment of contact
    contact_x = prev_x + frac * (ball.x - prev_x)
    contact_y = prev_y + frac * (ball.y - prev_y)

    # Check the contact is within the wall segment (not past endpoints)
    along = (contact_x - wall.x1) * wall.tx + (contact_y - wall.y1) * wall.ty
    if along < -ball.radius or along > wall.length + ball.radius:
        return  # crossed the line extension outside the segment

    # Normal at crossing is always the wall face normal for a sweep
    nx, ny = wall.nx, wall.ny

    # If the ball was on the wrong side (negative signed dist at start),
    # flip normal — it came from behind the wall
    if d_prev < 0:
        nx, ny = -nx, -ny

    # Velocity response
    vel_along_normal = ball.vx * nx + ball.vy * ny
    if vel_along_normal >= 0:
        return  # separating

    REST_THRESHOLD = 0.3
    restitution = 0.0 if abs(vel_along_normal) < REST_THRESHOLD else state.e
    j = -(1.0 + restitution) * vel_along_normal / (1.0 / ball.mass)
    ball.vx += j * nx / ball.mass
    ball.vy += j * ny / ball.mass

    # Place ball exactly at contact position, on the correct side
    ball.x = contact_x + nx * ball.radius
    ball.y = contact_y + ny * ball.radius

def rect_vs_wall(rect, wall):
    corners = [
        (rect.x - rect.length/2, rect.y - rect.width/2),
        (rect.x + rect.length/2, rect.y - rect.width/2),
        (rect.x - rect.length/2, rect.y + rect.width/2),
        (rect.x + rect.length/2, rect.y + rect.width/2),
    ]

    for (cx, cy) in corners:
        dx = cx - wall.x1
        dy = cy - wall.y1

        t = dx * wall.tx + dy * wall.ty
        t = max(0.0, min(wall.length, t))
        closest_x = wall.x1 + t * wall.tx
        closest_y = wall.y1 + t * wall.ty

        pdx = cx - closest_x
        pdy = cy - closest_y
        dist = math.sqrt(pdx * pdx + pdy * pdy)

        CORNER_RADIUS = 0.05
        if dist < CORNER_RADIUS:
            # Normal always opposes incoming velocity
            vel_along = rect.vx * pdx + rect.vy * pdy  # dot with raw offset
            if dist < 1e-8:
                nx, ny = wall.nx, wall.ny
            else:
                nx = pdx / dist
                ny = pdy / dist

            # Flip normal to oppose velocity if needed
            if (rect.vx * nx + rect.vy * ny) > 0:
                nx, ny = -nx, -ny

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

def clamp_ball_to_world(ball):
    """Hard clamp: if a ball escapes the boundary box, snap it back and reflect velocity."""
    if not ball.can_move:
        return

    # Left wall
    if ball.x - ball.radius < state.left_wall:
        ball.x = state.left_wall + ball.radius
        if ball.vx < 0:
            ball.vx = abs(ball.vx) * state.e

    # Right wall
    if ball.x + ball.radius > state.right_wall:
        ball.x = state.right_wall - ball.radius
        if ball.vx > 0:
            ball.vx = -abs(ball.vx) * state.e

    # Ground
    if ball.y - ball.radius < state.ground:
        ball.y = state.ground + ball.radius
        if ball.vy < 0:
            ball.vy = abs(ball.vy) * state.e

    # Ceiling
    if ball.y + ball.radius > state.ceiling:
        ball.y = state.ceiling - ball.radius
        if ball.vy > 0:
            ball.vy = -abs(ball.vy) * state.e

def clamp_rect_to_world(rect):
    """Hard clamp: if a rectangle escapes the boundary box, snap it back and reflect velocity."""
    if not rect.can_move:
        return

    # Left wall
    if rect.x - rect.length/2 < state.left_wall:
        rect.x = state.left_wall + rect.length/2
        if rect.vx < 0:
            rect.vx = abs(rect.vx) * state.e

    # Right wall
    if rect.x + rect.length/2 > state.right_wall:
        rect.x = state.right_wall - rect.length/2
        if rect.vx > 0:
            rect.vx = -abs(rect.vx) * state.e

    # Ground
    if rect.y - rect.width/2 < state.ground:
        rect.y = state.ground + rect.width/2
        if rect.vy < 0:
            rect.vy = abs(rect.vy) * state.e

    # Ceiling
    if rect.y + rect.width/2 > state.ceiling:
        rect.y = state.ceiling - rect.width/2
        if rect.vy > 0:
            rect.vy = -abs(rect.vy) * state.e
