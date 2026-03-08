# ai/rl_interceptor.py
# ============================================================
# Reinforcement Learning Interceptor Agent
# Trains inside the simulation using PPO algorithm
# ============================================================

import numpy as np
import math
import os
import config

# ── Simple RL Environment ────────────────────────────────────

class InterceptEnv:
    """
    Minimal RL environment for interceptor guidance.

    State:  [rel_x, rel_y, rel_vx, rel_vy,
             own_x, own_y, distance, angle]  (8 values)

    Action: [thrust_x, thrust_y]  (continuous, -1 to 1)

    Reward: +100 for intercept
            -1   per step (time penalty)
            +small reward for getting closer
    """

    def __init__(self):
        self.max_steps   = 300
        self.step_count  = 0
        self.reset()

    def reset(self, missile=None, interceptor_pos=None):
        cx, cy = config.RADAR_CENTER
        r      = config.RADAR_RADIUS

        if missile is not None:
            self.target_x  = missile.x
            self.target_y  = missile.y
            self.target_vx = missile.vx
            self.target_vy = missile.vy
        else:
            # random training scenario
            angle          = np.random.uniform(0, 2 * math.pi)
            self.target_x  = cx + r * 0.7 * math.cos(angle)
            self.target_y  = cy + r * 0.7 * math.sin(angle)
            speed          = np.random.uniform(0.5, 1.5)
            toward_angle   = math.atan2(cy - self.target_y,
                                        cx - self.target_x)
            self.target_vx = speed * math.cos(toward_angle)
            self.target_vy = speed * math.sin(toward_angle)

        if interceptor_pos is not None:
            self.own_x, self.own_y = interceptor_pos
        else:
            self.own_x = float(cx)
            self.own_y = float(cy)

        self.own_vx     = 0.0
        self.own_vy     = 0.0
        self.step_count = 0
        self.prev_dist  = self._distance()
        return self._get_obs()

    def _distance(self):
        return math.hypot(self.own_x - self.target_x,
                          self.own_y - self.target_y)

    def _get_obs(self):
        cx, cy = config.RADAR_CENTER
        scale  = config.RADAR_RADIUS
        return np.array([
            (self.target_x - self.own_x)  / scale,
            (self.target_y - self.own_y)  / scale,
            self.target_vx / config.MISSILE_SPEED_MAX,
            self.target_vy / config.MISSILE_SPEED_MAX,
            (self.own_x - cx) / scale,
            (self.own_y - cy) / scale,
            self._distance() / scale,
            math.atan2(self.target_y - self.own_y,
                       self.target_x - self.own_x) / math.pi,
        ], dtype=np.float32)

    def step(self, action):
        """
        action: [ax, ay] normalized thrust direction
        """
        # normalize action to unit vector
        ax, ay  = float(action[0]), float(action[1])
        mag     = math.hypot(ax, ay)
        if mag > 0:
            ax /= mag
            ay /= mag

        speed        = config.INTERCEPTOR_SPEED
        self.own_x  += ax * speed
        self.own_y  += ay * speed

        # move target
        self.target_x += self.target_vx
        self.target_y += self.target_vy

        self.step_count += 1
        dist     = self._distance()
        obs      = self._get_obs()

        # -- reward --
        reward   = (self.prev_dist - dist) * 0.5  # closing reward
        reward  -= 0.5                              # time penalty

        done     = False

        # intercept success
        if dist < 15:
            reward  = 100.0
            done    = True

        # timeout
        if self.step_count >= self.max_steps:
            reward -= 20.0
            done    = True

        # out of bounds
        cx, cy = config.RADAR_CENTER
        if math.hypot(self.own_x - cx,
                      self.own_y - cy) > config.RADAR_RADIUS * 1.3:
            reward -= 30.0
            done    = True

        self.prev_dist = dist
        return obs, reward, done, {}


# ── RL Agent (simple neural network policy) ──────────────────

