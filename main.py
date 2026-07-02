import pygame
import random
import coords
import config
import bodies
import wall
import spring
import collisions
import gravity_well
import state
import math

# ------------------------
# Walls + Springs + Balls
# ------------------------

walls = []
springs = []

walls.append(wall.Wall(state.left_wall, state.ground, state.right_wall, state.ground))
walls.append(wall.Wall(state.right_wall, state.ceiling, state.left_wall, state.ceiling))
walls.append(wall.Wall(state.left_wall, state.ceiling, state.left_wall, state.ground))
walls.append(wall.Wall(state.right_wall, state.ground, state.right_wall, state.ceiling))

NUM_BOUNDARY_WALLS = 4

balls = []
ball_1 = bodies.Ball(x=15, y=19,  vx=20,  vy=0,  mass=1, radius=0.5, colour=(255, 100, 100))
# ball_2 = Ball(x=14, y=15,  vx=3, vy=0,  mass=1, radius=0.5, colour=(100, 255, 100))
balls += [ball_1]

wells = []
well_1 = gravity_well.Gravity_Well(x=20, y=20, mass=100)
# wells.append(well_1)

rectangles = []
rect_1 = bodies.Rectangle(x=20, y=20, vx=-10, vy=0, mass=1, length=2, width=2, colour=(100, 255, 100))
# rect_2 = Rectangle(x=13, y=20, vx=5, vy=0, mass=1, length=1, width=1, colour=(100, 255, 100))
rectangles += [rect_1]

pygame.init()

import ui

screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
pygame.display.set_caption("Physics Sandbox")
clock = pygame.time.Clock()

