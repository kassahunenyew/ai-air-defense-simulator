# config.py
# ============================================================
# SINGLE SOURCE OF TRUTH — all constants live here
# ============================================================

# --- Display ---
SCREEN_WIDTH  = 1400
SCREEN_HEIGHT = 860
FPS           = 60
TITLE         = "AI Air-Defense Command — CLASSIFIED"

# --- Radar ---
RADAR_CENTER  = (700, 440)
RADAR_RADIUS  = 380
SWEEP_SPEED   = 1.5
BLIP_FADE_MS  = 3000

# --- Colors ---
BLACK         = (0,   0,   0)
RADAR_GREEN   = (0,   255, 70)
DIM_GREEN     = (0,   80,  25)
SWEEP_COLOR   = (0,   255, 70)
THREAT_RED    = (255, 50,  50)
INTERCEPT_BLU = (50,  180, 255)
HUD_AMBER     = (255, 180, 0)
GRID_COLOR    = (0,   40,  15)

# --- Protected Zone ---
PROTECTED_RADIUS = 40

# --- Missiles ---
MISSILE_SPEED_MIN   = 0.8
MISSILE_SPEED_MAX   = 2.2
MISSILE_SPAWN_RATE  = 120
MISSILE_SPAWN_COUNT = 2

# --- Interceptors ---
INTERCEPTOR_SPEED = 4.0
MAX_INTERCEPTORS  = 4