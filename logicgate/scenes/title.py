"""Title screen: menu, settings, top 10 table and bilingual instructions."""
import math

import pygame

from .. import WEB, __version__, art, i18n, storage
from ..app import Scene
from ..levels import DIFFICULTIES
from ..ui import Button, ButtonGroup

DIFF_COLORS = {"easy": (40, 160, 90), "medium": (200, 140, 30), "hard": (200, 60, 70)}


def _other(key):
    en, ja = i18n.both(key)
    return en if i18n.lang() == "ja" else ja


class TitleScene(Scene):
    music = "title"

    def __init__(self, app):
        super().__init__(app)
        self.t = 0.0
        self.scores = storage.load_scores()
        self.buttons = ButtonGroup()
        x, y, w = 50, 196, 320
        self.buttons.add(Button((x, y, w, 70), lambda: i18n.t("play"), self.play, color=(30, 160, 90),
                                size=32, sub=lambda: _other("play")))
        items = [("intro", self.intro, (52, 96, 190)), ("parents", self.parents, (110, 80, 180)),
                 ("credits", self.credits, (52, 96, 190))] + ([] if WEB else [("quit", self.quit, (120, 60, 80))])
        y += 84
        for key, action, color in items:
            self.buttons.add(Button((x, y, w, 52), (lambda k=key: i18n.t(k)), action, color=color, size=22,
                                    sub=(lambda k=key: _other(k))))
            y += 62
        # difficulty selector
        self.diff_buttons = []
        dy = 556
        for i, d in enumerate(DIFFICULTIES):
            b = Button((x + i * 108, dy, 100, 40), (lambda d=d: i18n.t(d)), (lambda d=d: self.set_diff(d)),
                       color=DIFF_COLORS[d], size=17)
            self.diff_buttons.append((d, b))
            self.buttons.add(b)
        ty = 640
        self.buttons.add(Button((x, ty, 100, 40), lambda: f"♪ {i18n.t('on') if self.app.settings['bgm'] else i18n.t('off')}",
                                self.toggle_bgm, color=(60, 80, 130), size=17))
        self.buttons.add(Button((x + 108, ty, 100, 40),
                                lambda: f"FX {i18n.t('on') if self.app.settings['sfx'] else i18n.t('off')}",
                                self.toggle_sfx, color=(60, 80, 130), size=17))
        self.buttons.add(Button((x + 216, ty, 100, 40), lambda: "日本語" if i18n.lang() == "en" else "English",
                                self.toggle_lang, color=(60, 80, 130), size=17))

    # actions
    def play(self):
        from .game import GameScene
        self.app.switch(GameScene(self.app, self.app.settings["difficulty"]))

    def intro(self):
        from .intro import IntroScene
        self.app.switch(IntroScene(self.app))

    def parents(self):
        from .parents import ParentGateScene
        self.app.switch(ParentGateScene(self.app))

    def credits(self):
        from .credits import CreditsScene
        self.app.switch(CreditsScene(self.app))

    def quit(self):
        self.app.running = False

    def set_diff(self, d):
        self.app.settings["difficulty"] = d
        self.app.save()

    def toggle_bgm(self):
        self.app.settings["bgm"] = not self.app.settings["bgm"]
        self.app.save()
        self.app.audio.current = None
        self.app.audio.music("title")

    def toggle_sfx(self):
        self.app.settings["sfx"] = not self.app.settings["sfx"]
        self.app.save()

    def toggle_lang(self):
        self.app.set_language("ja" if i18n.lang() == "en" else "en")

    def handle(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.play()
            elif event.key == pygame.K_ESCAPE and not WEB:
                self.quit()
        self.buttons.handle(event, self.app.audio)

    def update(self, dt):
        self.t += dt
        self.buttons.update(self.app.mouse, dt)

    # drawing
    def _logo(self, surface):
        t = self.t
        cx = 50
        # gate emblem
        ex, ey = cx + 44, 92
        art.blit_glow(surface, (ex, ey), 70, (40, 140, 255), 0.6 + 0.15 * math.sin(t * 2))
        art._BG_FILL["color"] = (14, 22, 48)
        art.draw_gate_symbol(surface, "AND", (ex, ey), 70, (120, 220, 255), 4, leads=True)
        on = int(t / 1.2) % 2 == 0
        art.circle(surface, (255, 220, 90) if on else (80, 70, 40), (ex + 56, ey), 8)
        if on:
            art.blit_glow(surface, (ex + 56, ey), 30, (255, 200, 80), 0.9)
        title = "LogicGate"
        art.text(surface, title, (cx + 110, 40), 66, (20, 40, 90), kind="display")
        art.text(surface, title, (cx + 106, 36), 66, (235, 245, 255), kind="display")
        art.text(surface, "ロジックゲート  ·  " + i18n.t("title_sub"), (cx + 112, 120), 20, art.ACCENT)

    def _ages(self, surface):
        r = pygame.Rect(1050, 34, 190, 58)
        art.panel(surface, r, color=(120, 40, 60), border=(255, 140, 150), radius=14)
        art.text(surface, "Ages 10+", (r.centerx, r.y + 18), 22, art.TEXT, anchor="center")
        art.text(surface, "対象年齢 10才以上", (r.centerx, r.y + 42), 15, (255, 210, 215), anchor="center")

    def _how_to(self, surface):
        r = pygame.Rect(400, 182, 430, 508)
        art.panel(surface, r)
        art.text(surface, "How to Play", (r.x + 20, r.y + 14), 24, art.GOLD)
        y = r.y + 50
        for line in i18n.HOW_TO["en"]:
            art.circle(surface, art.ACCENT, (r.x + 26, y + 11), 4)
            y = art.paragraph(surface, line, (r.x + 38, y, r.w - 56, 100), 16, art.TEXT, spacing=1.32) + 4
        pygame.draw.line(surface, (60, 90, 150), (r.x + 20, y + 4), (r.right - 20, y + 4), 1)
        y += 14
        art.text(surface, "遊び方", (r.x + 20, y), 24, art.GOLD)
        y += 36
        for line in i18n.HOW_TO["ja"]:
            art.circle(surface, art.ACCENT, (r.x + 26, y + 11), 4)
            y = art.paragraph(surface, line, (r.x + 38, y, r.w - 56, 100), 15, art.TEXT, spacing=1.36) + 4

    def _scores(self, surface):
        r = pygame.Rect(850, 110, 390, 580)
        art.panel(surface, r)
        art.text(surface, "Top 10", (r.x + 20, r.y + 14), 26, art.GOLD, kind="display")
        art.text(surface, "トップ10", (r.right - 20, r.y + 20), 18, art.TEXT_DIM, anchor="topright")
        hy = r.y + 60
        for label, x in ((i18n.t("score"), r.x + 196), (i18n.t("level"), r.x + 262)):
            art.text(surface, label, (x, hy), 13, art.TEXT_DIM, anchor="midtop")
        if not self.scores:
            art.paragraph(surface, i18n.both("no_scores")[0] + "\n" + i18n.both("no_scores")[1],
                          (r.x + 24, r.y + 120, r.w - 48, 200), 17, art.TEXT_DIM, align="center")
            return
        y = r.y + 82
        medal = [(255, 205, 80), (210, 215, 230), (215, 140, 80)]
        for i, s in enumerate(self.scores):
            row = pygame.Rect(r.x + 12, y, r.w - 24, 46)
            if i % 2 == 0:
                pygame.draw.rect(surface, (30, 44, 82), row, border_radius=10)
            c = medal[i] if i < 3 else (90, 110, 160)
            art.circle(surface, c, (row.x + 22, row.centery), 15)
            art.text(surface, str(i + 1), (row.x + 22, row.centery), 16, (20, 20, 30) if i < 3 else art.TEXT,
                     anchor="center")
            art.text(surface, s["name"][:12], (row.x + 46, row.centery), 18, art.TEXT, anchor="midleft")
            art.text(surface, f"{s['score']:,}", (row.x + 184, row.centery), 18, art.GOLD, kind="display",
                     anchor="center")
            art.text(surface, str(s["level"]), (row.x + 250, row.centery), 18, art.TEXT, anchor="center")
            d = s.get("difficulty", "easy")
            badge = pygame.Rect(row.right - 78, row.centery - 11, 70, 22)
            pygame.draw.rect(surface, DIFF_COLORS.get(d, (90, 90, 90)), badge, border_radius=11)
            art.text(surface, i18n.t(d) if d in DIFFICULTIES else d, badge.center, 12, art.TEXT, anchor="center")
            y += 49

    def draw(self, surface):
        self.app.backdrop.draw(surface, self.t)
        self._logo(surface)
        self._ages(surface)
        self._how_to(surface)
        self._scores(surface)
        x = 50
        art.text(surface, f"{i18n.t('difficulty')}", (x, 530), 17, art.TEXT_DIM)
        art.text(surface, f"{i18n.t('bgm')} · {i18n.t('sfx')} · {i18n.t('language')}", (x, 614), 17, art.TEXT_DIM)
        self.buttons.draw(surface)
        current = self.app.settings["difficulty"]
        for d, b in self.diff_buttons:
            if d == current:
                pygame.draw.rect(surface, (255, 255, 255), b.rect.inflate(6, 6), 3, border_radius=b.rect.h // 3 + 3)
        art.text(surface, f"v{__version__}  ·  Shouku Games  ·  F11 fullscreen", (640, 712), 13, art.TEXT_DIM,
                 anchor="midbottom")
