# simulation/missile.py
# ============================================================
# Missile — three types: Ballistic, Evasive, Stealth
# ============================================================

import math
import random
import config
from perception.kalman_tracker import KalmanTracker

# ── Missile types ────────────────────────────────────────────
TYPE_BALLISTIC = "BALLISTIC"   # straight flight
TYPE_EVASIVE   = "EVASIVE"     # dodges when interceptor close
TYPE_STEALTH   = "STEALTH"     # slow, hard to see

TYPE_COLORS = {
    TYPE_BALLISTIC : config.THREAT_RED,
    TYPE_EVASIVE   : (255, 100, 255),   # magenta
    TYPE_STEALTH   : (100, 200, 100),   # dim green
}

TYPE_WEIGHTS = [0.5, 0.3, 0.2]   # 50% ballistic, 30% evasive, 20% stealth

class Missile:
    def __init__(self):
        # -- type --
        self.type  = random.choices(
            [TYPE_BALLISTIC, TYPE_EVASIVE, TYPE_STEALTH],
            weights=TYPE_WEIGHTS
        )[0]

        # -- spawn at radar edge --
        angle      = random.uniform(0, 2 * math.pi)
        cx, cy     = config.RADAR_CENTER
        self.x     = cx + config.RADAR_RADIUS * math.cos(angle)
        self.y     = cy + config.RADAR_RADIUS * math.sin(angle)

        # -- speed by type --
        if self.type == TYPE_BALLISTIC:
            self.speed = random.uniform(0.6, 1.0)
        elif self.type == TYPE_EVASIVE:
            self.speed = random.uniform(0.8, 1.3)
        else:  # STEALTH
            self.speed = random.uniform(0.3, 0.6)

        # -- velocity toward center --
        tx     = cx + random.uniform(-30, 30)
        ty     = cy + random.uniform(-30, 30)
        dx     = tx - self.x
        dy     = ty - self.y
        dist   = math.hypot(dx, dy)
        self.vx = self.speed * dx / dist
        self.vy = self.speed * dy / dist

        # -- base direction for evasive reset --
        self.base_vx = self.vx
        self.base_vy = self.vy

        # -- state --
        self.alive          = True
        self.id             = random.randint(1000, 9999)
        self.trail          = []
        self.predicted_path = []
        self.evasion_timer  = 0
        self.stealth_blink  = 0    # stealth flickers on radar

        # -- Kalman tracker --
        self.tracker = KalmanTracker(self.x, self.y)

    def _evade(self):
        """
        Evasive maneuver — sharp perpendicular turn
        then gradually return to original heading.
        """
        if self.evasion_timer > 0:
            self.evasion_timer -= 1
            # gradually blend back to base direction
            blend = 1.0 - (self.evasion_timer / 40)
            self.vx = self.vx * (1-blend*0.05) + self.base_vx * (blend*0.05)
            self.vy = self.vy * (1-blend*0.05) + self.base_vy * (blend*0.05)
            # renormalize speed
            spd     = math.hypot(self.vx, self.vy)
            if spd > 0:
                self.vx = self.vx / spd * self.speed
                self.vy = self.vy / spd * self.speed
            return

        # random chance to evade even without interceptor nearby
        if random.random() < 0.003:
            self._trigger_evasion()

    def _trigger_evasion(self):
        """Execute a sharp perpendicular dodge."""
        # rotate velocity 60-120 degrees
        turn   = random.choice([-1, 1]) * random.uniform(
                     math.pi/3, math.pi * 0.7)
        cos_t  = math.cos(turn)
        sin_t  = math.sin(turn)
        new_vx = self.vx * cos_t - self.vy * sin_t
        new_vy = self.vx * sin_t + self.vy * cos_t
        self.vx         = new_vx
        self.vy         = new_vy
        self.evasion_timer = 40

    def notify_interceptor_close(self, dist):
        """Called by interceptor AI when interceptor is nearby."""
        if self.type == TYPE_EVASIVE and self.evasion_timer == 0:
            if dist < 80:
                self._trigger_evasion()

    def update(self):
        if not self.alive:
            return

        # trail
        self.trail.append((self.x, self.y))
        if len(self.trail) > 20:
            self.trail.pop(0)

        # type-specific behavior
        if self.type == TYPE_EVASIVE:
            self._evade()
        elif self.type == TYPE_STEALTH:
            self.stealth_blink = (self.stealth_blink + 1) % 90

        # move
        self.x += self.vx
        self.y += self.vy

        # noisy radar measurement
        noise_x = self.x + random.gauss(0, 3.0)
        noise_y = self.y + random.gauss(0, 3.0)

        # Kalman update
        self.tracker.predict()
        self.tracker.update(noise_x, noise_y)
        self.predicted_path = self.tracker.predict_future(steps=60)

        # check protected zone
        cx, cy = config.RADAR_CENTER
        if math.hypot(self.x - cx, self.y - cy) <= config.PROTECTED_RADIUS:
            self.alive = False

    def is_visible_on_radar(self):
        """Stealth missiles flicker — only visible 40% of the time."""
        if self.type == TYPE_STEALTH:
            return self.stealth_blink < 36   # visible 40% of cycle
        return True

    def distance_to_center(self):
        cx, cy = config.RADAR_CENTER
        return math.hypot(self.x - cx, self.y - cy)

    def is_inside_radar(self):
        cx, cy = config.RADAR_CENTER
        return math.hypot(self.x - cx,
                          self.y - cy) <= config.RADAR_RADIUS

    def get_type_color(self):
        return TYPE_COLORS.get(self.type, config.THREAT_RED)