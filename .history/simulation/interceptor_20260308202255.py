# simulation/interceptor.py
# ============================================================
# Interceptor — launches from center, chases target missile
# ============================================================

import math
import config

class Interceptor:
    def __init__(self, target):
        cx, cy       = config.RADAR_CENTER
        self.x       = float(cx)
        self.y       = float(cy)
        self.target  = target
        self.alive   = True
        self.hit     = False
        self.trail   = []
        self.id      = target.id
        self.vx      = 0.0
        self.vy      = 0.0
        self._update_velocity()

    def _update_velocity(self):
        if not self.target or not self.target.alive:
            return
        dx   = self.target.x - self.x
        dy   = self.target.y - self.y
        dist = math.hypot(dx, dy)
        if dist < 0.1:
            return
        self.vx = config.INTERCEPTOR_SPEED * dx / dist
        self.vy = config.INTERCEPTOR_SPEED * dy / dist

    def update(self):
        if not self.alive:
            return

        self.trail.append((self.x, self.y))
        if len(self.trail) > 25:
            self.trail.pop(0)

        if not self.target or not self.target.alive:
            self.alive = False
            return

        self._update_velocity()
        self.x += self.vx
        self.y += self.vy

        # increased hit radius to 15 for better explosion visibility
        dist = math.hypot(self.x - self.target.x,
                          self.y - self.target.y)
        if dist < 15:
            self.hit          = True
            self.alive        = False
            self.target.alive = False

        cx, cy = config.RADAR_CENTER
        if math.hypot(self.x - cx, self.y - cy) > config.RADAR_RADIUS * 1.2:
            self.alive = False