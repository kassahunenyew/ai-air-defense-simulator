# main.py
# ============================================================
# ENTRY POINT — game loop lives here
# ============================================================

import pygame
import sys
import math
import config
from simulation.missile import Missile

# ── Init ────────────────────────────────────────────────────
pygame.init()
screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
pygame.display.set_caption(config.TITLE)
clock  = pygame.time.Clock()

# ── State ────────────────────────────────────────────────────
sweep_angle  = 0.0
missiles     = []
spawn_timer  = 0
font_small   = pygame.font.SysFont("Courier New", 13)
font_big     = pygame.font.SysFont("Courier New", 20, bold=True)

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
    label = font_small.render("PROTECTED", True, config.THREAT_RED)
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
    for i in range(30):
        trail_angle = math.radians(angle_deg - i)
        alpha       = int(120 * (1 - i / 30))
        color       = (0, alpha, int(alpha * 0.3))
        ex = cx + config.RADAR_RADIUS * math.cos(trail_angle)
        ey = cy + config.RADAR_RADIUS * math.sin(trail_angle)
        pygame.draw.line(screen, color,
                         (cx, cy), (int(ex), int(ey)), 1)

def draw_missiles(missile_list):
    """Draw each missile as a red dot with a fading trail."""
    for m in missile_list:
        if not m.alive:
            continue
        # -- draw trail --
        for i, (tx, ty) in enumerate(m.trail):
            alpha = int(180 * i / len(m.trail))
            color = (alpha, 0, 0)
            pygame.draw.circle(screen, color, (int(tx), int(ty)), 2)
        # -- draw missile dot --
        pygame.draw.circle(screen, config.THREAT_RED,
                           (int(m.x), int(m.y)), 5)
        # -- draw ID label --
        label = font_small.render(f"TGT-{m.id}", True, config.THREAT_RED)
        screen.blit(label, (int(m.x) + 8, int(m.y) - 8))

def draw_predicted_paths(missile_list):
    """Draw Kalman Filter predicted trajectory for each missile."""
    for m in missile_list:
        if not m.alive or not m.predicted_path:
            continue
        for i, (px, py) in enumerate(m.predicted_path):
            alpha = int(180 * (1 - i / len(m.predicted_path)))
            color = (alpha, alpha, 0)   # yellow fading to black
            pygame.draw.circle(screen, color,
                               (int(px), int(py)), 1)

def draw_hud_frame(missile_list):
    title = font_big.render("◈ AIR DEFENSE COMMAND", True, config.RADAR_GREEN)
    screen.blit(title, (20, 15))
    status = font_small.render("SYSTEM STATUS: ONLINE  |  RADAR: ACTIVE",
                                True, config.DIM_GREEN)
    screen.blit(status, (20, 42))
    active = sum(1 for m in missile_list if m.alive)
    threat = font_small.render(f"ACTIVE THREATS: {active}",
                                True, config.HUD_AMBER)
    screen.blit(threat, (20, 65))
    angle_txt = font_small.render(
        f"SWEEP: {sweep_angle:06.2f}°", True, config.HUD_AMBER)
    screen.blit(angle_txt, (20, config.SCREEN_HEIGHT - 30))

# ── Main loop ────────────────────────────────────────────────

def main():
    global sweep_angle, spawn_timer

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        # -- spawn missiles --
        spawn_timer += 1
        if spawn_timer >= config.MISSILE_SPAWN_RATE:
            missiles.append(Missile())
            spawn_timer = 0

        # -- update missiles --
        for m in missiles:
            m.update()

        # -- remove dead missiles --
        missiles[:] = [m for m in missiles if m.alive]

        # -- update sweep --
        sweep_angle = (sweep_angle + config.SWEEP_SPEED) % 360

        # -- draw everything --
        draw_background()
        draw_range_rings()
        draw_crosshairs()
        draw_outer_ring()
        draw_protected_zone()
        draw_sweep(sweep_angle)
        draw_missiles(missiles)
        draw_predicted_paths(missiles)    # ← Kalman paths added here
        draw_hud_frame(missiles)

        pygame.display.flip()
        clock.tick(config.FPS)

if __name__ == "__main__":
    main()