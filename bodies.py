import state
import math

class RigidBody:
    def __init__(self, x, y, vx, vy, mass, can_move=True):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.mass = mass
        self.fx = 0.0
        self.fy = 0.0
        self.can_move = can_move

    def clear_forces(self):
        if self.can_move:
            self.fx = 0.0
            self.fy = self.mass * (-state.g)

    def apply_force(self, fx, fy):
        if self.can_move:
            self.fx += fx
            self.fy += fy

    def integrate(self, dt):
        if self.can_move:
            self.vx += (self.fx / self.mass) * dt
            self.vy += (self.fy / self.mass) * dt
            self.x += self.vx * dt
            self.y += self.vy * dt

class Ball(RigidBody):
    def __init__(self, x, y, vx, vy, mass, radius, colour, can_move=True):
        super().__init__(x, y, vx, vy, mass, can_move)
        self.radius = radius
        self.colour = colour

    def check_collision(self, other):
        dx = other.x - self.x
        dy = other.y - self.y
        dist_sq = dx * dx + dy * dy
        min_dist = self.radius + other.radius

        if dist_sq >= min_dist * min_dist:
            return

        distance = math.sqrt(dist_sq)
        if distance < 1e-8:
            nx, ny = 1.0, 0.0
            distance = 1e-8
        else:
            nx = dx / distance
            ny = dy / distance

        rvx = self.vx - other.vx
        rvy = self.vy - other.vy
        vel_along_normal = rvx * nx + rvy * ny

        if vel_along_normal <= 0:
            return

        REST_THRESHOLD = 0.3
        restitution = 0.0 if vel_along_normal < REST_THRESHOLD else state.e

        inv_mass_self = 0.0 if not self.can_move else 1.0 / self.mass
        inv_mass_other = 0.0 if not other.can_move else 1.0 / other.mass
        j = (1.0 + restitution) * vel_along_normal / (inv_mass_self + inv_mass_other)

        if self.can_move:
            self.vx -= j * nx / self.mass
            self.vy -= j * ny / self.mass
        if other.can_move:
            other.vx += j * nx / other.mass
            other.vy += j * ny / other.mass

        overlap = min_dist - distance
        total_mass = self.mass + other.mass
        if self.can_move:
            self.x -= nx * overlap * (other.mass / total_mass)
            self.y -= ny * overlap * (other.mass / total_mass)
        if other.can_move:
            other.x += nx * overlap * (self.mass / total_mass)
            other.y += ny * overlap * (self.mass / total_mass)

class Rectangle(RigidBody):
    def __init__(self, x, y, vx, vy, mass, length, width, colour, can_move=True):
        super().__init__(x, y, vx, vy, mass, can_move)
        self.length = length
        self.width = width
        self.colour = colour

    def left(self):
        return self.x - self.length/2

    def right(self):
        return self.x + self.length/2

    def bottom(self):
        return self.y - self.width/2

    def top(self):
        return self.y + self.width/2

    def closest_point_rec(self, px, py):
        cx = max(self.x-self.length/2, min(self.x+self.length/2, px))
        cy = max(self.y-self.width/2, min(self.y+self.width/2, py))
        return cx, cy

    def check_collision(self, other):
        dx = other.x - self.x
        dy = other.y - self.y
        dist_sq = dx * dx + dy * dy
        if abs(dx) > (self.length + other.length)/2 or abs(dy) > (self.width + other.width)/2:
            return

        distance = math.sqrt(dist_sq)
        if distance < 1e-8:
            nx, ny = 1.0, 0.0
            distance = 1e-8
        else:
            nx = dx / distance
            ny = dy / distance

        rvx = self.vx - other.vx
        rvy = self.vy - other.vy
        vel_along_normal = rvx * nx + rvy * ny

        if vel_along_normal <= 0:
            return

        REST_THRESHOLD = 0.3
        restitution = 0.0 if vel_along_normal < REST_THRESHOLD else state.e

        inv_mass_self = 0.0 if not self.can_move else 1.0 / self.mass
        inv_mass_other = 0.0 if not other.can_move else 1.0 / other.mass
        j = (1.0 + restitution) * vel_along_normal / (inv_mass_self + inv_mass_other)

        if self.can_move:
            self.vx -= j * nx / self.mass
            self.vy -= j * ny / self.mass
        if other.can_move:
            other.vx += j * nx / other.mass
            other.vy += j * ny / other.mass

        overlap_x = (self.length + other.length) / 2 - abs(dx)
        overlap_y = (self.width + other.width) / 2 - abs(dy)
        if overlap_x < overlap_y:
            nx, ny = (1.0 if dx > 0 else -1.0), 0.0
            overlap = overlap_x
        else:
            nx, ny = 0.0, (1.0 if dy > 0 else -1.0)
            overlap = overlap_y

        total_mass = self.mass + other.mass

        if self.can_move:
            self.x -= nx * overlap * (other.mass / total_mass)
            self.y -= ny * overlap * (other.mass / total_mass)
        if other.can_move:
            other.x += nx * overlap * (self.mass / total_mass)
            other.y += ny * overlap * (self.mass / total_mass)

    def check_collision_ball(self, ball):
        """Resolve collision between this rectangle and a ball."""
        cx, cy = self.closest_point_rec(ball.x, ball.y)
        dx = ball.x - cx
        dy = ball.y - cy
        dist_sq = dx * dx + dy * dy

        if dist_sq >= ball.radius * ball.radius:
            return  # no contact

        dist = math.sqrt(dist_sq) if dist_sq > 1e-12 else 0.0

        # Normal pointing from rect surface toward ball centre
        if dist < 1e-8:
            # ball centre is inside rect — push out along shortest axis
            ox = self.length/2 - abs(ball.x - self.x)
            oy = self.width/2 - abs(ball.y - self.y)
            if ox < oy:
                nx = 1.0 if ball.x > self.x else -1.0
                ny = 0.0
            else:
                nx = 0.0
                ny = 1.0 if ball.y > self.y else -1.0
            dist = 0.0
        else:
            nx = dx / dist
            ny = dy / dist

        # Relative velocity along normal
        rvx = ball.vx - self.vx
        rvy = ball.vy - self.vy
        vel_along = rvx * nx + rvy * ny

        if vel_along > 0:
            return  # separating

        REST_THRESHOLD = 0.3
        restitution = 0.0 if abs(vel_along) < REST_THRESHOLD else state.e

        inv_ball = 0.0 if not ball.can_move else 1.0 / ball.mass
        inv_rect = 0.0 if not self.can_move else 1.0 / self.mass
        j = -(1.0 + restitution) * vel_along / (inv_ball + inv_rect)

        if ball.can_move:
            ball.vx += j * nx * inv_ball
            ball.vy += j * ny * inv_ball
        if self.can_move:
            self.vx -= j * nx * inv_rect
            self.vy -= j * ny * inv_rect

        # Positional correction
        overlap = ball.radius - dist
        total_inv = inv_ball + inv_rect
        if total_inv > 0:
            if ball.can_move:
                ball.x += nx * overlap * (inv_ball / total_inv)
                ball.y += ny * overlap * (inv_ball / total_inv)
            if self.can_move:
                self.x -= nx * overlap * (inv_rect / total_inv)
                self.y -= ny * overlap * (inv_rect / total_inv)