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
from ai.interceptor_ai import InterceptorAI

# ── Init ────────────────────────────────────────────────────
pygame.init()
screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
pygame.display.set_caption(config.TITLE)
clock  = pygame.time.Clock()

# ── State ────────────────────────────────────────────────────
sweep_angle    = 0.0
missiles       = []
spawn_timer    = 0
ranked         = []
interceptor_ai = InterceptorAI()
explosions     = []
font_small     = pygame.font.SysFont("Courier New", 13)
font_big       = pygame.font.SysFont("Courier New", 20, bold=True)
font_med       = pygame.font.SysFont("Courier New", 15, bold=True)

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
    if score > 0.7:
        return config.THREAT_RED
    elif score > 0.4:
        return config.HUD_AMBER
    else:
        return config.RADAR_GREEN

def draw_missile_shape(surface, x, y, vx, vy, color,
                       size=14, is_interceptor=False):
    """
    Draw a realistic missile shape with:
    - Long cylindrical body
    - Sharp nose cone
    - Swept tail fins
    - Engine flame
    """
    angle = math.atan2(vy, vx)
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    def rot(px, py):
        """Rotate and translate point to world space."""
        return (
            px * cos_a - py * sin_a + x,
            px * sin_a + py * cos_a + y
        )

    body_len = size * 2.4
    body_w   = size * 0.32

    # ── BODY ────────────────────────────────────────────────
    body = [
        rot(-body_len * 0.35, -body_w),
        rot( body_len * 0.55, -body_w),
        rot( body_len * 0.55,  body_w),
        rot(-body_len * 0.35,  body_w),
    ]
    pygame.draw.polygon(surface, color, body)
    pygame.draw.polygon(surface, (255, 255, 255), body, 1)

    # ── NOSE CONE ───────────────────────────────────────────
    nose_color = (255, 255, 255) if not is_interceptor else (180, 230, 255)
    nose = [
        rot(body_len * 0.55, -body_w),
        rot(body_len * 1.15,  0),
        rot(body_len * 0.55,  body_w),
    ]
    pygame.draw.polygon(surface, nose_color, nose)
    pygame.draw.polygon(surface, (200, 200, 200), nose, 1)

    # ── WING FINS (mid body, small) ─────────────────────────
    wing_color = (180, 180, 180) if not is_interceptor else (100, 180, 255)
    wing_top = [
        rot( body_len * 0.2, -body_w),
        rot( body_len * 0.0, -body_w * 3.5),
        rot(-body_len * 0.1, -body_w),
    ]
    wing_bot = [
        rot( body_len * 0.2,  body_w),
        rot( body_len * 0.0,  body_w * 3.5),
        rot(-body_len * 0.1,  body_w),
    ]
    pygame.draw.polygon(surface, wing_color, wing_top)
    pygame.draw.polygon(surface, wing_color, wing_bot)
    pygame.draw.polygon(surface, (255,255,255), wing_top, 1)
    pygame.draw.polygon(surface, (255,255,255), wing_bot, 1)

    # ── TAIL FINS (swept back) ───────────────────────────────
    fin_color = (200, 200, 200) if not is_interceptor else (80, 160, 255)
    tail_top = [
        rot(-body_len * 0.35, -body_w),
        rot(-body_len * 0.35 - size * 0.7, -body_w * 3.2),
        rot(-body_len * 0.10, -body_w),
    ]
    tail_bot = [
        rot(-body_len * 0.35,  body_w),
        rot(-body_len * 0.35 - size * 0.7,  body_w * 3.2),
        rot(-body_len * 0.10,  body_w),
    ]
    pygame.draw.polygon(surface, fin_color, tail_top)
    pygame.draw.polygon(surface, fin_color, tail_bot)
    pygame.draw.polygon(surface, (255,255,255), tail_top, 1)
    pygame.draw.polygon(surface, (255,255,255), tail_bot, 1)

    # ── ENGINE FLAME ────────────────────────────────────────
    flame_layers = [
        (size * 0.55, (255, 220, 80)),   # outer flame — yellow
        (size * 0.38, (255, 120, 20)),   # mid flame   — orange
        (size * 0.20, (255, 60,  0)),    # core flame  — red
    ]
    for fl, fc in flame_layers:
        flame = [
            rot(-body_len * 0.35, -body_w * 0.5),
            rot(-body_len * 0.35 - fl, 0),
            rot(-body_len * 0.35,  body_w * 0.5),
        ]
        pygame.draw.polygon(surface, fc, flame)

def draw_missiles(ranked_list):
    for i, (m, score, tti) in enumerate(ranked_list):
        if not m.alive:
            continue
        color = threat_color(score)

        # -- fading red trail --
        for j, (tx, ty) in enumerate(m.trail):
            alpha = int(180 * j / max(len(m.trail), 1))
            pygame.draw.circle(screen, (min(alpha, 255), 0, 0),
                               (int(tx), int(ty)), 2)

        # -- priority ring on #1 threat --
        if i == 0:
            pygame.draw.circle(screen, config.THREAT_RED,
                               (int(m.x), int(m.y)), 20, 1)

        # -- realistic missile shape --
        draw_missile_shape(screen, m.x, m.y, m.vx, m.vy,
                           color, size=12, is_interceptor=False)

        # -- label --
        label = font_small.render(f"TGT-{m.id}", True, color)
        screen.blit(label, (int(m.x) + 18, int(m.y) - 8))

