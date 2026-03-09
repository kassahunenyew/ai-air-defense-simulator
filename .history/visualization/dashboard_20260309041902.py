# visualization/dashboard.py
# ============================================================
# Live AI Performance Dashboard
# Opens a separate Matplotlib window with 4 live graphs
# ============================================================

import matplotlib
matplotlib.use("TkAgg")   # works alongside Pygame
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from collections import deque

class AIDashboard:
    def __init__(self, maxlen=300):
        self.maxlen = maxlen

        # data buffers
        self.frames          = deque(maxlen=maxlen)
        self.threat_counts   = deque(maxlen=maxlen)
        self.hit_rates       = deque(maxlen=maxlen)
        self.lstm_errors     = deque(maxlen=maxlen)
        self.rl_rewards      = deque(maxlen=maxlen)
        self.intercept_times = deque(maxlen=maxlen)
        # heatmap — 2D grid over radar area
        self.heatmap = np.zeros((100, 100))
        self.heatmap_extent = [
            config.RADAR_CENTER[0] - config.RADAR_RADIUS,
            config.RADAR_CENTER[0] + config.RADAR_RADIUS,
            config.RADAR_CENTER[1] - config.RADAR_RADIUS,
            config.RADAR_CENTER[1] + config.RADAR_RADIUS,
        ]

        self.total_hits      = 0
        self.total_launched  = 0
        self.last_hits       = 0
        self.last_launched   = 0

        self._setup_figure()
        self.update_counter  = 0
        self.update_every    = 30   # refresh every 30 frames

    def _setup_figure(self):
        plt.ion()
        self.fig = plt.figure(
            figsize=(15, 7),
            facecolor="#000a00"
        )
        self.fig.canvas.manager.set_window_title(
            "AI Performance Dashboard")

        gs = gridspec.GridSpec(
            2, 3,
            figure=self.fig,
            hspace=0.45,
            wspace=0.35
        )

        self.ax1 = self.fig.add_subplot(gs[0, 0])
        self.ax2 = self.fig.add_subplot(gs[0, 1])
        self.ax3 = self.fig.add_subplot(gs[1, 0])
        self.ax4 = self.fig.add_subplot(gs[1, 1])
        self.ax5 = self.fig.add_subplot(gs[:, 2])  # heatmap spans both rows

        for ax in [self.ax1, self.ax2,
                   self.ax3, self.ax4, self.ax5]:
            ax.set_facecolor("#001400")
            ax.tick_params(colors="#00cc44", labelsize=8)
            for spine in ax.spines.values():
                spine.set_edgecolor("#004400")

        self.fig.patch.set_facecolor("#000a00")
        plt.show(block=False)

    def log(self, frame, missiles, stats, lstm_error=None):
        self.frames.append(frame)

        # threat count
        active = sum(1 for m in missiles if m.alive)
        self.threat_counts.append(active)

        # hit rate
        hits     = stats.get("hits", 0)
        misses   = stats.get("misses", 0)
        total    = hits + misses
        hit_rate = hits / max(total, 1) * 100
        self.hit_rates.append(hit_rate)

        # LSTM prediction error
        if lstm_error is not None:
            self.lstm_errors.append(lstm_error)
        elif self.lstm_errors:
            self.lstm_errors.append(
                self.lstm_errors[-1])
        else:
            self.lstm_errors.append(0.0)

        # RL win rate as reward proxy
        rl_rate = stats.get("rl_rate", 0) * 100
        self.rl_rewards.append(rl_rate)
    
    def log_intercept(self, x, y):
        """Call this on every successful intercept."""
        cx = config.RADAR_CENTER[0]
        cy = config.RADAR_CENTER[1]
        r  = config.RADAR_RADIUS

        # normalize to 0-1
        nx = (x - (cx - r)) / (2 * r)
        ny = (y - (cy - r)) / (2 * r)

        # convert to grid index
        ix = int(nx * 99)
        iy = int(ny * 99)

        if 0 <= ix <= 99 and 0 <= iy <= 99:
            self.heatmap[iy, ix] += 1
            # spread heat to neighbors for smoothness
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    nx2 = ix + dx
                    ny2 = iy + dy
                    if 0 <= nx2 <= 99 and \
                       0 <= ny2 <= 99:
                        self.heatmap[ny2, nx2] += 0.3

    def _compute_lstm_error(self, missiles):
        """
        Estimate LSTM prediction error by comparing
        predicted position to actual position.
        """
        errors = []
        for m in missiles:
            if not m.alive:
                continue
            if not hasattr(m, 'lstm_predicted_path'):
                continue
            path = m.lstm_predicted_path
            if len(path) < 5:
                continue
            # compare first predicted point to
            # actual current position
            px, py = path[0]
            import math
            err = math.hypot(px - m.x, py - m.y)
            errors.append(err)
        return sum(errors)/len(errors) if errors else 0.0

    def update(self, frame, missiles, stats):
        self.update_counter += 1
        lstm_err = self._compute_lstm_error(missiles)
        self.log(frame, missiles, stats, lstm_err)

        if self.update_counter % self.update_every != 0:
            return

        try:
            self._redraw()
        except Exception:
            pass   # never crash the simulation

    def _redraw(self):
        frames = list(self.frames)
        if not frames:
            return

        # ── Plot 1: Active Threats ────────────────────
        self.ax1.clear()
        self.ax1.set_facecolor("#001400")
        self.ax1.plot(frames,
                      list(self.threat_counts),
                      color="#ff3333", linewidth=1.5,
                      label="Active Threats")
        self.ax1.fill_between(frames,
                              list(self.threat_counts),
                              alpha=0.2, color="#ff3333")
        self.ax1.set_title("Active Threats Over Time",
                           color="#00ff44", fontsize=9,
                           fontweight="bold")
        self.ax1.set_xlabel("Frame",
                            color="#00cc44", fontsize=7)
        self.ax1.set_ylabel("Count",
                            color="#00cc44", fontsize=7)
        self.ax1.tick_params(colors="#00cc44",
                             labelsize=7)
        for sp in self.ax1.spines.values():
            sp.set_edgecolor("#004400")
        self.ax1.legend(fontsize=7,
                        labelcolor="#00cc44",
                        facecolor="#001400",
                        edgecolor="#004400")

        # ── Plot 2: Intercept Success Rate ────────────
        self.ax2.clear()
        self.ax2.set_facecolor("#001400")
        self.ax2.plot(frames,
                      list(self.hit_rates),
                      color="#00ff88", linewidth=1.5,
                      label="Hit Rate %")
        self.ax2.fill_between(frames,
                              list(self.hit_rates),
                              alpha=0.2,
                              color="#00ff88")
        self.ax2.axhline(y=50, color="#ffaa00",
                         linestyle="--",
                         linewidth=0.8, alpha=0.6,
                         label="50% baseline")
        self.ax2.set_ylim(0, 105)
        self.ax2.set_title(
            "Intercept Success Rate (%)",
            color="#00ff44", fontsize=9,
            fontweight="bold")
        self.ax2.set_xlabel("Frame",
                            color="#00cc44", fontsize=7)
        self.ax2.set_ylabel("Hit Rate %",
                            color="#00cc44", fontsize=7)
        self.ax2.tick_params(colors="#00cc44",
                             labelsize=7)
        for sp in self.ax2.spines.values():
            sp.set_edgecolor("#004400")
        self.ax2.legend(fontsize=7,
                        labelcolor="#00cc44",
                        facecolor="#001400",
                        edgecolor="#004400")

        # ── Plot 3: LSTM Prediction Error ─────────────
        self.ax3.clear()
        self.ax3.set_facecolor("#001400")
        errors = list(self.lstm_errors)
        self.ax3.plot(frames, errors,
                      color="#00ccff", linewidth=1.5,
                      label="LSTM Error (px)")

        # rolling average
        if len(errors) >= 10:
            kernel  = np.ones(10) / 10
            smoothed = np.convolve(errors, kernel,
                                   mode="valid")
            smooth_frames = frames[9:]
            self.ax3.plot(smooth_frames, smoothed,
                          color="#ffffff",
                          linewidth=1.0,
                          linestyle="--",
                          label="10-frame avg",
                          alpha=0.7)

        self.ax3.fill_between(frames, errors,
                              alpha=0.15,
                              color="#00ccff")
        self.ax3.set_title(
            "LSTM Prediction Error (pixels)",
            color="#00ff44", fontsize=9,
            fontweight="bold")
        self.ax3.set_xlabel("Frame",
                            color="#00cc44", fontsize=7)
        self.ax3.set_ylabel("Error (px)",
                            color="#00cc44", fontsize=7)
        self.ax3.tick_params(colors="#00cc44",
                             labelsize=7)
        for sp in self.ax3.spines.values():
            sp.set_edgecolor("#004400")
        self.ax3.legend(fontsize=7,
                        labelcolor="#00cc44",
                        facecolor="#001400",
                        edgecolor="#004400")

        # ── Plot 4: RL Win Rate ───────────────────────
        self.ax4.clear()
        self.ax4.set_facecolor("#001400")
        self.ax4.plot(frames,
                      list(self.rl_rewards),
                      color="#ffaa00", linewidth=1.5,
                      label="RL Win Rate %")
        self.ax4.fill_between(frames,
                              list(self.rl_rewards),
                              alpha=0.2,
                              color="#ffaa00")
        self.ax4.set_ylim(0, 105)
        self.ax4.set_title(
            "RL Agent Win Rate (%)",
            color="#00ff44", fontsize=9,
            fontweight="bold")
        self.ax4.set_xlabel("Frame",
                            color="#00cc44", fontsize=7)
        self.ax4.set_ylabel("Win Rate %",
                            color="#00cc44", fontsize=7)
        self.ax4.tick_params(colors="#00cc44",
                             labelsize=7)
        for sp in self.ax4.spines.values():
            sp.set_edgecolor("#004400")
        self.ax4.legend(fontsize=7,
                        labelcolor="#00cc44",
                        facecolor="#001400",
                        edgecolor="#004400")

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        
        # ── Plot 5: Intercept Heatmap ─────────────
        self.ax5.clear()
        self.ax5.set_facecolor("#001400")

        if self.heatmap.max() > 0:
            # smooth the heatmap
            from scipy.ndimage import gaussian_filter
            smoothed = gaussian_filter(self.heatmap, sigma=2)

            self.ax5.imshow(
                smoothed,
                cmap="hot",
                interpolation="bilinear",
                origin="upper",
                aspect="auto"
            )

            # draw protected zone circle
            theta = np.linspace(0, 2*np.pi, 100)
            pr    = config.PROTECTED_RADIUS / \
                    (2 * config.RADAR_RADIUS) * 99
            px    = 50 + pr * np.cos(theta)
            py    = 50 + pr * np.sin(theta)
            self.ax5.plot(px, py, 'c--',
                          linewidth=1, alpha=0.7,
                          label="Protected zone")

            # radar boundary
            rx = 50 + 49 * np.cos(theta)
            ry = 50 + 49 * np.sin(theta)
            self.ax5.plot(rx, ry, color="#004400",
                          linewidth=1)
        else:
            self.ax5.text(
                0.5, 0.5,
                "Waiting for\nintercepts...",
                transform=self.ax5.transAxes,
                color="#00cc44", fontsize=10,
                ha="center", va="center")

        self.ax5.set_title(
            "Intercept Heatmap",
            color="#00ff44", fontsize=9,
            fontweight="bold")
        self.ax5.set_xlabel("X",
                            color="#00cc44", fontsize=7)
        self.ax5.set_ylabel("Y",
                            color="#00cc44", fontsize=7)
        self.ax5.tick_params(colors="#00cc44",
                             labelsize=7)
        for sp in self.ax5.spines.values():
            sp.set_edgecolor("#004400")
        self.ax5.legend(fontsize=7,
                        labelcolor="#00cc44",
                        facecolor="#001400",
                        edgecolor="#004400")

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def close(self):
        plt.close(self.fig)