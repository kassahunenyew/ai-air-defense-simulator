# main.py
# ============================================================
# ENTRY POINT — game loop lives here
# ============================================================

import pygame
import sys
import math
import config
from simulation.missile import Missile
from ai.threat_scorer import rank_threats

# ── Init ────────────────────────────────────────────────────
pygame.init()
screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
pygame.display.set_caption(config.TITLE)
clock  = pygame.time.Clock()

# ── State ────────────────────────────────────────────────────
sweep_angle   = 0.0
missiles      = []
spawn_timer   = 0
ranked        = []     # threat ranking updated each frame
font_small    = pygame.font.SysFont("Courier New", 13)
font_big      = pygame.font.SysFont("Courier New", 20, bold=True)
font_med      = pygame.font.SysFont("Courier New", 15, bold=True)

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

def threat_color(score):
    """Return color based on threat score: green → amber → red."""
    if score > 0.7:
        return config.THREAT_RED
    elif score > 0.4:
        return config.HUD_AMBER
    else:
        return config.RADAR_GREEN

def draw_missiles(ranked_list):
    """Draw missiles — color coded by threat level."""
    for i, (m, score, tti) in enumerate(ranked_list):
        if not m.alive:
            continue

        color = threat_color(score)

        # -- draw trail --
        for j, (tx, ty) in enumerate(m.trail):
            alpha = int(180 * j / max(len(m.trail), 1))
            trail_col = (min(alpha, 255), 0, 0)
            pygame.draw.circle(screen, trail_col,
                               (int(tx), int(ty)), 2)

        # -- draw missile --
        pygame.draw.circle(screen, color, (int(m.x), int(m.y)), 5)

        # -- priority ring on #1 threat --
        if i == 0:
            pygame.draw.circle(screen, config.THREAT_RED,
                               (int(m.x), int(m.y)), 12, 1)

        # -- label --
        label = font_small.render(f"TGT-{m.id}", True, color)
        screen.blit(label, (int(m.x) + 8, int(m.y) - 8))

def draw_predicted_paths(missile_list):
    """Draw Kalman predicted path for each missile."""
    for m in missile_list:
        if not m.alive or not m.predicted_path:
            continue
        for i, (px, py) in enumerate(m.predicted_path):
            alpha = int(180 * (1 - i / len(m.predicted_path)))
            color = (alpha, alpha, 0)
            pygame.draw.circle(screen, color,
                               (int(px), int(py)), 1)

def draw_threat_panel(ranked_list):
    """Draw threat priority panel on the right side."""
    panel_x = config.SCREEN_WIDTH - 280
    panel_y = 20

    # panel header
    header = font_med.render("◈ THREAT ASSESSMENT", True, config.RADAR_GREEN)
    screen.blit(header, (panel_x, panel_y))
    pygame.draw.line(screen, config.DIM_GREEN,
                     (panel_x, panel_y + 22),
                     (panel_x + 260, panel_y + 22), 1)

    if not ranked_list:
        no_threat = font_small.render("NO ACTIVE THREATS",
                                       True, config.DIM_GREEN)
        screen.blit(no_threat, (panel_x, panel_y + 35))
        return

    for i, (m, score, tti) in enumerate(ranked_list[:6]):
        y = panel_y + 35 + i * 55
        color = threat_color(score)

        # target ID + priority
        priority = ["◉ PRIORITY-1", "◎ PRIORITY-2",
                    "○ PRIORITY-3", "○ PRIORITY-4",
                    "○ PRIORITY-5", "○ PRIORITY-6"]
        pri_label = font_small.render(
            priority[i] if i < len(priority) else f"○ PRIORITY-{i+1}",
            True, color)
        screen.blit(pri_label, (panel_x, y))

        # target ID
        id_label = font_small.render(f"  TGT-{m.id}", True, color)
        screen.blit(id_label, (panel_x, y + 14))

        # threat score bar
        bar_w = int(200 * score)
        pygame.draw.rect(screen, config.GRID_COLOR,
                         (panel_x, y + 28, 200, 8))
        pygame.draw.rect(screen, color,
                         (panel_x, y + 28, bar_w, 8))

        # score + TTI
        info = font_small.render(
            f"  SCORE:{score:.2f}  TTI:{int(tti)}f",
            True, config.DIM_GREEN)
        screen.blit(info, (panel_x, y + 38))

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
    global sweep_angle, spawn_timer, ranked

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

        # -- rank threats --
        ranked = rank_threats(missiles)

        # -- update sweep --
        sweep_angle = (sweep_angle + config.SWEEP_SPEED) % 360

        # -- draw everything --
        draw_background()
        draw_range_rings()
        draw_crosshairs()
        draw_outer_ring()
        draw_protected_zone()
        draw_sweep(sweep_angle)
        draw_predicted_paths(missiles)
        draw_missiles(ranked)
        draw_threat_panel(ranked)
        draw_hud_frame(missiles)

        pygame.display.flip()
        clock.tick(config.FPS)

if __name__ == "__main__":
    main()