# ai/threat_scorer.py
# ============================================================
# Threat Scoring AI — ranks missiles by danger level
# ============================================================

import math
import config

# -- Scoring weights (must sum to 1.0) --
W_DISTANCE = 0.50    # how close to center (most important)
W_SPEED    = 0.30    # how fast it's moving
W_TIME     = 0.20    # time to impact

def time_to_impact(missile):
    """Estimate seconds until missile reaches protected zone."""
    dist  = missile.distance_to_center() - config.PROTECTED_RADIUS
    dist  = max(dist, 0.1)   # avoid division by zero
    speed = math.hypot(missile.vx, missile.vy)
    speed = max(speed, 0.01)
    return dist / speed      # frames to impact

def score_missile(missile, all_missiles):
    """
    Calculate threat score for a single missile.
    Returns float between 0.0 (no threat) and 1.0 (critical).
    """
    if not missile.alive:
        return 0.0

    # -- Distance score (closer = more dangerous) --
    dist          = missile.distance_to_center()
    max_dist      = config.RADAR_RADIUS
    dist_score    = 1.0 - (dist / max_dist)   # 1.0 = at center

    # -- Speed score (faster = more dangerous) --
    speed         = math.hypot(missile.vx, missile.vy)
    max_speed     = config.MISSILE_SPEED_MAX
    speed_score   = min(speed / max_speed, 1.0)

    # -- Time to impact score (less time = more dangerous) --
    tti           = time_to_impact(missile)
    max_tti       = 600.0    # 600 frames = ~10 seconds at 60fps
    time_score    = 1.0 - min(tti / max_tti, 1.0)

    # -- Combined weighted score --
    total = (W_DISTANCE * dist_score +
             W_SPEED    * speed_score +
             W_TIME     * time_score)

    return round(total, 3)

def rank_threats(missile_list):
    """
    Score all missiles and return them sorted by threat level.
    Returns list of (missile, score, tti) tuples — highest first.
    """
    ranked = []
    for m in missile_list:
        if not m.alive:
            continue
        score = score_missile(m, missile_list)
        tti   = time_to_impact(m)
        ranked.append((m, score, tti))

    # sort by score descending (most dangerous first)
    ranked.sort(key=lambda x: x[1], reverse=True)
    return ranked