class Wall:
    def __init__(self, x1, y1, x2, y2):
        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2, y2
        dx = x2 - x1
        dy = y2 - y1
        self.length = (dx * dx + dy * dy) ** 0.5
        self.tx = dx / self.length
        self.ty = dy / self.length
        self.nx = -self.ty
        self.ny = self.tx