"""All drawing: fonts, panels, glows, realistic parts and schematic symbols.

Parts are drawn at twice their size and smoothly scaled down, which gives soft,
anti-aliased edges with plain pygame drawing calls. Static pictures are cached.
"""
import math

import pygame
import pygame.gfxdraw

from . import parts
from .paths import asset

SS = 2  # supersampling factor

# Palette
BG_TOP = (14, 22, 48)
BG_BOTTOM = (6, 9, 22)
PANEL = (22, 32, 62)
PANEL_LIGHT = (34, 48, 88)
EDGE = (80, 120, 200)
TEXT = (232, 240, 255)
TEXT_DIM = (150, 170, 210)
ACCENT = (90, 220, 255)
GOLD = (255, 205, 80)
GREEN = (80, 230, 140)
RED = (255, 90, 90)
ORANGE = (255, 160, 60)
COPPER = (214, 150, 70)
COPPER_DARK = (120, 74, 30)
COPPER_LIT = (255, 225, 140)
PCB_TOP = (16, 104, 70)
PCB_BOTTOM = (8, 66, 46)
SILK = (225, 240, 230)
SOLDER = (200, 205, 215)

_fonts = {}
_cache = {}


def font(size, kind="bold"):
    key = (size, kind)
    if key not in _fonts:
        name = {"bold": "MPLUS1p-Bold.ttf", "regular": "MPLUS1p-Regular.ttf", "display": "Orbitron.ttf"}[kind]
        try:
            f = pygame.font.Font(asset("fonts", name), size)
            if kind == "display":
                f.set_bold(True)
        except (OSError, pygame.error):
            f = pygame.font.Font(None, size)
        _fonts[key] = f
    return _fonts[key]


def render(text, size, color=TEXT, kind="bold"):
    if kind == "display":
        text = text.replace("0", "O")  # Orbitron's zero is slashed; its O reads as a clean zero
    key = ("txt", text, size, color, kind)
    surf = _cache.get(key)
    if surf is None:
        surf = font(size, kind).render(text, True, color)
        if len(_cache) > 6000:
            for k in [k for k in _cache if k[0] == "txt"]:
                del _cache[k]
        _cache[key] = surf
    return surf


