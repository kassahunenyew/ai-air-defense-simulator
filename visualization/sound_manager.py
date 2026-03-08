# visualization/sound_manager.py
# ============================================================
# Sound Manager — generates all sounds procedurally
# No audio files needed — pure NumPy synthesis
# ============================================================

import numpy as np
import pygame
import config

# sample rate for audio
SAMPLE_RATE = 44100

def _make_sound(samples):
    """Convert numpy array to Pygame sound object."""
    samples = np.clip(samples, -1.0, 1.0)
    samples = (samples * 32767).astype(np.int16)
    # make stereo
    stereo  = np.column_stack([samples, samples])
    return pygame.sndarray.make_sound(stereo)

def generate_explosion_sound():
    """
    Deep boom explosion — layered noise burst with decay.
    """
    duration = 1.2
    t        = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # white noise burst
    noise    = np.random.uniform(-1, 1, len(t))

    # low frequency rumble
    rumble   = np.sin(2 * np.pi * 60 * t) * 0.4
    rumble  += np.sin(2 * np.pi * 80 * t) * 0.3

    # combine and apply exponential decay
    wave     = (noise * 0.6 + rumble * 0.4)
    decay    = np.exp(-4.0 * t)
    wave     = wave * decay * 0.9

    return _make_sound(wave)

def generate_launch_sound():
    """
    Missile launch — rising whoosh with tail.
    """
    duration = 0.7
    t        = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # frequency rises from 200Hz to 800Hz (whoosh effect)
    freq     = np.linspace(200, 800, len(t))
    phase    = np.cumsum(2 * np.pi * freq / SAMPLE_RATE)
    tone     = np.sin(phase) * 0.5

    # add noise layer
    noise    = np.random.uniform(-0.3, 0.3, len(t))

    # envelope — fast attack, slow decay
    attack   = np.minimum(t / 0.05, 1.0)
    decay    = np.exp(-3.0 * t)
    envelope = attack * decay

    wave     = (tone + noise) * envelope * 0.8
    return _make_sound(wave)

def generate_radar_ping():
    """
    Radar sweep ping — short clean tone.
    """
    duration = 0.12
    t        = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # clean sine tone at 880Hz
    tone     = np.sin(2 * np.pi * 880 * t)

    # quick decay
    decay    = np.exp(-20.0 * t)
    wave     = tone * decay * 0.4

    return _make_sound(wave)

def generate_alert_sound():
    """
    Threat alert — two-tone urgent beep.
    """
    duration = 0.6
    t        = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # alternating tones 440Hz / 880Hz
    freq     = np.where((t * 4).astype(int) % 2 == 0, 440, 880)
    phase    = np.cumsum(2 * np.pi * freq / SAMPLE_RATE)
    wave     = np.sin(phase) * 0.5

    # pulse envelope
    pulse    = np.where((t * 4).astype(int) % 2 == 0, 1.0, 0.7)
    wave     = wave * pulse * 0.6

    return _make_sound(wave)

def generate_intercept_success():
    """
    Intercept confirmed — ascending success chime.
    """
    duration = 0.5
    t        = np.linspace(0, duration, int(SAMPLE_RATE * duration))

    # three ascending notes
    note1    = np.sin(2 * np.pi * 523 * t) * np.exp(-8 * t)
    note2    = np.sin(2 * np.pi * 659 * t) * np.exp(-8 * (t - 0.15)) * (t > 0.15)
    note3    = np.sin(2 * np.pi * 784 * t) * np.exp(-8 * (t - 0.30)) * (t > 0.30)

    wave     = (note1 + note2 + note3) * 0.4
    return _make_sound(wave)


class SoundManager:
    def __init__(self):
        pygame.mixer.init(
            frequency = SAMPLE_RATE,
            size      = -16,
            channels  = 2,
            buffer    = 512
        )
        pygame.mixer.set_num_channels(16)

        print("Generating sounds...")
        self.explosion        = generate_explosion_sound()
        self.launch           = generate_launch_sound()
        self.radar_ping       = generate_radar_ping()
        self.alert            = generate_alert_sound()
        self.intercept_success = generate_intercept_success()
        print("✅ Sounds ready.")

        # -- state tracking --
        self.last_ping_angle  = 0
        self.ping_interval    = 90       # degrees between pings
        self.alert_cooldown   = 0
        self.launch_cooldown  = 0

    def play_explosion(self):
        self.explosion.play()
        self.intercept_success.play()

    def play_launch(self):
        if self.launch_cooldown <= 0:
            self.launch.play()
            self.launch_cooldown = 30    # frames between launch sounds
        self.launch_cooldown -= 1

    def check_radar_ping(self, sweep_angle):
        """Play ping every 90 degrees of sweep."""
        delta = (sweep_angle - self.last_ping_angle) % 360
        if delta >= self.ping_interval:
            self.radar_ping.play()
            self.last_ping_angle = sweep_angle

    def check_threat_alert(self, ranked_threats):
        """Play alert if any missile is critically close."""
        self.alert_cooldown = max(0, self.alert_cooldown - 1)
        if self.alert_cooldown > 0:
            return
        for m, score, tti in ranked_threats:
            if score > 0.75:
                self.alert.play()
                self.alert_cooldown = 120   # 2 seconds between alerts
                break

    def update(self, sweep_angle, ranked_threats):
        self.check_radar_ping(sweep_angle)
        self.check_threat_alert(ranked_threats)