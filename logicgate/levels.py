"""Random circuit puzzles.

Each template builds a circuit on a board measured in "units" (1 unit = 100
pixels on the main board, the board is 7.6 x 5.2 units). Every call picks new
parts, positions, colours and layouts, so no two puzzles are quite the same.
"""
import random

from . import parts
from .circuit import Circuit, Slot

BOARD_W = 7.6
BOARD_H = 5.2

DIFFICULTIES = ("easy", "medium", "hard")
LEVEL_SHIFT = {"easy": 0, "medium": 1, "hard": 2}
SCORE_MULT = {"easy": 1.0, "medium": 1.5, "hard": 2.0}
# Levels (from) at which the help on the board is reduced
STAGE_START = {
    "easy": {"symbols": 5, "description": 9},
    "medium": {"symbols": 3, "description": 6},
    "hard": {"symbols": 2, "description": 4},
}
DISTRACTORS = {"easy": 1, "medium": 2, "hard": 3}

LOAD_NAME = {
    "bulb": ("light bulb", "電球"),
    "led": ("LED", "LED"),
    "buzzer": ("buzzer", "ブザー"),
    "motor": ("motor fan", "モーター（ファン）"),
}
VERB = {  # (EN present, EN base, JA)
    "bulb": ("lights up", "light up", "光る"),
    "led": ("lights up", "light up", "光る"),
    "buzzer": ("sounds", "sound", "鳴る"),
    "motor": ("spins", "spin", "回る"),
}
COLOR_NAME = {"red": ("red", "赤"), "green": ("green", "緑"), "blue": ("blue", "青"), "yellow": ("yellow", "黄色")}


def stage_for(level, difficulty):
    start = STAGE_START[difficulty]
    if level >= start["description"]:
        return "description"
    if level >= start["symbols"]:
        return "symbols"
    return "full"


class Builder:
    def __init__(self):
        self.c = Circuit()
        self._ids = {}
        self._n = 0

    def pad(self, x, y):
        key = (round(x, 3), round(y, 3))
        if key not in self._ids:
            pid = f"p{len(self._ids)}"
            self._ids[key] = pid
            self.c.pads[pid] = key
        return self._ids[key]

    def _sid(self):
        self._n += 1
        return f"s{self._n}"

    def edge(self, p, q, kind, role="slot", label=None, forward=True, via=None):
        a, b = self.pad(*p), self.pad(*q)
        s = Slot(self._sid(), a, b, forward=forward, label=label,
                 via=[tuple(v) for v in (via or [])])
        if role == "trace":
            s.kind, s.fixed, s.trace, s.solution = "wire", True, True, "wire"
        elif role == "fixed":
            s.kind, s.fixed, s.solution = kind, True, kind
        else:
            s.solution = kind
        self.c.slots.append(s)
        return s

    def path(self, points, kind="wire"):
        """A trace that may bend: through all the points."""
        return self.edge(points[0], points[-1], kind, role="trace", via=points[1:-1])

    def gate(self, cx, cy, kind, role="slot", uses_b=True):
        pins = {"a": self.pad(cx - 0.6, cy - 0.45), "b": self.pad(cx - 0.6, cy + 0.45),
                "out": self.pad(cx + 0.6, cy)}
        s = Slot(self._sid(), pins=pins, center=(cx, cy), uses_b=uses_b)
        s.solution = kind
        if role == "fixed":
            s.kind, s.fixed = kind, True
        self.c.slots.append(s)
        return s


def _load_with_resistor(load, rng):
    """The parts a load needs in series: an LED always gets a resistor."""
    return [load, "resistor"] if load == "led" else [load]


# ---------------------------------------------------------------- templates
LOOP = [(1.0, 0.8), (3.8, 0.8), (6.6, 0.8), (6.6, 2.6), (6.6, 4.4), (3.8, 4.4), (1.0, 4.4)]


def _series_loop(b, rng, elements, labels=None, fixed=()):
    """Battery on the left, elements spread round the other sides of a loop."""
    labels = labels or {}
    b.edge(LOOP[0], LOOP[-1], "battery", role="fixed", forward=True)
    segments = list(range(6))
    chosen = sorted(rng.sample(segments, len(elements)))
    slots = []
    for seg in segments:
        p, q = LOOP[seg], LOOP[seg + 1]
        if seg in chosen:
            idx = chosen.index(seg)
            kind = elements[idx]
            role = "fixed" if idx in fixed else "slot"
            slots.append(b.edge(p, q, kind, role=role, label=labels.get(idx)))
        else:
            b.edge(p, q, "wire", role="trace")
    return slots


