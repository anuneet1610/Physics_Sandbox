import math

class Gravity_Well:
    def __init__(self, x, y, mass):
        self.x = x
        self.y = y
        self.mass = mass

    def ball_vs_well(self, ball):
        r = max(0.5, math.sqrt((ball.x - self.x) ** 2 + (ball.y - self.y) ** 2))
        well_force = G * ball.mass * self.mass / (r ** 2)
        ball.apply_force(well_force * (self.x-ball.x)/r ,well_force * (self.y-ball.y)/r)

    def rect_vs_well(self, rect):
        r = max(0.5, math.sqrt((rect.x - self.x) ** 2 + (rect.y - self.y) ** 2))
        well_force = G * rect.mass * self.mass / (r ** 2)
        ball.apply_force(well_force * (self.x-rect.x)/r ,well_force * (self.y-rect.y)/r)