def text(surface, s, pos, size=20, color=TEXT, kind="bold", anchor="topleft", shadow=False, alpha=255):
    img = render(s, size, color, kind)
    rect = img.get_rect(**{anchor: (int(pos[0]), int(pos[1]))})
    if shadow:
        sh = render(s, size, (0, 0, 0), kind)
        sh = sh.copy()
        sh.set_alpha(140 * alpha // 255)
        surface.blit(sh, rect.move(2, 2))
    if alpha < 255:
        img = img.copy()
        img.set_alpha(alpha)
    surface.blit(img, rect)
    return rect


def _is_cjk(ch):
    return ord(ch) > 0x2E7F


def wrap(s, size, width, kind="bold"):
    """Wrap English at spaces and Japanese between characters."""
    f = font(size, kind)
    lines = []
    for para in s.split("\n"):
        tokens = []
        word = ""
        for ch in para:
            if _is_cjk(ch):
                if word:
                    tokens.append(word)
                    word = ""
                tokens.append(ch)
            elif ch == " ":
                word += ch
                tokens.append(word)
                word = ""
            else:
                word += ch
        if word:
            tokens.append(word)
        line = ""
        for tok in tokens:
            trial = line + tok
            if f.size(trial.rstrip())[0] <= width or not line:
                line = trial
            else:
                lines.append(line.rstrip())
                # keep Japanese closing punctuation on the previous line
                line = tok.lstrip()
        lines.append(line.rstrip())
    return lines


def paragraph(surface, s, rect, size=18, color=TEXT, kind="bold", spacing=1.3, align="left"):
    rect = pygame.Rect(rect)
    y = rect.top
    for line in wrap(s, size, rect.width, kind):
        if align == "center":
            text(surface, line, (rect.centerx, y), size, color, kind, anchor="midtop")
        else:
            text(surface, line, (rect.left, y), size, color, kind)
        y += int(size * spacing)
    return y


def gradient(size, top, bottom, horizontal=False):
    w, h = size
    surf = pygame.Surface((w, h))
    steps = w if horizontal else h
    for i in range(steps):
        t = i / max(1, steps - 1)
        c = [int(top[k] + (bottom[k] - top[k]) * t) for k in range(3)]
        if horizontal:
            pygame.draw.line(surf, c, (i, 0), (i, h))
        else:
            pygame.draw.line(surf, c, (0, i), (w, i))
    return surf


def glow(radius, color, strength=1.0):
    """Soft radial light, premultiplied, for additive blending."""
    key = ("glow", radius, color, round(strength, 2))
    if key in _cache:
        return _cache[key]
    surf = pygame.Surface((radius * 2, radius * 2))
    surf.fill((0, 0, 0))
    for r in range(radius, 0, -1):
        t = r / radius
        k = strength * (1 - t) ** 2.2
        pygame.draw.circle(surf, tuple(min(255, int(c * k)) for c in color), (radius, radius), r)
    _cache[key] = surf
    return surf


def blit_glow(surface, center, radius, color, strength=1.0):
    g = glow(max(2, int(radius)), color, strength)
    surface.blit(g, g.get_rect(center=(int(center[0]), int(center[1]))), special_flags=pygame.BLEND_RGB_ADD)


def panel(surface, rect, color=PANEL, border=EDGE, radius=16, alpha=235, shadow=True, width=2):
    rect = pygame.Rect(rect)
    key = ("panel", rect.size, color, radius, alpha, shadow)
    cached = _cache.get(key)
    if cached is None:
        sh = None
        if shadow:
            sh = pygame.Surface((rect.w + 16, rect.h + 16), pygame.SRCALPHA)
            for i in range(8, 0, -2):
                pygame.draw.rect(sh, (0, 0, 0, 18), sh.get_rect().inflate(-i * 2 + 4, -i * 2 + 4).move(0, 2),
                                 border_radius=radius + i)
        body = pygame.Surface(rect.size, pygame.SRCALPHA)
        top = tuple(min(255, c + 12) for c in color)
        for y in range(rect.h):
            t = y / max(1, rect.h - 1)
            c = [int(top[k] + (color[k] - top[k]) * t) for k in range(3)]
            pygame.draw.line(body, (*c, alpha), (0, y), (rect.w, y))
        mask = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=radius)
        body.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        cached = (sh, body)
        _cache[key] = cached
    sh, body = cached
    if sh is not None:
        surface.blit(sh, (rect.x - 8, rect.y - 4))
    surface.blit(body, rect)
    if border:
        pygame.draw.rect(surface, border, rect, width, border_radius=radius)
        hl = pygame.Rect(rect.x + radius, rect.y + 1, rect.w - radius * 2, 1)
        pygame.draw.rect(surface, tuple(min(255, c + 60) for c in border), hl)


def aaline(surface, color, p1, p2, width=2):
    """Thick anti-aliased line with round caps."""
    x1, y1 = p1
    x2, y2 = p2
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    if length < 0.01:
        pygame.gfxdraw.filled_circle(surface, int(x1), int(y1), max(1, int(width / 2)), color)
        return
    if width <= 1.5:
        pygame.draw.aaline(surface, color, p1, p2)
        return
    nx, ny = -dy / length * width / 2, dx / length * width / 2
    pts = [(x1 + nx, y1 + ny), (x2 + nx, y2 + ny), (x2 - nx, y2 - ny), (x1 - nx, y1 - ny)]
    pygame.gfxdraw.aapolygon(surface, pts, color)
    pygame.gfxdraw.filled_polygon(surface, pts, color)
    r = int(width / 2)
    for x, y in (p1, p2):
        pygame.gfxdraw.aacircle(surface, int(x), int(y), r, color)
        pygame.gfxdraw.filled_circle(surface, int(x), int(y), r, color)


def circle(surface, color, center, radius, width=0):
    x, y, r = int(center[0]), int(center[1]), int(radius)
    if r < 1:
        return
    if width == 0:
        pygame.gfxdraw.aacircle(surface, x, y, r, color)
        pygame.gfxdraw.filled_circle(surface, x, y, r, color)
    else:
        for i in range(width):
            pygame.gfxdraw.aacircle(surface, x, y, r - i, color)


def shade(color, amount):
    return tuple(max(0, min(255, int(c + amount))) for c in color)