def t_simple(rng, ctx):
    load = ctx.get("load") or rng.choice(["bulb", "buzzer", "motor", "led"])
    sw = "button" if load == "buzzer" and rng.random() < 0.5 else "switch"
    elements = [sw] + _load_with_resistor(load, rng)
    rng.shuffle(elements)
    b = Builder()
    _series_loop(b, rng, elements)
    b.c.goal = {"inputs": 1, "outputs": [{"kind": load, "count": 1, "fn": lambda v: v[0]}]}
    n_en, n_ja = LOAD_NAME[load]
    v = VERB[load]
    if sw == "button":
        en = f"Make a doorbell! The {n_en} {v[0]} while the push button is pressed."
        ja = f"ドアベルを作ろう！押しボタンを押している間、{n_ja}が{v[2]}ようにしよう。"
    else:
        en = f"Build a circuit where the {n_en} {v[0]} when the switch is turned ON."
        ja = f"スイッチをONにすると{n_ja}が{v[2]}回路を作ろう。"
    return b, en, ja, [load]


def _logic_loop(rng, ctx, mode):
    load = rng.choice(["bulb", "buzzer", "motor", "led"])
    b = Builder()
    b.edge(LOOP[0], LOOP[-1], "battery", role="fixed")
    sw_role = "slot" if rng.random() < ctx["socket_chance"] else "fixed"
    if mode == "and":
        top = [(1.0, 0.8), (2.6, 0.8), (5.0, 0.8), (6.6, 0.8)]
        b.edge(top[0], top[1], "switch", role=sw_role, label="A")
        b.edge(top[1], top[2], "wire", role="trace")
        b.edge(top[2], top[3], "switch", role=sw_role, label="B")
    else:
        p, q = (2.6, 0.8), (5.0, 0.8)
        b.edge((1.0, 0.8), p, "wire", role="trace")
        b.edge(p, q, "switch", role=sw_role, label="A")
        b.edge(q, (6.6, 0.8), "wire", role="trace")
        b.edge(p, (2.6, 2.2), "wire", role="trace")
        b.edge((2.6, 2.2), (5.0, 2.2), "switch", role=sw_role, label="B")
        b.edge((5.0, 2.2), q, "wire", role="trace")
    rest = [(6.6, 0.8), (6.6, 2.6), (6.6, 4.4), (3.8, 4.4), (1.0, 4.4)]
    elements = _load_with_resistor(load, rng)
    rng.shuffle(elements)
    chosen = sorted(rng.sample(range(4), len(elements)))
    for seg in range(4):
        if seg in chosen:
            b.edge(rest[seg], rest[seg + 1], elements[chosen.index(seg)])
        else:
            b.edge(rest[seg], rest[seg + 1], "wire", role="trace")
    n_en, n_ja = LOAD_NAME[load]
    v = VERB[load]
    if mode == "and":
        fn = lambda vals: vals[0] and vals[1]  # noqa: E731
        en = f"The {n_en} should {v[1]} only when BOTH switches are ON. (Switches in a row = AND)"
        ja = f"2つのスイッチが両方ONのときだけ{n_ja}が{v[2]}ようにしよう。（直列＝AND）"
    else:
        fn = lambda vals: vals[0] or vals[1]  # noqa: E731
        en = f"The {n_en} should {v[1]} when EITHER switch is ON. (Side-by-side switches = OR)"
        ja = f"どちらかのスイッチがONなら{n_ja}が{v[2]}ようにしよう。（並列＝OR）"
    b.c.goal = {"inputs": 2, "outputs": [{"kind": load, "count": 1, "fn": fn}]}
    return b, en, ja, [load]


def t_and(rng, ctx):
    return _logic_loop(rng, ctx, "and")


def t_or(rng, ctx):
    return _logic_loop(rng, ctx, "or")


