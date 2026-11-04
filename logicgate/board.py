"""Draws a circuit as a real-looking circuit board, or as a blueprint schematic."""
import math
import random

import pygame

from . import art, parts


class BoardView:
    def __init__(self, circuit, rect, unit=100, pcb=True):
        self.circuit = circuit
        self.rect = pygame.Rect(rect)
        self.unit = unit
        self.pcb = pcb
        self.hover = None          # socket under a dragged part
        self.hint = False          # show ghost parts in empty sockets
        self.sim = None
        self.time = 0.0
        self.motor_angle = {}
        self.particles = []
        self._bg = None
        self._rng = random.Random(4)

    # ------------------------------------------------------------ geometry
    def pt(self, p):
        return (self.rect.x + p[0] * self.unit, self.rect.y + p[1] * self.unit)

    def pad_xy(self, pid):
        return self.pt(self.circuit.pads[pid])

    def slot_center(self, s):
        if s.is_gate_socket:
            return self.pt(s.center)
        (x1, y1), (x2, y2) = self.pad_xy(s.a), self.pad_xy(s.b)
        return ((x1 + x2) / 2, (y1 + y2) / 2)

    def vertical(self, s):
        if s.is_gate_socket:
            return False
        (x1, y1), (x2, y2) = self.pad_xy(s.a), self.pad_xy(s.b)
        return abs(y2 - y1) > abs(x2 - x1)

    def slot_rect(self, s):
        cx, cy = self.slot_center(s)
        u = self.unit
        if s.is_gate_socket:
            return pygame.Rect(0, 0, u * 1.0, u * 1.1).move(cx - u * 0.5, cy - u * 0.55)
        w, h = u * 1.0, u * 0.62
        if self.vertical(s):
            w, h = h, w
        return pygame.Rect(cx - w / 2, cy - h / 2, w, h)

    def slot_at(self, pos, sockets_only=True):
        best, dist = None, 1e9
        for s in self.circuit.slots:
            if sockets_only and not s.is_socket:
                continue
            if s.trace:
                continue
            r = self.slot_rect(s).inflate(self.unit * 0.2, self.unit * 0.2)
            if r.collidepoint(pos):
                cx, cy = self.slot_center(s)
                d = math.hypot(pos[0] - cx, pos[1] - cy)
                if d < dist:
                    best, dist = s, d
        return best

    def polyline(self, s):
        if s.is_gate_socket:
            return []
        pts = [self.pad_xy(s.a)] + [self.pt(v) for v in s.via] + [self.pad_xy(s.b)]
        out = [pts[0]]
        for p in pts[1:]:
            q = out[-1]
            if abs(p[0] - q[0]) > 0.5 and abs(p[1] - q[1]) > 0.5:
                out.append((p[0], q[1]))   # route at right angles
            out.append(p)
        return out

    # ------------------------------------------------------------ backgrounds
    def _background(self):
        if self._bg is not None:
            return self._bg
        r = self.rect
        surf = pygame.Surface(r.size, pygame.SRCALPHA)
        if self.pcb:
            body = art.gradient(r.size, art.PCB_TOP, art.PCB_BOTTOM)
            grid = pygame.Surface(r.size, pygame.SRCALPHA)
            step = max(6, int(self.unit / 5))
            for x in range(step // 2, r.w, step):
                for y in range(step // 2, r.h, step):
                    pygame.draw.circle(grid, (0, 0, 0, 40), (x, y), max(1, step // 7))
            body.blit(grid, (0, 0))
            # subtle silkscreen marks
            for x in range(0, r.w, int(self.unit)):
                pygame.draw.line(body, (40, 140, 100), (x, 0), (x, 6))
                pygame.draw.line(body, (40, 140, 100), (x, r.h - 6), (x, r.h))
            surf.blit(body, (0, 0))
            mask = pygame.Surface(r.size, pygame.SRCALPHA)
            pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=int(self.unit * 0.18))
            surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            pygame.draw.rect(surf, (120, 220, 170), surf.get_rect(), 2, border_radius=int(self.unit * 0.18))
            for hx, hy in ((0.16, 0.16), (r.w / self.unit - 0.16, 0.16), (0.16, r.h / self.unit - 0.16),
                           (r.w / self.unit - 0.16, r.h / self.unit - 0.16)):
                c = (int(hx * self.unit), int(hy * self.unit))
                art.circle(surf, art.SOLDER, c, self.unit * 0.09)
                art.circle(surf, (10, 20, 30), c, self.unit * 0.055)
            if self.unit >= 60:
                art.text(surf, "LOGICGATE  REV 0.1.0", (r.w - self.unit * 0.35, self.unit * 0.1),
                         max(9, int(self.unit * 0.12)), art.SILK, kind="display", anchor="topright")
        else:
            body = art.gradient(r.size, (24, 70, 150), (14, 44, 110))
            grid = pygame.Surface(r.size, pygame.SRCALPHA)
            step = max(8, int(self.unit / 4))
            for x in range(0, r.w, step):
                pygame.draw.line(grid, (255, 255, 255, 18), (x, 0), (x, r.h))
            for y in range(0, r.h, step):
                pygame.draw.line(grid, (255, 255, 255, 18), (0, y), (r.w, y))
            body.blit(grid, (0, 0))
            surf.blit(body, (0, 0))
            mask = pygame.Surface(r.size, pygame.SRCALPHA)
            pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=10)
            surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            pygame.draw.rect(surf, (170, 210, 255), surf.get_rect(), 2, border_radius=10)
        self._bg = surf
        return surf

    # ------------------------------------------------------------ drawing
    def draw(self, surface, dt=0.0):
        self.time += dt
        if self.pcb:
            sh = pygame.Surface((self.rect.w + 20, self.rect.h + 20), pygame.SRCALPHA)
            pygame.draw.rect(sh, (0, 0, 0, 90), sh.get_rect().inflate(-8, -8), border_radius=int(self.unit * 0.2))
            surface.blit(sh, (self.rect.x - 4, self.rect.y + 2))
        surface.blit(self._background(), self.rect)
        if self.pcb:
            self._draw_pcb(surface, dt)
        else:
            self._draw_schematic(surface)

    def _flowing(self, s):
        return self.sim is not None and s.id in self.sim.flow

    def _draw_pcb(self, surface, dt):
        c = self.circuit
        u = self.unit
        tw = max(3, int(u * 0.09))
        glow_layer = []
        # copper traces (under everything)
        for s in c.slots:
            if s.is_gate_socket:
                continue
            pts = self.polyline(s)
            lit = self._flowing(s)
            col = art.COPPER_LIT if lit else art.COPPER
            for p, q in zip(pts, pts[1:]):
                art.aaline(surface, art.COPPER_DARK, (p[0], p[1] + 1), (q[0], q[1] + 1), tw + 2)
            for p, q in zip(pts, pts[1:]):
                art.aaline(surface, col, p, q, tw)
            for p, q in zip(pts, pts[1:]):
                art.aaline(surface, art.shade(col, 45), (p[0], p[1] - tw * 0.2), (q[0], q[1] - tw * 0.2),
                           max(1, tw // 3))
        # gate sockets: pin traces to the chip
        for s in c.slots:
            if s.is_gate_socket:
                cx, cy = self.slot_center(s)
                pins = [s.pins["a"], s.pins["b"], s.pins["out"]]
                for i, pid in enumerate(pins):
                    px, py = self.pad_xy(pid)
                    x2 = cx - u * 0.38 if i < 2 else cx + u * 0.38
                    art.aaline(surface, art.COPPER_DARK, (px, py + 1), (x2, py + 1), tw + 2)
                    art.aaline(surface, art.COPPER, (px, py), (x2, py), tw)
        # pads
        for pid, p in c.pads.items():
            x, y = self.pt(p)
            art.circle(surface, (90, 90, 96), (x, y + 1), u * 0.085)
            art.circle(surface, art.SOLDER, (x, y), u * 0.08)
            art.circle(surface, (245, 245, 250), (x - u * 0.02, y - u * 0.02), u * 0.03)
        # current dots
        if self.sim is not None:
            for s in c.slots:
                d = self.sim.flow.get(s.id)
                if d is None or s.is_gate_socket:
                    continue
                pts = self.polyline(s)
                if d < 0:
                    pts = pts[::-1]
                self._dots(surface, pts, u)
        # sockets and parts
        for s in c.slots:
            if s.trace:
                continue
            if s.kind is None:
                self._draw_socket(surface, s)
            else:
                self._draw_part(surface, s, dt, glow_layer)
        for s in c.slots:
            if s.label and s.kind:
                cx, cy = self.slot_center(s)
                off = (-u * 0.42, 0) if self.vertical(s) else (0, -u * 0.38)
                p = (cx + off[0], cy + off[1])
                art.circle(surface, (10, 20, 40), p, u * 0.15)
                art.circle(surface, art.GOLD, p, u * 0.13)
                art.text(surface, s.label, p, max(10, int(u * 0.2)), (30, 20, 0), kind="display", anchor="center")
        for center, radius, color, strength in glow_layer:
            art.blit_glow(surface, center, radius, color, strength)
        self._particles(surface, dt)

    def _dots(self, surface, pts, u):
        segs = []
        total = 0
        for p, q in zip(pts, pts[1:]):
            L = math.hypot(q[0] - p[0], q[1] - p[1])
            segs.append((p, q, L))
            total += L
        if total < 1:
            return
        spacing = u * 0.5
        offset = (self.time * u * 1.2) % spacing
        d = offset
        while d < total:
            acc = 0
            for p, q, L in segs:
                if acc + L >= d:
                    t = (d - acc) / L if L else 0
                    x, y = p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t
                    art.blit_glow(surface, (x, y), int(u * 0.12), (255, 200, 90), 0.8)
                    art.circle(surface, (255, 250, 225), (x, y), max(2, u * 0.03))
                    break
                acc += L
            d += spacing

    def _draw_socket(self, surface, s):
        r = self.slot_rect(s)
        u = self.unit
        hover = self.hover is s
        col = art.ACCENT if hover else (170, 235, 205)
        layer = pygame.Surface(r.size, pygame.SRCALPHA)
        fill = (90, 220, 255, 70) if hover else (0, 40, 25, 120)
        pygame.draw.rect(layer, fill, layer.get_rect(), border_radius=int(u * 0.1))
        surface.blit(layer, r)
        # dashed outline
        dash = max(4, int(u * 0.07))
        perim = [(r.left, r.top), (r.right, r.top), (r.right, r.bottom), (r.left, r.bottom), (r.left, r.top)]
        phase = (self.time * 20) % (dash * 2)
        for p, q in zip(perim, perim[1:]):
            L = math.hypot(q[0] - p[0], q[1] - p[1])
            n = 0.0 - phase
            while n < L:
                a = max(0, n)
                b = min(L, n + dash)
                if b > a:
                    pa = (p[0] + (q[0] - p[0]) * a / L, p[1] + (q[1] - p[1]) * a / L)
                    pb = (p[0] + (q[0] - p[0]) * b / L, p[1] + (q[1] - p[1]) * b / L)
                    pygame.draw.line(surface, col, pa, pb, 2)
                n += dash * 2
        if self.hint and s.solution:
            img = self._oriented(s, s.solution, {"color": s.led_color} if s.solution == "led" else {}, ghost=True)
            surface.blit(img, img.get_rect(center=r.center))
            name = s.solution
            from . import i18n
            label = i18n.part_name(name)
            right_half = r.centerx > self.rect.centerx
            if not self.vertical(s):
                tx, ty, anchor = r.centerx, r.bottom + u * 0.04, "midtop"
            elif right_half:
                tx, ty, anchor = r.left - u * 0.06, r.centery, "midright"
            else:
                tx, ty, anchor = r.right + u * 0.06, r.centery, "midleft"
            art.text(surface, label, (tx, ty), max(10, int(u * 0.15)), (255, 255, 200), anchor=anchor, shadow=True)
        elif hover:
            art.blit_glow(surface, r.center, int(u * 0.5), (60, 200, 255), 0.5)

    def _oriented(self, s, kind, state, ghost=False):
        img = art.part_image(kind, self.unit, state)
        if kind in art.LINEAR and not s.is_gate_socket:
            flip = False
            if kind in ("battery", "led"):
                flip = not s.forward
            if flip:
                img = pygame.transform.flip(img, True, False)
            if self.vertical(s):
                (x1, y1), (x2, y2) = self.pad_xy(s.a), self.pad_xy(s.b)
                img = pygame.transform.rotate(img, -90 if y2 > y1 else 90)
            else:
                (x1, _), (x2, _) = self.pad_xy(s.a), self.pad_xy(s.b)
                if x2 < x1:
                    img = pygame.transform.flip(img, True, False)
        if ghost:
            img = img.copy()
            img.set_alpha(95)
        return img

    def part_state(self, s):
        state = {}
        sim = self.sim
        if parts.is_switch(s.kind):
            state["closed"] = s.closed
        if s.kind == "led":
            state["color"] = s.led_color
        if s.kind == "wire":
            state["color"] = art.WIRE_COLORS[int(s.id[1:]) % len(art.WIRE_COLORS)]
        if sim is not None and parts.is_output(s.kind):
            state["on"] = sim.on.get(s.id, False)
            if s.id in sim.burned:
                state["burned"] = True
        return state

    def _draw_part(self, surface, s, dt, glow_layer):
        u = self.unit
        state = self.part_state(s)
        cx, cy = self.slot_center(s)
        on = state.get("on", False)
        if s.is_gate_socket:
            img = art.part_image(s.kind, u)
            surface.blit(img, img.get_rect(center=(cx, cy)))
            if self.sim is not None and self.sim.gate_out.get(s.id):
                ox, oy = self.pad_xy(s.pins["out"])
                art.circle(surface, (90, 255, 140), (ox - u * 0.12, oy - u * 0.14), u * 0.04)
                glow_layer.append(((ox - u * 0.12, oy - u * 0.14), u * 0.12, (60, 255, 120), 0.8))
            return
        img = self._oriented(s, s.kind, state)
        jitter = (0, 0)
        if s.kind == "buzzer" and on:
            jitter = (math.sin(self.time * 90) * u * 0.012, math.cos(self.time * 77) * u * 0.012)
        rect = img.get_rect(center=(cx + jitter[0], cy + jitter[1]))
        shadow = pygame.mask.from_surface(img).to_surface(setcolor=(0, 0, 0, 70), unsetcolor=(0, 0, 0, 0))
        surface.blit(shadow, rect.move(3, 4))
        surface.blit(img, rect)
        if s.kind == "motor":
            speed = 900 if on else 0
            ang = self.motor_angle.get(s.id, self._rng.uniform(0, 120)) + speed * dt
            self.motor_angle[s.id] = ang
            r = min(rect.w, rect.h) * 0.46
            if on:
                blur = pygame.Surface((r * 2.4, r * 2.4), pygame.SRCALPHA)
                pygame.draw.circle(blur, (140, 200, 255, 50), (r * 1.2, r * 1.2), r * 1.05)
                surface.blit(blur, blur.get_rect(center=(cx, cy)))
            art.draw_fan(surface, (cx, cy), r, ang, (90, 180, 255) if not on else (150, 210, 255))
        if on:
            if s.kind == "bulb":
                gc = (cx, rect.y + rect.h * 0.34)
                pulse = 1 + 0.04 * math.sin(self.time * 7)
                glow_layer.append((gc, u * 1.1 * pulse, (255, 190, 70), 0.8))
                glow_layer.append((gc, u * 0.45, (255, 255, 210), 0.7))
            elif s.kind == "led":
                col = parts.LED_COLORS.get(s.led_color, (255, 60, 60))
                gc = (cx, cy) if self.vertical(s) else (cx, rect.y + rect.h * 0.3)
                glow_layer.append((gc, u * 0.8, col, 0.85))
                glow_layer.append((gc, u * 0.25, (255, 255, 255), 0.5))
            elif s.kind == "buzzer":
                self._waves(surface, (cx, cy), u)
        if state.get("burned") and self._rng.random() < 0.3:
            self.particles.append([cx + self._rng.uniform(-5, 5), cy - u * 0.1, self._rng.uniform(-8, 8), -40,
                                   1.2, (120, 120, 120)])

    def _waves(self, surface, center, u):
        for i in range(3):
            phase = (self.time * 1.6 + i / 3) % 1
            r = u * (0.35 + phase * 0.5)
            alpha = int(220 * (1 - phase))
            layer = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
            for side in (-1, 1):
                rect = pygame.Rect(2, 2, r * 2, r * 2)
                start = math.radians(-35 if side > 0 else 145)
                pygame.draw.arc(layer, (255, 240, 120, alpha), rect, start, start + math.radians(70), 3)
            surface.blit(layer, layer.get_rect(center=center))

    def sparks(self, pos, color=(255, 230, 120), n=30):
        for _ in range(n):
            a = self._rng.uniform(0, math.tau)
            sp = self._rng.uniform(60, 260)
            self.particles.append([pos[0], pos[1], math.cos(a) * sp, math.sin(a) * sp - 60,
                                   self._rng.uniform(0.4, 1.0), color])

    def _particles(self, surface, dt):
        alive = []
        for p in self.particles:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[3] += 300 * dt if p[5] != (120, 120, 120) else -10 * dt
            p[4] -= dt
            if p[4] > 0:
                alive.append(p)
                if p[5] == (120, 120, 120):
                    r = int(self.unit * 0.12 * (1.6 - p[4]))
                    layer = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
                    pygame.draw.circle(layer, (130, 130, 130, int(110 * p[4] / 1.2)), (r + 1, r + 1), r)
                    surface.blit(layer, (p[0] - r, p[1] - r))
                else:
                    art.circle(surface, p[5], (p[0], p[1]), max(1, 3 * p[4]))
        self.particles = alive

    # ------------------------------------------------------------ schematic
    def _draw_schematic(self, surface):
        c = self.circuit
        u = self.unit
        col = (235, 245, 255)
        w = max(2, int(u * 0.045))
        fill = (20, 58, 130)
        art._BG_FILL["color"] = fill
        degree = {}
        for s in c.slots:
            if s.is_gate_socket:
                for pid in s.pins.values():
                    degree[pid] = degree.get(pid, 0) + 1
                continue
            degree[s.a] = degree.get(s.a, 0) + 1
            degree[s.b] = degree.get(s.b, 0) + 1
        for s in c.slots:
            if s.is_gate_socket:
                kind = s.solution
                art.draw_gate_socket_symbol(surface, kind, self.pt(s.center), u, col, w, fill)
                continue
            pts = self.polyline(s)
            kind = s.solution or "wire"
            if kind == "wire" or len(pts) > 2:
                for p, q in zip(pts, pts[1:]):
                    art.aaline(surface, col, p, q, w)
            else:
                length = math.hypot(pts[1][0] - pts[0][0], pts[1][1] - pts[0][1])
                size = min(u * (0.62 if u >= 50 else 0.95), length * 0.8)
                art.draw_symbol(surface, kind, pts[0], pts[1], size, col, w, closed=False, forward=s.forward)
                if s.label:
                    cx, cy = self.slot_center(s)
                    off = (-u * 0.38, 0) if self.vertical(s) else (0, -u * 0.36)
                    art.text(surface, s.label, (cx + off[0], cy + off[1]), max(9, int(u * 0.3)), art.GOLD,
                             kind="display", anchor="center")
        for pid, d in degree.items():
            if d >= 3:
                art.circle(surface, col, self.pad_xy(pid), max(2, u * 0.06))