class RLAgent:
    """
    Lightweight PPO-style policy network.
    Trained directly inside the simulation.
    Uses numpy only — no heavy dependencies.
    """

    def __init__(self):
        # simple 2-layer neural network
        # input(8) → hidden(32) → hidden(32) → output(2)
        self.W1 = np.random.randn(8,  32) * 0.1
        self.b1 = np.zeros(32)
        self.W2 = np.random.randn(32, 32) * 0.1
        self.b2 = np.zeros(32)
        self.W3 = np.random.randn(32, 2)  * 0.1
        self.b3 = np.zeros(2)

        self.lr          = 0.001
        self.trained     = False
        self.train_steps = 0
        self.episodes    = 0
        self.wins        = 0
        self.total_reward = 0.0

        # experience buffer
        self.buffer_obs  = []
        self.buffer_acts = []
        self.buffer_rew  = []

        self.env         = InterceptEnv()

        # pre-train for 50 episodes at startup
        print("Pre-training RL agent...")
        self._pretrain(episodes=50)
        print(f"✅ RL Agent ready — "
              f"win rate: {self.wins}/{self.episodes}")

    def _relu(self, x):
        return np.maximum(0, x)

    def _tanh(self, x):
        return np.tanh(x)

    def forward(self, obs):
        """Forward pass — returns action."""
        h1  = self._relu(obs @ self.W1 + self.b1)
        h2  = self._relu(h1 @ self.W2 + self.b2)
        out = self._tanh(h2 @ self.W3 + self.b3)
        return out

    def _pretrain(self, episodes=50):
        """
        Train agent using simple policy gradient
        before simulation starts.
        """
        for _ in range(episodes):
            obs      = self.env.reset()
            done     = False
            ep_obs   = []
            ep_acts  = []
            ep_rews  = []

            while not done:
                # add exploration noise during training
                action   = self.forward(obs)
                noise    = np.random.randn(2) * 0.3
                action   = np.clip(action + noise, -1, 1)

                next_obs, reward, done, _ = self.env.step(action)
                ep_obs.append(obs)
                ep_acts.append(action)
                ep_rews.append(reward)
                obs      = next_obs

            self.episodes += 1
            if ep_rews and ep_rews[-1] > 50:
                self.wins += 1

            # compute returns
            returns  = []
            G        = 0
            for r in reversed(ep_rews):
                G    = r + 0.95 * G
                returns.insert(0, G)

            returns  = np.array(returns)
            if returns.std() > 0:
                returns = (returns - returns.mean()) / \
                          (returns.std() + 1e-8)

            # gradient update
            for obs_i, act_i, ret_i in zip(
                    ep_obs, ep_acts, returns):
                pred     = self.forward(obs_i)
                error    = (act_i - pred) * ret_i
                self._backward(obs_i, error)

        self.trained = True

    def _backward(self, obs, error):
        """Simple gradient step."""
        h1   = self._relu(obs @ self.W1 + self.b1)
        h2   = self._relu(h1 @ self.W2 + self.b2)

        dW3  = np.outer(h2, error)
        db3  = error

        dh2  = error @ self.W3.T
        dh2 *= (h2 > 0)
        dW2  = np.outer(h1, dh2)
        db2  = dh2

        dh1  = dh2 @ self.W2.T
        dh1 *= (h1 > 0)
        dW1  = np.outer(obs, dh1)
        db1  = dh1

        self.W1 += self.lr * dW1
        self.b1 += self.lr * db1
        self.W2 += self.lr * dW2
        self.b2 += self.lr * db2
        self.W3 += self.lr * dW3
        self.b3 += self.lr * db3

    def get_action(self, obs):
        """Get action for live simulation."""
        return self.forward(np.array(obs, dtype=np.float32))

    def get_stats(self):
        return {
            "episodes": self.episodes,
            "wins":     self.wins,
            "rate":     self.wins / max(self.episodes, 1)
        }