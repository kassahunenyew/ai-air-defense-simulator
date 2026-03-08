# ai/interceptor_ai.py
# ============================================================
# Interceptor AI — blended RL + proportional navigation
# RL steers, but proportional nav keeps it on target
# ============================================================

import math
import numpy as np
import config
from simulation.interceptor import Interceptor
from ai.rl_interceptor import RLAgent, InterceptEnv


class RLInterceptor(Interceptor):
    """
    Interceptor guided by a blend of RL agent + proportional nav.
    RL contributes steering intelligence; prop-nav ensures
    it always closes toward the target.
    """
    def __init__(self, target, agent):
        # MUST set agent before super().__init__
        # because parent calls _update_velocity() immediately
        self.agent      = agent
        self.env        = InterceptEnv()
        self.rl_weight  = 0.35   # how much RL influences direction
                                  # rest is pure proportional nav
        super().__init__(target)

        self.obs = self.env.reset(
            missile         = target,
            interceptor_pos = (self.x, self.y)
        )

    def _get_obs(self):
        scale  = config.RADAR_RADIUS
        cx, cy = config.RADAR_CENTER
        dist   = math.hypot(self.x - self.target.x,
                            self.y - self.target.y)
        return [
            (self.target.x - self.x) / scale,
            (self.target.y - self.y) / scale,
            self.target.vx / max(config.MISSILE_SPEED_MAX, 0.001),
            self.target.vy / max(config.MISSILE_SPEED_MAX, 0.001),
            (self.x - cx)  / scale,
            (self.y - cy)  / scale,
            dist           / scale,
            math.atan2(self.target.y - self.y,
                       self.target.x - self.x) / math.pi,
        ]

    def _update_velocity(self):
        if not self.target or not self.target.alive:
            return

        # ── Proportional navigation (always works) ──────────
        # lead the target: aim at predicted position
        dx   = self.target.x - self.x
        dy   = self.target.y - self.y
        dist = math.hypot(dx, dy)
        if dist < 0.1:
            return

        # predict where target will be in N frames
        lead = max(1, int(dist / config.INTERCEPTOR_SPEED))
        lead = min(lead, 20)
        pred_x = self.target.x + self.target.vx * lead
        pred_y = self.target.y + self.target.vy * lead
        pdx    = pred_x - self.x
        pdy    = pred_y - self.y
        pmag   = math.hypot(pdx, pdy)
        if pmag < 0.1:
            pmag = 0.1
        nav_ax = pdx / pmag
        nav_ay = pdy / pmag

        # ── RL agent guidance ────────────────────────────────
        rl_ax, rl_ay = nav_ax, nav_ay   # default fallback
        if hasattr(self, 'agent') and self.agent is not None:
            try:
                obs    = self._get_obs()
                action = self.agent.get_action(obs)
                ax, ay = float(action[0]), float(action[1])
                mag    = math.hypot(ax, ay)
                if mag > 0.01:
                    rl_ax = ax / mag
                    rl_ay = ay / mag
            except Exception:
                pass

        # ── Blend: mostly prop-nav, some RL ─────────────────
        w       = self.rl_weight
        bx      = (1 - w) * nav_ax + w * rl_ax
        by      = (1 - w) * nav_ay + w * rl_ay
        bmag    = math.hypot(bx, by)
        if bmag < 0.01:
            bmag = 0.01
        self.vx = config.INTERCEPTOR_SPEED * bx / bmag
        self.vy = config.INTERCEPTOR_SPEED * by / bmag


class InterceptorAI:
    def __init__(self):
        self.interceptors    = []
        self.launch_cooldown = 0
        self.cooldown_frames = 10
        self.targets_engaged = set()
        self.intercept_count = 0
        self.miss_count      = 0

        # initialize RL agent (pre-trains at startup)
        self.agent = RLAgent()

    def update(self, ranked_threats):
        self.launch_cooldown = max(0, self.launch_cooldown - 1)

        for inc in self.interceptors:
            inc.update()

        for inc in self.interceptors:
            if inc.hit:
                self.intercept_count += 1

        dead = [i for i in self.interceptors
                if not i.alive and not i.hit]
        self.miss_count     += len(dead)
        self.interceptors    = [i for i in self.interceptors
                                 if i.alive]
        self.targets_engaged = {i.id for i in self.interceptors}

        if (self.launch_cooldown == 0 and
                len(self.interceptors) < config.MAX_INTERCEPTORS):
            for missile, score, tti in ranked_threats:
                if missile.id not in self.targets_engaged:
                    self._launch(missile)
                    break

    def _launch(self, target):
        inc = RLInterceptor(target, self.agent)
        self.interceptors.append(inc)
        self.targets_engaged.add(target.id)
        self.launch_cooldown = self.cooldown_frames

    def get_stats(self):
        rl_stats = self.agent.get_stats()
        return {
            "active":  len(self.interceptors),
            "hits":    self.intercept_count,
            "misses":  self.miss_count,
            "rl_eps":  rl_stats["episodes"],
            "rl_rate": rl_stats["rate"],
        }