def mix(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


# ---------------------------------------------------------------- realistic parts
# Every part is drawn into a W x H box. "Linear" parts lie horizontally with
# leads at the left and right middle; they are rotated for vertical slots.

LINEAR = ("battery", "resistor", "switch", "wire", "led")


def part_size(kind, unit):
    if parts.is_gate(kind):
        return int(unit * 0.95), int(unit * 1.05)
    w = {"battery": 0.92, "resistor": 0.8, "switch": 0.86, "wire": 0.7, "led": 0.62,
         "bulb": 0.66, "buzzer": 0.62, "motor": 0.7, "button": 0.6}[kind]
    h = {"battery": 0.42, "resistor": 0.26, "switch": 0.5, "wire": 0.26, "led": 0.58,
         "bulb": 0.8, "buzzer": 0.62, "motor": 0.7, "button": 0.56}[kind]
    return int(unit * w * 1.3), int(unit * h * 1.3)


def _hgrad_rect(surf, rect, c_top, c_mid, c_bot, radius=0):
    """A cylinder-like shading across the rectangle's height."""
    rect = pygame.Rect(rect)
    body = pygame.Surface(rect.size, pygame.SRCALPHA)
    for y in range(rect.h):
        t = y / max(1, rect.h - 1)
        c = mix(c_top, c_mid, t / 0.35) if t < 0.35 else mix(c_mid, c_bot, (t - 0.35) / 0.65)
        pygame.draw.line(body, (*c, 255), (0, y), (rect.w, y))
    if radius:
        mask = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=radius)
        body.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    surf.blit(body, rect)


def _lead(s, p1, p2, w):
    aaline(s, (150, 150, 160), p1, p2, max(2, int(w)))
    aaline(s, (225, 228, 235), (p1[0], p1[1] - w * 0.2), (p2[0], p2[1] - w * 0.2), max(1, int(w * 0.35)))


def _draw_battery(s, W, H, state):
    u = H / 0.42
    cy = H / 2
    _lead(s, (0, cy), (W * 0.1, cy), u * 0.035)
    _lead(s, (W * 0.9, cy), (W, cy), u * 0.035)
    body = pygame.Rect(W * 0.12, H * 0.08, W * 0.7, H * 0.84)
    _hgrad_rect(s, body, (90, 90, 100), (40, 40, 48), (12, 12, 16), int(H * 0.12))
    top = pygame.Rect(W * 0.12, H * 0.08, W * 0.22, H * 0.84)
    _hgrad_rect(s, top, (255, 200, 90), (220, 140, 30), (120, 70, 10), int(H * 0.12))
    pygame.draw.rect(s, (220, 140, 30), (top.right - H * 0.12, top.y, H * 0.12, top.h))
    pygame.draw.rect(s, (40, 40, 48), (top.right, top.y, 2, top.h))
    nub = pygame.Rect(W * 0.04, H * 0.3, W * 0.09, H * 0.4)
    _hgrad_rect(s, nub, (240, 240, 245), (170, 170, 180), (90, 90, 100), int(H * 0.06))
    cap = pygame.Rect(W * 0.82, H * 0.14, W * 0.07, H * 0.72)
    _hgrad_rect(s, cap, (220, 220, 230), (150, 150, 160), (80, 80, 90), int(H * 0.05))
    f = int(H * 0.42)
    text(s, "+", (top.centerx, cy), f, (40, 20, 0), anchor="center")
    text(s, "1.5V", (body.x + body.w * 0.62, cy), int(H * 0.3), (230, 230, 240), anchor="center")
    text(s, "-", (W * 0.76, cy), f, (230, 230, 240), anchor="center")


RES_BANDS = [(150, 75, 0), (20, 20, 20), (230, 40, 40), (212, 175, 55)]  # 1k ohm


def _draw_resistor(s, W, H, state):
    u = H / 0.26
    cy = H / 2
    _lead(s, (0, cy), (W, cy), u * 0.03)
    body = pygame.Rect(W * 0.18, H * 0.1, W * 0.64, H * 0.8)
    _hgrad_rect(s, body, (250, 230, 190), (215, 185, 135), (130, 105, 70), int(H * 0.38))
    for i, c in enumerate(RES_BANDS):
        x = body.x + body.w * (0.2 + i * 0.17) if i < 3 else body.x + body.w * 0.8
        band = pygame.Rect(x - body.w * 0.045, body.y, body.w * 0.09, body.h)
        _hgrad_rect(s, band, shade(c, 60), c, shade(c, -60))


