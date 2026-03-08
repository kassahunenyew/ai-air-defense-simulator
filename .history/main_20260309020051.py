# main.py
# ============================================================
# ENTRY POINT — WITH BATTLE REPLAY SYSTEM
# R = start/stop recording
# P = play last replay
# SPACE = pause replay
# LEFT/RIGHT = scrub replay
# ============================================================

import pygame
import sys
import math
import random
import config
from simulation.missile import Missile
from ai.threat_scorer import rank_threats
from ai.interceptor_ai import InterceptorAI
from visualization.sound_manager import SoundManager
from data.replay_logger import ReplayLogger, ReplayPlayer

pygame.init()
screen = pygame.display.set_mode((1400, 860))
pygame.display.set_caption(config.TITLE)
clock  = pygame.time.Clock()

RADAR_CENTER = config.RADAR_CENTER
RADAR_RADIUS = config.RADAR_RADIUS

sweep_angle    = 0.0
missiles       = []
spawn_timer    = 0
ranked         = []
interceptor_ai = InterceptorAI()
explosions     = []
particles      = []
frame_count    = 0

font_small  = pygame.font.SysFont("Courier New", 13)
font_big    = pygame.font.SysFont("Courier New", 20, bold=True)
font_med    = pygame.font.SysFont("Courier New", 15, bold=True)
font_title  = pygame.font.SysFont("Courier New", 24, bold=True)
sound       = SoundManager()

# replay system
logger = ReplayLogger()
player = ReplayPlayer(logger)

# ── Helpers ──────────────────────────────────────────────────

def spawn_explosion(x, y):
    explosions.append([x, y, 90, 90])
    for _ in range(30):
        angle = random.uniform(0, 2*math.pi)
        speed = random.uniform(2.0, 7.0)
        color = random.choice([
            (255,220,80),(255,120,20),(255,60,0),
            (255,255,200),(200,200,255),(255,255,255),
        ])
        particles.append([
            x, y,
            math.cos(angle)*speed,
            math.sin(angle)*speed,
            random.randint(40,70), color
        ])

# ── Core radar ────────────────────────────────────────────────

def draw_background():
    screen.fill(config.BLACK)

def draw_range_rings():
    cx, cy = RADAR_CENTER
    for i in range(1, 5):
        r = int(RADAR_RADIUS * i / 4)
        pygame.draw.circle(screen, config.GRID_COLOR,
                           (cx,cy), r, 1)
        label = font_small.render(f"{i*25}km",
                                  True, config.GRID_COLOR)
        screen.blit(label, (cx+r-28, cy+4))

def draw_crosshairs():
    cx, cy = RADAR_CENTER
    pygame.draw.line(screen, config.GRID_COLOR,
                     (cx-RADAR_RADIUS,cy),
                     (cx+RADAR_RADIUS,cy), 1)
    pygame.draw.line(screen, config.GRID_COLOR,
                     (cx,cy-RADAR_RADIUS),
                     (cx,cy+RADAR_RADIUS), 1)

def draw_outer_ring():
    pygame.draw.circle(screen, config.DIM_GREEN,
                       RADAR_CENTER, RADAR_RADIUS, 2)

def draw_protected_zone():
    pygame.draw.circle(screen, config.THREAT_RED,
                       RADAR_CENTER,
                       config.PROTECTED_RADIUS, 2)
    label = font_small.render("PROTECTED",
                               True, config.THREAT_RED)
    cx, cy = RADAR_CENTER
    screen.blit(label,
                (cx - label.get_width()//2,
                 cy + config.PROTECTED_RADIUS + 4))

def draw_sweep(angle_deg):
    cx, cy    = RADAR_CENTER
    angle_rad = math.radians(angle_deg)
    end_x = cx + RADAR_RADIUS * math.cos(angle_rad)
    end_y = cy + RADAR_RADIUS * math.sin(angle_rad)
    pygame.draw.line(screen, config.SWEEP_COLOR,
                     (cx,cy), (int(end_x),int(end_y)), 2)
    for i in range(30):
        trail_angle = math.radians(angle_deg - i)
        alpha       = int(120 * (1 - i/30))
        color       = (0, alpha, int(alpha*0.3))
        ex = cx + RADAR_RADIUS * math.cos(trail_angle)
        ey = cy + RADAR_RADIUS * math.sin(trail_angle)
        pygame.draw.line(screen, color,
                         (cx,cy), (int(ex),int(ey)), 1)

