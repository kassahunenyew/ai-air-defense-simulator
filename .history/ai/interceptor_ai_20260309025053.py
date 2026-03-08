# ai/interceptor_ai.py
# ============================================================
# Interceptor AI — Hungarian Algorithm assignment
#               + RL/PN blended guidance
# ============================================================

import math
import numpy as np
import config
from simulation.interceptor import Interceptor
from ai.rl_interceptor import RLAgent, InterceptEnv
from ai.assignment import assign_targets


class RLInterceptor(Interceptor):
    def __init__(self, target, agent):
        self.agent = agent
        self.env   = InterceptEnv()
        super().__init__(target)
        self.obs   = self.env.reset(
            missile         = target,
            interceptor_pos = (self.x, self.y)
        )

    def _get_obs(self):
        scale  = config.RADAR_RADIUS
        cx, cy = config.RADAR_CENTER
        dist   = math.hypot(self.x - self.target.x,
                            self.y - self.target.y)
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
        """70% proportional navigation + 30% RL."""
        if not self.target or not self.target.alive:
            return

        dx   = self.target.x - self.x
        dy   = self.target.y - self.y
        dist = math.hypot(dx, dy)
        if dist < 0.1:
            return

        # proportional navigation with lead
        lead   = min(dist / max(config.INTERCEPTOR_SPEED,
                                0.1), 30)
        lead_x = self.target.x + self.target.vx * lead
        lead_y = self.target.y + self.target.vy * lead
        ldx    = lead_x - self.x
        ldy    = lead_y - self.y
        lmag   = math.hypot(ldx, ldy)
        if lmag > 0:
            pn_ax = ldx / lmag
            pn_ay = ldy / lmag
        else:
            pn_ax = dx / dist
            pn_ay = dy / dist

        # RL suggestion
        if hasattr(self, 'agent') and self.agent is not None:
            obs    = self._get_obs()
            action = self.agent.get_action(obs)
            rl_ax  = float(action[0])
            rl_ay  = float(action[1])
            rl_mag = math.hypot(rl_ax, rl_ay)
            if rl_mag > 0:
                rl_ax /= rl_mag
                rl_ay /= rl_mag
            ax = 0.7 * pn_ax + 0.3 * rl_ax
            ay = 0.7 * pn_ay + 0.3 * rl_ay
        else:
            ax = pn_ax
            ay = pn_ay

        mag = math.hypot(ax, ay)
        if mag > 0:
            ax /= mag
            ay /= mag

        self.vx = config.INTERCEPTOR_SPEED * ax
        self.vy = config.INTERCEPTOR_SPEED * ay


class InterceptorAI:
    def __init__(self):
        self.interceptors    = []
        self.launch_cooldown = 0
        self.cooldown_frames = 10
        self.targets_engaged = set()
        self.intercept_count = 0
        self.miss_count      = 0
        self.agent           = RLAgent()

        # assignment stats
        self.last_assignments = []   # for HUD display

    def update(self, ranked_threats):
        self.launch_cooldown = max(0, self.launch_cooldown - 1)

        # update all interceptors
        for inc in self.interceptors:
            inc.update()

        # let main.py see hits BEFORE we remove them
        # count hits but don't clear inc.hit here
        for inc in self.interceptors:
            if inc.hit and not getattr(inc, '_counted', False):
                self.intercept_count += 1
                inc._counted = True

        # remove dead but keep hit ones for one frame
        # so main.py can spawn explosions
        self.interceptors = [i for i in self.interceptors
                             if i.alive or i.hit]

        self.targets_engaged = {i.target.id
                                 for i in self.interceptors
                                 if i.target
                                 and i.target.alive}

        slots = config.MAX_INTERCEPTORS - len(self.interceptors)
        if slots > 0 and self.launch_cooldown == 0:
            self._hungarian_launch(ranked_threats, slots)
            
    def _hungarian_launch(self, ranked_threats, slots):
        """
        Use Hungarian Algorithm to optimally assign
        new interceptors to unengaged threats.
        """
        # create virtual 'free launcher' positions
        # each slot launches from radar center
        cx, cy = config.RADAR_CENTER

        class FreeLauncher:
            def __init__(self):
                self.x = float(cx)
                self.y = float(cy)

        free = [FreeLauncher() for _ in range(slots)]

        assignments = assign_targets(
            free, ranked_threats, self.targets_engaged)

        for _, missile in assignments:
            if len(self.interceptors) >= config.MAX_INTERCEPTORS:
                break
            self._launch(missile)

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