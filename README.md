# LogicGate v0.1.0

**Build circuits. Learn logic.** · **回路を作って、ロジックを学ぼう。**

LogicGate is a circuit-building puzzle game for **ages 10+**, in **English and Japanese**.
Drag real-looking parts (batteries, switches, light bulbs, LEDs, resistors,
buzzers, motors and logic gate chips) onto a circuit board and finish each
circuit before the **120-second** timer runs out. When the circuit works it
comes to life: bulbs glow, LEDs light, buzzers buzz, fans spin, current flows
along the copper, and the switches flip on and off by themselves so you can see
what you built.

- Creator: **Shawn Rapaz**, with **Claude Code**
- Website: <https://shoukugames.org/> · Email: <info@shoukugames.org>
- Release: v0.1.0, 2026-11-04
- License: **GNU GPL v3.0** (see [LICENSE](LICENSE))

## Features

- **Introduction** section: what every part looks like, its schematic symbol,
  what it does and where it is used. Each page has a live demo, plus pages on
  circuits, series (AND), parallel (OR), short circuits and logic gates with
  interactive truth tables.
- **Drag and drop** building: a parts tray on the left, the board in the middle,
  and the goal and schematic on the right. Right-click a placed part to flip it
  (LEDs) or remove it. Click switches to try your circuit while you build.
- **Every circuit is randomized**, including its parts, layout, LED colour and
  which sockets are empty, across 7 kinds of puzzle: simple loops, doorbells,
  series (AND), parallel (OR), parallel loads, two separate circuits, single
  logic gates (AND, OR, NOT, NAND, NOR, XOR) and two-gate combinations.
- **Help fades as you improve:**
  1. *Schematic + hints*: ghost parts show what goes where.
  2. *Schematic only*: read the blueprint and work out the parts.
  3. *Description only*: only the goal text, and on Medium and Hard some copper
     is missing too.
- **Difficulty:** Easy, Medium or Hard. Harder levels bring in new puzzle types
  sooner, remove the help sooner, add more decoy parts, and score up to 2×.
- **Friendly feedback** on a failed test (each one costs 5 seconds): short
  circuit, burned-out LED (no resistor), backwards LED, missing parts, wrong
  logic.
- **Scoring by speed:** 100 points for a finished circuit, plus 10 points per
  second left on the timer, plus a level bonus, all multiplied by difficulty.
  The run ends when time runs out.
- **Top 10 scoreboard** and bilingual instructions on the title screen.
- **Parents Only** (behind a simple multiplication question): games played,
  circuits solved, highest level, average solve time, first-try success rate,
  a solve-time chart and a table of every circuit with date, level, time, tests
  and score.
- **Relaxing ambient music** (with an on/off toggle) and sound effects, all
  original and synthesised for this game.
- **Credits** with the full GPL v3.0 text.

## Controls

| Action | Control |
| --- | --- |
| Place a part | Drag it from the left tray onto a dashed socket |
| Move or remove a part | Drag it to another socket, or off the board |
| Flip an LED / remove a part | Right-click it |
| Flip a switch | Click it |
| Test the circuit | **Test Circuit** button or `T` |
| Pause | `Esc` or **Menu** |
| Full screen | `F11` |

## Install

- **Windows:** run `LogicGate-v0.1.0.exe`. Nothing to install.
- **Debian / Ubuntu:** `sudo apt install ./logicgate_v0.1.0_amd64.deb`, then
  start *LogicGate* from the games menu or type `logicgate`.

Saved data (settings, scores, parent records) lives in
`%APPDATA%\LogicGate` on Windows and `~/.local/share/logicgate` on Linux.

## Run from source

```sh
python3 -m pip install -r requirements.txt
python3 run_game.py            # add --windowed to ignore the saved full-screen setting
```

## Build the installers

```sh
./build.sh                     # both
packaging/build_linux.sh       # dist/logicgate_v0.1.0_amd64.deb
packaging/build_windows.sh     # dist/LogicGate-v0.1.0.exe (built on Linux with Wine)
```

The Linux build needs `python3-venv` and `dpkg-deb`. The Windows build needs
`wine` and `xvfb-run`; the first run downloads Windows Python into a private
Wine prefix under `build/`. Each build ends by running the packaged game's
built-in self-test (`--smoke-test`), which opens every screen in both languages
and solves 36 random puzzles.

## Development

```sh
python3 -m pip install -r requirements-dev.txt
python3 -m pytest              # unit tests: simulator, puzzle generator, storage
python3 tools/make_audio.py    # regenerate assets/audio (needs numpy)
python3 tools/make_icon.py     # regenerate assets/icon.png / icon.ico (needs pillow)
```

Code layout: `logicgate/circuit.py` (circuit model, simulator, grader),
`levels.py` (random puzzle templates), `board.py` (board and schematic
drawing), `art.py` (all part artwork), `scenes/` (title, game, introduction,
parents, credits).

## Reporting bugs

See [BUGREPORT.md](BUGREPORT.md).

## Credits

- Game design and production: Shawn Rapaz, with Claude Code
- Fonts: [M PLUS 1p](https://fonts.google.com/specimen/M+PLUS+1p) and
  [Orbitron](https://fonts.google.com/specimen/Orbitron), SIL Open Font License 1.1
  (`assets/fonts/OFL-*.txt`)
- Music and sound: original, synthesised by `tools/make_audio.py`

---

## 日本語

**LogicGate（ロジックゲート）** は、**10才以上**向けの回路づくりパズルゲームです（英語・日本語対応）。
電池、スイッチ、電球、LED、抵抗、ブザー、モーター、ロジックゲートを基板にドラッグして、
**120秒**以内に回路を完成させよう。完成すると電球が光り、ブザーが鳴り、ファンが回り、
スイッチが自動でON/OFFして動きを見せてくれます。

- **パーツ紹介**：見た目、回路記号、はたらき、使われている所を、動くデモつきで学べます。
- **回路は毎回ランダム**：パーツ、配置、LEDの色が毎回変わります。
- **レベルが上がると回路図が消えます**：ヒント → 回路図のみ → 説明文のみ。
- **難易度**：かんたん・ふつう・むずかしい。
- **スコア**：早くクリアするほど高得点。タイトル画面にトップ10を表示します。
- **保護者の方へ**：プレイ回数、クリア数、最高レベル、クリア時間などの記録を確認できます。
- **BGM**：落ち着いたアンビエント音楽（ON/OFF切りかえ可）。

制作：Shawn Rapaz（Claude Code協力）
ウェブサイト：<https://shoukugames.org/> ・ メール：<info@shoukugames.org>
ライセンス：GNU GPL v3.0
