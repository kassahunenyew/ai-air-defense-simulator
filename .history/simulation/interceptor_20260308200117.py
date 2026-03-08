# simulation/interceptor.py
# ============================================================
# Interceptor — launches from center, chases target missile
# ============================================================

import math
import config

class Interceptor:
    def __init__(self, target):
        # -- launch from center --
        cx, cy     = config.RADAR_CENTER
        self.x     = float(cx)
        self.y     = float(cy)

        # -- assign target --
        self.target   = target
        self.alive    = True
        self.hit      = False
        self.trail    = []
        self.id       = target.id

        # -- initialize vx/vy BEFORE calling _update_velocity --
        self.vx = 0.0
        self.vy = 0.0

        # -- initial velocity toward target --
        self._update_velocity()

    def _update_velocity(self):
        """Recalculate velocity to steer toward target."""
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
        """Move interceptor, steer toward target, check hit."""
        if not self.alive:
            return

        # -- save trail --
        self.trail.append((self.x, self.y))
        if len(self.trail) > 25:
            self.trail.pop(0)

        # -- if target is dead, interceptor also dies --
        if not self.target or not self.target.alive:
            self.alive = False
            return

        # -- steer toward target every frame --
        self._update_velocity()

        # -- move --
        self.x += self.vx
        self.y += self.vy

        # -- check intercept --
        dist = math.hypot(self.x - self.target.x,
                          self.y - self.target.y)
        if dist < 10:
            self.hit          = True
            self.alive        = False
            self.target.alive = False

        # -- remove if out of radar bounds --
        cx, cy = config.RADAR_CENTER
        if math.hypot(self.x - cx, self.y - cy) > config.RADAR_RADIUS * 1.2:
            self.alive = False