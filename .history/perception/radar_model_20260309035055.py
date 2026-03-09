# perception/radar_model.py
# ============================================================
# RCS-based radar detection model
# Now supports Electronic Warfare / Jamming
# ============================================================

import math
import config


def get_snr(rcs, distance):
    """Radar range equation SNR."""
    if distance < 1.0:
        distance = 1.0
    snr = (config.RADAR_POWER
           * config.RADAR_GAIN ** 2
           * config.RADAR_WAVELENGTH ** 2
           * rcs) \
          / (((4 * math.pi) ** 3)
             * distance ** 4
             * config.RADAR_NOISE)
    return snr


def get_effective_snr(rcs, distance, jamming_factor=0.0):
    """
    SNR reduced by electronic jamming.
    jamming_factor: 0.0 = no jamming, 1.0 = full jamming
    SNR_effective = SNR_base * (1 - jam_intensity)
    """
    base_snr = get_snr(rcs, distance)
    jam_intensity = jamming_factor * config.EW_JAMMING_STRENGTH
    effective_snr = base_snr * (1.0 - jam_intensity)
    return max(effective_snr, 0.0)


def detection_probability(snr):
    """P(detect) = 1 - exp(-SNR)"""
    return 1.0 - math.exp(-snr)


def should_detect(snr):
    import random
    p = detection_probability(snr)
    return random.random() < p


def get_detection_color(prob):
    if prob > 0.75:
        return config.RADAR_GREEN
    elif prob > 0.40:
        return config.HUD_AMBER
    else:
        return (255, 50, 50)


def get_detection_strength(rcs, distance,
                           jamming_factor=0.0):
    snr  = get_effective_snr(rcs, distance,
                              jamming_factor)
    prob = detection_probability(snr)
    return prob