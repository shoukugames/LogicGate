"""Introduction: what each part looks like, its symbol, what it does, with live demos."""
import math

import pygame

from .. import art, i18n, parts
from ..app import Scene
from ..board import BoardView
from ..circuit import simulate
from ..levels import Builder
from ..ui import Button, ButtonGroup

PART_ORDER = ["battery", "wire", "switch", "button", "bulb", "led", "resistor", "buzzer", "motor",
              "AND", "OR", "NOT", "NAND", "NOR", "XOR"]
LIST_RECT = pygame.Rect(20, 92, 290, 612)
DETAIL = pygame.Rect(326, 92, 934, 612)


def _demo(kind):
    """Small fixed circuits for the concept pages."""
    b = Builder()
    loop = [(1.0, 0.8), (3.8, 0.8), (6.6, 0.8), (6.6, 4.4), (3.8, 4.4), (1.0, 4.4)]
    b.edge(loop[0], loop[-1], "battery", role="fixed")
    if kind == "circuit":
        b.edge(loop[0], loop[1], "switch", role="fixed")
        b.edge(loop[1], loop[2], "wire", role="trace")
        b.edge(loop[2], loop[3], "bulb", role="fixed")
        b.edge(loop[3], loop[4], "wire", role="trace")
        b.edge(loop[4], loop[5], "wire", role="trace")
    elif kind == "series":
        b.edge(loop[0], loop[1], "switch", role="fixed", label="A")
        b.edge(loop[1], loop[2], "switch", role="fixed", label="B")
        b.edge(loop[2], loop[3], "bulb", role="fixed")
        b.edge(loop[3], loop[4], "wire", role="trace")
        b.edge(loop[4], loop[5], "wire", role="trace")
    elif kind == "parallel":
        b.edge((1.0, 0.8), (2.6, 0.8), "wire", role="trace")
        b.edge((2.6, 0.8), (5.0, 0.8), "switch", role="fixed", label="A")
        b.edge((5.0, 0.8), (6.6, 0.8), "wire", role="trace")
        b.edge((2.6, 0.8), (2.6, 2.3), "wire", role="trace")
        b.edge((2.6, 2.3), (5.0, 2.3), "switch", role="fixed", label="B")
        b.edge((5.0, 2.3), (5.0, 0.8), "wire", role="trace")
        b.edge(loop[2], loop[3], "bulb", role="fixed")
        b.edge(loop[3], loop[4], "wire", role="trace")
        b.edge(loop[4], loop[5], "wire", role="trace")
    elif kind == "short":
        b.edge(loop[0], loop[1], "switch", role="fixed")
        b.edge(loop[1], loop[2], "wire", role="trace")
        b.edge(loop[2], loop[3], "bulb", role="fixed")
        b.edge(loop[3], loop[4], "wire", role="trace")
        b.edge(loop[4], loop[5], "wire", role="trace")
        b.edge(loop[1], (3.8, 2.6), "wire", role="trace")
        b.edge((3.8, 2.6), loop[4], "wire", role="fixed")
    elif kind == "logic":
        b.edge((1.0, 0.8), (2.0, 0.8), "wire", role="trace")
        g = b.gate(4.6, 2.2, "AND", role="fixed")
        pa, pb = b.c.pads[g.pins["a"]], b.c.pads[g.pins["b"]]
        b.edge((2.0, 0.8), (2.0, pa[1]), "wire", role="trace")
        b.edge((2.0, pa[1]), pa, "switch", role="fixed", label="A")
        b.edge((2.0, pa[1]), (2.0, pb[1]), "wire", role="trace")
        b.edge((2.0, pb[1]), pb, "switch", role="fixed", label="B")
        out = b.c.pads[g.pins["out"]]
        b.edge(out, (6.6, out[1]), "led", role="fixed")
        b.edge((6.6, out[1]), (6.6, 4.4), "resistor", role="fixed")
        b.edge((6.6, 4.4), (3.8, 4.4), "wire", role="trace")
        b.edge((3.8, 4.4), (1.0, 4.4), "wire", role="trace")
    for s in b.c.slots:
        s.led_color = "green"
    return b.c


