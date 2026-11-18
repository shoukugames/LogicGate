"""Every piece of on-screen text, in English and Japanese."""

LANG = {"current": "en"}

STRINGS = {
    "title_sub": ("Build circuits. Learn logic.", "回路を作って、ロジックを学ぼう。"),
    "play": ("Play", "プレイ"),
    "intro": ("Introduction", "パーツ紹介"),
    "parents": ("Parents Only", "保護者の方へ"),
    "credits": ("Credits", "クレジット"),
    "quit": ("Quit", "終了"),
    "difficulty": ("Difficulty", "難易度"),
    "easy": ("Easy", "かんたん"),
    "medium": ("Medium", "ふつう"),
    "hard": ("Hard", "むずかしい"),
    "bgm": ("Music", "BGM"),
    "sfx": ("Sound FX", "効果音"),
    "on": ("ON", "ON"),
    "off": ("OFF", "OFF"),
    "language": ("Language", "言語"),
    "ages": ("Ages 10+", "対象年齢 10才以上"),
    "top10": ("Top 10 Scores", "トップ10"),
    "no_scores": ("No scores yet - be the first!", "まだ記録がありません。一番乗りしよう！"),
    "how_to_play": ("How to Play", "遊び方"),
    "back": ("Back", "もどる"),
    "level": ("Level", "レベル"),
    "score": ("Score", "スコア"),
    "time": ("Time", "時間"),
    "goal": ("Goal", "ミッション"),
    "schematic": ("Schematic", "回路図"),
    "no_schematic": ("No schematic this time!\nRead the goal and work it out.",
                     "今回は回路図なし！\nミッションを読んで考えよう。"),
    "test": ("Test Circuit", "回路をテスト"),
    "clear": ("Clear", "クリア"),
    "menu": ("Menu", "メニュー"),
    "parts": ("Parts", "パーツ"),
    "start": ("Start!", "スタート！"),
    "next": ("Next Level", "次のレベル"),
    "new_parts": ("Parts in this circuit", "この回路のパーツ"),
    "paused": ("Paused", "一時停止"),
    "resume": ("Resume", "つづける"),
    "quit_run": ("Quit to Title", "タイトルへ"),
    "complete": ("Circuit Complete!", "回路完成！"),
    "watch": ("Watch it work - click the switches too!", "動きを見てみよう。スイッチもクリックできるよ！"),
    "time_bonus": ("Time bonus", "タイムボーナス"),
    "level_bonus": ("Level bonus", "レベルボーナス"),
    "base": ("Circuit complete", "回路完成"),
    "multiplier": ("Difficulty", "難易度ボーナス"),
    "solved_in": ("Solved in {t} seconds", "{t}秒でクリア"),
    "times_up": ("Time's Up!", "タイムアップ！"),
    "game_over": ("Game Over", "ゲームオーバー"),
    "final_score": ("Final score", "最終スコア"),
    "reached": ("You reached level {n}", "レベル{n}まで到達"),
    "new_high": ("New Top 10 score! Type your name:", "トップ10入り！名前を入力してね："),
    "ok": ("OK", "OK"),
    "continue": ("Continue", "つづける"),
    "penalty": ("-5 seconds", "-5秒"),
    "stage_full": ("Schematic + hints", "回路図＋ヒント"),
    "stage_symbols": ("Schematic only", "回路図のみ"),
    "stage_description": ("Description only", "説明文のみ"),
    "drag_hint": ("Drag parts from the left onto the dashed sockets. Right-click a part to flip or remove it.",
                  "左のパーツを点線のソケットへドラッグしよう。右クリックで向きを変える／外す。"),
    # Touch screens have no right-click: tap an LED to flip it, drag a part off the board to remove it.
    "drag_hint_touch": ("Drag parts from the left onto the dashed sockets. Tap an LED to flip it; drag a part off to remove it.",
                        "左のパーツを点線のソケットへドラッグしよう。LEDはタップで向きを変える。外すときはボードの外へドラッグ。"),
    "tutorial": ("1. Drag a part from the left onto a socket\n2. Fill every socket the circuit needs\n"
                 "3. Press Test Circuit before time runs out!",
                 "1. 左のパーツをソケットへドラッグ\n2. 回路に必要なソケットをうめる\n3. 時間内に「回路をテスト」を押そう！"),
    # Failure messages
    "fail_short": ("Short circuit! Power goes straight back to the battery without passing through anything.",
                   "ショート！電気が何も通らずに電池へ戻っているよ。"),
    "fail_burned": ("Pop! The LED burned out. LEDs need a resistor to limit the current.",
                    "パチッ！LEDが焼けちゃった。LEDには電流を弱める抵抗が必要だよ。"),
    "fail_led_backwards": ("The LED is backwards! LEDs only work one way. Right-click it to flip it.",
                           "LEDの向きが逆だよ！LEDは一方向にしか電気を通さない。右クリックで向きを変えよう。"),
    "fail_led_backwards_touch": ("The LED is backwards! LEDs only work one way. Tap it to flip it.",
                                 "LEDの向きが逆だよ！LEDは一方向にしか電気を通さない。タップで向きを変えよう。"),
    "fail_switch_count": ("This circuit needs exactly {n} switch(es) to control it.",
                          "この回路にはスイッチがちょうど{n}個必要だよ。"),
    "fail_missing_output": ("Something is missing: the circuit needs a {part}.", "{part}が足りないよ。"),
    "fail_extra_part": ("There is an extra {part} that this circuit doesn't need.",
                        "この回路にいらない{part}があるよ。"),
    "fail_never_on": ("The {part} never turns on. Is the circuit a complete loop?",
                      "{part}が一度も動かないよ。回路はひと回りつながっているかな？"),
    "fail_always_on": ("The {part} is always on. The switches should control it.",
                       "{part}がつきっぱなしだよ。スイッチで操作できるようにしよう。"),
    "fail_wrong_logic": ("The {part} turns on at the wrong times. Read the goal again!",
                         "{part}が動くタイミングがちがうよ。ミッションをもう一度読もう！"),
    # Parents
    "parent_gate": ("Parents Only - please answer to continue", "保護者の方へ - 答えを入力してください"),
    "parent_wrong": ("Not quite. Try again.", "ちがいます。もう一度どうぞ。"),
    "progress": ("Player Progress", "プレイ記録"),
    "plays": ("Games played", "プレイ回数"),
    "solved": ("Circuits solved", "クリアした回路"),
    "best_level": ("Highest level", "最高レベル"),
    "avg_time": ("Average solve time", "平均クリア時間"),
    "success_rate": ("First-try success", "一発クリア率"),
    "recent": ("Recent circuits", "最近の回路"),
    "date": ("Date", "日付"),
    "circuit": ("Circuit", "回路"),
    "result": ("Result", "結果"),
    "tries": ("Tests", "テスト"),
    "solved_word": ("Solved", "クリア"),
    "timeout_word": ("Time up", "時間切れ"),
    "quit_word": ("Quit", "中断"),
    "reset": ("Reset all records", "記録をすべて消す"),
    "reset_confirm": ("Click again to erase everything", "もう一度クリックで全て消去"),
    "times_chart": ("Solve time, last 20 circuits (seconds)", "クリア時間（直近20回・秒）"),
    "page": ("Page", "ページ"),
    "no_records": ("No circuits played yet.", "まだプレイ記録がありません。"),
    # Credits
    "created_by": ("Created by", "制作"),
    "with": ("with", "協力"),
    "release": ("Release", "リリース"),
    "website": ("Website", "ウェブサイト"),
    "email": ("Email", "メール"),
    "license": ("License", "ライセンス"),
    "view_license": ("View full license", "ライセンス全文"),
    "fonts_credit": ("Fonts: M PLUS 1p and Orbitron (SIL Open Font License 1.1)",
                     "フォント：M PLUS 1p、Orbitron（SIL Open Font License 1.1）"),
    "music_credit": ("Music and sound: original, synthesised for this game", "音楽・効果音：本作のためのオリジナル合成音"),
    "gpl_short": ("LogicGate is free software: you can redistribute it and/or modify it under the terms of the "
                  "GNU General Public License version 3 as published by the Free Software Foundation. "
                  "It comes with ABSOLUTELY NO WARRANTY.",
                  "LogicGateはフリーソフトウェアです。フリーソフトウェア財団が公表したGNU一般公衆利用許諾書"
                  "第3版の条件のもとで再配布・改変できます。本ソフトウェアは無保証です。"),
    # Intro
    "intro_title": ("Introduction to Circuits", "回路入門"),
    "what_it_does": ("What it does", "はたらき"),
    "how_used": ("Where it is used", "使われている所"),
    "symbol": ("Schematic symbol", "回路記号"),
    "looks_like": ("What it looks like", "見た目"),
    "truth_table": ("Truth table", "真理値表"),
    "click_try": ("Click the switches to try it!", "スイッチをクリックして試そう！"),
}

