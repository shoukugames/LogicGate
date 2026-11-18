"""Music and sound effects. If there is no audio device the game stays silent."""
import os

import pygame

from . import WEB
from .paths import asset

MUSIC = {"title": "bgm_title.wav", "game": "bgm_game.wav"}
EFFECTS = ["click", "hover", "pickup", "drop", "remove", "switch", "flip", "error", "tick",
           "success", "level_complete", "time_up", "buzz", "motor", "start", "new_record"]
VOLUME = {"hover": 0.25, "tick": 0.5, "buzz": 0.35, "motor": 0.4, "click": 0.6}


class Audio:
    def __init__(self, settings):
        self.settings = settings
        self.ok = False
        self.sounds = {}
        self.current = None
        self.loops = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(44100, -16, 2, 1024)
            pygame.mixer.set_num_channels(24)
            for name in EFFECTS:
                snd = pygame.mixer.Sound(asset("audio", name + ".wav"))
                snd.set_volume(VOLUME.get(name, 0.8))
                self.sounds[name] = snd
            self.ok = True
        except (pygame.error, FileNotFoundError, OSError) as error:
            print(f"Audio disabled: {error}")

    def play(self, name):
        if self.ok and self.settings["sfx"] and name in self.sounds:
            self.sounds[name].play()

    def loop(self, name, on):
        """Keep a looping effect (buzzer, motor) running while 'on'."""
        if not self.ok:
            return
        playing = name in self.loops
        if on and self.settings["sfx"] and not playing:
            self.loops[name] = self.sounds[name].play(-1, fade_ms=60)
        elif (not on or not self.settings["sfx"]) and playing:
            channel = self.loops.pop(name)
            if channel:
                channel.fadeout(120)

    def stop_loops(self):
        for name in list(self.loops):
            self.loop(name, False)

    def music(self, which):
        if not self.ok:
            return
        if not self.settings["bgm"]:
            if WEB:  # a new track waits for a fade-out, which can't finish while the page waits
                pygame.mixer.music.stop()
            else:
                pygame.mixer.music.fadeout(400)
            self.current = None
            return
        if which == self.current:
            return
        self.current = which
        try:
            pygame.mixer.music.load(asset("audio", MUSIC[which]))
            pygame.mixer.music.set_volume(0.55)
            pygame.mixer.music.play(-1, fade_ms=1500)
        except pygame.error as error:
            print(f"Music unavailable: {error}")

    def refresh_music(self, which):
        self.current = None if self.settings["bgm"] else self.current
        self.music(which)


def exists():
    return os.path.exists(asset("audio", "click.wav"))
