# ai/interceptor_ai.py
# ============================================================
# Interceptor AI — decides when and what to intercept
# ============================================================

import config
from simulation.interceptor import Interceptor

class InterceptorAI:
    def __init__(self):
        self.interceptors     = []
        self.launch_cooldown  = 0
        self.cooldown_frames  = 10     # 1 second between launches
        self.targets_engaged  = set()  # missile IDs already targeted
        self.intercept_count  = 0
        self.miss_count       = 0

    def update(self, ranked_threats):
        """
        Check ranked threats and launch interceptors
        at the highest priority untargeted missile.
        """
        self.launch_cooldown = max(0, self.launch_cooldown - 1)

        # -- update existing interceptors --
        for inc in self.interceptors:
            inc.update()

        # -- track successful hits --
        for inc in self.interceptors:
            if inc.hit:
                self.intercept_count += 1

        # -- clean up dead interceptors --
        dead = [i for i in self.interceptors
                if not i.alive and not i.hit]
        self.miss_count += len(dead)

        self.interceptors = [i for i in self.interceptors if i.alive]

        # -- update engaged targets set --
        self.targets_engaged = {i.id for i in self.interceptors}

        # -- launch at highest priority untargeted threat --
        if (self.launch_cooldown == 0 and
                len(self.interceptors) < config.MAX_INTERCEPTORS):
            for missile, score, tti in ranked_threats:
                if missile.id not in self.targets_engaged:
                    self._launch(missile)
                    break

    def _launch(self, target):
        """Launch a new interceptor at target."""
        inc = Interceptor(target)
        self.interceptors.append(inc)
        self.targets_engaged.add(target.id)
        self.launch_cooldown = self.cooldown_frames

    def get_stats(self):
        return {
            "active":    len(self.interceptors),
            "hits":      self.intercept_count,
            "misses":    self.miss_count,
        }