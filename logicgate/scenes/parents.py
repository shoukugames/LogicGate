"""Parents Only: a simple grown-up check, then the progress record."""
import random

import pygame

from .. import art, i18n, storage
from ..app import Scene
from ..ui import Button, ButtonGroup

CIRCUIT_NAMES = {
    "simple": ("Simple loop", "かんたんな回路"),
    "and": ("Series (AND)", "直列（AND）"),
    "or": ("Parallel (OR)", "並列（OR）"),
    "parallel": ("Parallel loads", "並列の負荷"),
    "two_loops": ("Two circuits", "2つの回路"),
    "gate": ("Logic gate", "ロジックゲート"),
    "two_gates": ("Two gates", "2つのゲート"),
}
DIFF_COLORS = {"easy": (40, 160, 90), "medium": (200, 140, 30), "hard": (200, 60, 70)}


def _back(app):
    from .title import TitleScene
    app.switch(TitleScene(app))


class ParentGateScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.t = 0.0
        self.a, self.b = random.randint(6, 9), random.randint(6, 9)
        self.entry = ""
        self.wrong = 0.0
        self.buttons = ButtonGroup([Button((20, 22, 150, 50), lambda: i18n.t("back"), lambda: _back(app),
                                           color=(90, 100, 140), size=20)])
        for i, label in enumerate(["7", "8", "9", "4", "5", "6", "1", "2", "3", "←", "0", "OK"]):
            col, row = i % 3, i // 3
            rect = (520 + col * 84, 330 + row * 72, 76, 62)
            color = (30, 160, 90) if label == "OK" else (60, 80, 130)
            self.buttons.add(Button(rect, label, (lambda k=label: self.key(k)), color=color, size=26, kind="display"))

    def key(self, k):
        if k == "←":
            self.entry = self.entry[:-1]
        elif k == "OK":
            self.check()
        elif len(self.entry) < 3:
            self.entry += k

    def check(self):
        if self.entry == str(self.a * self.b):
            self.app.switch(ParentsScene(self.app))
        else:
            self.wrong = 2.0
            self.entry = ""
            self.app.audio.play("error")
            self.a, self.b = random.randint(6, 9), random.randint(6, 9)

    def handle(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                _back(self.app)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.check()
            elif event.key == pygame.K_BACKSPACE:
                self.entry = self.entry[:-1]
            elif event.unicode and event.unicode.isdigit() and len(self.entry) < 3:
                self.entry += event.unicode
        self.buttons.handle(event, self.app.audio)

    def update(self, dt):
        self.t += dt
        self.wrong = max(0.0, self.wrong - dt)
        self.buttons.update(self.app.mouse, dt)

    def draw(self, surface):
        self.app.backdrop.draw(surface, self.t)
        art.panel(surface, (400, 90, 480, 600), radius=24)
        en, ja = i18n.both("parent_gate")
        art.text(surface, i18n.t("parents"), (640, 110), 34, art.TEXT, anchor="midtop")
        art.text(surface, en, (640, 160), 16, art.TEXT_DIM, anchor="midtop")
        art.text(surface, ja, (640, 184), 15, art.TEXT_DIM, anchor="midtop")
        art.text(surface, f"{self.a} × {self.b} = ?", (640, 220), 40, art.GOLD, kind="display", anchor="midtop")
        field = pygame.Rect(540, 274, 200, 46)
        pygame.draw.rect(surface, (12, 18, 40), field, border_radius=10)
        pygame.draw.rect(surface, art.RED if self.wrong else art.ACCENT, field, 2, border_radius=10)
        art.text(surface, self.entry or " ", field.center, 30, art.TEXT, kind="display", anchor="center")
        if self.wrong:
            art.text(surface, i18n.t("parent_wrong"), (640, 640), 16, art.RED, anchor="midtop")
        self.buttons.draw(surface)


class ParentsScene(Scene):
    PER_PAGE = 9

    def __init__(self, app):
        super().__init__(app)
        self.t = 0.0
        self.data = storage.load_progress()
        self.page = 0
        self.confirm = 0.0
        self.buttons = ButtonGroup([
            Button((20, 22, 150, 50), lambda: i18n.t("back"), lambda: _back(app), color=(90, 100, 140), size=20),
            Button((1000, 22, 260, 50), lambda: i18n.t("reset_confirm") if self.confirm else i18n.t("reset"),
                   self.reset, color=(150, 60, 70), size=16),
            Button((560, 664, 70, 40), "◀", lambda: self.turn(-1), color=(60, 80, 130), size=18),
            Button((650, 664, 70, 40), "▶", lambda: self.turn(1), color=(60, 80, 130), size=18),
        ])

    def turn(self, d):
        pages = max(1, -(-len(self.data["attempts"]) // self.PER_PAGE))
        self.page = max(0, min(pages - 1, self.page + d))

    def reset(self):
        if self.confirm > 0:
            storage.reset_progress()
            self.data = storage.load_progress()
            self.confirm = 0
            self.page = 0
        else:
            self.confirm = 3.0

    def handle(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            _back(self.app)
        if event.type == pygame.MOUSEWHEEL:
            self.turn(-event.y)
        self.buttons.handle(event, self.app.audio)

    def update(self, dt):
        self.t += dt
        self.confirm = max(0.0, self.confirm - dt)
        self.buttons.update(self.app.mouse, dt)

    def stats(self):
        attempts = self.data["attempts"]
        solved = [a for a in attempts if a["result"] == "solved"]
        best = {}
        for a in attempts:
            if a["result"] == "solved":
                best[a["difficulty"]] = max(best.get(a["difficulty"], 0), a["level"])
        avg = sum(a["seconds"] for a in solved) / len(solved) if solved else 0
        first = sum(1 for a in solved if a["tests"] <= 1)
        rate = first / len(solved) * 100 if solved else 0
        return solved, best, avg, rate

    def draw(self, surface):
        self.app.backdrop.draw(surface, self.t)
        art.text(surface, i18n.t("progress"), (190, 24), 32, art.TEXT, shadow=True)
        art.text(surface, i18n.both("progress")[1 if i18n.lang() == "en" else 0], (192, 62), 15, art.TEXT_DIM)
        solved, best, avg, rate = self.stats()
        best_txt = " / ".join(f"{i18n.t(d)[:1] if i18n.lang() == 'en' else i18n.t(d)} {best[d]}"
                              for d in ("easy", "medium", "hard") if d in best) or "-"
        tiles = [(i18n.t("plays"), str(self.data["games"])), (i18n.t("solved"), str(len(solved))),
                 (i18n.t("best_level"), best_txt), (i18n.t("avg_time"), f"{avg:.1f}s" if solved else "-"),
                 (i18n.t("success_rate"), f"{rate:.0f}%" if solved else "-")]
        for i, (label, value) in enumerate(tiles):
            r = pygame.Rect(20 + i * 250, 90, 238, 90)
            art.panel(surface, r)
            art.text(surface, label, (r.x + 14, r.y + 10), 15, art.TEXT_DIM)
            art.text(surface, value, (r.x + 14, r.y + 38), 30 if len(value) < 10 else 20, art.GOLD, kind="bold")
        self._chart(surface, pygame.Rect(20, 196, 420, 460), solved)
        self._table(surface, pygame.Rect(456, 196, 804, 460))
        self.buttons.draw(surface)

    def _chart(self, surface, r, solved):
        art.panel(surface, r)
        art.text(surface, i18n.t("times_chart"), (r.x + 14, r.y + 12), 15, art.TEXT)
        recent = solved[-20:]
        plot = pygame.Rect(r.x + 46, r.y + 50, r.w - 66, r.h - 90)
        for v in (0, 30, 60, 90, 120):
            y = plot.bottom - plot.h * v / 120
            pygame.draw.line(surface, (44, 60, 104), (plot.x, y), (plot.right, y), 1)
            art.text(surface, str(v), (plot.x - 8, y), 12, art.TEXT_DIM, anchor="midright")
        if not recent:
            art.text(surface, i18n.t("no_records"), plot.center, 16, art.TEXT_DIM, anchor="center")
            return
        bw = plot.w / 20
        for i, a in enumerate(recent):
            h = plot.h * min(120, a["seconds"]) / 120
            bar = pygame.Rect(plot.x + i * bw + 3, plot.bottom - h, bw - 6, h)
            col = DIFF_COLORS.get(a["difficulty"], art.ACCENT)
            pygame.draw.rect(surface, col, bar, border_top_left_radius=4, border_top_right_radius=4)
            art.text(surface, str(a["level"]), (bar.centerx, plot.bottom + 6), 11, art.TEXT_DIM, anchor="midtop")
        x = r.x + 14
        for d in ("easy", "medium", "hard"):
            pygame.draw.rect(surface, DIFF_COLORS[d], (x, r.bottom - 22, 12, 12), border_radius=3)
            x = art.text(surface, i18n.t(d), (x + 18, r.bottom - 25), 12, art.TEXT_DIM).right + 14

    def _table(self, surface, r):
        art.panel(surface, r)
        art.text(surface, i18n.t("recent"), (r.x + 14, r.y + 12), 15, art.TEXT)
        attempts = list(reversed(self.data["attempts"]))
        if not attempts:
            art.text(surface, i18n.t("no_records"), r.center, 16, art.TEXT_DIM, anchor="center")
            return
        cols = [(i18n.t("date"), 14), (i18n.t("difficulty"), 170), (i18n.t("level"), 280), (i18n.t("circuit"), 340),
                (i18n.t("result"), 520), (i18n.t("time"), 620), (i18n.t("tries"), 690), (i18n.t("score"), 740)]
        hy = r.y + 44
        for label, x in cols:
            art.text(surface, label, (r.x + x, hy), 13, art.ACCENT)
        page = attempts[self.page * self.PER_PAGE:(self.page + 1) * self.PER_PAGE]
        y = hy + 26
        for i, a in enumerate(page):
            row = pygame.Rect(r.x + 6, y - 4, r.w - 12, 40)
            if i % 2 == 0:
                pygame.draw.rect(surface, (30, 44, 82), row, border_radius=8)
            res_col = {"solved": art.GREEN, "timeout": art.ORANGE, "quit": art.TEXT_DIM}.get(a["result"], art.TEXT)
            res_txt = {"solved": i18n.t("solved_word"), "timeout": i18n.t("timeout_word"),
                       "quit": i18n.t("quit_word")}.get(a["result"], a["result"])
            name = CIRCUIT_NAMES.get(a["circuit"], (a["circuit"], a["circuit"]))
            cells = [(a["when"], art.TEXT), (i18n.t(a["difficulty"]), DIFF_COLORS.get(a["difficulty"], art.TEXT)),
                     (str(a["level"]), art.TEXT), (name[1] if i18n.lang() == "ja" else name[0], art.TEXT),
                     (res_txt, res_col), (f"{a['seconds']:.0f}s", art.TEXT), (str(a["tests"]), art.TEXT),
                     (f"{a['score']:,}", art.GOLD)]
            for (txt, col), (_l, x) in zip(cells, cols):
                art.text(surface, txt, (r.x + x, row.centery), 14, col, anchor="midleft")
            y += 42
        pages = max(1, -(-len(attempts) // self.PER_PAGE))
        art.text(surface, f"{i18n.t('page')} {self.page + 1} / {pages}", (r.right - 16, r.bottom + 20), 14,
                 art.TEXT_DIM, anchor="midright")
