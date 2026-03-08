# simulation/interceptor.py
# ============================================================
# Interceptor — chases target across full radar area
# ============================================================

import math
import random
import config

class Interceptor:
    def __init__(self, target):
        self.target  = target
        self.x       = float(config.RADAR_CENTER[0])
        self.y       = float(config.RADAR_CENTER[1])
        self.speed   = config.INTERCEPTOR_SPEED
        self.alive   = True
        self.hit     = False
        self.trail   = []
        self.id      = random.randint(1000, 9999)
        self.vx      = 0.0
        self.vy      = 0.0
        self._update_velocity()

    def _update_velocity(self):
        """Direct proportional navigation toward target."""
        if not self.target or not self.target.alive:
            return
        dx   = self.target.x - self.x
        dy   = self.target.y - self.y
        dist = math.hypot(dx, dy)
        if dist < 0.1:
            return
        self.vx = self.speed * dx / dist
        self.vy = self.speed * dy / dist

    def update(self):
        if not self.alive:
            return

        # kill if target is gone
        if not self.target or not self.target.alive:
            self.alive = False
            return

        self._update_velocity()

        self.trail.append((self.x, self.y))
        if len(self.trail) > 25:
            self.trail.pop(0)

        self.x += self.vx
        self.y += self.vy

        # check hit
        dist = math.hypot(self.x - self.target.x,
                          self.y - self.target.y)
        if dist < 15:
            self.hit           = True
            self.target.alive  = False
            self.alive         = False
            return

        # die only if WAY outside radar (give room to chase)
        cx, cy = config.RADAR_CENTER
        if math.hypot(self.x - cx,
                      self.y - cy) > config.RADAR_RADIUS * 1.5:
            self.alive = False