PART_NAMES = {
    "battery": ("Battery", "電池"),
    "wire": ("Wire", "導線"),
    "resistor": ("Resistor", "抵抗"),
    "switch": ("Switch", "スイッチ"),
    "button": ("Push Button", "押しボタン"),
    "bulb": ("Light Bulb", "電球"),
    "led": ("LED", "LED"),
    "buzzer": ("Buzzer", "ブザー"),
    "motor": ("Motor", "モーター"),
    "AND": ("AND Gate", "ANDゲート"),
    "OR": ("OR Gate", "ORゲート"),
    "NOT": ("NOT Gate", "NOTゲート"),
    "NAND": ("NAND Gate", "NANDゲート"),
    "NOR": ("NOR Gate", "NORゲート"),
    "XOR": ("XOR Gate", "XORゲート"),
}

PART_INFO = {
    "battery": (
        ("Stores energy and pushes electricity around a circuit. Current leaves the + end, travels round the loop and comes back to the - end.",
         "Torches, remote controls, toys, phones and cars."),
        ("エネルギーをたくわえ、回路に電気を流す力を出します。電流は＋極から出て、回路をひと回りして－極へもどります。",
         "懐中電灯、リモコン、おもちゃ、スマホ、自動車。")),
    "wire": (
        ("A metal path that lets electricity flow easily from one part to another. On a circuit board the wires are copper lines called traces.",
         "Inside every electrical thing - from chargers to computers."),
        ("電気を通しやすい金属の道です。パーツとパーツをつなぎます。基板の上では「パターン」と呼ばれる銅の線になっています。",
         "充電器からコンピューターまで、すべての電気製品の中。")),
    "resistor": (
        ("Slows the flow of current. The coloured stripes tell you how strong it is. It protects delicate parts such as LEDs.",
         "Next to almost every LED, and in volume and brightness controls."),
        ("電流の流れをおさえます。色の帯で強さがわかります。LEDのような弱いパーツを守ります。",
         "ほとんどのLEDのとなり、音量や明るさの調節。")),
    "switch": (
        ("Opens or closes a gap in the circuit. ON (closed) lets current flow, OFF (open) breaks the loop. A switch is an input: it is how YOU control the circuit.",
         "Light switches, power buttons on toys and computers."),
        ("回路のすき間を開けたり閉じたりします。ON（閉じる）で電気が流れ、OFF（開く）で止まります。スイッチは「入力」です。",
         "部屋の電気のスイッチ、おもちゃやパソコンの電源。")),
    "button": (
        ("A switch that is only ON while you hold it down. Let go and it springs back to OFF.",
         "Doorbells, keyboards, game controllers, lift buttons."),
        ("押している間だけONになるスイッチです。はなすとバネでOFFにもどります。",
         "ドアベル、キーボード、ゲームのコントローラー、エレベーター。")),
    "bulb": (
        ("Current heats a very thin wire called a filament until it glows and gives off light.",
         "Lamps, torches and old-style car lights."),
        ("電流が「フィラメント」という細い線を熱くして、光らせます。",
         "電気スタンド、懐中電灯、昔の車のライト。")),
    "led": (
        ("Light Emitting Diode: a tiny light that uses very little power. Current only flows one way - from the long leg (+, anode) to the short leg (-, cathode). Always use a resistor with it!",
         "Screens, traffic lights, indicator lights, torches."),
        ("発光ダイオード：少しの電気で光る小さなライトです。電気は長い足（＋）から短い足（－）への一方向にしか流れません。必ず抵抗といっしょに使おう！",
         "画面、信号機、表示ランプ、懐中電灯。")),
    "buzzer": (
        ("Turns electricity into sound. A small disc inside vibrates very fast to make a beep.",
         "Alarms, microwaves, timers, doorbells."),
        ("電気を音に変えます。中の小さな板がとても速くふるえてピーと鳴ります。",
         "目覚まし時計、電子レンジ、タイマー、ドアベル。")),
    "motor": (
        ("Turns electricity into spinning motion using magnets and coils of wire.",
         "Fans, toy cars, drones, washing machines."),
        ("磁石とコイルを使って、電気を回転する動きに変えます。",
         "扇風機、ミニカー、ドローン、洗濯機。")),
    "AND": (
        ("A logic chip. The output is ON (1) only when input A AND input B are both ON. It works like two switches in a row.",
         "Safety systems: a machine runs only when the guard is closed AND the start button is pressed."),
        ("ロジック回路のチップです。入力AとBが両方ON（1）のときだけ出力がONになります。直列の2つのスイッチと同じです。",
         "安全装置：カバーが閉じていて、かつスタートボタンを押したときだけ機械が動く。")),
    "OR": (
        ("Output is ON when input A OR input B (or both) is ON. It works like two switches side by side.",
         "A car's interior light comes on when ANY door is open."),
        ("入力AかB（または両方）がONなら出力がONになります。並列の2つのスイッチと同じです。",
         "車のドアがどれか1つでも開くと室内灯がつく。")),
    "NOT": (
        ("Also called an inverter. The output is the opposite of the input: ON becomes OFF, OFF becomes ON. It only uses input A.",
         "Night lights that turn ON when it is NOT bright."),
        ("インバーターとも呼びます。出力は入力の反対です。ONはOFFに、OFFはONになります。入力Aだけを使います。",
         "明るくないときにつく常夜灯。")),
    "NAND": (
        ("NOT-AND: the opposite of AND. The output is ON unless both inputs are ON. Every computer chip can be built from NAND gates alone!",
         "Computer memory and processors."),
        ("NOT＋AND：ANDの反対です。両方の入力がONのとき以外は出力がONです。コンピューターはNANDだけで作ることもできます！",
         "コンピューターのメモリやCPU。")),
    "NOR": (
        ("NOT-OR: the opposite of OR. The output is ON only when both inputs are OFF.",
         "An 'all clear' light that shows only when no alarm is ringing."),
        ("NOT＋OR：ORの反対です。両方の入力がOFFのときだけ出力がONになります。",
         "どの警報も鳴っていないときだけつく「異常なし」ランプ。")),
    "XOR": (
        ("Exclusive OR: the output is ON when the inputs are DIFFERENT - exactly one is ON.",
         "Stair lights you can switch from the top OR the bottom; adding numbers in a computer."),
        ("排他的論理和：入力がちがうとき（どちらか片方だけがON）に出力がONになります。",
         "階段の上と下どちらからでも切りかえられる照明、コンピューターの足し算。")),
}