# ── Missile shape ─────────────────────────────────────────────

def draw_missile_shape(surface, x, y, vx, vy, color,
                       size=14, is_interceptor=False):
    angle = math.atan2(vy, vx)
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    def rot(px, py):
        return (px*cos_a - py*sin_a + x,
                px*sin_a + py*cos_a + y)

    body_len = size * 3.2
    body_w   = size * 0.22

    body = [rot(-body_len*0.30,-body_w),
            rot( body_len*0.58,-body_w),
            rot( body_len*0.58, body_w),
            rot(-body_len*0.30, body_w)]
    pygame.draw.polygon(surface, color, body)
    pygame.draw.polygon(surface, (255,255,255), body, 1)

    nose_color = (255,255,255) if not is_interceptor \
                 else (180,230,255)
    nose = [rot(body_len*0.58,-body_w*0.8),
            rot(body_len*1.25, 0),
            rot(body_len*0.58, body_w*0.8)]
    pygame.draw.polygon(surface, nose_color, nose)

    canard_color = (160,160,160) if not is_interceptor \
                   else (80,160,255)
    for sign in [-1,1]:
        canard = [rot(body_len*0.35, sign*body_w),
                  rot(body_len*0.20, sign*body_w*4.0),
                  rot(body_len*0.10, sign*body_w)]
        pygame.draw.polygon(surface, canard_color, canard)

    fin_color = (200,200,200) if not is_interceptor \
                else (60,140,255)
    for sign in [-1,1]:
        tail = [rot(-body_len*0.30,  sign*body_w),
                rot(-body_len*0.30 - size*1.1,
                    sign*body_w*4.5),
                rot(-body_len*0.05,  sign*body_w)]
        pygame.draw.polygon(surface, fin_color, tail)
        pygame.draw.polygon(surface, (255,255,255), tail, 1)

    for fl, fc in [(size*0.9,(255,220,80)),
                   (size*0.6,(255,120,20)),
                   (size*0.35,(255,60,0))]:
        flame = [rot(-body_len*0.30,-body_w*0.6),
                 rot(-body_len*0.30-fl, 0),
                 rot(-body_len*0.30, body_w*0.6)]
        pygame.draw.polygon(surface, fc, flame)

# ── Tactical HUD ──────────────────────────────────────────────

