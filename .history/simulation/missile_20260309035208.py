# simulation/missile.py
# ============================================================
# Missile — three types with RCS-based radar detection
# ============================================================

import math
import random
import config
from perception.kalman_tracker import KalmanTracker
from perception.lstm_predictor import LSTMPredictor
from perception.radar_model import should_detect, get_detection_strength

TYPE_BALLISTIC = "BALLISTIC"
TYPE_EVASIVE   = "EVASIVE"
TYPE_STEALTH   = "STEALTH"

TYPE_COLORS = {
    TYPE_BALLISTIC : config.THREAT_RED,
    TYPE_EVASIVE   : (255, 100, 255),
    TYPE_STEALTH   : (100, 200, 100),
}

TYPE_WEIGHTS = [0.5, 0.3, 0.2]


class Missile:
    def __init__(self):
        self.type  = random.choices(
            [TYPE_BALLISTIC, TYPE_EVASIVE, TYPE_STEALTH],
            weights=TYPE_WEIGHTS
        )[0]

        angle      = random.uniform(0, 2 * math.pi)
        cx, cy     = config.RADAR_CENTER
        self.x     = cx + config.RADAR_RADIUS * math.cos(angle)
        self.y     = cy + config.RADAR_RADIUS * math.sin(angle)

        if self.type == TYPE_BALLISTIC:
            self.speed = random.uniform(0.6, 1.0)
        elif self.type == TYPE_EVASIVE:
            self.speed = random.uniform(0.8, 1.3)
        else:
            self.speed = random.uniform(0.3, 0.6)

        tx     = cx + random.uniform(-30, 30)
        ty     = cy + random.uniform(-30, 30)
        dx     = tx - self.x
        dy     = ty - self.y
        dist   = math.hypot(dx, dy)
        self.vx = self.speed * dx / dist
        self.vy = self.speed * dy / dist

        self.base_vx = self.vx
        self.base_vy = self.vy

        self.alive               = True
        self.id                  = random.randint(1000, 9999)
        self.trail               = []
        self.predicted_path      = []
        self.lstm_predicted_path = []
        self.evasion_timer       = 0
        self.stealth_blink       = 0

        self.detected          = False
        self.detection_prob    = 0.0
        
        self.detection_history = []

        self.tracker        = KalmanTracker(self.x, self.y)
        self.lstm_predictor = LSTMPredictor(
            seq_len=15, output_steps=30)

    def _evade(self):
        if self.evasion_timer > 0:
            self.evasion_timer -= 1
            blend   = 1.0 - (self.evasion_timer / 40)
            self.vx = self.vx * (1 - blend * 0.05) + \
                      self.base_vx * (blend * 0.05)
            self.vy = self.vy * (1 - blend * 0.05) + \
                      self.base_vy * (blend * 0.05)
            spd = math.hypot(self.vx, self.vy)
            if spd > 0:
                self.vx = self.vx / spd * self.speed
                self.vy = self.vy / spd * self.speed
            return
        if random.random() < 0.003:
            self._trigger_evasion()

    def _trigger_evasion(self):
        turn   = random.choice([-1, 1]) * random.uniform(
                     math.pi / 3, math.pi * 0.7)
        cos_t  = math.cos(turn)
        sin_t  = math.sin(turn)
        new_vx = self.vx * cos_t - self.vy * sin_t
        new_vy = self.vx * sin_t + self.vy * cos_t
        self.vx            = new_vx
        self.vy            = new_vy
        self.evasion_timer = 40

    def notify_interceptor_close(self, dist):
        if self.type == TYPE_EVASIVE and self.evasion_timer == 0:
            if dist < 80:
                self._trigger_evasion()

    def _update_detection(self):
        cx, cy   = config.RADAR_CENTER
        distance = math.hypot(self.x - cx, self.y - cy)
        prob     = get_detection_strength(distance, self.type)
        self.detection_history.append(prob)
        if len(self.detection_history) > 10:
            self.detection_history.pop(0)
        self.detection_prob = sum(self.detection_history) / \
                              len(self.detection_history)
        self.detected = should_detect(distance, self.type)

    def update(self):
        if not self.alive:
            return

        self.trail.append((self.x, self.y))
        if len(self.trail) > 20:
            self.trail.pop(0)

        if self.type == TYPE_EVASIVE:
            self._evade()
        elif self.type == TYPE_STEALTH:
            self.stealth_blink = (self.stealth_blink + 1) % 90

        self.x += self.vx
        self.y += self.vy

        self._update_detection()

        noise_x = self.x + random.gauss(0, 3.0)
        noise_y = self.y + random.gauss(0, 3.0)

        self.tracker.predict()
        self.tracker.update(noise_x, noise_y)
        self.predicted_path = self.tracker.predict_future(steps=60)

        self.lstm_predictor.update(self.x, self.y)
        self.lstm_predicted_path = \
            self.lstm_predictor.get_predicted_path()

        cx, cy = config.RADAR_CENTER
        if math.hypot(self.x - cx,
                      self.y - cy) <= config.PROTECTED_RADIUS:
            self.alive = False

    def is_visible_on_radar(self):
        if self.type == TYPE_STEALTH:
            return self.detected
        elif self.type == TYPE_EVASIVE:
            return self.detection_prob > 0.20
        else:
            return self.detection_prob > 0.05

    def distance_to_center(self):
        cx, cy = config.RADAR_CENTER
        return math.hypot(self.x - cx, self.y - cy)

    def is_inside_radar(self):
        cx, cy = config.RADAR_CENTER
        return math.hypot(self.x - cx,
                          self.y - cy) <= config.RADAR_RADIUS

    def get_type_color(self):
        return TYPE_COLORS.get(self.type, config.THREAT_RED)