class IntroScene(Scene):
    music = "title"

    def __init__(self, app):
        super().__init__(app)
        self.t = 0.0
        self.entries = [("concept", c[0]) for c in i18n.CONCEPTS] + [("part", k) for k in PART_ORDER]
        self.index = 0
        self.buttons = ButtonGroup([Button((20, 22, 150, 50), lambda: i18n.t("back"), self.back,
                                           color=(90, 100, 140), size=20)])
        self.gate_inputs = [False, False]
        self.motor_angle = 0.0
        self._select(0)

    def back(self):
        from .title import TitleScene
        self.app.switch(TitleScene(self.app))

    def _select(self, i):
        self.index = i
        kind, key = self.entries[i]
        self.view = None
        if kind == "concept":
            c = _demo(key)
            self.view = BoardView(c, (DETAIL.x + 24, DETAIL.y + 240, 7.6 * 58, 5.2 * 58), 58)
            self.view.sim = simulate(c)
        self.gate_inputs = [False, False]

    def _row_rect(self, i):
        return pygame.Rect(LIST_RECT.x + 8, LIST_RECT.y + 8 + i * 30, LIST_RECT.w - 16, 28)

    def handle(self, event):
        if self.buttons.handle(event, self.app.audio):
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.back()
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._select((self.index + 1) % len(self.entries))
            elif event.key in (pygame.K_UP, pygame.K_w):
                self._select((self.index - 1) % len(self.entries))
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i in range(len(self.entries)):
                if self._row_rect(i).collidepoint(event.pos):
                    self.app.audio.play("click")
                    self._select(i)
                    return
            if self.view is not None:
                s = self.view.slot_at(event.pos, sockets_only=False)
                if s is not None and parts.is_switch(s.kind):
                    s.closed = not s.closed
                    self.app.audio.play("switch")
                    sim = simulate(self.view.circuit)
                    if sim.short and not (self.view.sim and self.view.sim.short):
                        bat = next(x for x in self.view.circuit.slots if x.kind == "battery")
                        self.view.sparks(self.view.slot_center(bat), (255, 200, 80), 50)
                        self.app.audio.play("error")
                    self.view.sim = sim
            for i, r in enumerate(self._gate_buttons()):
                if r.collidepoint(event.pos):
                    self.gate_inputs[i] = not self.gate_inputs[i]
                    self.app.audio.play("switch")

    def update(self, dt):
        self.t += dt
        self.buttons.update(self.app.mouse, dt)
        self.motor_angle += dt * 600

    def _gate_buttons(self):
        kind, key = self.entries[self.index]
        if kind != "part" or not parts.is_gate(key):
            return []
        n = 1 if key == "NOT" else 2
        return [pygame.Rect(DETAIL.x + 40, DETAIL.y + 300 + i * 70, 120, 52) for i in range(n)]

    def draw(self, surface):
        self.app.backdrop.draw(surface, self.t * 0.6)
        self.buttons.draw(surface)
        art.text(surface, i18n.t("intro_title"), (190, 28), 34, art.TEXT, kind="bold", shadow=True)
        other = i18n.both("intro_title")[1 if i18n.lang() == "en" else 0]
        art.text(surface, other, (192, 66), 15, art.TEXT_DIM)
        art.panel(surface, LIST_RECT)
        for i, (kind, key) in enumerate(self.entries):
            r = self._row_rect(i)
            sel = i == self.index
            hov = r.collidepoint(self.app.mouse)
            if sel:
                pygame.draw.rect(surface, (52, 96, 190), r, border_radius=8)
            elif hov:
                pygame.draw.rect(surface, (36, 54, 100), r, border_radius=8)
            if kind == "concept":
                title = dict((c[0], c[1]) for c in i18n.CONCEPTS)[key]
                label = title[1] if i18n.lang() == "ja" else title[0]
                art.circle(surface, art.GOLD, (r.x + 16, r.centery), 6)
                art.text(surface, label, (r.x + 34, r.centery), 15, art.GOLD if not sel else art.TEXT,
                         anchor="midleft")
            else:
                icon = art.part_icon(key, 26, {"color": "red"} if key == "led" else {})
                surface.blit(icon, icon.get_rect(center=(r.x + 16, r.centery)))
                art.text(surface, i18n.part_name(key), (r.x + 34, r.centery), 15, art.TEXT, anchor="midleft")
        art.panel(surface, DETAIL)
        kind, key = self.entries[self.index]
        if kind == "concept":
            self._concept(surface, key)
        else:
            self._part(surface, key)

    def _concept(self, surface, key):
        c = next(x for x in i18n.CONCEPTS if x[0] == key)
        (en_t, ja_t), (en, ja) = c[1], c[2]
        art.text(surface, en_t, (DETAIL.x + 24, DETAIL.y + 16), 30, art.TEXT)
        art.text(surface, ja_t, (DETAIL.x + 26, DETAIL.y + 56), 18, art.TEXT_DIM)
        y = art.paragraph(surface, en, (DETAIL.x + 24, DETAIL.y + 92, DETAIL.w - 48, 80), 17, art.TEXT)
        art.paragraph(surface, ja, (DETAIL.x + 24, y + 4, DETAIL.w - 48, 80), 15, art.TEXT_DIM)
        self.view.draw(surface, 1 / 60)
        side = pygame.Rect(self.view.rect.right + 20, self.view.rect.y, DETAIL.right - self.view.rect.right - 40,
                           self.view.rect.h)
        art.panel(surface, side, color=(30, 44, 82))
        art.paragraph(surface, i18n.t("click_try"), (side.x + 16, side.y + 16, side.w - 32, 60), 17, art.ACCENT)
        sim = self.view.sim
        status_y = side.y + 90
        if sim.short:
            art.paragraph(surface, i18n.t("fail_short"), (side.x + 16, status_y, side.w - 32, 200), 15, art.RED)
        else:
            lit = any(sim.on.values())
            word = ("ON!", "点灯！") if lit else ("OFF", "消灯")
            img = art.part_icon("bulb" if key != "logic" else "led", 80, {"on": lit, "color": "green"})
            surface.blit(img, img.get_rect(center=(side.centerx, status_y + 60)))
            if lit:
                art.blit_glow(surface, (side.centerx, status_y + 50), 70, (255, 200, 80), 0.6)
            art.text(surface, f"{word[0]} / {word[1]}", (side.centerx, status_y + 120), 22,
                     art.GOLD if lit else art.TEXT_DIM, anchor="midtop")
            states = [s for s in self.view.circuit.switches()]
            yy = status_y + 160
            for s in states:
                name = f"{i18n.part_name('switch')} {s.label or ''}".strip()
                st = i18n.t("on") if s.closed else i18n.t("off")
                art.text(surface, f"{name}: {st}", (side.x + 20, yy), 16, art.GREEN if s.closed else art.TEXT_DIM)
                yy += 26

    def _part(self, surface, key):
        name_en, name_ja = i18n.PART_NAMES[key]
        art.text(surface, name_en, (DETAIL.x + 24, DETAIL.y + 16), 32, art.TEXT)
        art.text(surface, name_ja, (DETAIL.x + 26, DETAIL.y + 58), 20, art.TEXT_DIM)
        cycle = int(self.t / 1.5) % 2 == 0
        # picture
        pic = pygame.Rect(DETAIL.x + 24, DETAIL.y + 96, 300, 180)
        art.panel(surface, pic, color=(16, 92, 62), border=(120, 220, 170), shadow=False)
        art.text(surface, i18n.t("looks_like"), (pic.x + 12, pic.y + 8), 14, art.SILK)
        state = {"on": cycle, "closed": cycle, "color": "red"}
        if key == "wire":
            state = {"color": (230, 60, 60)}
        if parts.is_gate(key):
            img = art.part_image(key, 130)
        else:
            img = art.part_icon(key, 150, state)
        center = (pic.centerx, pic.centery + 10)
        if key == "buzzer" and cycle:
            center = (center[0] + math.sin(self.t * 80) * 1.5, center[1])
        surface.blit(img, img.get_rect(center=center))
        if key == "motor":
            art.draw_fan(surface, center, img.get_width() * 0.46, self.motor_angle, (110, 190, 255))
        if state.get("on") and key == "bulb":
            art.blit_glow(surface, (center[0], center[1] - img.get_height() * 0.16), 120, (255, 190, 70), 0.8)
        if state.get("on") and key == "led":
            art.blit_glow(surface, (center[0], center[1] - img.get_height() * 0.2), 90, (255, 60, 60), 0.9)
        if key == "buzzer" and cycle:
            for i in range(3):
                ph = (self.t * 1.5 + i / 3) % 1
                rr = 60 + ph * 50
                layer = pygame.Surface((rr * 2 + 4, rr * 2 + 4), pygame.SRCALPHA)
                for st in (-35, 145):
                    pygame.draw.arc(layer, (255, 240, 120, int(220 * (1 - ph))), (2, 2, rr * 2, rr * 2),
                                    math.radians(st), math.radians(st + 70), 3)
                surface.blit(layer, layer.get_rect(center=center))
        # symbol
        sym = pygame.Rect(pic.right + 20, pic.y, 260, 180)
        art.panel(surface, sym, color=(20, 58, 130), border=(170, 210, 255), shadow=False)
        art.text(surface, i18n.t("symbol"), (sym.x + 12, sym.y + 8), 14, (200, 225, 255))
        art._BG_FILL["color"] = (20, 58, 130)
        if parts.is_gate(key):
            art.draw_gate_symbol(surface, key, (sym.centerx, sym.centery + 10), 120, (235, 245, 255), 3, leads=True)
        else:
            art.draw_symbol(surface, key, (sym.x + 30, sym.centery + 10), (sym.right - 30, sym.centery + 10), 110,
                            (235, 245, 255), 3, closed=cycle and key in ("switch", "button"))
        # text
        info = i18n.part_info(key)
        tx = sym.right + 24
        tw = DETAIL.right - tx - 24
        art.text(surface, i18n.t("what_it_does"), (tx, pic.y), 18, art.GOLD)
        y = art.paragraph(surface, info[0], (tx, pic.y + 28, tw, 200), 15, art.TEXT, spacing=1.32)
        art.text(surface, i18n.t("how_used"), (tx, y + 10), 18, art.GOLD)
        art.paragraph(surface, info[1], (tx, y + 38, tw, 200), 15, art.TEXT, spacing=1.32)
        other = i18n.PART_INFO[key][1 if i18n.lang() == "en" else 0]
        box = pygame.Rect(DETAIL.x + 24, DETAIL.bottom - 130, DETAIL.w - 48, 110)
        if parts.is_gate(key):
            self._truth(surface, key)
        else:
            pygame.draw.rect(surface, (30, 44, 82), box, border_radius=12)
            y = art.paragraph(surface, other[0], (box.x + 14, box.y + 10, box.w - 28, 60), 14, art.TEXT_DIM)
            art.paragraph(surface, other[1], (box.x + 14, y + 2, box.w - 28, 40), 14, art.TEXT_DIM)
            self._usage_demo(surface, key, pygame.Rect(DETAIL.x + 24, pic.bottom + 20, 584, 96))

    def _usage_demo(self, surface, key, rect):
        """A friendly tip panel for each part."""
        tips = {
            "battery": ("+ goes out, - comes back. Never join + and - with only a wire!",
                        "＋から出て－にもどる。＋と－を導線だけでつながないこと！"),
            "wire": ("Copper traces on the board are wires too. A gap means no current.",
                     "基板の銅の線も導線だよ。すき間があると電気は流れない。"),
            "switch": ("Click a switch on the board to flip it ON and OFF.", "基板のスイッチはクリックでON/OFFできるよ。"),
            "button": ("In this game, click it to press and release.", "このゲームではクリックで押す・はなすを切りかえるよ。"),
            "bulb": ("Two bulbs side by side (parallel) both stay bright.", "並列につないだ2つの電球はどちらも明るく光るよ。"),
            "led": ("Long leg to +. Right-click an LED on the board to flip it.",
                    "長い足を＋側へ。基板のLEDは右クリックで向きを変えられるよ。"),
            "resistor": ("Put it in the same loop as the LED, before or after it.",
                         "LEDと同じ輪の中に入れよう。前でも後ろでもOK。"),
            "buzzer": ("Listen! It buzzes when current flows through it.", "電気が流れるとブーッと鳴るよ。"),
            "motor": ("The fan spins when the circuit is complete.", "回路がつながるとファンが回るよ。"),
        }
        tip = tips.get(key)
        if not tip:
            return
        pygame.draw.rect(surface, (40, 60, 40), rect, border_radius=12)
        pygame.draw.rect(surface, (120, 220, 140), rect, 2, border_radius=12)
        art.text(surface, "TIP", (rect.x + 14, rect.y + 10), 16, art.GREEN, kind="display")
        y = art.paragraph(surface, tip[0], (rect.x + 70, rect.y + 10, rect.w - 84, 60), 16, art.TEXT)
        art.paragraph(surface, tip[1], (rect.x + 70, y + 2, rect.w - 84, 60), 15, art.TEXT_DIM)

    def _truth(self, surface, key):
        fn = parts.PARTS[key]["fn"]
        buttons = self._gate_buttons()
        art.text(surface, i18n.t("click_try"), (DETAIL.x + 40, DETAIL.y + 296 - 30), 16, art.ACCENT)
        for i, r in enumerate(buttons):
            on = self.gate_inputs[i]
            pygame.draw.rect(surface, (30, 150, 80) if on else (70, 50, 60), r, border_radius=12)
            pygame.draw.rect(surface, art.TEXT, r, 2, border_radius=12)
            art.text(surface, f"{'AB'[i]} = {1 if on else 0}", r.center, 22, art.TEXT, kind="display",
                     anchor="center")
        a, b = self.gate_inputs
        out = bool(fn(a, b))
        cx, cy = DETAIL.x + 300, DETAIL.y + 360
        art._BG_FILL["color"] = PANEL_BG
        art.draw_gate_symbol(surface, key, (cx, cy), 120, (235, 245, 255), 3, leads=True)
        led = art.part_icon("led", 70, {"on": out, "color": "green"})
        surface.blit(led, led.get_rect(center=(cx + 130, cy - 6)))
        if out:
            art.blit_glow(surface, (cx + 130, cy - 20), 70, (60, 255, 110), 0.8)
        art.text(surface, f"OUT = {1 if out else 0}", (cx + 130, cy + 40), 22, art.GREEN if out else art.TEXT_DIM,
                 kind="display", anchor="midtop")
        # table
        tx, ty = DETAIL.x + 560, DETAIL.y + 280
        art.text(surface, i18n.t("truth_table"), (tx, ty - 28), 18, art.GOLD)
        rows = [(0,), (1,)] if key == "NOT" else [(0, 0), (0, 1), (1, 0), (1, 1)]
        heads = ["A", "OUT"] if key == "NOT" else ["A", "B", "OUT"]
        cw = 90
        for j, h in enumerate(heads):
            art.text(surface, h, (tx + j * cw + cw / 2, ty + 4), 18, art.ACCENT, kind="display", anchor="midtop")
        for i, row in enumerate(rows):
            yy = ty + 36 + i * 44
            vals = list(row) + [int(bool(fn(bool(row[0]), bool(row[1]) if len(row) > 1 else False)))]
            current = tuple(int(v) for v in ([a] if key == "NOT" else [a, b])) == row
            rr = pygame.Rect(tx, yy, cw * len(heads), 40)
            pygame.draw.rect(surface, (52, 96, 190) if current else (30, 44, 82), rr, border_radius=8)
            for j, v in enumerate(vals):
                col = art.GREEN if (j == len(vals) - 1 and v) else art.TEXT
                art.text(surface, str(v), (tx + j * cw + cw / 2, yy + 20), 20, col, kind="display", anchor="center")


PANEL_BG = (24, 34, 66)