def draw_target_diamond(x, y, size, color, frame,
                        is_locked=False):
    x, y = int(x), int(y)
    if is_locked:
        pulse = math.sin(frame * 0.12) * 4
        size  = int(size + pulse)
    points = [(x, y-size),(x+size,y),
              (x, y+size),(x-size, y)]
    pygame.draw.polygon(screen, color, points, 1)
    if is_locked:
        s2 = max(4, size//2)
        inner = [(x,y-s2),(x+s2,y),(x,y+s2),(x-s2,y)]
        pygame.draw.polygon(screen, color, inner, 1)
        pygame.draw.circle(screen, color, (x,y), 2)

def draw_threat_cone(missile, color, alpha_mult=0.4):
    if not missile.alive:
        return
    speed = math.hypot(missile.vx, missile.vy)
    if speed < 0.01:
        return
    angle   = math.atan2(missile.vy, missile.vx)
    length  = 40 + speed * 20
    spread  = math.radians(18)
    tip_x, tip_y = missile.x, missile.y
    left_x  = tip_x + length * math.cos(angle - spread)
    left_y  = tip_y + length * math.sin(angle - spread)
    right_x = tip_x + length * math.cos(angle + spread)
    right_y = tip_y + length * math.sin(angle + spread)
    cone_surf = pygame.Surface((1400,860), pygame.SRCALPHA)
    r,g,b = color
    pygame.draw.polygon(cone_surf, (r,g,b,int(20*alpha_mult)),
                        [(int(tip_x),int(tip_y)),
                         (int(left_x),int(left_y)),
                         (int(right_x),int(right_y))])
    screen.blit(cone_surf, (0,0))
    pygame.draw.line(screen, color,
                     (int(tip_x),int(tip_y)),
                     (int(left_x),int(left_y)), 1)
    pygame.draw.line(screen, color,
                     (int(tip_x),int(tip_y)),
                     (int(right_x),int(right_y)), 1)

def draw_intercept_prediction(interceptor):
    if not interceptor.alive or not interceptor.target:
        return
    if not interceptor.target.alive:
        return
    inc = interceptor
    tgt = interceptor.target
    dx      = tgt.x - inc.x
    dy      = tgt.y - inc.y
    dist    = math.hypot(dx, dy)
    t_steps = min(dist / max(config.INTERCEPTOR_SPEED,
                              0.1), 60)
    pred_x  = tgt.x + tgt.vx * t_steps
    pred_y  = tgt.y + tgt.vy * t_steps
    cross   = 8
    color   = (100, 255, 100)
    pygame.draw.line(screen, color,
                     (int(pred_x-cross),int(pred_y-cross)),
                     (int(pred_x+cross),int(pred_y+cross)),1)
    pygame.draw.line(screen, color,
                     (int(pred_x+cross),int(pred_y-cross)),
                     (int(pred_x-cross),int(pred_y+cross)),1)
    pygame.draw.circle(screen, color,
                       (int(pred_x),int(pred_y)), cross+3, 1)
    steps = 12
    for s in range(steps):
        t0  = s/steps
        t1  = (s+0.5)/steps
        lx0 = inc.x + (pred_x-inc.x)*t0
        ly0 = inc.y + (pred_y-inc.y)*t0
        lx1 = inc.x + (pred_x-inc.x)*t1
        ly1 = inc.y + (pred_y-inc.y)*t1
        a   = int(180*(1-s/steps))
        pygame.draw.line(screen, (0,a//2,a),
                         (int(lx0),int(ly0)),
                         (int(lx1),int(ly1)), 1)

def draw_engagement_lines(interceptors):
    for inc in interceptors:
        if not inc.alive or not inc.target:
            continue
        if not inc.target.alive:
            continue
        x0,y0 = int(inc.x), int(inc.y)
        x1,y1 = int(inc.target.x), int(inc.target.y)
        pygame.draw.line(screen,(0,40,80),(x0,y0),(x1,y1),3)
        pygame.draw.line(screen,(0,100,200),(x0,y0),(x1,y1),1)

def draw_lock_rings(missile, frame, color):
    x, y  = int(missile.x), int(missile.y)
    pulse = abs(math.sin(frame * 0.08))
    for ring_i, base_r in enumerate([18,26,36]):
        r     = int(base_r + pulse*6)
        alpha = int(180*(1-ring_i*0.3)*pulse)
        if alpha < 10:
            continue
        surf  = pygame.Surface((1400,860), pygame.SRCALPHA)
        rc,gc,bc = color
        pygame.draw.circle(surf,(rc,gc,bc,alpha),(x,y),r,1)
        screen.blit(surf,(0,0))

# ── Draw missiles / interceptors ─────────────────────────────

def draw_missiles(ranked_list, frame):
    for i, (m, score, tti) in enumerate(ranked_list):
        if not m.alive or not m.is_visible_on_radar():
            continue
        prob       = getattr(m,'detection_prob',1.0)
        base_color = m.get_type_color()
        draw_threat_cone(m, base_color,
                         0.6 if i==0 else 0.25)

    for i, (m, score, tti) in enumerate(ranked_list):
        if not m.alive or not m.is_visible_on_radar():
            continue
        base_color = m.get_type_color()
        prob       = getattr(m,'detection_prob',1.0)
        brightness = max(0.3, prob)
        color      = tuple(int(c*brightness)
                           for c in base_color)

        for j, (tx,ty) in enumerate(m.trail):
            alpha = int(180*j/max(len(m.trail),1))
            tc    = (int(min(alpha,255)*max(0.2,prob)),0,0)
            pygame.draw.circle(screen,tc,(int(tx),int(ty)),2)

        if i == 0:
            draw_lock_rings(m, frame, base_color)

        draw_missile_shape(screen, m.x, m.y,
                           m.vx, m.vy, color,
                           size=11, is_interceptor=False)

        is_locked     = (i == 0)
        bracket_color = (255,255,100) if is_locked \
                        else base_color
        bracket_size  = 22 if is_locked else 16
        draw_target_diamond(m.x, m.y, bracket_size,
                            bracket_color, frame, is_locked)

        type_short = {"BALLISTIC":"BAL",
                      "EVASIVE":  "EVA",
                      "STEALTH":  "STL"}
        t = type_short.get(m.type,"UNK")
        if m.type == "STEALTH":
            lbl = font_small.render(
                f"TGT-{m.id}[{t}]{prob*100:.0f}%",
                True, color)
        else:
            lbl = font_small.render(
                f"TGT-{m.id} [{t}]", True, color)
        screen.blit(lbl,(int(m.x)+20,int(m.y)-8))

def draw_interceptors(inc_list, frame):
    draw_engagement_lines(inc_list)
    for inc in inc_list:
        draw_intercept_prediction(inc)
    for inc in inc_list:
        if not inc.alive:
            continue
        for j,(tx,ty) in enumerate(inc.trail):
            alpha = int(200*j/max(len(inc.trail),1))
            pygame.draw.circle(screen,
                               (0,int(alpha*0.5),
                                min(alpha,255)),
                               (int(tx),int(ty)),2)
        draw_missile_shape(screen,inc.x,inc.y,
                           inc.vx,inc.vy,
                           config.INTERCEPT_BLU,
                           size=13,is_interceptor=True)
        draw_target_diamond(inc.x,inc.y,14,
                            config.INTERCEPT_BLU,
                            frame,is_locked=False)
        lbl = font_small.render(f"INT-{inc.id}",
                                 True,config.INTERCEPT_BLU)
        screen.blit(lbl,(int(inc.x)+20,int(inc.y)-8))

# ── Predictions ───────────────────────────────────────────────

def draw_predicted_paths(missile_list):
    for m in missile_list:
        if not m.alive or not m.predicted_path:
            continue
        if not m.is_visible_on_radar():
            continue
        for i,(px,py) in enumerate(m.predicted_path):
            alpha = int(180*(1-i/len(m.predicted_path)))
            pygame.draw.circle(screen,(alpha,alpha,0),
                               (int(px),int(py)),1)

def draw_lstm_paths(missile_list):
    for m in missile_list:
        if not m.alive or not m.lstm_predicted_path:
            continue
        if not m.is_visible_on_radar():
            continue
        for i,(px,py) in enumerate(m.lstm_predicted_path):
            alpha = int(200*(1-i/
                             len(m.lstm_predicted_path)))
            pygame.draw.circle(screen,(0,alpha,alpha),
                               (int(px),int(py)),1)

# ── Explosions ────────────────────────────────────────────────

def draw_explosions_and_particles():
    for exp in explosions:
        x,y,timer,max_t = exp
        if timer > max_t*0.88:
            flash = pygame.Surface((1400,860),
                                   pygame.SRCALPHA)
            flash.fill((255,200,50,45))
            screen.blit(flash,(0,0))
    for exp in explosions:
        x,y,timer,max_t = exp
        progress = 1.0-(timer/max_t)
        for radius,color,width in [
            (80,(255,200,50),3),(55,(255,100,0),2),
            (45,(255,60,0),1), (30,(255,255,200),0)]:
            r = int(progress*radius)
            if r>1:
                if width==0:
                    pygame.draw.circle(screen,color,
                                       (int(x),int(y)),r)
                else:
                    pygame.draw.circle(screen,color,
                                       (int(x),int(y)),r,width)
        if timer > max_t*0.5:
            txt = font_med.render("✦ INTERCEPT",
                                  True,(255,255,100))
            screen.blit(txt,(int(x)-52,int(y)-52))
    for p in particles:
        size = max(1,int(p[4]/15))
        pygame.draw.circle(screen,p[5],
                           (int(p[0]),int(p[1])),size)
        pygame.draw.line(screen,p[5],
                         (int(p[0]),int(p[1])),
                         (int(p[0]-p[2]*2),
                          int(p[1]-p[3]*2)),1)

# ── Replay drawing ────────────────────────────────────────────

def draw_replay_frame(frame_data, frame_num):
    """Draw a single replay frame from recorded data."""
    if not frame_data:
        return

    sweep = frame_data.get("sweep", 0)
    draw_sweep(sweep)

    # draw missiles from recorded state
    for m in frame_data.get("missiles", []):
        color = {
            "BALLISTIC": config.THREAT_RED,
            "EVASIVE":   (255,100,255),
            "STEALTH":   (100,200,100),
        }.get(m["type"], config.THREAT_RED)

        prob       = m.get("det", 1.0)
        brightness = max(0.3, prob)
        color      = tuple(int(c*brightness) for c in color)

        vx, vy = m["vx"], m["vy"]
        if abs(vx) < 0.001 and abs(vy) < 0.001:
            vx = 1.0
        draw_missile_shape(screen, m["x"], m["y"],
                           vx, vy, color,
                           size=11, is_interceptor=False)

        type_short = {"BALLISTIC":"BAL",
                      "EVASIVE":  "EVA",
                      "STEALTH":  "STL"}
        t   = type_short.get(m["type"],"UNK")
        lbl = font_small.render(
            f"TGT-{m['id']} [{t}]", True, color)
        screen.blit(lbl,(int(m["x"])+20,int(m["y"])-8))

    # draw interceptors from recorded state
    for inc in frame_data.get("interceptors", []):
        vx, vy = inc["vx"], inc["vy"]
        if abs(vx) < 0.001 and abs(vy) < 0.001:
            vx = 1.0
        draw_missile_shape(screen, inc["x"], inc["y"],
                           vx, vy,
                           config.INTERCEPT_BLU,
                           size=13, is_interceptor=True)
        lbl = font_small.render(
            f"INT-{inc['id']}",
            True, config.INTERCEPT_BLU)
        screen.blit(lbl,
                    (int(inc["x"])+20, int(inc["y"])-8))

    # draw events at this frame
    for evt in player.get_events_at_frame(frame_num):
        if evt["type"] == "explosion":
            pygame.draw.circle(screen,(255,200,50),
                               (int(evt["x"]),
                                int(evt["y"])),20,3)
            pygame.draw.circle(screen,(255,100,0),
                               (int(evt["x"]),
                                int(evt["y"])),12,2)
            txt = font_med.render("✦ INTERCEPT",
                                  True,(255,255,100))
            screen.blit(txt,(int(evt["x"])-52,
                             int(evt["y"])-52))


def draw_replay_hud():
    """Overlay shown during replay mode."""
    # top banner
    banner = pygame.Surface((1400,50), pygame.SRCALPHA)
    banner.fill((0,0,0,160))
    screen.blit(banner,(0,0))

    status = "⏸ PAUSED" if player.paused else "▶ REPLAYING"
    screen.blit(font_big.render(
        f"◉ REPLAY MODE  {status}",
        True,(255,200,0)),(20,14))

    # frame counter
    screen.blit(font_small.render(
        f"FRAME {player.frame_idx} / "
        f"{player.total_frames}",
        True,config.DIM_GREEN),(700,18))

    # speed
    screen.blit(font_small.render(
        f"SPEED: {player.speed:.1f}x  "
        f"[←→ SCRUB]  [SPACE PAUSE]  [ESC EXIT]",
        True,config.DIM_GREEN),(900,18))

    # progress bar
    bar_y  = 840
    bar_w  = 1360
    bar_x  = 20
    pygame.draw.rect(screen, config.GRID_COLOR,
                     (bar_x,bar_y,bar_w,12))
    fill_w = int(bar_w * player.progress)
    pygame.draw.rect(screen,(255,200,0),
                     (bar_x,bar_y,fill_w,12))
    pygame.draw.rect(screen,config.RADAR_GREEN,
                     (bar_x,bar_y,bar_w,12),1)

    # event markers on progress bar
    for evt in logger.events:
        if logger.total_frames > 0:
            ex = bar_x + int(bar_w * evt["frame"] /
                             logger.total_frames)
            color = (255,100,0) \
                if evt["type"]=="explosion" \
                else (0,150,255)
            pygame.draw.line(screen, color,
                             (ex,bar_y),(ex,bar_y+12),2)


def draw_recording_indicator(frame):
    """Blinking red dot when recording."""
    if not logger.recording:
        return
    if (frame // 30) % 2 == 0:
        pygame.draw.circle(screen,(255,0,0),(1370,25),8)
        screen.blit(font_small.render(
            "● REC",True,(255,0,0)),(1310,18))

# ── Panels ────────────────────────────────────────────────────

def draw_threat_panel(ranked_list):
    panel_x = 1090
    panel_y = 20
    screen.blit(font_med.render("◈ THREAT ASSESSMENT",
                True,config.RADAR_GREEN),(panel_x,panel_y))
    pygame.draw.line(screen,config.DIM_GREEN,
                     (panel_x,panel_y+22),
                     (panel_x+290,panel_y+22),1)
    if not ranked_list:
        screen.blit(font_small.render("NO ACTIVE THREATS",
                    True,config.DIM_GREEN),
                    (panel_x,panel_y+35))
        return
    for i,(m,score,tti) in enumerate(ranked_list[:5]):
        y     = panel_y+35+i*58
        color = m.get_type_color()
        pri   = ["◉ PRIORITY-1","◎ PRIORITY-2",
                 "○ PRIORITY-3","○ PRIORITY-4",
                 "○ PRIORITY-5"]
        screen.blit(font_small.render(pri[i],True,color),
                    (panel_x,y))
        screen.blit(font_small.render(
            f"  TGT-{m.id} [{m.type[:3]}]",True,color),
            (panel_x,y+15))
        pygame.draw.rect(screen,config.GRID_COLOR,
                         (panel_x,y+30,220,9))
        pygame.draw.rect(screen,color,
                         (panel_x,y+30,int(220*score),9))
        screen.blit(font_small.render(
            f"  SCORE:{score:.2f}  TTI:{int(tti)}f",
            True,config.DIM_GREEN),(panel_x,y+42))

def draw_bottom_dashboard(stats, missile_list):
    dash_y = 800
    dash_h = 58
    pygame.draw.rect(screen,(0,18,6),
                     (0,dash_y,1400,dash_h))
    pygame.draw.line(screen,config.RADAR_GREEN,
                     (0,dash_y),(1400,dash_y),1)
    active  = sum(1 for m in missile_list if m.alive)
    rl_rate = f"{stats.get('rl_rate',0)*100:.0f}%"
    cols = [
        ("ACTIVE THREATS",  str(active),
         config.THREAT_RED),
        ("INTERCEPTORS",    str(stats['active']),
         config.INTERCEPT_BLU),
        ("SUCCESSFUL HITS", str(stats['hits']),
         config.RADAR_GREEN),
        ("MISSED",          str(stats['misses']),
         config.HUD_AMBER),
        ("RL EPISODES",     str(stats.get('rl_eps',0)),
         (0,200,200)),
        ("RL WIN RATE",     rl_rate,
         (0,200,200)),
        ("SYSTEM STATUS",   "ONLINE",
         config.RADAR_GREEN),
    ]
    col_w = 1400//len(cols)
    for i,(label,value,color) in enumerate(cols):
        cx = i*col_w + col_w//2
        l  = font_small.render(label,True,config.DIM_GREEN)
        v  = font_med.render(value,True,color)
        screen.blit(l,(cx-l.get_width()//2,dash_y+8))
        screen.blit(v,(cx-v.get_width()//2,dash_y+26))
        if i>0:
            pygame.draw.line(screen,config.GRID_COLOR,
                             (i*col_w,dash_y+6),
                             (i*col_w,dash_y+dash_h-6),1)

def draw_left_panel():
    px,py = 15,70
    screen.blit(font_med.render("◈ SYSTEM STATUS",
                True,config.RADAR_GREEN),(px,py))
    pygame.draw.line(screen,config.DIM_GREEN,
                     (px,py+20),(px+200,py+20),1)
    lines = [
        ("RADAR",       "ACTIVE",    config.RADAR_GREEN),
        ("KALMAN AI",   "TRACKING",  config.RADAR_GREEN),
        ("LSTM AI",     "LEARNING",  (0,200,200)),
        ("THREAT AI",   "ONLINE",    config.RADAR_GREEN),
        ("RL AGENT",    "TRAINED",   (0,200,200)),
        ("HUNGARIAN",   "OPTIMAL",   (0,200,200)),
        ("RCS MODEL",   "ACTIVE",    config.RADAR_GREEN),
        ("TACTICAL HUD","ONLINE",    (255,200,0)),
        ("REPLAY",      "READY",     (255,200,0)),
        ("INTERCEPTOR", "ARMED",     config.INTERCEPT_BLU),
        ("PROTECTED",   "ZONE LIVE", config.THREAT_RED),
    ]
    for i,(k,v,c) in enumerate(lines):
        y = py+30+i*22
        screen.blit(font_small.render(
            f"  {k:<12}: ",True,config.DIM_GREEN),(px,y))
        screen.blit(font_small.render(v,True,c),
                    (px+140,y))

def draw_legend():
    px,py = 15,560
    screen.blit(font_small.render("◈ MISSILE TYPES",
                True,config.RADAR_GREEN),(px,py))
    pygame.draw.line(screen,config.DIM_GREEN,
                     (px,py+16),(px+200,py+16),1)
    for i,(label,color) in enumerate([
        ("● BALLISTIC",config.THREAT_RED),
        ("● EVASIVE",  (255,100,255)),
        ("● STEALTH",  (100,200,100)),
    ]):
        screen.blit(font_small.render(label,True,color),
                    (px,py+22+i*16))

    py2 = py+78
    screen.blit(font_small.render("◈ PREDICTIONS",
                True,config.RADAR_GREEN),(px,py2))
    pygame.draw.line(screen,config.DIM_GREEN,
                     (px,py2+16),(px+200,py2+16),1)
    screen.blit(font_small.render(
        "── KALMAN (yellow)",True,(180,180,0)),(px,py2+22))
    screen.blit(font_small.render(
        "── LSTM   (cyan)",  True,(0,180,180)), (px,py2+38))

    py3 = py2+66
    screen.blit(font_small.render("◈ CONTROLS",
                True,config.RADAR_GREEN),(px,py3))
    pygame.draw.line(screen,config.DIM_GREEN,
                     (px,py3+16),(px+200,py3+16),1)
    screen.blit(font_small.render(
        "R = START/STOP REC",True,(255,80,80)),
        (px,py3+22))
    screen.blit(font_small.render(
        "P = PLAY REPLAY",True,(255,200,0)),
        (px,py3+36))
    screen.blit(font_small.render(
        "SPACE = PAUSE",True,config.DIM_GREEN),
        (px,py3+50))
    screen.blit(font_small.render(
        "← → = SCRUB",True,config.DIM_GREEN),
        (px,py3+64))

def draw_hud_frame():
    screen.blit(font_title.render(
        "◈  AI AIR DEFENSE COMMAND SYSTEM",
        True,config.RADAR_GREEN),(20,12))
    screen.blit(font_small.render(
        "KALMAN  |  LSTM  |  RL  |  HUNGARIAN  "
        "|  RCS  |  TACTICAL HUD  |  REPLAY",
        True,config.DIM_GREEN),(20,40))

# ── Main loop ─────────────────────────────────────────────────

def main():
    global sweep_angle, spawn_timer, ranked
    global explosions, particles, frame_count

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if player.playing:
                        player.stop()
                    else:
                        pygame.quit(); sys.exit()

                # R — toggle recording
                elif event.key == pygame.K_r:
                    if not logger.recording:
                        logger.start_recording()
                    else:
                        logger.stop_recording()
                        logger.save()

                # P — play last replay
                elif event.key == pygame.K_p:
                    if not player.playing:
                        player.start()
                    else:
                        player.stop()

                # SPACE — pause replay
                elif event.key == pygame.K_SPACE:
                    if player.playing:
                        player.toggle_pause()

                # LEFT/RIGHT — scrub
                elif event.key == pygame.K_LEFT:
                    if player.playing:
                        player.scrub(-30)
                elif event.key == pygame.K_RIGHT:
                    if player.playing:
                        player.scrub(30)

                # UP/DOWN — speed
                elif event.key == pygame.K_UP:
                    if player.playing:
                        player.speed = min(4.0,
                            player.speed + 0.5)
                elif event.key == pygame.K_DOWN:
                    if player.playing:
                        player.speed = max(0.25,
                            player.speed - 0.25)

        # ── REPLAY MODE ──────────────────────────────────
        if player.playing:
            player.advance()
            frame_data = player.get_current_frame()

            draw_background()
            draw_range_rings()
            draw_crosshairs()
            draw_outer_ring()
            draw_protected_zone()
            draw_replay_frame(frame_data, player.frame_idx)
            draw_explosions_and_particles()
            draw_replay_hud()

            pygame.display.flip()
            clock.tick(config.FPS)
            continue

        # ── LIVE SIMULATION ──────────────────────────────
        frame_count += 1

        # spawn missiles
        spawn_timer += 1
        if spawn_timer >= config.MISSILE_SPAWN_RATE:
            for _ in range(config.MISSILE_SPAWN_COUNT):
                m      = Missile()
                angle  = random.uniform(0,2*math.pi)
                cx,cy  = RADAR_CENTER
                m.x    = cx + RADAR_RADIUS*math.cos(angle)
                m.y    = cy + RADAR_RADIUS*math.sin(angle)

                if m.type == "BALLISTIC":
                    tx = cx+random.uniform(-20,20)
                    ty = cy+random.uniform(-20,20)
                elif m.type == "EVASIVE":
                    ia = random.uniform(0,2*math.pi)
                    ir = random.uniform(0,RADAR_RADIUS*0.4)
                    tx = cx+ir*math.cos(ia)
                    ty = cy+ir*math.sin(ia)
                elif m.type == "STEALTH":
                    ia = random.uniform(0,2*math.pi)
                    ir = random.uniform(RADAR_RADIUS*0.1,
                                        RADAR_RADIUS*0.5)
                    tx = cx+ir*math.cos(ia)
                    ty = cy+ir*math.sin(ia)
                else:
                    tx = cx+random.uniform(-30,30)
                    ty = cy+random.uniform(-30,30)

                dx   = tx-m.x
                dy   = ty-m.y
                dist = math.hypot(dx,dy)
                if dist > 0:
                    m.vx = m.speed*dx/dist
                    m.vy = m.speed*dy/dist
                m.base_vx = m.vx
                m.base_vy = m.vy
                missiles.append(m)

                logger.log_event("launch",m.x,m.y,
                                 frame_count,
                                 {"type":m.type,
                                  "id":m.id})
            spawn_timer = 0

        # update missiles
        for m in missiles:
            m.update()
            cx,cy = RADAR_CENTER
            if math.hypot(m.x-cx,m.y-cy) <= \
                    config.PROTECTED_RADIUS:
                m.alive = False

        # notify evasive
        for m in missiles:
            if m.type == "EVASIVE":
                for inc in interceptor_ai.interceptors:
                    if inc.alive:
                        d = math.hypot(m.x-inc.x,
                                       m.y-inc.y)
                        m.notify_interceptor_close(d)

        ranked     = rank_threats(missiles)
        prev_count = len(interceptor_ai.interceptors)
        interceptor_ai.update(ranked)
        if len(interceptor_ai.interceptors) > prev_count:
            sound.play_launch()

        # hits
        for inc in interceptor_ai.interceptors:
            if inc.hit:
                spawn_explosion(inc.target.x,
                                inc.target.y)
                logger.log_event("explosion",
                                 inc.target.x,
                                 inc.target.y,
                                 frame_count)
                sound.play_explosion()
                inc.hit = False

        # log frame
        logger.log_frame(missiles,
                         interceptor_ai.interceptors,
                         sweep_angle, frame_count)

        # update explosions
        explosions = [[x,y,t-1,mt]
                      for x,y,t,mt in explosions if t>0]

        # update particles
        new_p = []
        for p in particles:
            p[0]+=p[2]; p[1]+=p[3]
            p[3]+=0.08; p[4]-=1
            if p[4]>0: new_p.append(p)
        particles = new_p

        missiles[:] = [m for m in missiles if m.alive]
        sweep_angle  = (sweep_angle+config.SWEEP_SPEED)%360
        sound.update(sweep_angle, ranked)

        # draw
        draw_background()
        draw_range_rings()
        draw_crosshairs()
        draw_outer_ring()
        draw_protected_zone()
        draw_sweep(sweep_angle)
        draw_predicted_paths(missiles)
        draw_lstm_paths(missiles)
        draw_missiles(ranked, frame_count)
        draw_interceptors(interceptor_ai.interceptors,
                          frame_count)
        draw_explosions_and_particles()
        draw_left_panel()
        draw_legend()
        draw_threat_panel(ranked)
        draw_bottom_dashboard(interceptor_ai.get_stats(),
                              missiles)
        draw_hud_frame()
        draw_recording_indicator(frame_count)

        pygame.display.flip()
        clock.tick(config.FPS)

if __name__ == "__main__":
    main()