def _draw_switch(s, W, H, state):
    closed = state.get("closed", False)
    u = H / 0.5
    base = pygame.Rect(W * 0.04, H * 0.52, W * 0.92, H * 0.4)
    _hgrad_rect(s, base, (80, 90, 110), (45, 52, 66), (20, 24, 32), int(H * 0.1))
    _lead(s, (0, H * 0.72), (W * 0.18, H * 0.72), u * 0.035)
    _lead(s, (W * 0.82, H * 0.72), (W, H * 0.72), u * 0.035)
    left = (W * 0.22, H * 0.62)
    right = (W * 0.78, H * 0.62)
    # contact clip on the right
    pygame.draw.rect(s, (200, 200, 210), (right[0] - W * 0.04, H * 0.42, W * 0.08, H * 0.24),
                     border_radius=int(H * 0.03))
    circle(s, (215, 215, 225), left, H * 0.08)
    angle = 0 if closed else -38
    length = W * 0.6
    rad = math.radians(angle)
    tip = (left[0] + length * math.cos(rad), left[1] + length * math.sin(rad))
    aaline(s, (200, 202, 212), left, tip, int(H * 0.09))
    aaline(s, (250, 250, 255), (left[0], left[1] - H * 0.02), (tip[0], tip[1] - H * 0.02), int(H * 0.03))
    mid = (left[0] + length * 0.75 * math.cos(rad), left[1] + length * 0.75 * math.sin(rad))
    handle_end = (mid[0] + H * 0.22 * math.sin(-rad) * 0, mid[1] - H * 0.28)
    aaline(s, (60, 60, 70), mid, handle_end, int(H * 0.06))
    knob = (255, 70, 70) if not closed else (80, 220, 120)
    circle(s, shade(knob, -60), (handle_end[0], handle_end[1] + 1), H * 0.11)
    circle(s, knob, handle_end, H * 0.1)
    circle(s, shade(knob, 80), (handle_end[0] - H * 0.03, handle_end[1] - H * 0.03), H * 0.035)
    circle(s, (90, 90, 100), left, H * 0.04)


def _draw_button(s, W, H, state):
    pressed = state.get("closed", False)
    base = pygame.Rect(W * 0.1, H * 0.35, W * 0.8, H * 0.55)
    _hgrad_rect(s, base, (70, 74, 86), (36, 38, 46), (14, 14, 18), int(H * 0.1))
    for x in (W * 0.18, W * 0.82):
        circle(s, (190, 190, 200), (x, H * 0.8), H * 0.05)
    cy = H * (0.4 if pressed else 0.32)
    circle(s, (20, 20, 24), (W / 2, H * 0.45), W * 0.3)
    circle(s, (160, 20, 30), (W / 2, cy + H * 0.05), W * 0.26)
    circle(s, (235, 50, 60), (W / 2, cy), W * 0.26)
    circle(s, (255, 130, 130), (W / 2 - W * 0.08, cy - W * 0.08), W * 0.08)


def _draw_bulb(s, W, H, state):
    on = state.get("on", False)
    cx = W / 2
    # holder
    holder = pygame.Rect(W * 0.12, H * 0.74, W * 0.76, H * 0.22)
    _hgrad_rect(s, holder, (60, 62, 72), (30, 32, 38), (10, 10, 14), int(H * 0.05))
    screw = pygame.Rect(W * 0.32, H * 0.56, W * 0.36, H * 0.2)
    _hgrad_rect(s, screw, (240, 240, 245), (170, 170, 180), (90, 90, 100), int(H * 0.03))
    for i in range(3):
        y = screw.y + screw.h * (0.25 + i * 0.25)
        pygame.draw.line(s, (110, 110, 120), (screw.x, y), (screw.right, y), max(1, int(H * 0.012)))
    gr = W * 0.34
    gc = (cx, H * 0.34)
    glass = (255, 245, 170) if on else (215, 230, 245)
    circle(s, shade(glass, -50), gc, gr)
    circle(s, glass, gc, gr * 0.94)
    if on:
        circle(s, (255, 255, 230), gc, gr * 0.7)
    # neck
    pygame.draw.polygon(s, shade(glass, -10), [(cx - gr * 0.55, gc[1] + gr * 0.7), (cx + gr * 0.55, gc[1] + gr * 0.7),
                                               (screw.right - 2, screw.y + 2), (screw.x + 2, screw.y + 2)])
    # filament
    fc = (255, 255, 255) if on else (120, 90, 60)
    supp = (150, 150, 160)
    aaline(s, supp, (cx - gr * 0.25, screw.y), (cx - gr * 0.3, gc[1]), max(1, int(H * 0.015)))
    aaline(s, supp, (cx + gr * 0.25, screw.y), (cx + gr * 0.3, gc[1]), max(1, int(H * 0.015)))
    pts = []
    for i in range(13):
        x = cx - gr * 0.3 + gr * 0.6 * i / 12
        y = gc[1] - (gr * 0.08 if i % 2 else -gr * 0.02)
        pts.append((x, y))
    for a, b in zip(pts, pts[1:]):
        aaline(s, fc, a, b, max(1, int(H * 0.02)))
    # highlight
    hl = pygame.Surface((W, H), pygame.SRCALPHA)
    pygame.draw.ellipse(hl, (255, 255, 255, 110), (gc[0] - gr * 0.6, gc[1] - gr * 0.75, gr * 0.45, gr * 0.6))
    s.blit(hl, (0, 0))


