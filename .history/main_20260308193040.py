# main.py
# ============================================================
# ENTRY POINT — game loop lives here
# ============================================================

import pygame
import sys
import math
import config

# ── Init ────────────────────────────────────────────────────
pygame.init()
screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
pygame.display.set_caption(config.TITLE)
clock  = pygame.time.Clock()

# ── Radar sweep state ───────────────────────────────────────
sweep_angle = 0.0

# ── Drawing functions ────────────────────────────────────────

def draw_background():
    screen.fill(config.BLACK)

def draw_range_rings():
    cx, cy = config.RADAR_CENTER
    for i in range(1, 5):
        radius = int(config.RADAR_RADIUS * i / 4)
        pygame.draw.circle(screen, config.GRID_COLOR, (cx, cy), radius, 1)

def draw_crosshairs():
    cx, cy = config.RADAR_CENTER
    r      = config.RADAR_RADIUS
    pygame.draw.line(screen, config.GRID_COLOR,
                     (cx - r, cy), (cx + r, cy), 1)
    pygame.draw.line(screen, config.GRID_COLOR,
                     (cx, cy - r), (cx, cy + r), 1)

def draw_outer_ring():
    pygame.draw.circle(screen, config.DIM_GREEN,
                       config.RADAR_CENTER, config.RADAR_RADIUS, 2)

def draw_protected_zone():
    pygame.draw.circle(screen, config.THREAT_RED,
                       config.RADAR_CENTER, config.PROTECTED_RADIUS, 2)
    font  = pygame.font.SysFont("Courier New", 11)
    label = font.render("PROTECTED", True, config.THREAT_RED)
    cx, cy = config.RADAR_CENTER
    screen.blit(label, (cx - label.get_width() // 2,
                         cy + config.PROTECTED_RADIUS + 4))

def draw_sweep(angle_deg):
    cx, cy    = config.RADAR_CENTER
    angle_rad = math.radians(angle_deg)
    end_x = cx + config.RADAR_RADIUS * math.cos(angle_rad)
    end_y = cy + config.RADAR_RADIUS * math.sin(angle_rad)
    pygame.draw.line(screen, config.SWEEP_COLOR,
                     (cx, cy), (int(end_x), int(end_y)), 2)
    steps = 30
    for i in range(steps):
        trail_angle = math.radians(angle_deg - i)
        alpha       = int(120 * (1 - i / steps))
        color       = (0, alpha, int(alpha * 0.3))
        ex = cx + config.RADAR_RADIUS * math.cos(trail_angle)
        ey = cy + config.RADAR_RADIUS * math.sin(trail_angle)
        pygame.draw.line(screen, color,
                         (cx, cy), (int(ex), int(ey)), 1)

def draw_hud_frame():
    font_big   = pygame.font.SysFont("Courier New", 20, bold=True)
    font_small = pygame.font.SysFont("Courier New", 13)
    title = font_big.render("◈ AIR DEFENSE COMMAND", True, config.RADAR_GREEN)
    screen.blit(title, (20, 15))
    status = font_small.render("SYSTEM STATUS: ONLINE  |  RADAR: ACTIVE",
                                True, config.DIM_GREEN)
    screen.blit(status, (20, 42))
    angle_txt = font_small.render(
        f"SWEEP: {sweep_angle:06.2f}°", True, config.HUD_AMBER)
    screen.blit(angle_txt, (20, config.SCREEN_HEIGHT - 30))

# ── Main loop ────────────────────────────────────────────────

def main():
    global sweep_angle

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        sweep_angle = (sweep_angle + config.SWEEP_SPEED) % 360

        draw_background()
        draw_range_rings()
        draw_crosshairs()
        draw_outer_ring()
        draw_protected_zone()
        draw_sweep(sweep_angle)
        draw_hud_frame()

        pygame.display.flip()
        clock.tick(config.FPS)

if __name__ == "__main__":
    main()