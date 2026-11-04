#!/usr/bin/env python3
"""Draw the game icon with the game's own art: assets/icon.png and assets/icon.ico.

Run this only when the design changes. Needs Pillow for the .ico file.
"""
import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)

import pygame  # noqa: E402
from PIL import Image  # noqa: E402

from logicgate import art  # noqa: E402

pygame.init()
pygame.display.set_mode((16, 16))
SIZE = 512
canvas = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
back = art.gradient((SIZE, SIZE), art.PCB_TOP, (4, 40, 30)).convert_alpha()
for x in range(16, SIZE, 32):
    for y in range(16, SIZE, 32):
        pygame.draw.circle(back, (0, 0, 0, 50), (x, y), 3)
mask = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=110)
back.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
canvas.blit(back, (0, 0))
# copper traces into the gate
for y in (196, 316):
    art.aaline(canvas, art.COPPER_DARK, (40, y + 3), (170, y + 3), 26)
    art.aaline(canvas, art.COPPER, (40, y), (170, y), 22)
    art.circle(canvas, art.SOLDER, (52, y), 22)
    art.circle(canvas, (250, 250, 255), (46, y - 6), 7)
art.aaline(canvas, art.COPPER_DARK, (360, 259), (440, 259), 26)
art.aaline(canvas, art.COPPER_LIT, (360, 256), (440, 256), 22)
art._BG_FILL["color"] = art.PCB_TOP
art.draw_gate_symbol(canvas, "AND", (262, 256), 250, (240, 250, 255), 22)
light = pygame.Surface((SIZE, SIZE))
light.fill((0, 0, 0))
art.blit_glow(light, (440, 256), 120, (255, 200, 70), 1.0)
canvas.blit(light, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
art.circle(canvas, (255, 235, 150), (440, 256), 34)
art.circle(canvas, (255, 255, 235), (432, 248), 14)
canvas.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
pygame.draw.rect(canvas, (120, 230, 180), canvas.get_rect().inflate(-8, -8), 8, border_radius=106)

png = os.path.join(ROOT, "assets", "icon.png")
pygame.image.save(canvas, png)
Image.open(png).save(os.path.join(ROOT, "assets", "icon.ico"),
                     sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("wrote assets/icon.png and assets/icon.ico")
