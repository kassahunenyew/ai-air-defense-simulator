# perception/radar_model.py
# ============================================================
# Radar Detection Probability Model
# Based on simplified radar range equation
# ============================================================

import math
import random
import config


# RCS lookup by missile type
RCS_TABLE = {
    "BALLISTIC" : config.RCS_BALLISTIC,
    "EVASIVE"   : config.RCS_EVASIVE,
    "STEALTH"   : config.RCS_STEALTH,
}


def get_snr(distance, rcs):
    """
    Compute signal-to-noise ratio using simplified
    radar range equation.
    SNR = (Pt * G^2 * lambda^2 * RCS) / (R^4 * noise)
    """
    if distance < 1.0:
        distance = 1.0

    numerator   = (config.RADAR_POWER *
                   config.RADAR_GAIN ** 2 *
                   config.RADAR_WAVELENGTH ** 2 *
                   rcs)
    denominator = (distance ** 4 * config.RADAR_NOISE)

    return numerator / denominator


def detection_probability(distance, rcs):
    """
    P(detect) = 1 - exp(-SNR)
    Returns value 0.0 to 1.0.
    """
    snr = get_snr(distance, rcs)
    # clamp SNR to avoid overflow
    snr = min(snr, 50.0)
    return 1.0 - math.exp(-snr)


def should_detect(distance, missile_type):
    """
    Roll detection dice for this frame.
    Returns True if missile is detected this sweep.
    """
    rcs  = RCS_TABLE.get(missile_type, config.RCS_BALLISTIC)
    prob = detection_probability(distance, rcs)
    return random.random() < prob


def get_detection_color(prob):
    """
    Returns color tint based on detection confidence.
    High confidence = bright, low = dim.
    """
    if prob > 0.85:
        return None          # full color, no tint needed
    elif prob > 0.5:
        # amber warning — partial detection
        return (255, 180, 0)
    else:
        # very dim — barely visible
        return (80, 80, 80)


def get_detection_strength(distance, missile_type):
    """
    Returns detection probability for HUD display.
    """
    rcs = RCS_TABLE.get(missile_type, config.RCS_BALLISTIC)
    return detection_probability(distance, rcs)