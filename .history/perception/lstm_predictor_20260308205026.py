# perception/lstm_predictor.py
# ============================================================
# LSTM Neural Network — predicts missile trajectory
# Trained online as missiles move across radar
# ============================================================

import torch
import torch.nn as nn
import numpy as np
import config

class LSTMNetwork(nn.Module):
    """
    LSTM that takes last N positions and predicts
    the next M positions.
    """
    def __init__(self, input_size=2, hidden_size=64,
                 num_layers=2, output_steps=30):
        super().__init__()
        self.hidden_size  = hidden_size
        self.num_layers   = num_layers
        self.output_steps = output_steps

        self.lstm = nn.LSTM(
            input_size  = input_size,
            hidden_size = hidden_size,
            num_layers  = num_layers,
            batch_first = True,
            dropout     = 0.1
        )
        self.fc = nn.Linear(hidden_size, output_steps * 2)

    def forward(self, x):
        # x shape: (batch, seq_len, 2)
        out, _ = self.lstm(x)
        # take last hidden state
        out     = out[:, -1, :]
        out     = self.fc(out)
        # reshape to (batch, output_steps, 2)
        return out.view(-1, self.output_steps, 2)


class LSTMPredictor:
    """
    Per-missile LSTM predictor.
    Collects position history, trains online, predicts future.
    """
    def __init__(self, seq_len=15, output_steps=30):
        self.seq_len      = seq_len
        self.output_steps = output_steps
        self.history      = []       # raw (x, y) positions
        self.predicted    = []       # predicted future path
        self.trained      = False
        self.train_every  = 10       # retrain every N new points
        self.train_count  = 0

        # normalize around radar center
        self.cx, self.cy  = config.RADAR_CENTER
        self.scale        = config.RADAR_RADIUS

        # model
        self.model     = LSTMNetwork(
            output_steps=output_steps)
        self.optimizer = torch.optim.Adam(
            self.model.parameters(), lr=0.01)
        self.criterion = nn.MSELoss()

    def _normalize(self, x, y):
        return (
            (x - self.cx) / self.scale,
            (y - self.cy) / self.scale
        )

    def _denormalize(self, nx, ny):
        return (
            nx * self.scale + self.cx,
            ny * self.scale + self.cy
        )

    def update(self, x, y):
        """Add new position measurement."""
        nx, ny = self._normalize(x, y)
        self.history.append((nx, ny))

        # keep only recent history
        if len(self.history) > 60:
            self.history = self.history[-60:]

        self.train_count += 1

        # train once we have enough data
        if (len(self.history) >= self.seq_len + self.output_steps
                and self.train_count % self.train_every == 0):
            self._train()
            self.trained = True

        # always predict if trained
        if self.trained and len(self.history) >= self.seq_len:
            self._predict()

    def _train(self):
        """
        Online training — create samples from history
        and do a few gradient steps.
        """
        history = self.history
        X, Y    = [], []

        # create sliding window samples
        for i in range(len(history) - self.seq_len - self.output_steps + 1):
            X.append(history[i : i + self.seq_len])
            Y.append(history[i + self.seq_len :
                              i + self.seq_len + self.output_steps])

        if not X:
            return

        X_t = torch.tensor(X, dtype=torch.float32)
        Y_t = torch.tensor(Y, dtype=torch.float32)

        # 3 gradient steps per update (fast online learning)
        self.model.train()
        for _ in range(3):
            self.optimizer.zero_grad()
            pred = self.model(X_t)
            loss = self.criterion(pred, Y_t)
            loss.backward()
            self.optimizer.step()

    def _predict(self):
        """Run inference to get future path."""
        seq = self.history[-self.seq_len:]
        x_t = torch.tensor([seq], dtype=torch.float32)

        self.model.eval()
        with torch.no_grad():
            pred = self.model(x_t)   # (1, output_steps, 2)

        pred = pred.squeeze(0).numpy()
        self.predicted = [
            self._denormalize(p[0], p[1])
            for p in pred
        ]

    def get_predicted_path(self):
        return self.predicted