def draw_interceptors(inc_list):
    for inc in inc_list:
        if not inc.alive:
            continue

        # -- fading blue trail --
        for j, (tx, ty) in enumerate(inc.trail):
            alpha = int(200 * j / max(len(inc.trail), 1))
            pygame.draw.circle(screen,
                               (0, int(alpha * 0.5), min(alpha, 255)),
                               (int(tx), int(ty)), 2)

        # -- realistic interceptor shape --
        draw_missile_shape(screen, inc.x, inc.y,
                           inc.vx, inc.vy,
                           config.INTERCEPT_BLU, size=14,
                           is_interceptor=True)

        # -- label --
        label = font_small.render(f"INT-{inc.id}",
                                   True, config.INTERCEPT_BLU)
        screen.blit(label, (int(inc.x) + 18, int(inc.y) - 8))

def draw_predicted_paths(missile_list):
    for m in missile_list:
        if not m.alive or not m.predicted_path:
            continue
        for i, (px, py) in enumerate(m.predicted_path):
            alpha = int(180 * (1 - i / len(m.predicted_path)))
            pygame.draw.circle(screen, (alpha, alpha, 0),
                               (int(px), int(py)), 1)

def draw_explosions(explosion_list):
    for exp in explosion_list:
        x, y, timer = exp
        radius = int((30 - timer) * 2.5)
        pygame.draw.circle(screen, (255, 200, 50),
                           (int(x), int(y)), max(radius, 1), 2)
        pygame.draw.circle(screen, (255, 100, 0),
                           (int(x), int(y)), max(radius - 5, 1), 1)
        pygame.draw.circle(screen, (255, 255, 255),
                           (int(x), int(y)), max(radius - 10, 1), 1)

def draw_threat_panel(ranked_list):
    panel_x = config.SCREEN_WIDTH - 280
    panel_y = 20
    screen.blit(font_med.render("◈ THREAT ASSESSMENT",
                True, config.RADAR_GREEN), (panel_x, panel_y))
    pygame.draw.line(screen, config.DIM_GREEN,
                     (panel_x, panel_y + 22),
                     (panel_x + 260, panel_y + 22), 1)
    if not ranked_list:
        screen.blit(font_small.render("NO ACTIVE THREATS",
                    True, config.DIM_GREEN), (panel_x, panel_y + 35))
        return
    for i, (m, score, tti) in enumerate(ranked_list[:5]):
        y     = panel_y + 35 + i * 55
        color = threat_color(score)
        pri   = ["◉ PRIORITY-1", "◎ PRIORITY-2", "○ PRIORITY-3",
                 "○ PRIORITY-4", "○ PRIORITY-5"]
        screen.blit(font_small.render(
            pri[i], True, color), (panel_x, y))
        screen.blit(font_small.render(
            f"  TGT-{m.id}", True, color), (panel_x, y + 14))
        pygame.draw.rect(screen, config.GRID_COLOR,
                         (panel_x, y + 28, 200, 8))
        pygame.draw.rect(screen, color,
                         (panel_x, y + 28, int(200 * score), 8))
        screen.blit(font_small.render(
            f"  SCORE:{score:.2f}  TTI:{int(tti)}f",
            True, config.DIM_GREEN), (panel_x, y + 38))

def draw_stats_panel(stats):
    panel_x = config.SCREEN_WIDTH - 280
    panel_y = config.SCREEN_HEIGHT - 120
    screen.blit(font_med.render("◈ INTERCEPT STATS",
                True, config.RADAR_GREEN), (panel_x, panel_y))
    pygame.draw.line(screen, config.DIM_GREEN,
                     (panel_x, panel_y + 22),
                     (panel_x + 260, panel_y + 22), 1)
    screen.blit(font_small.render(
        f"INTERCEPTORS ACTIVE : {stats['active']}",
        True, config.INTERCEPT_BLU), (panel_x, panel_y + 30))
    screen.blit(font_small.render(
        f"SUCCESSFUL HITS     : {stats['hits']}",
        True, config.RADAR_GREEN), (panel_x, panel_y + 48))
    screen.blit(font_small.render(
        f"MISSED              : {stats['misses']}",
        True, config.HUD_AMBER), (panel_x, panel_y + 66))

def draw_hud_frame(missile_list):
    screen.blit(font_big.render(
        "◈ AIR DEFENSE COMMAND", True, config.RADAR_GREEN), (20, 15))
    screen.blit(font_small.render(
        "SYSTEM STATUS: ONLINE  |  RADAR: ACTIVE",
        True, config.DIM_GREEN), (20, 42))
    active = sum(1 for m in missile_list if m.alive)
    screen.blit(font_small.render(
        f"ACTIVE THREATS: {active}",
        True, config.HUD_AMBER), (20, 65))
    screen.blit(font_small.render(
        f"SWEEP: {sweep_angle:06.2f}°",
        True, config.HUD_AMBER), (20, config.SCREEN_HEIGHT - 30))

# ── Main loop ────────────────────────────────────────────────

def main():
    global sweep_angle, spawn_timer, ranked, explosions

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
            for _ in range(config.MISSILE_SPAWN_COUNT):
                missiles.append(Missile())
            spawn_timer = 0

        # -- update missiles --
        for m in missiles:
            m.update()

        # -- rank threats --
        ranked = rank_threats(missiles)

        # -- run interceptor AI --
        interceptor_ai.update(ranked)

        # -- detect hits and spawn explosions --
        for inc in interceptor_ai.interceptors:
            if inc.hit:
                explosions.append([inc.x, inc.y, 30])

        # -- update explosions --
        explosions = [[x, y, t-1] for x, y, t in explosions if t > 0]

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
        draw_predicted_paths(missiles)
        draw_missiles(ranked)
        draw_interceptors(interceptor_ai.interceptors)
        draw_explosions(explosions)
        draw_threat_panel(ranked)
        draw_stats_panel(interceptor_ai.get_stats())
        draw_hud_frame(missiles)

        pygame.display.flip()
        clock.tick(config.FPS)

if __name__ == "__main__":
    main()