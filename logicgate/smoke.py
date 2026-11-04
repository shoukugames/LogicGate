"""Automatic self-test: visits every screen and solves real puzzles.

Used by the build scripts to prove a packaged game really starts and plays:
    logicgate --smoke-test result.txt
Set LOGICGATE_SHOTS=<folder> to also save a screenshot of each screen.
"""
import os
import random
import sys
import tempfile
import traceback


def smoke_test(out_path=None):
    os.environ.setdefault("LOGICGATE_DATA", tempfile.mkdtemp(prefix="logicgate-smoke-"))
    shots = os.environ.get("LOGICGATE_SHOTS")
    lines = []
    ok = True
    try:
        import pygame

        from . import circuit, i18n, levels
        from .app import App
        from .scenes.credits import CreditsScene, LicenseScene
        from .scenes.game import GameScene
        from .scenes.intro import IntroScene
        from .scenes.parents import ParentGateScene, ParentsScene
        from .scenes.title import TitleScene

        app = App(windowed=True, smoke=True)
        count = {"n": 0}

        def frames(scene, n=20, name=None):
            for _ in range(n):
                pygame.event.pump()
                scene.update(1 / 60)
                scene.draw(app.canvas)
                app.present()
            if shots and name:
                os.makedirs(shots, exist_ok=True)
                count["n"] += 1
                pygame.image.save(app.canvas, os.path.join(shots, f"{count['n']:02d}_{name}.png"))

        # Every screen, in both languages
        for language in ("en", "ja"):
            app.set_language(language)
            for cls in (TitleScene, CreditsScene, LicenseScene, ParentGateScene, ParentsScene):
                scene = cls(app)
                app.switch(scene)
                frames(scene, 10, f"{cls.__name__}_{language}")
            intro = IntroScene(app)
            app.switch(intro)
            for i in range(len(intro.entries)):
                intro._select(i)
                key = intro.entries[i][1]
                frames(intro, 3, f"intro_{key}_{language}" if key in ("circuit", "logic", "led", "AND", "motor")
                       else None)
        lines.append("screens ok")
        app.set_language("en")

        # Play and solve real, random levels on every difficulty
        solved = 0
        for diff in levels.DIFFICULTIES:
            game = GameScene(app, diff, seed=42)
            app.switch(game)
            for n in range(1, 13):
                frames(game, 4, f"game_{diff}_{n}_brief" if n in (1, 6, 10) else None)
                game.start_level()
                if n == 2:
                    # a wrong answer must be refused with a message
                    game.circuit.clear()
                    game.test()
                    assert game.state == "play" and game.toast.timer > 0, "empty board accepted"
                game.circuit.place_solution()
                game._resim()
                frames(game, 4, f"game_{diff}_{n}_play" if n in (1, 6, 10) else None)
                game.test()
                if game.state != "complete":
                    raise AssertionError(f"{diff} level {n} ({game.level.template}) solution refused")
                solved += 1
                frames(game, 40, f"game_{diff}_{n}_done" if n in (1, 6, 10) else None)
                game.after_complete()
            game.circuit.place_solution()
            game.game_over("quit")
            game.name = "SMOKE"
            frames(game, 4, f"game_over_{diff}")
            game.finish()
        lines.append(f"solved {solved} random levels")

        # The generator must always give solvable puzzles
        rng = random.Random(7)
        for _ in range(300):
            lv = levels.generate(rng.randint(1, 30), rng.choice(levels.DIFFICULTIES), rng)
            lv.circuit.place_solution()
            if not circuit.evaluate(lv.circuit).ok:
                raise AssertionError(f"unsolvable {lv.template}")
        lines.append("generator ok")
        frames(TitleScene(app), 5, "title_scores")
        i18n.LANG["current"] = "en"
        app.audio.stop_loops()
        pygame.quit()
    except Exception:  # noqa: BLE001 - report every failure
        ok = False
        lines.append("FAILED\n" + traceback.format_exc())
    text = ("OK " if ok else "") + "; ".join(lines)
    if out_path:
        with open(out_path, "w", encoding="utf-8") as handle:
            handle.write(text + "\n")
    print(text, file=sys.stdout if ok else sys.stderr)
    return 0 if ok else 1
