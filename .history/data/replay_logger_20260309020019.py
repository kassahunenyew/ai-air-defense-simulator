# data/replay_logger.py
# ============================================================
# Records every simulation frame to memory,
# then saves to JSON for replay.
# ============================================================

import json
import os
import time


class ReplayLogger:
    def __init__(self):
        self.recording = False
        self.frames    = []
        self.events    = []   # launches, hits, explosions
        self.start_time = None

    def start_recording(self):
        self.recording  = True
        self.frames     = []
        self.events     = []
        self.start_time = time.time()
        print("◉ RECORDING STARTED")

    def stop_recording(self):
        self.recording = False
        print(f"◉ RECORDING STOPPED — {len(self.frames)} frames")

    def log_frame(self, missiles, interceptors,
                  sweep_angle, frame_num):
        if not self.recording:
            return

        missile_states = []
        for m in missiles:
            if not m.alive:
                continue
            missile_states.append({
                "id":    m.id,
                "type":  m.type,
                "x":     round(m.x, 1),
                "y":     round(m.y, 1),
                "vx":    round(m.vx, 3),
                "vy":    round(m.vy, 3),
                "alive": m.alive,
                "det":   round(getattr(m,
                               'detection_prob', 1.0), 2),
            })

        interceptor_states = []
        for inc in interceptors:
            if not inc.alive:
                continue
            interceptor_states.append({
                "id":       inc.id,
                "x":        round(inc.x, 1),
                "y":        round(inc.y, 1),
                "vx":       round(inc.vx, 3),
                "vy":       round(inc.vy, 3),
                "target_id": inc.target.id
                              if inc.target else None,
            })

        self.frames.append({
            "frame":        frame_num,
            "sweep":        round(sweep_angle, 1),
            "missiles":     missile_states,
            "interceptors": interceptor_states,
        })

    def log_event(self, event_type, x, y, frame_num,
                  details=None):
        """Log discrete events: launch, hit, explosion."""
        if not self.recording:
            return
        self.events.append({
            "type":   event_type,
            "frame":  frame_num,
            "x":      round(x, 1),
            "y":      round(y, 1),
            "details": details or {},
        })

    def save(self, path="data/replays/"):
        if not self.frames:
            print("Nothing to save.")
            return None

        os.makedirs(path, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename  = f"{path}replay_{timestamp}.json"

        data = {
            "meta": {
                "timestamp":   timestamp,
                "total_frames": len(self.frames),
                "total_events": len(self.events),
                "duration_sec": round(
                    time.time() - self.start_time, 1)
                    if self.start_time else 0,
            },
            "frames": self.frames,
            "events": self.events,
        }

        with open(filename, "w") as f:
            json.dump(data, f)

        print(f"✅ Replay saved: {filename}")
        return filename

    def load(self, filename):
        with open(filename, "r") as f:
            data = json.load(f)
        self.frames = data["frames"]
        self.events = data["events"]
        print(f"✅ Replay loaded: "
              f"{len(self.frames)} frames, "
              f"{len(self.events)} events")
        return data["meta"]


class ReplayPlayer:
    """
    Plays back a loaded replay frame by frame.
    Supports pause, scrub, speed control.
    """
    def __init__(self, logger):
        self.logger      = logger
        self.playing     = False
        self.frame_idx   = 0
        self.speed       = 1.0   # 1.0 = realtime, 2.0 = 2x
        self.paused      = False
        self.frame_timer = 0.0

    def start(self):
        if not self.logger.frames:
            print("No replay data loaded.")
            return
        self.playing   = True
        self.frame_idx = 0
        self.paused    = False
        print(f"▶ REPLAY STARTED — "
              f"{len(self.logger.frames)} frames")

    def stop(self):
        self.playing = False
        print("■ REPLAY STOPPED")

    def toggle_pause(self):
        self.paused = not self.paused
        print("⏸ PAUSED" if self.paused else "▶ RESUMED")

    def scrub(self, delta):
        """Jump forward/back by delta frames."""
        self.frame_idx = max(0, min(
            len(self.logger.frames) - 1,
            self.frame_idx + delta
        ))

    def get_current_frame(self):
        if not self.logger.frames:
            return None
        idx = min(self.frame_idx,
                  len(self.logger.frames) - 1)
        return self.logger.frames[idx]

    def get_events_at_frame(self, frame_num):
        return [e for e in self.logger.events
                if e["frame"] == frame_num]

    def advance(self):
        """Call once per game loop tick."""
        if not self.playing or self.paused:
            return

        self.frame_timer += self.speed
        if self.frame_timer >= 1.0:
            self.frame_timer -= 1.0
            self.frame_idx   += 1

        if self.frame_idx >= len(self.logger.frames):
            self.playing   = False
            self.frame_idx = len(self.logger.frames) - 1
            print("■ REPLAY FINISHED")

    @property
    def progress(self):
        if not self.logger.frames:
            return 0.0
        return self.frame_idx / len(self.logger.frames)

    @property
    def total_frames(self):
        return len(self.logger.frames)