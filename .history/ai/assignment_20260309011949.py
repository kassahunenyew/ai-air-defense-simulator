# ai/assignment.py
# ============================================================
# Hungarian Algorithm — optimal interceptor-to-missile
# assignment. Minimizes total cost across all pairings.
# ============================================================

import numpy as np
import math
from scipy.optimize import linear_sum_assignment
import config


def build_cost_matrix(interceptors, threats):
    """
    Build an (N interceptors) x (M threats) cost matrix.

    Cost for each pair = weighted combination of:
      - distance from interceptor to missile
      - time to intercept (lower = cheaper)
      - threat score (higher threat = cheaper to assign)
      - missile speed (faster = more urgent)
    """
    n = len(interceptors)
    m = len(threats)

    # large value for impossible assignments
    INF = 1e6

    cost = np.full((n, m), INF)

    for i, inc in enumerate(interceptors):
        for j, (missile, score, tti) in enumerate(threats):
            if not missile.alive:
                continue

            # distance from interceptor to missile
            dist = math.hypot(inc.x - missile.x,
                              inc.y - missile.y)

            # predicted intercept distance
            # (where will missile be when interceptor arrives)
            travel_time = dist / max(config.INTERCEPTOR_SPEED,
                                     0.1)
            pred_x = missile.x + missile.vx * travel_time
            pred_y = missile.y + missile.vy * travel_time
            pred_dist = math.hypot(inc.x - pred_x,
                                   inc.y - pred_y)

            # normalize components to 0-1
            scale     = config.RADAR_RADIUS * 2
            d_norm    = pred_dist / scale
            tti_norm  = min(tti, 300) / 300.0
            score_inv = 1.0 - score   # low score = high cost

            # weighted cost
            # low cost = good assignment
            cost[i, j] = (0.40 * d_norm +
                          0.35 * tti_norm +
                          0.25 * score_inv)

    return cost


def assign_targets(free_interceptors, ranked_threats,
                   already_engaged):
    """
    Use Hungarian Algorithm to find optimal
    interceptor → missile assignments.

    Returns list of (interceptor, missile) pairs.
    """
    if not free_interceptors or not ranked_threats:
        return []

    # filter to unengaged missiles only
    available = [(m, s, t) for m, s, t in ranked_threats
                 if m.id not in already_engaged and m.alive]

    if not available:
        return []

    # pad matrix to square if needed
    n = len(free_interceptors)
    m = len(available)

    cost = build_cost_matrix(free_interceptors, available)

    # scipy linear_sum_assignment = Hungarian Algorithm
    row_ind, col_ind = linear_sum_assignment(cost)

    assignments = []
    for r, c in zip(row_ind, col_ind):
        if cost[r, c] < 1e5:   # valid assignment only
            interceptor = free_interceptors[r]
            missile, _, _ = available[c]
            assignments.append((interceptor, missile))

    return assignments