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
MISSILE_SPEED_MIN   = 0.5
MISSILE_SPEED_MAX   = 1.2
MISSILE_SPAWN_RATE  = 70
MISSILE_SPAWN_COUNT = 4

# --- Interceptors ---
INTERCEPTOR_SPEED = 3.0
MAX_INTERCEPTORS  = 4
# --- Radar Detection Model ---
RADAR_POWER        = 1000.0   # arbitrary transmit power units
RADAR_GAIN         = 100.0    # antenna gain
RADAR_WAVELENGTH   = 0.03     # meters (X-band radar ~10GHz)
RADAR_NOISE        = 1e-8     # receiver noise floor

# Radar Cross Section per missile type (m²)
# larger = easier to detect
RCS_BALLISTIC      = 1.0      # big metal rocket
RCS_EVASIVE        = 0.3      # smaller maneuvering missile
RCS_STEALTH        = 0.01     # stealth coating, angled surfaces

# Electronic Warfare
EW_JAMMING_RANGE    = 200.0   # px — jamming activates within this range
EW_JAMMING_STRENGTH = 0.85    # 0-1 — how much SNR is reduced at max jamming
EW_JAMMING_COLOR    = (255, 200, 0)  # amber warning color