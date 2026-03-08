# ai/interceptor_ai.py
# ============================================================
# Interceptor AI — uses RL agent for smart guidance
# ============================================================

import math
import numpy as np
import config
from simulation.interceptor import Interceptor
from ai.rl_interceptor import RLAgent, InterceptEnv

class RLInterceptor(Interceptor):
    """
    Interceptor guided by RL agent instead of
    direct proportional navigation.
    """
    def __init__(self, target, agent):
        # set agent BEFORE calling super().__init__
        # because super().__init__ calls _update_velocity()
        self.agent   = agent
        self.env     = InterceptEnv()

        # now safe to call parent init
        super().__init__(target)

        self.obs     = self.env.reset(
            missile         = target,
            interceptor_pos = (self.x, self.y)
        )

    def _get_obs(self):
        scale  = config.RADAR_RADIUS
        cx, cy = config.RADAR_CENTER
        dist   = math.hypot(self.x  - self.target.x,
                            self.y  - self.target.y)
        return [
            (self.target.x - self.x)  / scale,
            (self.target.y - self.y)  / scale,
            self.target.vx / config.MISSILE_SPEED_MAX,
            self.target.vy / config.MISSILE_SPEED_MAX,
            (self.x - cx)  / scale,
            (self.y - cy)  / scale,
            dist           / scale,
            math.atan2(self.target.y - self.y,
                       self.target.x - self.x) / math.pi,
        ]

    def _update_velocity(self):
        """RL agent decides direction."""
        if not hasattr(self, 'agent') or self.agent is None:
            # fallback to direct navigation if agent not ready
            if not self.target or not self.target.alive:
                return
            dx   = self.target.x - self.x
            dy   = self.target.y - self.y
            dist = math.hypot(dx, dy)
            if dist < 0.1:
                return
            self.vx = config.INTERCEPTOR_SPEED * dx / dist
            self.vy = config.INTERCEPTOR_SPEED * dy / dist
            return

        if not self.target or not self.target.alive:
            return

        obs        = self._get_obs()
        action     = self.agent.get_action(obs)
        ax, ay     = float(action[0]), float(action[1])
        mag        = math.hypot(ax, ay)
        if mag > 0:
            ax /= mag
            ay /= mag
        self.vx    = config.INTERCEPTOR_SPEED * ax
        self.vy    = config.INTERCEPTOR_SPEED * ay


class InterceptorAI:
    def __init__(self):
        self.interceptors    = []
        self.launch_cooldown = 0
        self.cooldown_frames = 10
        self.targets_engaged = set()
        self.intercept_count = 0
        self.miss_count      = 0

        # initialize RL agent (pre-trains at startup)
        self.agent           = RLAgent()

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
            "active":   len(self.interceptors),
            "hits":     self.intercept_count,
            "misses":   self.miss_count,
            "rl_eps":   rl_stats["episodes"],
            "rl_rate":  rl_stats["rate"],
        }