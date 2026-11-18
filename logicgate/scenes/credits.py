"""Credits and the full GNU GPL v3 licence text."""
import webbrowser

import pygame

from .. import WEB, RELEASE_DATE, __version__, art, i18n
from ..app import Scene
from ..paths import root
from ..ui import Button, ButtonGroup

WEBSITE = "https://shoukugames.org/"
EMAIL = "info@shoukugames.org"


def _back(app):
    from .title import TitleScene
    app.switch(TitleScene(app))


class CreditsScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.t = 0.0
        self.buttons = ButtonGroup([
            Button((20, 22, 150, 50), lambda: i18n.t("back"), lambda: _back(app), color=(90, 100, 140), size=20),
            Button((490, 590, 300, 52), lambda: i18n.t("view_license"), lambda: app.switch(LicenseScene(app)),
                   color=(52, 96, 190), size=20),
        ])
        self.links = {}

    def handle(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            _back(self.app)
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            for url, rect in self.links.items():
                if rect.collidepoint(event.pos):
                    try:
                        if WEB:
                            import platform  # pygbag's bridge to the page
                            platform.window.open(url, "_blank")
                        else:
                            webbrowser.open(url)
                    except Exception:  # noqa: BLE001 - no browser is fine
                        pass
        self.buttons.handle(event, self.app.audio)

    def update(self, dt):
        self.t += dt
        self.buttons.update(self.app.mouse, dt)

    def draw(self, surface):
        self.app.backdrop.draw(surface, self.t)
        box = pygame.Rect(240, 40, 800, 640)
        art.panel(surface, box, radius=24)
        art.text(surface, "LogicGate", (640, 64), 56, art.TEXT, kind="display", anchor="midtop", shadow=True)
        art.text(surface, f"v{__version__}  ·  {i18n.t('release')} {RELEASE_DATE}", (640, 138), 18, art.ACCENT,
                 anchor="midtop")
        y = 186
        rows = [
            (i18n.t("created_by"), "Shawn Rapaz"),
            (i18n.t("with"), "Claude Code (Anthropic)"),
            (i18n.t("website"), WEBSITE),
            (i18n.t("email"), EMAIL),
            (i18n.t("license"), "GNU General Public License v3.0 (GPL-3.0)"),
        ]
        self.links = {}
        for label, value in rows:
            art.text(surface, label, (600, y), 20, art.TEXT_DIM, anchor="topright")
            link = value in (WEBSITE, EMAIL)
            col = art.ACCENT if link else art.TEXT
            rect = art.text(surface, value, (624, y), 20, col)
            if link:
                pygame.draw.line(surface, col, (rect.x, rect.bottom), (rect.right, rect.bottom), 1)
                self.links[WEBSITE if value == WEBSITE else "mailto:" + EMAIL] = rect
            y += 38
        y += 8
        art.text(surface, "Ages 10+ · 対象年齢 10才以上", (640, y), 18, art.GOLD, anchor="midtop")
        y += 40
        en, ja = i18n.both("gpl_short")
        y = art.paragraph(surface, en, (300, y, 680, 100), 14, art.TEXT_DIM, align="center")
        y = art.paragraph(surface, ja, (300, y + 4, 680, 100), 13, art.TEXT_DIM, align="center")
        y += 10
        art.text(surface, i18n.t("fonts_credit"), (640, y), 13, art.TEXT_DIM, anchor="midtop")
        art.text(surface, i18n.t("music_credit"), (640, y + 22), 13, art.TEXT_DIM, anchor="midtop")
        art.text(surface, f"© 2026 Shawn Rapaz · Shouku Games", (640, 670), 13, art.TEXT_DIM, anchor="midbottom")
        self.buttons.draw(surface)


class LicenseScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.t = 0.0
        self.scroll = 0
        try:
            with open(f"{root()}/LICENSE", encoding="utf-8") as handle:
                raw = handle.read()
        except OSError:
            raw = "GNU General Public License v3.0\nhttps://www.gnu.org/licenses/gpl-3.0.html"
        self.lines = []
        for para in raw.split("\n"):
            self.lines.extend(art.wrap(para, 14, 1140, "regular") if para.strip() else [""])
        self.buttons = ButtonGroup([Button((20, 22, 150, 50), lambda: i18n.t("back"),
                                           lambda: app.switch(CreditsScene(app)), color=(90, 100, 140), size=20)])

    def handle(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.app.switch(CreditsScene(self.app))
            elif event.key in (pygame.K_DOWN, pygame.K_PAGEDOWN):
                self.scroll += 20 if event.key == pygame.K_PAGEDOWN else 3
            elif event.key in (pygame.K_UP, pygame.K_PAGEUP):
                self.scroll -= 20 if event.key == pygame.K_PAGEUP else 3
        if event.type == pygame.MOUSEWHEEL:
            self.scroll -= event.y * 3
        self.scroll = max(0, min(len(self.lines) - 28, self.scroll))
        self.buttons.handle(event, self.app.audio)

    def update(self, dt):
        self.t += dt
        self.buttons.update(self.app.mouse, dt)

    def draw(self, surface):
        self.app.backdrop.draw(surface, self.t)
        art.text(surface, "GNU GPL v3.0", (190, 30), 30, art.TEXT, kind="display")
        box = pygame.Rect(40, 90, 1200, 610)
        art.panel(surface, box)
        y = box.y + 16
        for line in self.lines[self.scroll:self.scroll + 30]:
            art.text(surface, line, (box.x + 24, y), 14, art.TEXT, kind="regular")
            y += 19.5
        total = max(1, len(self.lines) - 28)
        bar = pygame.Rect(box.right - 14, box.y + 12, 6, box.h - 24)
        pygame.draw.rect(surface, (30, 44, 82), bar, border_radius=3)
        knob = pygame.Rect(bar.x, bar.y + (bar.h - 60) * self.scroll / total, 6, 60)
        pygame.draw.rect(surface, art.ACCENT, knob, border_radius=3)
        self.buttons.draw(surface)
