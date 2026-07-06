import math


class Spring:
    def __init__(self, obj_a, obj_b, rest_length=None, k=5, c=0.1):
        self.a = obj_a
        self.b = obj_b
        if rest_length is None:
            dx = obj_b.x - obj_a.x
            dy = obj_b.y - obj_a.y
            self.L0 = math.sqrt(dx ** 2 + dy ** 2)
        else:
            self.L0 = rest_length
        self.k = k
        self.c = c

    def apply_forces(self):
        dx = self.b.x - self.a.x
        dy = self.b.y - self.a.y
        d = math.sqrt(dx * dx + dy * dy)
        if d < 1e-8:
            return
        nx = dx / d
        ny = dy / d
        v_rel = (self.b.vx - self.a.vx) * nx + (self.b.vy - self.a.vy) * ny
        F = self.k * (d - self.L0) + self.c * v_rel
        self.a.apply_force(+F * nx, +F * ny)
        self.b.apply_force(-F * nx, -F * ny)

    def to_dict(self):
        return {"a": self.a.id, "b": self.b.id, "L0": self.L0}