def _draw_led(s, W, H, state):
    """Side view: dome up, legs down then out. Anode (long leg, +) on the left."""
    on = state.get("on", False)
    burned = state.get("burned", False)
    color = parts.LED_COLORS.get(state.get("color", "red"), (255, 60, 60))
    u = H / 0.58
    cy = H * 0.86
    lw = u * 0.03
    cx = W / 2
    _lead(s, (0, cy), (cx - W * 0.1, cy), lw)
    _lead(s, (cx - W * 0.1, cy), (cx - W * 0.1, H * 0.6), lw)
    _lead(s, (W, cy), (cx + W * 0.1, cy), lw)
    _lead(s, (cx + W * 0.1, cy), (cx + W * 0.1, H * 0.66), lw)
    if burned:
        col = (60, 55, 50)
    elif on:
        col = mix(color, (255, 255, 255), 0.45)
    else:
        col = shade(color, -70)
    dome_r = W * 0.2
    rim = pygame.Rect(cx - dome_r * 1.2, H * 0.52, dome_r * 2.4, H * 0.09)
    pygame.draw.rect(s, shade(col, -30), rim, border_radius=int(H * 0.02))
    body = pygame.Rect(cx - dome_r, H * 0.2, dome_r * 2, H * 0.34)
    pygame.draw.rect(s, col, body)
    circle(s, col, (cx, H * 0.2), dome_r)
    if on and not burned:
        circle(s, mix(color, (255, 255, 255), 0.8), (cx, H * 0.3), dome_r * 0.55)
    hl = pygame.Surface((W, H), pygame.SRCALPHA)
    pygame.draw.ellipse(hl, (255, 255, 255, 120), (cx - dome_r * 0.7, H * 0.08, dome_r * 0.5, H * 0.3))
    s.blit(hl, (0, 0))
    text(s, "+", (W * 0.12, cy - H * 0.2), int(H * 0.26), (255, 230, 120), anchor="center")


def _draw_buzzer(s, W, H, state):
    cx, cy = W / 2, H / 2
    r = min(W, H) * 0.46
    circle(s, (8, 8, 10), (cx, cy + r * 0.06), r)
    circle(s, (40, 40, 46), (cx, cy), r)
    circle(s, (24, 24, 28), (cx, cy), r * 0.82)
    circle(s, (55, 55, 62), (cx - r * 0.1, cy - r * 0.1), r * 0.6)
    circle(s, (24, 24, 28), (cx, cy), r * 0.55)
    circle(s, (5, 5, 6), (cx, cy), r * 0.14)
    text(s, "+", (cx - r * 0.55, cy - r * 0.5), int(r * 0.5), (220, 220, 230), anchor="center")


def _draw_motor_body(s, W, H, state):
    cx, cy = W / 2, H / 2
    r = min(W, H) * 0.42
    circle(s, (40, 44, 52), (cx, cy + r * 0.08), r)
    circle(s, (190, 195, 205), (cx, cy), r)
    circle(s, (150, 155, 165), (cx, cy), r * 0.86)
    circle(s, (215, 220, 228), (cx - r * 0.12, cy - r * 0.12), r * 0.62)
    circle(s, (150, 155, 165), (cx, cy), r * 0.5)
    for a in range(0, 360, 60):
        x = cx + r * 0.7 * math.cos(math.radians(a))
        y = cy + r * 0.7 * math.sin(math.radians(a))
        circle(s, (110, 115, 125), (x, y), r * 0.06)


def draw_fan(surface, center, radius, angle, color=(80, 180, 255)):
    cx, cy = center
    for i in range(3):
        a = math.radians(angle + i * 120)
        pts = []
        for k in range(9):
            t = k / 8
            ang = a + (t - 0.5) * 0.9
            rr = radius * (0.25 + 0.75 * math.sin(t * math.pi) ** 0.5 if 0 < t < 1 else 0.25)
            pts.append((cx + math.cos(ang) * rr, cy + math.sin(ang) * rr))
        pts.append((cx + math.cos(a) * radius * 0.2, cy + math.sin(a) * radius * 0.2))
        pygame.gfxdraw.aapolygon(surface, pts, shade(color, -60))
        pygame.gfxdraw.filled_polygon(surface, pts, color)
    circle(surface, (230, 235, 240), center, radius * 0.22)
    circle(surface, (120, 125, 135), center, radius * 0.1)


