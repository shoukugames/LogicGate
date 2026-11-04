"""Buttons and small widgets shared by every screen."""
import pygame

from . import art


class Button:
    def __init__(self, rect, label, action=None, color=(52, 96, 190), size=24, kind="bold",
                 enabled=True, icon=None, sub=None):
        self.rect = pygame.Rect(rect)
        self.label = label          # str, or a callable returning str (for live language switching)
        self.sub = sub              # optional second line (callable or str)
        self.action = action
        self.color = color
        self.size = size
        self.kind = kind
        self.enabled = enabled
        self.icon = icon
        self.hover = 0.0
        self.hovered = False
        self.pressed = False

    def text(self):
        return self.label() if callable(self.label) else self.label

    def update(self, mouse, dt):
        self.hovered = self.enabled and self.rect.collidepoint(mouse)
        target = 1.0 if self.hovered else 0.0
        self.hover += (target - self.hover) * min(1.0, dt * 14)

    def handle(self, event, audio=None):
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            self.pressed = True
            return False
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            was = self.pressed
            self.pressed = False
            if was and self.rect.collidepoint(event.pos):
                if audio:
                    audio.play("click")
                if self.action:
                    self.action()
                return True
        return False

    def draw(self, surface):
        r = self.rect.copy()
        lift = int(self.hover * 3) - (2 if self.pressed else 0)
        r.y -= lift
        base = self.color if self.enabled else (60, 66, 84)
        hq = round(self.hover * 4) / 4
        key = ("btn", r.size, base, hq)
        body = art._cache.get(key)
        if body is None:
            top = art.shade(base, 40 + 30 * hq)
            bottom = art.shade(base, -30)
            body = pygame.Surface((r.w, r.h + 4), pygame.SRCALPHA)
            pygame.draw.rect(body, (0, 0, 0, 110), pygame.Rect(0, 4, r.w, r.h), border_radius=r.h // 3)
            face = art.gradient(r.size, top, bottom).convert_alpha()
            mask = pygame.Surface(r.size, pygame.SRCALPHA)
            pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=r.h // 3)
            face.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            body.blit(face, (0, 0))
            art._cache[key] = body
        surface.blit(body, r)
        edge = art.shade(base, 90 + 60 * self.hover) if self.enabled else (90, 96, 120)
        pygame.draw.rect(surface, edge, r, 2, border_radius=r.h // 3)
        if self.hover > 0.05:
            art.blit_glow(surface, r.center, int(r.w * 0.45), art.shade(base, 20), 0.25 * self.hover)
        color = art.TEXT if self.enabled else (140, 146, 170)
        label = self.text()
        x = r.centerx
        if self.icon:
            img = self.icon
            total = img.get_width() + 10 + art.font(self.size, self.kind).size(label)[0]
            surface.blit(img, img.get_rect(midleft=(r.centerx - total / 2, r.centery)))
            x = r.centerx + (img.get_width() + 10) / 2
        sub = self.sub() if callable(self.sub) else self.sub
        if sub:
            art.text(surface, label, (x, r.centery - self.size * 0.35), self.size, color, self.kind,
                     anchor="center", shadow=True)
            art.text(surface, sub, (x, r.centery + self.size * 0.55), int(self.size * 0.6), art.TEXT_DIM,
                     anchor="center")
        else:
            art.text(surface, label, (x, r.centery), self.size, color, self.kind, anchor="center", shadow=True)


class ButtonGroup:
    def __init__(self, buttons=None):
        self.buttons = list(buttons or [])

    def add(self, b):
        self.buttons.append(b)
        return b

    def update(self, mouse, dt):
        for b in self.buttons:
            b.update(mouse, dt)

    def handle(self, event, audio=None):
        for b in self.buttons:
            if b.handle(event, audio):
                return True
        return False

    def draw(self, surface):
        for b in self.buttons:
            b.draw(surface)


class Toast:
    """A message box that fades away."""

    def __init__(self):
        self.message = ""
        self.color = art.RED
        self.timer = 0.0

    def show(self, message, color=art.RED, seconds=4.5):
        self.message = message
        self.color = color
        self.timer = seconds

    def update(self, dt):
        self.timer = max(0.0, self.timer - dt)

    def draw(self, surface, rect, size=17):
        if self.timer <= 0 or not self.message:
            return
        alpha = min(1.0, self.timer / 0.5)
        layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        rect = pygame.Rect(rect)
        lines = art.wrap(self.message, size, rect.w - 28)
        h = len(lines) * int(size * 1.35) + 22
        box = pygame.Rect(rect.x, rect.y, rect.w, h)
        art.panel(layer, box, color=art.shade(self.color, -150), border=self.color, radius=12, alpha=240)
        y = box.y + 11
        for line in lines:
            art.text(layer, line, (box.x + 14, y), size, art.TEXT)
            y += int(size * 1.35)
        layer.set_alpha(int(255 * alpha))
        surface.blit(layer, (0, 0))


def overlay(surface, alpha=170):
    shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    shade.fill((4, 8, 20, alpha))
    surface.blit(shade, (0, 0))