def t_parallel_lamps(rng, ctx):
    load = rng.choice(["bulb", "bulb", "motor", "buzzer"])
    b = Builder()
    b.edge((1.0, 0.8), (1.0, 4.4), "battery", role="fixed")
    b.edge((1.0, 0.8), (2.8, 0.8), "switch")
    b.edge((2.8, 0.8), (4.4, 0.8), "wire", role="trace")
    b.edge((4.4, 0.8), (6.6, 0.8), "wire", role="trace")
    b.edge((4.4, 0.8), (4.4, 4.4), load)
    b.edge((6.6, 0.8), (6.6, 4.4), load)
    b.edge((6.6, 4.4), (4.4, 4.4), "wire", role="trace")
    b.edge((4.4, 4.4), (1.0, 4.4), "wire", role="trace")
    b.c.goal = {"inputs": 1, "outputs": [{"kind": load, "count": 2, "fn": lambda v: v[0]}]}
    n_en, n_ja = LOAD_NAME[load]
    v = VERB[load]
    en = f"One switch should make TWO {n_en}s {v[1]} at the same time. Put them side by side (in parallel)."
    ja = f"1つのスイッチで2つの{n_ja}が同時に{v[2]}ようにしよう。横に並べて（並列に）つなごう。"
    return b, en, ja, [load]


def t_two_loops(rng, ctx):
    loads = rng.sample(["bulb", "buzzer", "motor"], 2)
    b = Builder()
    b.edge((1.0, 0.8), (1.0, 4.4), "battery", role="fixed")
    b.edge((1.0, 0.8), (3.8, 0.8), "wire", role="trace")
    b.edge((3.8, 0.8), (6.6, 0.8), "wire", role="trace")
    b.edge((3.8, 0.8), (3.8, 2.6), "switch", role="fixed", label="A")
    b.edge((3.8, 2.6), (3.8, 4.4), loads[0])
    b.edge((6.6, 0.8), (6.6, 2.6), "switch", role="fixed", label="B")
    b.edge((6.6, 2.6), (6.6, 4.4), loads[1])
    b.edge((6.6, 4.4), (3.8, 4.4), "wire", role="trace")
    b.edge((3.8, 4.4), (1.0, 4.4), "wire", role="trace")
    b.c.goal = {"inputs": 2, "outputs": [{"kind": loads[0], "count": 1, "fn": lambda v: v[0]},
                                          {"kind": loads[1], "count": 1, "fn": lambda v: v[1]}]}
    a_en, a_ja = LOAD_NAME[loads[0]]
    b_en, b_ja = LOAD_NAME[loads[1]]
    en = f"Switch A should control the {a_en}, and switch B should control the {b_en}."
    ja = f"スイッチAで{a_ja}を、スイッチBで{b_ja}を動かせるようにしよう。"
    return b, en, ja, loads


GATE_TEXT = {
    "AND": ("Light the LED only when switch A AND switch B are both ON.",
            "スイッチAとスイッチBが両方ONのときだけLEDを光らせよう。"),
    "OR": ("Light the LED when switch A OR switch B (or both) is ON.",
           "スイッチAかスイッチB（または両方）がONのときLEDを光らせよう。"),
    "XOR": ("Light the LED only when exactly ONE switch is ON - not both!",
            "どちらか片方のスイッチだけがONのときLEDを光らせよう（両方はダメ）。"),
    "NAND": ("Keep the LED on all the time, EXCEPT when A and B are both ON.",
             "AとBが両方ONのとき以外は、いつもLEDを光らせよう。"),
    "NOR": ("Light the LED only when BOTH switches are OFF.",
            "2つのスイッチが両方OFFのときだけLEDを光らせよう。"),
    "NOT": ("Light the LED when switch A is OFF, and turn it off when A is ON. (Opposite!)",
            "スイッチAがOFFのときLEDを光らせ、ONのとき消そう。（反対にする！）"),
}


def _led_output(b, rng, start, ground_y):
    """From a gate output: LED and resistor down to the ground rail."""
    x, y = start
    order = ["led", "resistor"] if rng.random() < 0.5 else ["resistor", "led"]
    b.edge((x, y), (6.8, y), order[0])
    b.edge((6.8, y), (6.8, ground_y), order[1])
    b.edge((6.8, ground_y), (3.6, ground_y), "wire", role="trace")
    b.edge((3.6, ground_y), (0.8, ground_y), "wire", role="trace")