def _draw_wire(s, W, H, state):
    color = state.get("color", (230, 60, 60))
    cy = H / 2
    _lead(s, (0, cy), (W * 0.18, cy), H * 0.16)
    _lead(s, (W * 0.82, cy), (W, cy), H * 0.16)
    pts = []
    for i in range(21):
        t = i / 20
        x = W * 0.15 + W * 0.7 * t
        y = cy - math.sin(t * math.pi) * H * 0.18
        pts.append((x, y))
    for a, b in zip(pts, pts[1:]):
        aaline(s, shade(color, -70), a, b, int(H * 0.5))
    for a, b in zip(pts, pts[1:]):
        aaline(s, color, (a[0], a[1] - 1), (b[0], b[1] - 1), int(H * 0.38))
    for a, b in zip(pts[3:-3], pts[4:-3]):
        aaline(s, shade(color, 90), (a[0], a[1] - H * 0.1), (b[0], b[1] - H * 0.1), max(1, int(H * 0.08)))


def _draw_chip(s, W, H, kind, state):
    body = pygame.Rect(W * 0.12, H * 0.08, W * 0.76, H * 0.84)
    # pins on the long sides, like a real DIP chip
    for i in range(4):
        y = body.y + body.h * (0.14 + i * 0.24)
        for x in (body.x - W * 0.07, body.right):
            pin = pygame.Rect(x, y, W * 0.07, body.h * 0.1)
            _hgrad_rect(s, pin, (240, 240, 245), (180, 180, 190), (110, 110, 120), 2)
    _hgrad_rect(s, body, (58, 60, 68), (30, 31, 36), (12, 12, 15), int(W * 0.05))
    pygame.draw.circle(s, (20, 20, 24), (int(body.centerx), int(body.y)), int(W * 0.07))
    circle(s, (70, 72, 80), (body.x + W * 0.1, body.y + H * 0.12), W * 0.03)
    sym_color = (235, 240, 255)
    draw_gate_symbol(s, kind, (body.centerx, body.y + body.h * 0.42), W * 0.42, sym_color, max(2, int(W * 0.03)),
                     leads=True)
    text(s, kind, (body.centerx, body.bottom - body.h * 0.2), int(H * 0.17), sym_color, kind="display", anchor="center")
    code = {"AND": "74HC08", "OR": "74HC32", "NOT": "74HC04", "NAND": "74HC00", "NOR": "74HC02", "XOR": "74HC86"}
    text(s, code[kind], (body.centerx, body.bottom - body.h * 0.06), int(H * 0.09), (150, 150, 165),
         kind="regular", anchor="center")


DRAWERS = {
    "battery": _draw_battery, "resistor": _draw_resistor, "switch": _draw_switch, "button": _draw_button,
    "bulb": _draw_bulb, "led": _draw_led, "buzzer": _draw_buzzer, "motor": _draw_motor_body, "wire": _draw_wire,
}

WIRE_COLORS = [(230, 60, 60), (60, 140, 240), (60, 200, 110), (240, 200, 50), (240, 130, 40)]


def part_image(kind, unit, state=None):
    """Picture of a part, horizontal. state: on, closed, color, burned, wire color."""
    state = state or {}
    key = ("part", kind, unit, tuple(sorted((k, str(v)) for k, v in state.items())))
    img = _cache.get(key)
    if img is not None:
        return img
    W, H = part_size(kind, unit)
    big = pygame.Surface((W * SS, H * SS), pygame.SRCALPHA)
    if parts.is_gate(kind):
        _draw_chip(big, W * SS, H * SS, kind, state)
    else:
        DRAWERS[kind](big, W * SS, H * SS, state)
    img = pygame.transform.smoothscale(big, (W, H))
    _cache[key] = img
    return img


def part_icon(kind, box, state=None):
    """Fit a part picture into a square box (palette cards, intro)."""
    unit = box
    w, h = part_size(kind, unit)
    scale = min(box / w, box / h) * 0.9
    return part_image(kind, max(8, int(unit * scale)), state)


# ---------------------------------------------------------------- schematic symbols