running = True
while running:
    dt = clock.tick(120) / 1000.0
    state.dt = dt

    if not state.paused:
        state.sim_time += dt

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            # If a field is being edited, consume the keystroke there first
            if state.editing_field is not None and state.selected_obj is not None:
                ui.handle_info_keydown(event, state.selected_obj)
                continue   # don't let the keypress also trigger mode switches etc.

            keys = pygame.key.get_pressed()  # snapshot of all held keys

            if event.key == pygame.K_g:
                if keys[pygame.K_z]:           # Z+G → delete last well
                    if wells:
                        wells.pop()
                else:
                    state.mode = "WELL" if state.mode != "WELL" else "BALL"
                    state.wall_drawing = False
                    state.spring_selected_obj = None

            elif event.key == pygame.K_w:
                if keys[pygame.K_z]:  # Z+W → delete last user wall
                    if len(walls) > NUM_BOUNDARY_WALLS:
                        walls.pop()
                else:
                    state.mode = "WALL" if state.mode != "WALL" else "BALL"
                    state.wall_drawing = False

            elif event.key == pygame.K_b:
                if keys[pygame.K_z]:  # Z+B → delete last ball
                    if balls:
                        if state.selected_obj is balls[-1]:
                            state.selected_obj = None
                            state.position_history = []
                        balls.pop()
                else:
                    state.mode = "BALL"
                    state.wall_drawing = False
                    state.spring_selected_obj = None

            elif event.key == pygame.K_r:
                if keys[pygame.K_z]:  # Z+R → delete last rectangle
                    if rectangles:
                        if state.selected_obj is rectangles[-1]:
                            state.selected_obj = None
                            state.position_history = []
                        rectangles.pop()
                else:
                    state.mode = "RECTANGLE" if state.mode != "RECTANGLE" else "BALL"
                    state.wall_drawing = False

            elif event.key == pygame.K_s:
                if keys[pygame.K_z]:  # Z+S → delete last spring
                    if springs:
                        springs.pop()
                else:
                    state.mode = "SPRING" if state.mode != "SPRING" else "BALL"
                    state.spring_selected_obj = None

            elif event.key == pygame.K_z:
                pass  # Z alone does nothing now; it's only used as a modifier

            elif event.key == pygame.K_p:
                state.paused = not state.paused

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()

            # If clicking outside the info panel while editing, commit the edit
            if state.editing_field is not None and state.selected_obj is not None:
                ui.commit_edit(state.selected_obj)

            # Check if a click landed on an editable info-panel field
            if state.selected_obj is not None:
                clicked_field = ui.info_field_at(mx, my)
                if clicked_field is not None:
                    ui.start_edit(state.selected_obj, clicked_field)
                    continue   # don't let the click fall through to other handlers

            # Sliders always take priority
            if ui.point_on_slider_handle(mx, my):
                ui.slider_dragging = True
            elif ui.point_on_slider2_handle(mx, my):
                ui.slider2_dragging = True

            # Panel click — toggle controlled ball / wire springs (always available)
            elif ui.panel_object_at(mx, my, balls, rectangles) is not None:
                clicked = ui.panel_object_at(mx, my, balls, rectangles)

                # Selecting an object in the panel always shows its info in the bottom panel
                new_selected = None if state.selected_obj is clicked else clicked
                if new_selected is not state.selected_obj:
                    state.position_history = []
                state.selected_obj = new_selected

                if state.mode == "SPRING":
                    # Spring wiring: left click (ball-ball, ball-rect, rect-rect all allowed)
                    if state.spring_selected_obj is None:
                        state.spring_selected_obj = clicked
                    elif state.spring_selected_obj is clicked:
                        state.spring_selected_obj = None
                    else:
                        existing = None
                        for sp in springs:
                            if (sp.a is state.spring_selected_obj and sp.b is clicked) or \
                               (sp.b is state.spring_selected_obj and sp.a is clicked):
                                existing = sp
                                break
                        if existing:
                            springs.remove(existing)
                        else:
                            springs.append(spring.Spring(state.spring_selected_obj, clicked))
                        state.spring_selected_obj = None

            else:
                # Simulation area clicks
                wx, wy = coords.screen_to_world(mx, my)
                inside = state.left_wall <= wx <= state.right_wall and state.ground <= wy <= state.ceiling

                if state.mode == "WELL" and inside:
                    wells.append(gravity_well.Gravity_Well(x=wx, y=wy, mass=1000))

                elif state.mode == "BALL" and inside:
                    balls.append(bodies.Ball(
                        x=wx, y=wy,
                        vx=random.uniform(-15, 15),
                        vy=random.uniform(-15, 15),
                        mass=5, radius=0.5,
                        colour=(random.randint(100, 255),
                                random.randint(100, 255),
                                random.randint(100, 255))
                    ))

                elif state.mode == "WALL" and inside:
                    state.wall_drawing  = True
                    state.wall_start_wx = wx
                    state.wall_start_wy = wy

                elif state.mode == "RECTANGLE" and inside:
                    rectangles.append(bodies.Rectangle(
                        x=wx, y=wy,
                        vx=random.uniform(-15, 15),
                        vy=random.uniform(-15, 15),
                        mass=5, length=random.uniform(1,5),
                        width=random.uniform(1,5),
                        colour=(random.randint(100, 255),
                                random.randint(100, 255),
                                random.randint(100, 255))
                    ))

        elif event.type == pygame.MOUSEBUTTONUP:
            ui.slider_dragging  = False
            ui.slider2_dragging = False

            if state.wall_drawing:
                state.wall_drawing = False
                mx, my = pygame.mouse.get_pos()
                wx, wy = coords.screen_to_world(mx, my)
                ddx = wx - state.wall_start_wx
                ddy = wy - state.wall_start_wy
                if math.sqrt(ddx * ddx + ddy * ddy) > 0.1:
                    walls.append(wall.Wall(state.wall_start_wx, state.wall_start_wy, wx, wy))

        elif event.type == pygame.MOUSEMOTION:
            if ui.slider_dragging:
                _, my = pygame.mouse.get_pos()
                state.g = ui.slider_y_to_g(my)
            elif ui.slider2_dragging:
                _, my = pygame.mouse.get_pos()
                state.e = ui.slider_y_to_e(my)

    # ------------------------
    # Physics
    # ------------------------

    if not state.paused:
        for ball in balls:
            ball.clear_forces()

        for rect in rectangles:
            rect.clear_forces()

        for sp in springs:
            sp.apply_forces()

        for well in wells:
            for ball in balls:
                well.ball_vs_well(ball)
            for rect in rectangles:
                well.rect_vs_well(rect)

        for ball in balls:
            ball.integrate(dt)

        for rect in rectangles:
            rect.integrate(dt)

        for ball in balls:
            for w in walls:
                collisions.ball_vs_wall(ball, w)

        for rect in rectangles:
            for w in walls:
                collisions.rect_vs_wall(rect, w)

        for ball in balls:
            for rect in rectangles:
                rect.check_collision_ball(ball)

        for i in range(len(balls)):
            for j in range(i + 1, len(balls)):
                balls[i].check_collision(balls[j])

        for i in range(len(rectangles)):
            for j in range(i + 1, len(rectangles)):
                rectangles[i].check_collision(rectangles[j])

        for ball in balls:
            collisions.clamp_ball_to_world(ball)

        for rect in rectangles:
            collisions.clamp_rect_to_world((rect))

    if not state.paused and state.selected_obj is not None:
        state.position_history.append((
            state.sim_time,
            state.selected_obj.x, state.selected_obj.y,
            state.selected_obj.vx, state.selected_obj.vy
        ))
        cutoff = state.sim_time - state.GRAPH_HISTORY_SECONDS
        state.position_history = [p for p in state.position_history if p[0] >= cutoff]

    # ------------------------
    # Render
    # ------------------------

    screen.fill((30, 30, 30))

    # Boundary box
    pygame.draw.line(screen, (255, 255, 255), (config.BOX_LEFT, config.BOX_BOTTOM), (config.BOX_RIGHT, config.BOX_BOTTOM), 3)
    pygame.draw.line(screen, (255, 255, 255), (config.BOX_LEFT, config.BOX_TOP),    (config.BOX_RIGHT, config.BOX_TOP),    3)
    pygame.draw.line(screen, (255, 255, 255), (config.BOX_LEFT, config.BOX_TOP),    (config.BOX_LEFT,  config.BOX_BOTTOM), 3)
    pygame.draw.line(screen, (255, 255, 255), (config.BOX_RIGHT, config.BOX_TOP),   (config.BOX_RIGHT, config.BOX_BOTTOM), 3)

    for well in wells:
        wsx, wsy = coords.world_to_screen(well.x, well.y)
        pygame.draw.circle(screen, (180, 60, 255), (wsx, wsy), 10)
        pygame.draw.circle(screen, (220, 140, 255), (wsx, wsy), 10, 2)
        lbl = ui.font_panel.render(f"M={int(well.mass)}", True, (220, 180, 255))
        screen.blit(lbl, (wsx + 13, wsy - lbl.get_height() // 2))

    # User-drawn walls
    for w in walls[NUM_BOUNDARY_WALLS:]:
        sx1, sy1 = coords.world_to_screen(w.x1, w.y1)
        sx2, sy2 = coords.world_to_screen(w.x2, w.y2)
        pygame.draw.line(screen, (255, 200, 80), (sx1, sy1), (sx2, sy2), 3)
        pygame.draw.circle(screen, (255, 200, 80), (sx1, sy1), 4)
        pygame.draw.circle(screen, (255, 200, 80), (sx2, sy2), 4)

    # Wall preview
    if state.wall_drawing:
        mx, my = pygame.mouse.get_pos()
        sx1, sy1 = coords.world_to_screen(state.wall_start_wx, state.wall_start_wy)
        pygame.draw.line(screen, (180, 140, 50), (sx1, sy1), (mx, my), 2)
        pygame.draw.circle(screen, (255, 200, 80), (sx1, sy1), 4)

    # Springs
    for sp in springs:
        sx1, sy1 = coords.world_to_screen(sp.a.x, sp.a.y)
        sx2, sy2 = coords.world_to_screen(sp.b.x, sp.b.y)
        dx = sp.b.x - sp.a.x
        dy = sp.b.y - sp.a.y
        d  = math.sqrt(dx * dx + dy * dy)
        strain = (d - sp.L0) / max(sp.L0, 1e-8)
        strain = max(-1.0, min(1.0, strain))
        if strain >= 0:
            col = (80, int(80 + 175 * strain), 80)
        else:
            col = (int(80 + 175 * -strain), 80, 80)
        pygame.draw.line(screen, col, (sx1, sy1), (sx2, sy2), 2)

    # Balls
    for ball in balls:
        sx, sy = coords.world_to_screen(ball.x, ball.y)
        rp = max(1, int(ball.radius * coords.pixels_per_meter_x))
        pygame.draw.circle(screen, ball.colour, (sx, sy), rp)
        # Green ring on the selected ball in simulation view
        if ball is state.selected_obj:
            pygame.draw.circle(screen, (80, 255, 80), (sx, sy), rp + 4, 2)

    for rect in rectangles:
        sx, sy = coords.world_to_screen(rect.x - rect.length / 2, rect.y + rect.width / 2)
        len_x = max(1, int(rect.length * coords.pixels_per_meter_x))
        len_y = max(1, int(rect.width * coords.pixels_per_meter_y))
        pygame.draw.rect(screen, rect.colour, (sx, sy, len_x, len_y), width=0, border_radius=0)
        # Green box on the selected rectangle in simulation view
        if rect is state.selected_obj:
            pygame.draw.rect(screen, (80, 255, 80), (sx - 3, sy - 3, len_x + 6, len_y + 6), 2)

    # White ring/box on selected object in simulation view
    if state.mode == "SPRING" and state.spring_selected_obj is not None:
        sx, sy = coords.world_to_screen(state.spring_selected_obj.x, state.spring_selected_obj.y)
        if isinstance(state.spring_selected_obj, bodies.Rectangle):
            len_x = max(1, int(state.spring_selected_obj.length * coords.pixels_per_meter_x))
            len_y = max(1, int(state.spring_selected_obj.width * coords.pixels_per_meter_y))
            box_x = int(config.BOX_LEFT + (state.spring_selected_obj.x - state.spring_selected_obj.length/2) * coords.pixels_per_meter_x)
            box_y = int(config.BOX_BOTTOM - (state.spring_selected_obj.y + state.spring_selected_obj.width/2) * coords.pixels_per_meter_y)
            pygame.draw.rect(screen, (255, 255, 255), (box_x - 3, box_y - 3, len_x + 6, len_y + 6), 2)
        else:
            rp = max(1, int(state.spring_selected_obj.radius * coords.pixels_per_meter_x))
            pygame.draw.circle(screen, (255, 255, 255), (sx, sy), rp + 3, 2)

    # Preview line from selected object to mouse
    if state.mode == "SPRING" and state.spring_selected_obj is not None:
        mx, my = pygame.mouse.get_pos()
        sx1, sy1 = coords.world_to_screen(state.spring_selected_obj.x, state.spring_selected_obj.y)
        pygame.draw.line(screen, (180, 180, 80), (sx1, sy1), (mx, my), 1)

    # Panel always visible
    ui.draw_spring_panel(screen, balls, rectangles, state.spring_selected_obj, springs, state.selected_obj)

    ui.draw_object_info_hud(screen, state.selected_obj, balls, rectangles, state.g)
    ui.draw_slider(screen, state.g)
    ui.draw_slider2(screen, state.e)
    ui.draw_mode_indicator(screen, state.mode)
    ui.draw_pause_indicator(screen, state.paused)
    if state.selected_obj is not None:
        ui.draw_kinematics_graphs(screen, state.position_history)

    pygame.display.flip()

pygame.quit()
