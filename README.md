# 🎯 AI Air Defense Simulator

![Python](https://img.shields.io/badge/Python-3.13-blue?style=flat-square&logo=python)
![Pygame](https://img.shields.io/badge/Pygame-2.6.1-green?style=flat-square)
![PyTorch](https://img.shields.io/badge/PyTorch-LSTM-orange?style=flat-square&logo=pytorch)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

A real-time AI-powered missile defense simulation featuring Kalman Filter tracking, LSTM neural network trajectory prediction, Reinforcement Learning interceptor guidance, and Hungarian Algorithm optimal target assignment — all running simultaneously in a military-style radar HUD.

---

## 📸 Demo

> Radar HUD with 15+ simultaneous targets, 3 missile types, AI intercept prediction, and live ML performance dashboard.

---

## 🧠 AI & ML Stack

| Component | Algorithm | Purpose |
|---|---|---|
| Tracking | Kalman Filter | Noisy radar → clean trajectory |
| Prediction | PyTorch LSTM | Online-trained curved path prediction |
| Threat Scoring | Weighted heuristic | Distance + speed + TTI ranking |
| Interception | RL + Proportional Nav | Smart lead-target guidance |
| Assignment | Hungarian Algorithm | Optimal interceptor-to-missile pairing |
| Detection | Radar Range Equation | RCS-based detection probability |

---

## ✨ Features

- **3 Missile Types**
  - 🔴 Ballistic — precision strike, high RCS
  - 🟣 Evasive — dodges interceptors, random maneuvers
  - 🟢 Stealth — low RCS, flickers on radar based on physics

- **Dual Trajectory Prediction**
  - Yellow dots — Kalman Filter (classical signal processing)
  - Cyan dots — LSTM neural network (learns online during simulation)

- **Tactical HUD**
  - Threat assessment panel with priority ranking
  - Target diamonds with lock indicators
  - Threat cones showing danger zones
  - Intercept prediction markers
  - Engagement lines showing Hungarian assignments

- **Battle Replay System**
  - Record any battle to JSON
  - Replay with pause, scrub, and speed control
  - Event markers on timeline (launches, explosions)

- **Live AI Dashboard**
  - Active threats over time
  - Intercept success rate
  - LSTM prediction error with rolling average
  - RL agent win rate

- **Realistic Effects**
  - Fire, smoke, and debris on intercept
  - Procedural sound (radar ping, launch whoosh, explosion)
  - Screen flash on intercept

---

## 🏗️ Architecture
```
┌─────────────────────────────────────────┐
│           SIMULATION ENGINE             │
│     (missile physics, spawning)         │
└──────────────────┬──────────────────────┘
                   │ raw positions
┌──────────────────▼──────────────────────┐
│           PERCEPTION LAYER              │
│   Kalman Filter + LSTM + RCS Model      │
└──────────────────┬──────────────────────┘
                   │ tracks + predictions
┌──────────────────▼──────────────────────┐
│         DECISION LAYER (AI)             │
│  Threat Scoring → Hungarian Algorithm   │
│  → RL Agent → Interceptor Guidance      │
└──────────────────┬──────────────────────┘
                   │ commands
┌──────────────────▼──────────────────────┐
│         VISUALIZATION LAYER             │
│   Pygame HUD + Matplotlib Dashboard     │
└─────────────────────────────────────────┘
```

---

## 🚀 Setup
```bash
# Clone
git clone https://github.com/kassahunenyew/ai-air-defense-simulator.git
cd ai-air-defense-simulator

# Install dependencies
pip install -r requirements.txt

# Run
python main.py
```

---

## 🎮 Controls

| Key | Action |
|---|---|
| `R` | Start / Stop recording |
| `P` | Play last replay |
| `SPACE` | Pause replay |
| `← →` | Scrub replay timeline |
| `↑ ↓` | Change replay speed |
| `ESC` | Exit replay / quit |

---

## 📁 Project Structure
```
air_defense_sim/
├── main.py                  # Entry point + game loop
├── config.py                # All constants
├── simulation/
│   ├── missile.py           # 3 missile types + RCS
│   └── interceptor.py       # Interceptor physics
├── perception/
│   ├── kalman_tracker.py    # Kalman Filter
│   ├── lstm_predictor.py    # PyTorch LSTM
│   └── radar_model.py       # RCS detection model
├── ai/
│   ├── threat_scorer.py     # Threat ranking
│   ├── interceptor_ai.py    # Hungarian + RL guidance
│   ├── assignment.py        # Hungarian Algorithm
│   └── rl_interceptor.py    # RL agent
├── visualization/
│   ├── sound_manager.py     # Procedural audio
│   └── dashboard.py         # Matplotlib dashboard
└── data/
    ├── replay_logger.py     # Battle recorder
    └── replays/             # Saved battles (JSON)
```

---

## 🔬 Technical Highlights

- **LSTM trains online** — no pre-recorded dataset needed. The network learns each missile's trajectory in real time from scratch using sliding window samples and 3 gradient steps per update.

- **Hungarian Algorithm** — O(n³) optimal assignment ensures no two interceptors waste resources on the same target. Cost matrix weighs predicted intercept distance, time-to-impact, and threat score.

- **Radar Range Equation** — P(detect) = 1 - exp(-SNR) where SNR scales with RCS and drops with R⁴. Stealth missiles (RCS = 0.01m²) are genuinely hard to track.

- **RL Agent** — custom policy gradient network (8→32→32→2) pre-trained for 50 episodes then blended 30/70 with proportional navigation for reliable real-time guidance.

---

## 🛠️ Tech Stack

- Python 3.13
- Pygame 2.6.1
- PyTorch (LSTM + RL)
- NumPy
- FilterPy (Kalman Filter)
- SciPy (Hungarian Algorithm)
- Matplotlib (Dashboard)

---

## 👤 Author

**Kassahun Aweke**
Electrical Engineering Undergraduate
[GitHub](https://github.com/kassahunenyew)

---

## 📄 License

MIT License — free to use and modify.