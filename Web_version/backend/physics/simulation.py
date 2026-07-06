import math
import random

from . import collisions
from .bodies import Ball, Rectangle
from .gravity_well import GravityWell
from .settings import (
    WORLD_WIDTH, WORLD_HEIGHT, GRAPH_HISTORY_SECONDS, NUM_BOUNDARY_WALLS,
    FIXED_DT, MAX_SUBSTEPS, SUBSTEP_DISTANCE,
)
from .spring import Spring
from .wall import Wall

_EDITABLE = {"mass", "radius", "length", "width", "x", "y", "vx", "vy"}


class SimulationState:
    """Owns all sim objects + tunables. One instance == one 'room' of the
    sandbox. step() mirrors the physics section of the old main.py loop;
    the handle_* methods mirror the old pygame event handlers."""

    def __init__(self):
        self.g = 9.81
        self.e = 1.0
        self.G = 1.0
        self.mode = "BALL"
        self.paused = False
        self.sim_time = 0.0

        self.left_wall, self.right_wall = 0, WORLD_WIDTH
        self.ground, self.ceiling = 0, WORLD_HEIGHT

        self.walls = [
            Wall(self.left_wall, self.ground, self.right_wall, self.ground),
            Wall(self.right_wall, self.ceiling, self.left_wall, self.ceiling),
            Wall(self.left_wall, self.ceiling, self.left_wall, self.ground),
            Wall(self.right_wall, self.ground, self.right_wall, self.ceiling),
        ]
        self.balls = [Ball(x=15, y=19, vx=20, vy=0, mass=1, radius=0.5, colour=(255, 100, 100))]
        self.rectangles = [Rectangle(x=20, y=20, vx=-10, vy=0, mass=1, length=2, width=2, colour=(100, 255, 100))]
        self.wells = []
        self.springs = []

        self.spring_selected_id = None
        self.selected_id = None
        self.editing_field = None
        self.editing_text = ""
        self.wall_drawing = False
        self.wall_start = (0.0, 0.0)
        self.wall_preview_end = None  # updated by client cursor pings while drawing

        self.position_history = []  # [(t, x, y, vx, vy)]

    # ---------- lookups ----------

    def _all_springable(self):
        return list(self.balls) + list(self.rectangles)

    def find_object(self, obj_id):
        for o in self._all_springable():
            if o.id == obj_id:
                return o
        return None

    @property
    def selected_obj(self):
        return self.find_object(self.selected_id) if self.selected_id is not None else None

    # ---------- physics step (mirrors main.py's "Physics" section) ----------

    def step(self):
        # Fixed timestep: deterministic regardless of asyncio/network jitter.
        if self.paused:
            return

        dt = FIXED_DT
        self.sim_time += dt

        for ball in self.balls:
            ball.clear_forces(self.g)
        for rect in self.rectangles:
            rect.clear_forces(self.g)

        for sp in self.springs:
            sp.apply_forces()

        for well in self.wells:
            for ball in self.balls:
                well.ball_vs_well(ball, self.G)
            for rect in self.rectangles:
                well.rect_vs_well(rect, self.G)

        # Sub-step: split this frame's dt into smaller increments if any
        # object would otherwise travel further than SUBSTEP_DISTANCE in
        # one go (fast bodies can tunnel through zero-thickness walls
        # otherwise, since the swept check only looks at start/end of a
        # single step).
        max_speed = 0.0
        for obj in self.balls + self.rectangles:
            speed = (obj.vx ** 2 + obj.vy ** 2) ** 0.5
            max_speed = max(max_speed, speed)

        n_sub = 1
        if max_speed > 0:
            n_sub = min(MAX_SUBSTEPS, max(1, math.ceil(max_speed * dt / SUBSTEP_DISTANCE)))
        sub_dt = dt / n_sub

        for _ in range(n_sub):
            self._integrate_and_resolve(sub_dt)

        if self.selected_obj is not None:
            sel = self.selected_obj
            self.position_history.append((self.sim_time, sel.x, sel.y, sel.vx, sel.vy))
            cutoff = self.sim_time - GRAPH_HISTORY_SECONDS
            self.position_history = [p for p in self.position_history if p[0] >= cutoff]

    def _integrate_and_resolve(self, dt):
        for ball in self.balls:
            ball.integrate(dt)
        for rect in self.rectangles:
            rect.integrate(dt)

        for ball in self.balls:
            for w in self.walls:
                collisions.ball_vs_wall(ball, w, self.e, dt)

        for rect in self.rectangles:
            for w in self.walls:
                collisions.rect_vs_wall(rect, w, self.e, dt)

        for ball in self.balls:
            for rect in self.rectangles:
                rect.check_collision_ball(ball, self.e)

        for i in range(len(self.balls)):
            for j in range(i + 1, len(self.balls)):
                self.balls[i].check_collision(self.balls[j], self.e)

        for i in range(len(self.rectangles)):
            for j in range(i + 1, len(self.rectangles)):
                self.rectangles[i].check_collision(self.rectangles[j], self.e)

        for ball in self.balls:
            collisions.clamp_ball_to_world(ball, self.e, self.left_wall, self.right_wall, self.ground, self.ceiling)
        for rect in self.rectangles:
            collisions.clamp_rect_to_world(rect, self.e, self.left_wall, self.right_wall, self.ground, self.ceiling)

    # ---------- command handlers (mirror the old pygame event branches) ----------

    def set_mode(self, mode):
        if mode not in ("BALL", "WALL", "SPRING", "RECTANGLE", "WELL"):
            return
        self.mode = mode
        self.wall_drawing = False
        if mode != "SPRING":
            self.spring_selected_id = None

    def toggle_pause(self):
        self.paused = not self.paused

    def set_g(self, value):
        self.g = max(-20.0, min(20.0, float(value)))

    def set_e(self, value):
        self.e = max(0.0, min(1.0, float(value)))

    def add_ball_at(self, wx, wy, random_vel=True):
        if not self._inside(wx, wy):
            return
        self.balls.append(Ball(
            x=wx, y=wy,
            vx=random.uniform(-15, 15) if random_vel else 0,
            vy=random.uniform(-15, 15) if random_vel else 0,
            mass=5, radius=0.5,
            colour=(random.randint(100, 255), random.randint(100, 255), random.randint(100, 255)),
        ))

    def add_rect_at(self, wx, wy):
        if not self._inside(wx, wy):
            return
        self.rectangles.append(Rectangle(
            x=wx, y=wy,
            vx=random.uniform(-15, 15), vy=random.uniform(-15, 15),
            mass=5, length=random.uniform(1, 5), width=random.uniform(1, 5),
            colour=(random.randint(100, 255), random.randint(100, 255), random.randint(100, 255)),
        ))

    def add_well_at(self, wx, wy):
        if not self._inside(wx, wy):
            return
        self.wells.append(GravityWell(x=wx, y=wy, mass=1000))

    def start_wall(self, wx, wy):
        self.wall_drawing = True
        self.wall_start = (wx, wy)

    def end_wall(self, wx, wy):
        if not self.wall_drawing:
            return
        self.wall_drawing = False
        sx, sy = self.wall_start
        ddx, ddy = wx - sx, wy - sy
        if (ddx * ddx + ddy * ddy) ** 0.5 > 0.1:
            self.walls.append(Wall(sx, sy, wx, wy))

    def delete_last(self, kind):
        if kind == "well" and self.wells:
            self.wells.pop()
        elif kind == "wall" and len(self.walls) > NUM_BOUNDARY_WALLS:
            self.walls.pop()
        elif kind == "ball" and self.balls:
            if self.selected_id == self.balls[-1].id:
                self.selected_id = None
                self.position_history = []
            self.balls.pop()
        elif kind == "rect" and self.rectangles:
            if self.selected_id == self.rectangles[-1].id:
                self.selected_id = None
                self.position_history = []
            self.rectangles.pop()
        elif kind == "spring" and self.springs:
            self.springs.pop()

    def select_object(self, obj_id):
        obj = self.find_object(obj_id) if obj_id is not None else None
        new_id = obj.id if obj else None
        if new_id != self.selected_id:
            self.position_history = []
        self.selected_id = new_id

        if self.mode == "SPRING" and obj is not None:
            self._wire_spring(obj)

    def _wire_spring(self, clicked):
        if self.spring_selected_id is None:
            self.spring_selected_id = clicked.id
        elif self.spring_selected_id == clicked.id:
            self.spring_selected_id = None
        else:
            a = self.find_object(self.spring_selected_id)
            existing = None
            for sp in self.springs:
                if (sp.a is a and sp.b is clicked) or (sp.b is a and sp.a is clicked):
                    existing = sp
                    break
            if existing:
                self.springs.remove(existing)
            else:
                self.springs.append(Spring(a, clicked))
            self.spring_selected_id = None

    def update_field(self, obj_id, field, value):
        if field not in _EDITABLE:
            return
        obj = self.find_object(obj_id)
        if obj is None:
            return
        try:
            val = float(value)
        except (TypeError, ValueError):
            return
        if field in ("mass", "radius", "length", "width") and val <= 0:
            return
        if hasattr(obj, field):
            setattr(obj, field, val)

    def _inside(self, wx, wy):
        return self.left_wall <= wx <= self.right_wall and self.ground <= wy <= self.ceiling

    # ---------- serialization ----------

    def to_state_dict(self):
        return {
            "g": self.g, "e": self.e, "mode": self.mode, "paused": self.paused,
            "sim_time": self.sim_time,
            "world": {
                "left": self.left_wall, "right": self.right_wall,
                "ground": self.ground, "ceiling": self.ceiling,
            },
            "balls": [b.to_dict() for b in self.balls],
            "rects": [r.to_dict() for r in self.rectangles],
            "walls": [w.to_dict() for w in self.walls[NUM_BOUNDARY_WALLS:]],
            "wells": [w.to_dict() for w in self.wells],
            "springs": [s.to_dict() for s in self.springs],
            "selected_id": self.selected_id,
            "spring_selected_id": self.spring_selected_id,
            "wall_drawing": self.wall_drawing,
            "wall_start": self.wall_start if self.wall_drawing else None,
            "position_history": [
                {"t": t, "x": x, "y": y, "vx": vx, "vy": vy}
                for (t, x, y, vx, vy) in self.position_history
            ] if self.selected_id is not None else [],
        }