def _mapper(p1, p2):
    """Local coordinates (u along the slot, v across it) to screen."""
    x1, y1 = p1
    x2, y2 = p2
    L = math.hypot(x2 - x1, y2 - y1) or 1
    ux, uy = (x2 - x1) / L, (y2 - y1) / L
    vx, vy = -uy, ux

    def m(u, v):
        return (x1 + ux * u + vx * v, y1 + uy * u + vy * v)
    return m, L


def draw_symbol(surface, kind, p1, p2, size, color, width=2, closed=False, forward=True):
    """Schematic symbol between points p1 and p2. size ~ symbol length in px."""
    m, L = _mapper(p1, p2)
    a = (L - size) / 2
    b = a + size
    c = L / 2

    def line(u1, v1, u2, v2, w=width):
        aaline(surface, color, m(u1, v1), m(u2, v2), w)

    def lead_in(u_start, u_end):
        line(0, 0, u_start, 0)
        line(u_end, 0, L, 0)

    h = size * 0.3
    if kind == "wire":
        line(0, 0, L, 0)
    elif kind == "battery":
        # + plate (long) on the p1 side if forward
        pl, mi = (c - size * 0.08, c + size * 0.08) if forward else (c + size * 0.08, c - size * 0.08)
        lead_in(min(pl, mi), max(pl, mi))
        line(pl, -h * 1.2, pl, h * 1.2, width + 1)
        line(mi, -h * 0.6, mi, h * 0.6, width + 3)
        pp = m(pl - (size * 0.22 if forward else -size * 0.22), -h * 1.1)
        text(surface, "+", pp, max(10, int(size * 0.28)), color, anchor="center")
    elif kind == "resistor":
        lead_in(a, b)
        pts = [(a, 0)]
        for i in range(6):
            pts.append((a + size * (i + 0.5) / 6, -h * 0.7 if i % 2 == 0 else h * 0.7))
        pts.append((b, 0))
        for p, q in zip(pts, pts[1:]):
            line(p[0], p[1], q[0], q[1])
    elif kind in ("switch", "button"):
        lead_in(a, b)
        circle(surface, color, m(a, 0), max(2, width + 1), 0)
        circle(surface, color, m(b, 0), max(2, width + 1), 0)
        if kind == "switch":
            if closed:
                line(a, 0, b, 0)
            else:
                ang = math.radians(28)
                line(a, 0, a + size * math.cos(ang), -size * math.sin(ang))
        else:
            off = 0 if closed else -h * 0.8
            line(a - 2, off - h * 0.2, b + 2, off - h * 0.2)
            line(c, off - h * 0.2, c, off - h * 1.1)
            line(c - h * 0.4, off - h * 1.1, c + h * 0.4, off - h * 1.1)
    elif kind == "bulb":
        r = size * 0.32
        lead_in(c - r, c + r)
        circle(surface, color, m(c, 0), r, max(1, width))
        d = r * 0.7
        line(c - d, -d, c + d, d)
        line(c - d, d, c + d, -d)
    elif kind == "led":
        s = size * 0.28
        lead_in(c - s, c + s)
        tri = [m(c - s, -s), m(c - s, s), m(c + s, 0)] if forward else [m(c + s, -s), m(c + s, s), m(c - s, 0)]
        pygame.gfxdraw.aapolygon(surface, tri, color)
        pygame.gfxdraw.filled_polygon(surface, tri, color)
        bar = c + s if forward else c - s
        line(bar, -s, bar, s, width + 1)
        for k in (0, 1):
            u0 = c - s * 0.2 + k * s * 0.6
            line(u0, -s * 1.2, u0 + s * 0.5, -s * 1.9)
            tip = m(u0 + s * 0.5, -s * 1.9)
            circle(surface, color, tip, max(1.5, width))
    elif kind == "buzzer":
        r = size * 0.3
        lead_in(c - r, c + r)
        pts = [m(c - r, 0)] + [m(c - r * math.cos(t), -r * math.sin(t))
                                for t in [i * math.pi / 12 for i in range(13)]] + [m(c + r, 0)]
        for p, q in zip(pts, pts[1:]):
            aaline(surface, color, p, q, width)
        line(c - r, 0, c + r, 0)
    elif kind == "motor":
        r = size * 0.32
        lead_in(c - r, c + r)
        circle(surface, color, m(c, 0), r, max(1, width))
        text(surface, "M", m(c, 0), max(10, int(r * 1.2)), color, anchor="center")
    elif parts.is_gate(kind):
        line(0, 0, L, 0)


_BG_FILL = {"color": (30, 31, 36)}