CONCEPTS = [
    ("circuit",
     ("What is a circuit?", "回路ってなに？"),
     ("A circuit is a complete loop. Electricity leaves the battery's + end, flows through the parts and returns to the - end. If the loop is broken anywhere, nothing works. Try the switch!",
      "回路とは、ひと回りつながった電気の通り道です。電気は電池の＋極から出てパーツを通り、－極へもどります。どこかが切れていると何も動きません。スイッチを試してみよう！")),
    ("series",
     ("Series = AND", "直列＝AND"),
     ("Parts in a row are 'in series'. Current must pass through every one, so the lamp lights only when switch A AND switch B are both ON.",
      "1列に並んだつなぎ方を「直列」といいます。電気は全部を通るので、スイッチAとBが両方ONのときだけ電球がつきます。")),
    ("parallel",
     ("Parallel = OR", "並列＝OR"),
     ("Parts side by side are 'in parallel'. Current can take either path, so the lamp lights when switch A OR switch B is ON.",
      "横に並んだつなぎ方を「並列」といいます。電気はどちらの道も通れるので、AかBどちらかがONなら電球がつきます。")),
    ("short",
     ("Short circuit!", "ショート回路"),
     ("If a wire connects + straight back to - with nothing in between, the current rushes round with nothing to slow it. Batteries get hot - never do this with real batteries!",
      "＋と－が何も通らずに導線だけでつながると、電気が一気に流れて電池が熱くなります。本物の電池では絶対にやめよう！")),
    ("logic",
     ("Logic gates", "ロジックゲート"),
     ("Logic gates are tiny chips that make decisions. Each input is 1 (ON) or 0 (OFF), and the gate's rule decides the output. Computers use billions of them!",
      "ロジックゲートは判断をする小さなチップです。入力は1（ON）か0（OFF）で、ゲートのルールが出力を決めます。コンピューターには何十億個も入っています！")),
]

HOW_TO = {
    "en": [
        "Every level is a circuit to finish in 120 seconds.",
        "Drag parts from the left onto the dashed sockets.",
        "Right-click a placed part to flip it; drag it off to remove.",
        "Press Test Circuit. A wrong test costs 5 seconds.",
        "Faster = more points! Later levels hide the schematic.",
    ],
    "ja": [
        "各レベルは120秒以内に回路を完成させよう。",
        "左のパーツを点線のソケットへドラッグ。",
        "置いたパーツは右クリックで向きを変え、外へドラッグで外す。",
        "「回路をテスト」を押そう。まちがうと5秒へるよ。",
        "早いほど高得点！レベルが上がると回路図が消えるよ。",
    ],
}


def lang():
    return LANG["current"]


def t(key, **fmt):
    en, ja = STRINGS[key]
    text = ja if lang() == "ja" else en
    return text.format(**fmt) if fmt else text


def both(key):
    return STRINGS[key]


def part_name(kind, language=None):
    en, ja = PART_NAMES[kind]
    return ja if (language or lang()) == "ja" else en


def part_info(kind):
    en, ja = PART_INFO[kind]
    return ja if lang() == "ja" else en
