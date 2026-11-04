"""The puzzle screen: parts on the left, the board in the middle, the goal on the right."""
import math
import random

import pygame

from .. import art, i18n, parts, storage
from ..app import Scene
from ..board import BoardView
from ..circuit import best_led_direction, evaluate, simulate
from ..levels import SCORE_MULT, generate
from ..ui import Button, ButtonGroup, Toast, overlay

TIME_LIMIT = 120.0
PENALTY = 5.0
BOARD_RECT = pygame.Rect(236, 92, 760, 520)
PALETTE_RECT = pygame.Rect(12, 92, 212, 616)
RIGHT_RECT = pygame.Rect(1008, 92, 260, 616)
CARD_W, CARD_H = 98, 96
DIFF_COLORS = {"easy": (40, 160, 90), "medium": (200, 140, 30), "hard": (200, 60, 70)}


class GameScene(Scene):
    music = "game"

    def __init__(self, app, difficulty, seed=None):
        super().__init__(app)
        self.difficulty = difficulty
        self.rng = random.Random(seed)
        self.level_no = 0
        self.score = 0
        self.shown_score = 0.0
        self.seen_parts = set()
        self.previous_template = None
        self.toast = Toast()
        self.t = 0.0
        self.name = app.settings.get("last_name", "")
        storage.record_game_start()
        self.next_level()

    # ------------------------------------------------------------ level flow
    def next_level(self):
        self.level_no += 1
        self.level = generate(self.level_no, self.difficulty, self.rng, self.previous_template)
        self.previous_template = self.level.template
        self.circuit = self.level.circuit
        self.view = BoardView(self.circuit, BOARD_RECT, 100)
        self.view.hint = self.level.stage == "full"
        self.schematic = BoardView(self.circuit, (RIGHT_RECT.x + 10, 344, 240, 164), 240 / 7.6, pcb=False)
        self.time_left = TIME_LIMIT
        self.tests = 0
        self.drag = None          # {"kind", "from": slot or None, "pos"}
        self.press = None         # pending click on a switch
        self.cycle_t = 0.0
        self.cycle_i = 0
        self.manual_until = 0.0
        self.last_tick = None
        self.result = None
        self.sim = simulate(self.circuit)
        self.view.sim = self.sim
        self.was_short = False
        self.new_cards = [k for k in self.level.new_parts() if k not in self.seen_parts]
        if self.level.stage == "description":
            self.new_cards = []
        self.seen_parts.update(self.level.new_parts())
        self.state = "briefing"
        self._build_buttons()
        self.palette = self._palette_cards()

    def _build_buttons(self):
        self.buttons = ButtonGroup()
        r = RIGHT_RECT
        self.btn_test = self.buttons.add(Button((r.x + 10, 526, r.w - 20, 62), lambda: i18n.t("test"), self.test,
                                                color=(30, 160, 90), size=24))
        self.buttons.add(Button((r.x + 10, 600, (r.w - 30) // 2, 46), lambda: i18n.t("clear"), self.clear,
                                color=(90, 100, 140), size=18))
        self.buttons.add(Button((r.x + 20 + (r.w - 30) // 2, 600, (r.w - 30) // 2, 46), lambda: i18n.t("menu"),
                                self.pause, color=(90, 100, 140), size=18))
        self.brief_buttons = ButtonGroup([Button((540, 600, 200, 60), lambda: i18n.t("start"), self.start_level,
                                                 color=(30, 160, 90), size=26)])
        self.done_buttons = ButtonGroup([Button((RIGHT_RECT.x + 10, 620, RIGHT_RECT.w - 20, 64),
                                                lambda: i18n.t("next"), self.after_complete,
                                                color=(30, 160, 90), size=24)])
        self.pause_buttons = ButtonGroup([
            Button((520, 330, 240, 60), lambda: i18n.t("resume"), self.resume, color=(30, 160, 90), size=24),
            Button((520, 410, 240, 60), lambda: i18n.t("quit_run"), self.quit_run, color=(150, 60, 70), size=22),
        ])
        self.over_buttons = ButtonGroup([Button((540, 520, 200, 60), lambda: i18n.t("ok"), self.finish,
                                                color=(30, 160, 90), size=24)])

    def _palette_cards(self):
        cards = []
        for i, kind in enumerate(self.level.palette):
            col, row = i % 2, i // 2
            rect = pygame.Rect(PALETTE_RECT.x + 6 + col * (CARD_W + 4), PALETTE_RECT.y + 40 + row * (CARD_H + 6),
                               CARD_W, CARD_H)
            cards.append((kind, rect))
        return cards

    def start_level(self):
        self.state = "play"
        self.app.audio.play("start")
        if self.level_no == 1:
            self.toast.show(i18n.t("drag_hint"), art.ACCENT, 7)

    def after_complete(self):
        self.app.audio.stop_loops()
        self.next_level()

    # ------------------------------------------------------------ actions
    def test(self):
        if self.state != "play":
            return
        self.tests += 1
        verdict = evaluate(self.circuit)
        if verdict.ok:
            self.complete()
            return
        self.app.audio.play("error")
        self.time_left = max(0.0, self.time_left - PENALTY)
        kind = verdict.kind
        part = i18n.part_name(kind) if isinstance(kind, str) and kind in i18n.PART_NAMES else ""
        msg = i18n.t("fail_" + verdict.code, part=part, n=kind if isinstance(kind, int) else "")
        self.toast.show(f"{msg}  ({i18n.t('penalty')})", art.RED, 6)
        if verdict.code == "short":
            self.view.sparks(self.view.slot_center(self._battery()), (255, 200, 80), 50)
        if verdict.code == "burned":
            for s in self.circuit.slots:
                if s.kind == "led":
                    self.view.sparks(self.view.slot_center(s), (255, 120, 80), 25)

    def complete(self):
        self.state = "complete"
        elapsed = TIME_LIMIT - self.time_left
        mult = SCORE_MULT[self.difficulty]
        time_bonus = int(self.time_left * 10)
        level_bonus = 50 * self.level_no
        gained = int((100 + time_bonus + level_bonus) * mult)
        self.result = {"elapsed": elapsed, "time_bonus": time_bonus, "level_bonus": level_bonus,
                       "mult": mult, "gained": gained}
        self.score += gained
        self.app.audio.play("level_complete")
        storage.record_attempt(self.level_no, self.difficulty, self.level.template, "solved", elapsed,
                               self.tests, gained)
        # walk the switch positions in an order where one switch changes at a time
        n = len(self.circuit.switches())
        self.combos = [tuple(bool((g ^ (g >> 1)) >> k & 1) for k in range(n)) for g in range(2 ** n)]
        self.cycle_i = 0
        self.cycle_t = 0.0
        self._apply_combo(self.combos[-1] if n else ())
        for _ in range(40):
            x = self.rng.uniform(BOARD_RECT.left, BOARD_RECT.right)
            self.view.sparks((x, BOARD_RECT.top + 10), self.rng.choice([(255, 220, 90), (90, 220, 255),
                                                                         (120, 255, 150)]), 1)

    def _apply_combo(self, combo):
        for s, v in zip(self.circuit.switches(), combo):
            s.closed = v
        self._resim()

    def clear(self):
        if self.state == "play":
            self.circuit.clear()
            self.app.audio.play("remove")
            self._resim()

    def pause(self):
        if self.state == "play":
            self.state = "paused"

    def resume(self):
        self.state = "play"

    def quit_run(self):
        storage.record_attempt(self.level_no, self.difficulty, self.level.template, "quit",
                               TIME_LIMIT - self.time_left, self.tests, 0)
        self.game_over("quit")

    def game_over(self, why):
        self.app.audio.stop_loops()
        self.over_reason = why
        self.state = "over"
        self.high = storage.qualifies(self.score)
        if self.high:
            self.app.audio.play("new_record")
            pygame.key.start_text_input()

    def finish(self):
        if self.state != "over":
            return
        if self.high:
            name = self.name.strip() or "PLAYER"
            storage.add_score(name, self.score, self.level_no, self.difficulty)
            self.app.settings["last_name"] = name
            self.app.save()
            pygame.key.stop_text_input()
        from .title import TitleScene
        self.app.switch(TitleScene(self.app))

    def _battery(self):
        return next(s for s in self.circuit.slots if s.kind == "battery")

    def _resim(self):
        self.sim = simulate(self.circuit)
        self.view.sim = self.sim
        if self.sim.short and not self.was_short:
            self.view.sparks(self.view.slot_center(self._battery()), (255, 200, 80), 40)
            self.app.audio.play("error")
        self.was_short = self.sim.short
        on_kinds = {s.kind for s in self.circuit.outputs() if self.sim.on.get(s.id)}
        self.app.audio.loop("buzz", "buzzer" in on_kinds)
        self.app.audio.loop("motor", "motor" in on_kinds)

    # ------------------------------------------------------------ input
    def _fits(self, kind, slot):
        return slot is not None and (parts.is_gate(kind) == slot.is_gate_socket)

    def _place(self, slot, kind):
        slot.kind = kind
        if kind == "led":
            if self.difficulty == "hard":
                slot.forward = self.rng.random() < 0.5
            elif slot.solution == "led":
                slot.forward = slot.solution_forward
            else:
                slot.forward = best_led_direction(self.circuit, slot)
        if parts.is_switch(kind):
            slot.closed = False
        self.app.audio.play("drop")
        self._resim()

    def handle(self, event):
        if self.state == "over":
            self._handle_name(event)
            self.over_buttons.handle(event, self.app.audio)
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.state == "play":
                self.pause()
            elif self.state == "paused":
                self.resume()
            return
        if self.state == "briefing":
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.start_level()
            self.brief_buttons.handle(event, self.app.audio)
            return
        if self.state == "paused":
            self.pause_buttons.handle(event, self.app.audio)
            return
        if self.state == "complete":
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.after_complete()
                return
            if self.done_buttons.handle(event, self.app.audio):
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                s = self.view.slot_at(event.pos, sockets_only=False)
                if s is not None and parts.is_switch(s.kind):
                    s.closed = not s.closed
                    self.manual_until = self.t + 5
                    self.app.audio.play("switch")
                    self._resim()
            return
        # play
        if self.buttons.handle(event, self.app.audio):
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_t:
            self.test()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for kind, rect in self.palette:
                if rect.collidepoint(event.pos):
                    self.drag = {"kind": kind, "from": None, "pos": event.pos}
                    self.app.audio.play("pickup")
                    return
            s = self.view.slot_at(event.pos, sockets_only=False)
            if s is not None and s.kind:
                if parts.is_switch(s.kind):
                    self.press = {"slot": s, "pos": event.pos}
                elif s.is_socket:
                    self._lift(s, event.pos)
        elif event.type == pygame.MOUSEMOTION:
            if self.press and math.dist(event.pos, self.press["pos"]) > 8:
                s = self.press["slot"]
                self.press = None
                if s.is_socket:
                    self._lift(s, event.pos)
            if self.drag:
                self.drag["pos"] = event.pos
                target = self.view.slot_at(event.pos)
                self.view.hover = target if self._fits(self.drag["kind"], target) else None
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.press:
                s = self.press["slot"]
                self.press = None
                s.closed = not s.closed
                self.app.audio.play("switch")
                self._resim()
            elif self.drag:
                target = self.view.slot_at(event.pos)
                if self._fits(self.drag["kind"], target):
                    self._place(target, self.drag["kind"])
                elif self.drag["from"] is not None:
                    self.app.audio.play("remove")
                self.drag = None
                self.view.hover = None
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            s = self.view.slot_at(event.pos)
            if s is not None and s.kind:
                if s.kind == "led":
                    s.forward = not s.forward
                    self.app.audio.play("flip")
                else:
                    s.kind = None
                    self.app.audio.play("remove")
                self._resim()

    def _lift(self, s, pos):
        self.drag = {"kind": s.kind, "from": s, "pos": pos}
        s.kind = None
        self.app.audio.play("pickup")
        self._resim()

    def _handle_name(self, event):
        if not self.high:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.finish()
            return
        if event.type == pygame.TEXTINPUT:
            if len(self.name) < 12:
                self.name += event.text
                self.name = self.name[:12]
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.name = self.name[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.finish()

    # ------------------------------------------------------------ update
    def update(self, dt):
        self.t += dt
        self.toast.update(dt)
        mouse = self.app.mouse
        if self.state == "play":
            self.time_left -= dt
            sec = math.ceil(self.time_left)
            if sec <= 10 and sec != self.last_tick and sec > 0:
                self.app.audio.play("tick")
                self.last_tick = sec
            if self.time_left <= 0:
                self.time_left = 0
                storage.record_attempt(self.level_no, self.difficulty, self.level.template, "timeout",
                                       TIME_LIMIT, self.tests, 0)
                self.app.audio.play("time_up")
                self.game_over("timeout")
            self.buttons.update(mouse, dt)
        elif self.state == "briefing":
            self.brief_buttons.update(mouse, dt)
        elif self.state == "paused":
            self.pause_buttons.update(mouse, dt)
        elif self.state == "complete":
            self.done_buttons.update(mouse, dt)
            if self.combos and len(self.combos[0]) and self.t > self.manual_until:
                self.cycle_t += dt
                if self.cycle_t > 1.4:
                    self.cycle_t = 0
                    self.cycle_i = (self.cycle_i + 1) % len(self.combos)
                    self._apply_combo(self.combos[self.cycle_i])
                    self.app.audio.play("switch")
        elif self.state == "over":
            self.over_buttons.update(mouse, dt)
        self.shown_score += (self.score - self.shown_score) * min(1, dt * 4)
        if abs(self.score - self.shown_score) < 1:
            self.shown_score = self.score

    # ------------------------------------------------------------ drawing
    def draw(self, surface):
        self.app.backdrop.draw(surface, self.t * 0.5)
        dt = 1 / 60
        self._top_bar(surface)
        self._palette(surface)
        self.view.draw(surface, dt)
        self._right(surface)
        if self.state == "play":
            if self.sim.short and self.toast.timer < 0.6:
                self.toast.show(i18n.t("fail_short"), art.ORANGE, 0.6)
            self.toast.draw(surface, (BOARD_RECT.x, BOARD_RECT.bottom + 8, BOARD_RECT.w, 100))
            if self.toast.timer <= 0:
                key = "stage_" + self.level.stage
                art.text(surface, f"{i18n.t('level')} {self.level_no}  ·  {i18n.t(key)}",
                         (BOARD_RECT.centerx, BOARD_RECT.bottom + 22), 16, art.TEXT_DIM, anchor="center")
                art.text(surface, i18n.t("drag_hint"), (BOARD_RECT.centerx, BOARD_RECT.bottom + 50), 14,
                         art.TEXT_DIM, anchor="center")
            if self.drag:
                self._drag_image(surface)
        elif self.state == "complete":
            self._complete(surface)
        elif self.state == "briefing":
            self._briefing(surface)
        elif self.state == "paused":
            overlay(surface, 235)
            art.text(surface, i18n.t("paused"), (640, 250), 54, art.TEXT, kind="display", anchor="center")
            self.pause_buttons.draw(surface)
        elif self.state == "over":
            self._over(surface)

    def _top_bar(self, surface):
        bar = pygame.Rect(12, 10, 1256, 72)
        art.panel(surface, bar, radius=18)
        art.text(surface, i18n.t("level"), (34, 18), 15, art.TEXT_DIM)
        art.text(surface, str(self.level_no), (34, 34), 34, art.TEXT, kind="display")
        badge = pygame.Rect(110, 40, 110, 28)
        pygame.draw.rect(surface, DIFF_COLORS[self.difficulty], badge, border_radius=14)
        art.text(surface, i18n.t(self.difficulty), badge.center, 15, art.TEXT, anchor="center")
        # timer
        tl = max(0.0, self.time_left)
        frac = tl / TIME_LIMIT
        col = art.GREEN if tl > 40 else (art.GOLD if tl > 15 else art.RED)
        cx = 640
        track = pygame.Rect(cx - 260, 60, 520, 12)
        pygame.draw.rect(surface, (20, 26, 48), track, border_radius=6)
        fill = track.copy()
        fill.w = max(0, int(track.w * frac))
        if fill.w:
            pygame.draw.rect(surface, col, fill, border_radius=6)
            pygame.draw.rect(surface, art.shade(col, 70), (fill.x + 4, fill.y + 2, max(0, fill.w - 8), 3),
                             border_radius=2)
        pulse = 1.0
        if tl <= 10 and self.state == "play":
            pulse = 1 + 0.12 * abs(math.sin(self.t * math.pi))
            art.blit_glow(surface, (cx, 34), int(70 * pulse), (255, 60, 60), 0.4)
        size = int(40 * pulse)
        art.text(surface, f"{math.ceil(tl):d}", (cx, 34), size, col, kind="display", anchor="center", shadow=True)
        art.text(surface, i18n.t("time"), (cx - 70, 34), 15, art.TEXT_DIM, anchor="midright")
        art.text(surface, "s", (cx + 52, 40), 16, art.TEXT_DIM, anchor="midleft")
        art.text(surface, i18n.t("score"), (1246, 18), 15, art.TEXT_DIM, anchor="topright")
        art.text(surface, f"{int(self.shown_score):,}", (1246, 34), 34, art.GOLD, kind="display", anchor="topright")

    def _palette(self, surface):
        art.panel(surface, PALETTE_RECT)
        art.text(surface, i18n.t("parts"), (PALETTE_RECT.centerx, PALETTE_RECT.y + 10), 20, art.GOLD,
                 anchor="midtop")
        mouse = self.app.mouse
        for kind, rect in self.palette:
            hover = rect.collidepoint(mouse) and self.state == "play" and not self.drag
            col = (48, 70, 124) if hover else (32, 46, 86)
            pygame.draw.rect(surface, col, rect, border_radius=12)
            pygame.draw.rect(surface, art.ACCENT if hover else (70, 96, 160), rect, 2, border_radius=12)
            state = {"color": self.circuit.slots[0].led_color} if kind == "led" else {}
            if kind == "wire":
                state = {"color": (230, 60, 60)}
            img = art.part_icon(kind, 64, state)
            surface.blit(img, img.get_rect(center=(rect.centerx, rect.y + 40)))
            name = i18n.part_name(kind)
            size = 14 if len(name) < 11 else 12
            art.text(surface, name, (rect.centerx, rect.bottom - 14), size, art.TEXT, anchor="center")
        if self.palette:
            last = self.palette[-1][1]
            if last.bottom + 70 < PALETTE_RECT.bottom:
                art.paragraph(surface, i18n.t("tutorial") if self.level_no <= 2 else "",
                              (PALETTE_RECT.x + 12, last.bottom + 16, PALETTE_RECT.w - 24, 200), 13, art.TEXT_DIM)

    def _drag_image(self, surface):
        kind = self.drag["kind"]
        state = {"color": self.circuit.slots[0].led_color} if kind == "led" else {}
        img = art.part_image(kind, 100, state)
        x, y = self.drag["pos"]
        sh = pygame.mask.from_surface(img).to_surface(setcolor=(0, 0, 0, 80), unsetcolor=(0, 0, 0, 0))
        surface.blit(sh, sh.get_rect(center=(x + 8, y + 10)))
        surface.blit(img, img.get_rect(center=(x, y)))

    def _right(self, surface):
        r = RIGHT_RECT
        art.panel(surface, (r.x, r.y, r.w, 220))
        art.text(surface, i18n.t("goal"), (r.x + 14, r.y + 10), 20, art.GOLD)
        art.paragraph(surface, self.level.text[i18n.lang()], (r.x + 14, r.y + 42, r.w - 28, 170),
                      16 if i18n.lang() == "en" else 15, art.TEXT, spacing=1.3)
        if self.state == "complete":
            return
        sp = pygame.Rect(r.x, 320, r.w, 192)
        art.panel(surface, sp)
        art.text(surface, i18n.t("schematic"), (sp.x + 14, sp.y + 4), 15, art.GOLD)
        if self.level.stage in ("full", "symbols"):
            self.schematic.draw(surface)
        else:
            art.paragraph(surface, i18n.t("no_schematic"), (sp.x + 16, sp.y + 70, sp.w - 32, 100), 16,
                          art.TEXT_DIM, align="center")
            art.text(surface, "?", (sp.centerx, sp.y + 50), 34, (90, 110, 170), kind="display", anchor="center")
        self.buttons.draw(surface)

    def _complete(self, surface):
        # banner over the board
        t = self.t
        b = pygame.Rect(BOARD_RECT.centerx - 230, BOARD_RECT.y - 6, 460, 56)
        art.panel(surface, b, color=(20, 90, 60), border=(120, 255, 170), radius=18)
        art.text(surface, i18n.t("complete"), b.center, 30, (220, 255, 230), anchor="center", shadow=True)
        art.text(surface, i18n.t("watch"), (BOARD_RECT.centerx, BOARD_RECT.bottom + 26), 17, art.ACCENT,
                 anchor="center")
        r = RIGHT_RECT
        p = pygame.Rect(r.x, 320, r.w, 290)
        art.panel(surface, p, color=(20, 50, 44), border=(120, 255, 170))
        res = self.result
        y = p.y + 16
        art.text(surface, i18n.t("solved_in", t=f"{res['elapsed']:.1f}"), (p.centerx, y), 17, art.TEXT,
                 anchor="midtop")
        y += 38
        rows = [(i18n.t("time_bonus"), res["time_bonus"]), (i18n.t("level_bonus"), res["level_bonus"]),
                (i18n.t("base"), 100), (i18n.t("multiplier"), f"x{res['mult']:.1f}")]
        for label, value in rows:
            art.text(surface, label, (p.x + 18, y), 16, art.TEXT_DIM)
            art.text(surface, f"{value}", (p.right - 18, y), 16, art.TEXT, anchor="topright")
            y += 28
        pygame.draw.line(surface, (120, 255, 170), (p.x + 16, y + 4), (p.right - 16, y + 4), 1)
        y += 14
        art.text(surface, f"+{res['gained']:,}", (p.centerx, y + 4), 38, art.GOLD, kind="display", anchor="midtop")
        stars = 3 if res["elapsed"] < 40 else (2 if res["elapsed"] < 80 else 1)
        for i in range(3):
            cx = p.centerx + (i - 1) * 44
            self._star(surface, (cx, p.bottom - 34), 17, art.GOLD if i < stars else (60, 70, 90),
                       t * 2 + i if i < stars else 0)
        self.done_buttons.draw(surface)

    def _star(self, surface, center, r, color, spin):
        pts = []
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5
            rr = r if i % 2 == 0 else r * 0.45
            pts.append((center[0] + math.cos(a) * rr, center[1] + math.sin(a) * rr))
        pygame.draw.polygon(surface, color, pts)
        if color == art.GOLD:
            art.blit_glow(surface, center, int(r * 1.8), (255, 190, 60), 0.35 + 0.1 * math.sin(spin))

    def _briefing(self, surface):
        overlay(surface, 200)
        box = pygame.Rect(200, 70, 880, 610)
        art.panel(surface, box, radius=24)
        art.text(surface, f"{i18n.t('level')} {self.level_no}", (box.centerx, box.y + 20), 46, art.TEXT,
                 kind="display", anchor="midtop", shadow=True)
        key = "stage_" + self.level.stage
        tag = pygame.Rect(0, 0, 260, 30)
        tag.midtop = (box.centerx, box.y + 82)
        pygame.draw.rect(surface, DIFF_COLORS[self.difficulty], tag, border_radius=15)
        art.text(surface, f"{i18n.t(self.difficulty)} · {i18n.t(key)}", tag.center, 15, art.TEXT, anchor="center")
        # goal in both languages
        y = box.y + 130
        art.text(surface, i18n.t("goal"), (box.x + 40, y), 20, art.GOLD)
        y = art.paragraph(surface, self.level.text["en"], (box.x + 40, y + 30, box.w - 80, 80), 19, art.TEXT)
        y = art.paragraph(surface, self.level.text["ja"], (box.x + 40, y + 6, box.w - 80, 80), 17, art.TEXT_DIM)
        cards = self.new_cards
        if cards:
            y += 14
            art.text(surface, i18n.t("new_parts"), (box.x + 40, y), 18, art.GOLD)
            y += 30
            n = len(cards)
            cw = min(260, (box.w - 80 - (n - 1) * 12) // n)
            for i, kind in enumerate(cards):
                cr = pygame.Rect(box.x + 40 + i * (cw + 12), y, cw, box.bottom - 100 - y)
                pygame.draw.rect(surface, (32, 46, 86), cr, border_radius=14)
                pygame.draw.rect(surface, (70, 96, 160), cr, 2, border_radius=14)
                state = {"on": True, "color": self.circuit.slots[0].led_color, "closed": True}
                img = art.part_icon(kind, 96, state)
                surface.blit(img, img.get_rect(center=(cr.centerx, cr.y + 56)))
                if kind in ("bulb", "led"):
                    col = (255, 190, 70) if kind == "bulb" else parts.LED_COLORS[self.circuit.slots[0].led_color]
                    art.blit_glow(surface, (cr.centerx, cr.y + 40), 50, col, 0.6)
                art.text(surface, i18n.part_name(kind), (cr.centerx, cr.y + 110), 17, art.TEXT, anchor="midtop")
                desc = i18n.part_info(kind)[0].split(". ")[0].rstrip(".") + "."
                if i18n.lang() == "ja":
                    desc = i18n.part_info(kind)[0].split("。")[0] + "。"
                art.paragraph(surface, desc, (cr.x + 10, cr.y + 140, cr.w - 20, cr.h - 150),
                              13 if n > 3 else 14, art.TEXT_DIM, spacing=1.25)
        elif self.level.stage == "description":
            art.paragraph(surface, i18n.t("no_schematic"), (box.x + 40, y + 30, box.w - 80, 100), 20, art.ACCENT,
                          align="center")
        self.brief_buttons.draw(surface)

    def _over(self, surface):
        overlay(surface, 220)
        box = pygame.Rect(340, 120, 600, 480)
        art.panel(surface, box, radius=24)
        title = i18n.t("times_up") if self.over_reason == "timeout" else i18n.t("game_over")
        art.text(surface, title, (box.centerx, box.y + 30), 48, art.RED if self.over_reason == "timeout" else art.TEXT,
                 kind="display", anchor="midtop", shadow=True)
        art.text(surface, i18n.t("final_score"), (box.centerx, box.y + 120), 18, art.TEXT_DIM, anchor="midtop")
        art.text(surface, f"{self.score:,}", (box.centerx, box.y + 146), 52, art.GOLD, kind="display",
                 anchor="midtop")
        art.text(surface, i18n.t("reached", n=self.level_no), (box.centerx, box.y + 218), 18, art.TEXT,
                 anchor="midtop")
        if self.high:
            art.text(surface, i18n.t("new_high"), (box.centerx, box.y + 270), 18, art.GOLD, anchor="midtop")
            field = pygame.Rect(box.centerx - 160, box.y + 302, 320, 52)
            pygame.draw.rect(surface, (12, 18, 40), field, border_radius=12)
            pygame.draw.rect(surface, art.ACCENT, field, 2, border_radius=12)
            caret = "|" if int(self.t * 2) % 2 == 0 else " "
            art.text(surface, self.name + caret, field.center, 26, art.TEXT, anchor="center")
        self.over_buttons.draw(surface)
