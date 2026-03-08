# config.py
# ============================================================
# SINGLE SOURCE OF TRUTH — all constants live here
# ============================================================

# --- Display ---
SCREEN_WIDTH  = 1200
SCREEN_HEIGHT = 900
FPS           = 60
TITLE         = "AI Air-Defense Command — CLASSIFIED"

# --- Radar ---
RADAR_CENTER  = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
RADAR_RADIUS  = 380        # outer radar ring radius in pixels
SWEEP_SPEED   = 1.5        # degrees the sweep rotates per frame
BLIP_FADE_MS  = 3000       # milliseconds before a blip fully fades

# --- Colors (phosphor green radar aesthetic) ---
BLACK         = (0,   0,   0)
RADAR_GREEN   = (0,   255, 70)
DIM_GREEN     = (0,   80,  25)
SWEEP_COLOR   = (0,   255, 70)
THREAT_RED    = (255, 50,  50)
INTERCEPT_BLU = (50,  180, 255)
HUD_AMBER     = (255, 180, 0)
GRID_COLOR    = (0,   40,  15)

# --- Protected Zone ---
PROTECTED_RADIUS = 40      # missile inside this = city hit

# --- Missiles ---
MISSILE_SPEED_MIN = 0.8    # pixels per frame (slowest missile)
MISSILE_SPEED_MAX = 2.2    # pixels per frame (fastest missile)
MISSILE_SPAWN_RATE = 90   # frames between spawns (3 sec at 60fps)

MISSILE_SPAWN_COUNT = 3      # spawn 3 missiles at a time
# --- Interceptors ---
INTERCEPTOR_SPEED = 4.0
MAX_INTERCEPTORS  = 6