def t_gate(rng, ctx):
    gate = rng.choice(ctx.get("gates") or ["AND", "OR", "NOT"])
    b = Builder()
    gy = 2.2
    b.edge((0.8, 0.8), (0.8, 4.5), "battery", role="fixed")
    b.edge((0.8, 0.8), (2.0, 0.8), "wire", role="trace")
    g = b.gate(4.6, gy, gate, uses_b=gate != "NOT")
    pa, pb = b.c.pads[g.pins["a"]], b.c.pads[g.pins["b"]]
    b.edge((2.0, 0.8), (2.0, pa[1]), "wire", role="trace")
    b.edge((2.0, pa[1]), pa, "switch", role="fixed", label="A")
    if gate != "NOT":
        b.edge((2.0, pa[1]), (2.0, pb[1]), "wire", role="trace")
        b.edge((2.0, pb[1]), pb, "switch", role="fixed", label="B")
    _led_output(b, rng, b.c.pads[g.pins["out"]], 4.5)
    fn = parts.PARTS[gate]["fn"]
    n = 1 if gate == "NOT" else 2
    b.c.goal = {"inputs": n, "outputs": [{"kind": "led", "count": 1,
                                          "fn": (lambda v: fn(v[0], False)) if n == 1 else (lambda v: fn(v[0], v[1]))}]}
    en, ja = GATE_TEXT[gate]
    return b, en, ja, ["led"]


COMBOS = [
    ("AND", "OR", lambda a, b, c: (a and b) or c,
     "Light the LED when C is ON, or when A and B are both ON.",
     "Cがオンのとき、またはAとBが両方オンのときにLEDを光らせよう。"),
    ("OR", "AND", lambda a, b, c: (a or b) and c,
     "Light the LED when C is ON together with A or B (or both).",
     "CがONで、さらにAかB（または両方）がONのときLEDを光らせよう。"),
    ("XOR", "AND", lambda a, b, c: (a != b) and c,
     "Light the LED when C is ON and exactly one of A or B is ON.",
     "CがONで、AとBのどちらか片方だけがONのときLEDを光らせよう。"),
    ("AND", "AND", lambda a, b, c: a and b and c,
     "Light the LED only when ALL THREE switches A, B and C are ON.",
     "A・B・Cの3つのスイッチがすべてONのときだけLEDを光らせよう。"),
    ("OR", "OR", lambda a, b, c: a or b or c,
     "Light the LED when ANY of the three switches is ON.",
     "3つのスイッチのどれか1つでもONならLEDを光らせよう。"),
    ("NOR", "AND", lambda a, b, c: (not (a or b)) and c,
     "Light the LED when C is ON but both A and B are OFF.",
     "CがONで、AとBが両方OFFのときLEDを光らせよう。"),
]


def t_two_gates(rng, ctx):
    g1k, g2k, f, en, ja = rng.choice(COMBOS)
    b = Builder()
    b.edge((0.7, 0.6), (0.7, 4.7), "battery", role="fixed")
    b.edge((0.7, 0.6), (1.5, 0.6), "wire", role="trace")
    g1 = b.gate(3.4, 1.55, g1k)
    g2 = b.gate(5.3, 2.75, g2k)
    pa, pb = b.c.pads[g1.pins["a"]], b.c.pads[g1.pins["b"]]
    o1 = b.c.pads[g1.pins["out"]]
    qa, qb = b.c.pads[g2.pins["a"]], b.c.pads[g2.pins["b"]]
    b.edge((1.5, 0.6), (1.5, pa[1]), "wire", role="trace")
    b.edge((1.5, pa[1]), pa, "switch", role="fixed", label="A")
    b.edge((1.5, pa[1]), (1.5, pb[1]), "wire", role="trace")
    b.edge((1.5, pb[1]), pb, "switch", role="fixed", label="B")
    b.edge((1.5, pb[1]), (1.5, qb[1]), "wire", role="trace")
    b.edge((1.5, qb[1]), qb, "switch", role="fixed", label="C")
    b.path([o1, (4.35, o1[1]), (4.35, qa[1]), qa])
    out = b.c.pads[g2.pins["out"]]
    order = ["led", "resistor"] if rng.random() < 0.5 else ["resistor", "led"]
    b.edge(out, (6.9, out[1]), "wire", role="trace")
    b.edge((6.9, out[1]), (6.9, 4.7), order[0])
    b.edge((6.9, 4.7), (4.2, 4.7), order[1])
    b.edge((4.2, 4.7), (0.7, 4.7), "wire", role="trace")
    b.c.goal = {"inputs": 3, "outputs": [{"kind": "led", "count": 1, "fn": lambda v: f(*v)}]}
    return b, en, ja, ["led"]


