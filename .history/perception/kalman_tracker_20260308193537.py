# perception/kalman_tracker.py
# ============================================================
# Kalman Filter — one instance per tracked missile
# Tracks position + velocity, predicts future positions
# ============================================================

import numpy as np

class KalmanTracker:
    def __init__(self, x, y):
        """
        State vector: [x, y, vx, vy]
        We track position AND velocity simultaneously.
        """

        # -- State vector [x, y, vx, vy] --
        self.state = np.array([x, y, 0.0, 0.0])

        # -- State covariance matrix (uncertainty) --
        self.P = np.eye(4) * 500.0

        # -- State transition matrix (physics: x = x + vx*dt) --
        self.F = np.array([
            [1, 0, 1, 0],   # x  = x  + vx
            [0, 1, 0, 1],   # y  = y  + vy
            [0, 0, 1, 0],   # vx = vx
            [0, 0, 0, 1],   # vy = vy
        ], dtype=float)

        # -- Measurement matrix (we only measure x, y) --
        self.H = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
        ], dtype=float)

        # -- Measurement noise (radar accuracy) --
        self.R = np.eye(2) * 10.0

        # -- Process noise (how much we trust physics model) --
        self.Q = np.eye(4) * 0.1

    def predict(self):
        """Step 1 — predict next state using physics model."""
        self.state = self.F @ self.state
        self.P     = self.F @ self.P @ self.F.T + self.Q
        return self.state[:2]   # return predicted (x, y)

    def update(self, measured_x, measured_y):
        """Step 2 — correct prediction with actual measurement."""
        z            = np.array([measured_x, measured_y])
        y            = z - self.H @ self.state          # innovation
        S            = self.H @ self.P @ self.H.T + self.R
        K            = self.P @ self.H.T @ np.linalg.inv(S)  # Kalman gain
        self.state   = self.state + K @ y
        self.P       = (np.eye(4) - K @ self.H) @ self.P

    def get_position(self):
        """Return current estimated position."""
        return self.state[0], self.state[1]

    def get_velocity(self):
        """Return current estimated velocity."""
        return self.state[2], self.state[3]

    def predict_future(self, steps=30):
        """
        Predict missile position N steps into the future.
        Returns list of (x, y) points — the predicted path.
        """
        future_state = self.state.copy()
        path         = []
        for _ in range(steps):
            future_state = self.F @ future_state
            path.append((future_state[0], future_state[1]))
        return path