def draw_gate_symbol(surface, kind, center, scale, color, width=2, leads=False):
    """ANSI logic gate. scale ~ body width in px. Inputs on the left, output on the right."""
    cx, cy = center
    w = scale
    h = scale * 0.8
    left = cx - w * 0.45
    right = cx + w * 0.45
    top, bot = cy - h / 2, cy + h / 2
    pts = []
    base = kind.replace("N", "") if kind in ("NAND", "NOR") else kind
    if kind == "NOT":
        pts = [(left, top), (right - w * 0.18, cy), (left, bot)]
    elif base == "AND":
        mid = left + w * 0.4
        pts = [(left, top), (mid, top)]
        for i in range(17):
            t = -math.pi / 2 + math.pi * i / 16
            pts.append((mid + (right - w * 0.15 - mid) * math.cos(t), cy + h / 2 * math.sin(t)))
        pts += [(mid, bot), (left, bot)]
    else:  # OR / XOR family
        tip = right - (w * 0.15 if kind == "NOR" else 0)
        back = []
        for i in range(17):
            t = i / 16
            back.append((left + w * 0.16 * math.sin(t * math.pi), bot - h * t))
        front_top = [(left + (tip - left) * t, top + (cy - top) * t ** 1.6) for t in [i / 12 for i in range(13)]]
        front_bot = [(left + (tip - left) * t, bot - (bot - cy) * t ** 1.6) for t in [i / 12 for i in range(12, -1, -1)]]
        pts = back + front_top[1:] + front_bot[1:]
    for p, q in zip(pts, pts[1:] + [pts[0]]):
        aaline(surface, color, p, q, width)
    if kind == "XOR":
        for i in range(16):
            t1, t2 = i / 16, (i + 1) / 16
            aaline(surface, color, (left - w * 0.1 + w * 0.16 * math.sin(t1 * math.pi), bot - h * t1),
                   (left - w * 0.1 + w * 0.16 * math.sin(t2 * math.pi), bot - h * t2), width)
    out_x = right
    if kind in ("NOT", "NAND", "NOR"):
        r = w * 0.07
        bx = (right - w * 0.18 + r) if kind == "NOT" else (right - w * 0.15 + r)
        circle(surface, color, (bx, cy), r + width / 2)
        circle(surface, _BG_FILL["color"], (bx, cy), max(1, r - width / 2))
        out_x = bx + r
    if leads:
        in_y = [cy] if kind == "NOT" else [cy - h * 0.25, cy + h * 0.25]
        for y in in_y:
            x0 = left + (w * 0.12 * math.sin((bot - y) / h * math.pi) if base == "OR" or kind == "XOR" else 0)
            aaline(surface, color, (left - w * 0.22, y), (x0, y), width)
        aaline(surface, color, (out_x, cy), (right + w * 0.2, cy), width)


def set_symbol_fill(color):
    _BG_FILL["color"] = color


def draw_gate_socket_symbol(surface, kind, center, unit, color, width, fill):
    """Gate symbol with pins matching the board gate socket geometry."""
    set_symbol_fill(fill)
    cx, cy = center
    draw_gate_symbol(surface, kind, (cx, cy), unit * 0.72, color, width)
    w = unit * 0.72
    h = w * 0.8
    left = cx - w * 0.45
    in_y = [cy] if kind == "NOT" else [cy - h * 0.25, cy + h * 0.25]
    pin_y = [cy - unit * 0.45] if kind == "NOT" else [cy - unit * 0.45, cy + unit * 0.45]
    for py, iy in zip(pin_y, in_y):
        x0 = cx - unit * 0.6
        aaline(surface, color, (x0, py), (x0 + unit * 0.1, py), width)
        aaline(surface, color, (x0 + unit * 0.1, py), (x0 + unit * 0.1, iy), width)
        aaline(surface, color, (x0 + unit * 0.1, iy), (left + w * 0.05, iy), width)
    aaline(surface, color, (cx + w * 0.45, cy), (cx + unit * 0.6, cy), width)


def background(size, t=0.0):
    key = ("bg", size)
    if key not in _cache:
        bg = gradient(size, BG_TOP, BG_BOTTOM)
        dots = pygame.Surface(size, pygame.SRCALPHA)
        for x in range(0, size[0], 32):
            for y in range(0, size[1], 32):
                pygame.draw.circle(dots, (120, 160, 255, 22), (x, y), 1)
        bg.blit(dots, (0, 0))
        _cache[key] = bg
    return _cache[key]


def clear_cache():
    _cache.clear()
