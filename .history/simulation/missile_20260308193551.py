# simulation/missile.py
# ============================================================
# Missile — spawns at radar edge, flies toward center
# Now includes Kalman Filter tracker
# ============================================================

import math
import random
import config
from perception.kalman_tracker import KalmanTracker

class Missile:
    def __init__(self):
        # -- spawn at a random point on the radar edge --
        angle        = random.uniform(0, 2 * math.pi)
        cx, cy       = config.RADAR_CENTER
        self.x       = cx + config.RADAR_RADIUS * math.cos(angle)
        self.y       = cy + config.RADAR_RADIUS * math.sin(angle)

        # -- random speed --
        self.speed   = random.uniform(config.MISSILE_SPEED_MIN,
                                      config.MISSILE_SPEED_MAX)

        # -- always flies toward center (with tiny random offset) --
        target_x     = cx + random.uniform(-30, 30)
        target_y     = cy + random.uniform(-30, 30)
        dx           = target_x - self.x
        dy           = target_y - self.y
        dist         = math.hypot(dx, dy)
        self.vx      = self.speed * dx / dist
        self.vy      = self.speed * dy / dist

        # -- state --
        self.alive   = True
        self.id      = random.randint(1000, 9999)

        # -- trail history --
        self.trail   = []

        # -- Kalman Filter tracker --
        self.tracker = KalmanTracker(self.x, self.y)

        # -- predicted future path --
        self.predicted_path = []

    def update(self):
        """Move missile, add noise, run Kalman Filter."""
        if not self.alive:
            return

        # save trail
        self.trail.append((self.x, self.y))
        if len(self.trail) > 20:
            self.trail.pop(0)

        # move
        self.x += self.vx
        self.y += self.vy

        # simulate noisy radar measurement
        noise_x = self.x + random.gauss(0, 3.0)
        noise_y = self.y + random.gauss(0, 3.0)

        # Kalman Filter — predict then update
        self.tracker.predict()
        self.tracker.update(noise_x, noise_y)

        # get predicted future path (next 60 steps)
        self.predicted_path = self.tracker.predict_future(steps=60)

        # check if reached protected zone
        cx, cy = config.RADAR_CENTER
        dist   = math.hypot(self.x - cx, self.y - cy)
        if dist <= config.PROTECTED_RADIUS:
            self.alive = False

    def distance_to_center(self):
        cx, cy = config.RADAR_CENTER
        return math.hypot(self.x - cx, self.y - cy)

    def is_inside_radar(self):
        cx, cy = config.RADAR_CENTER
        return math.hypot(self.x - cx, self.y - cy) <= config.RADAR_RADIUS