TEMPLATES = {
    # name: (builder, first level it appears on, weight)
    "simple": (t_simple, 1, 3),
    "and": (t_and, 3, 2),
    "or": (t_or, 3, 2),
    "parallel": (t_parallel_lamps, 5, 2),
    "two_loops": (t_two_loops, 5, 2),
    "gate": (t_gate, 6, 3),
    "two_gates": (t_two_gates, 10, 3),
}


class Level:
    def __init__(self, number, difficulty, template, circuit, text_en, text_ja, stage, palette, outputs):
        self.number = number
        self.difficulty = difficulty
        self.template = template
        self.circuit = circuit
        self.text = {"en": text_en, "ja": text_ja}
        self.stage = stage          # "full", "symbols" or "description"
        self.palette = palette      # part kinds offered on the left
        self.outputs = outputs

    def new_parts(self):
        """All the part kinds the solution uses (for the briefing cards)."""
        kinds = []
        for s in self.circuit.slots:
            k = s.solution
            if k and k not in kinds and not s.trace:
                kinds.append(k)
        return kinds


PALETTE_ORDER = ["wire", "resistor", "switch", "button", "bulb", "led", "buzzer", "motor",
                 "AND", "OR", "NOT", "NAND", "NOR", "XOR"]


def generate(number, difficulty, rng=None, previous=None):
    rng = rng or random.Random()
    eff = number + LEVEL_SHIFT[difficulty]
    stage = stage_for(number, difficulty)
    pool = [(name, t) for name, t in TEMPLATES.items() if t[1] <= eff and name != previous]
    if not pool:
        pool = [("simple", TEMPLATES["simple"])]
    def weight(t):
        age = eff - t[1]          # how long ago this kind of puzzle was introduced
        if age < 3:
            return t[2] * 2.0     # new ideas come up more often
        return t[2] * (0.35 if age > 6 else 1.0)
    weights = [weight(t) for _name, t in pool]
    name = rng.choices([p[0] for p in pool], weights)[0]
    ctx = {"socket_chance": 0.3 if stage == "full" else 0.8,
           "gates": ["AND", "OR", "NOT"] if eff < 8 else list(parts.GATES)}
    if number == 1 and difficulty == "easy":
        name = "simple"
        ctx["load"] = "bulb"
    builder, en, ja, outputs = TEMPLATES[name][0](rng, ctx)
    c = builder.c
    color = rng.choice(list(parts.LED_COLORS))
    for s in c.slots:
        s.led_color = color
        s.solution_forward = s.forward
        if parts.is_switch(s.kind):
            s.closed = False

    # Harder puzzles: some copper is missing too and must be filled with wire
    if stage == "description" and difficulty != "easy":
        gaps = {"medium": 1, "hard": 2 + (number > 8)}[difficulty]
        candidates = [s for s in c.slots if s.trace and not s.via and _length(c, s) >= 1.0]
        for s in rng.sample(candidates, min(gaps, len(candidates))):
            s.trace = False
            s.fixed = False
            s.kind = None

    if "led" in outputs:
        cname = COLOR_NAME[color]
        en = en.replace("LED", f"{cname[0]} LED", 1)
        ja = ja.replace("LED", f"{cname[1]}のLED", 1)
        if stage != "description":
            en += " Tip: an LED needs a resistor!"
            ja += " ヒント：LEDには抵抗が必要だよ！"

    needed = {s.solution for s in c.sockets()}
    palette = set(needed) | {"wire"}
    has_gate = any(s.is_gate_socket for s in c.slots)
    spare = [k for k in PALETTE_ORDER if k not in palette and (has_gate or not parts.is_gate(k))]
    if has_gate:
        spare_gates = [k for k in spare if parts.is_gate(k) and (eff >= 8 or k in ctx["gates"])]
        spare_other = [k for k in spare if not parts.is_gate(k)]
        extra = rng.sample(spare_gates, min(len(spare_gates), DISTRACTORS[difficulty]))
        extra += rng.sample(spare_other, min(len(spare_other), max(0, DISTRACTORS[difficulty] - 1)))
    else:
        extra = rng.sample(spare, min(len(spare), DISTRACTORS[difficulty]))
    palette |= set(extra)
    ordered = [k for k in PALETTE_ORDER if k in palette]
    return Level(number, difficulty, name, c, en, ja, stage, ordered, outputs)


def _length(c, s):
    (x1, y1), (x2, y2) = c.pads[s.a], c.pads[s.b]
    return abs(x1 - x2) + abs(y1 - y2)
