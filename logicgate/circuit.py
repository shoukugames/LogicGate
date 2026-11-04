"""Circuit model, a simple digital simulator and the checker that grades a build.

A circuit is a set of pads (solder points) joined by slots. A slot is either a
copper trace, a fixed part (such as the battery), an empty socket the player
fills, or a socket for a logic chip with pins A, B and OUT.

The simulator is deliberately simple and kid-friendly: a load is ON when there
is a path from a power source, through it, to the battery's minus side. LEDs
only pass current from anode to cathode, an LED with no resistor burns out, a
loop with nothing in it is a short circuit, and a gate output acts as a power
source whenever its logic says "1".
"""
import itertools
from collections import defaultdict, deque

from . import parts

SRC = "SRC"
GND = "GND"


class Slot:
    def __init__(self, sid, a=None, b=None, kind=None, fixed=False, trace=False, solution=None,
                 label=None, forward=True, via=None, pins=None, center=None, uses_b=True):
        self.id = sid
        self.a = a                    # pad ids (edge slots)
        self.b = b
        self.pins = pins              # {"a": pad, "b": pad, "out": pad} for gate sockets
        self.center = center          # gate socket centre in board units
        self.uses_b = uses_b
        self.kind = kind              # part currently in the slot, or None
        self.fixed = fixed            # part cannot be moved by the player
        self.trace = trace            # drawn as a copper trace, never a socket
        self.solution = solution      # the intended part (for hints and autoplay)
        self.label = label            # "A", "B", "C" for named switches
        self.forward = forward        # polarity: + / anode at pad a
        self.via = via or []          # bend points for traces
        self.closed = False           # switch state
        self.led_color = "red"
        self.solution_forward = forward

    @property
    def is_gate_socket(self):
        return self.pins is not None

    @property
    def is_socket(self):
        return not self.fixed and not self.trace

    def plus_pad(self):
        return self.a if self.forward else self.b

    def minus_pad(self):
        return self.b if self.forward else self.a

    def gate_inputs(self):
        return [self.pins["a"], self.pins["b"]] if self.uses_b else [self.pins["a"]]


class Circuit:
    def __init__(self):
        self.pads = {}     # id -> (x, y) in board units
        self.slots = []
        self.goal = None   # {"inputs": n, "outputs": [{"kind", "count", "fn"}]}

    def slot(self, sid):
        for s in self.slots:
            if s.id == sid:
                return s
        return None

    def sockets(self):
        return [s for s in self.slots if s.is_socket]

    def switches(self):
        """Switch slots in input order: named ones (A, B, C) first, then by position."""
        found = [s for s in self.slots if parts.is_switch(s.kind)]
        return sorted(found, key=lambda s: (s.label is None, s.label or "", s.id))

    def outputs(self):
        return [s for s in self.slots if parts.is_output(s.kind)]

    def clear(self):
        for s in self.sockets():
            s.kind = None

    def place_solution(self):
        for s in self.sockets():
            s.kind = s.solution
            if s.kind == "led":
                s.forward = s.solution_forward


class _UnionFind:
    def __init__(self):
        self.parent = {}

    def find(self, x):
        self.parent.setdefault(x, x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, x, y):
        self.parent[self.find(x)] = self.find(y)


class SimResult:
    def __init__(self):
        self.on = {}          # slot id -> bool for every output part
        self.flow = {}        # slot id -> +1 (a to b) or -1 (b to a) where current flows
        self.gate_out = {}    # gate slot id -> bool
        self.short = False
        self.burned = set()   # LED slot ids
        self.powered = False


def _reach(adj, start, banned):
    seen = {start}
    queue = deque([start])
    while queue:
        node = queue.popleft()
        for nxt, sid in adj[node]:
            if sid == banned or nxt in seen:
                continue
            seen.add(nxt)
            queue.append(nxt)
    return seen


def simulate(circuit, states=None):
    """states: optional {slot id: closed?} overriding each switch's own state."""
    states = states or {}
    result = SimResult()

    def closed(s):
        return states.get(s.id, s.closed)

    battery = next((s for s in circuit.slots if s.kind == "battery"), None)
    if battery is None:
        for s in circuit.outputs():
            result.on[s.id] = False
        return result
    plus, minus = battery.plus_pad(), battery.minus_pad()

    zero = _UnionFind()       # nets joined by wires and closed switches
    conductive = _UnionFind()  # ... and resistors too (for sensing gate inputs)
    for s in circuit.slots:
        if s.is_gate_socket or s.kind is None:
            continue
        r = parts.role(s.kind)
        if r == "conductor" or (r == "switch" and closed(s)):
            zero.union(s.a, s.b)
            conductive.union(s.a, s.b)
        elif r == "resistor":
            conductive.union(s.a, s.b)

    if zero.find(plus) == zero.find(minus):
        result.short = True
        for s in circuit.outputs():
            result.on[s.id] = False
        return result
    result.powered = True

    # Logic chips: settle their outputs (no feedback loops in this game)
    gates = [s for s in circuit.slots if s.is_gate_socket and s.kind]
    high = {conductive.find(plus)}
    outs = {g.id: False for g in gates}
    for _ in range(len(gates) + 1):
        changed = False
        for g in gates:
            a = conductive.find(g.pins["a"]) in high
            b = conductive.find(g.pins["b"]) in high
            value = bool(parts.PARTS[g.kind]["fn"](a, b))
            if value != outs[g.id]:
                outs[g.id] = value
                changed = True
            if value:
                high.add(conductive.find(g.pins["out"]))
        if not changed:
            break
    result.gate_out = outs

    # Current graph between pads, with a virtual source and ground
    adj = defaultdict(list)
    directed = []  # (u, v, slot id, sign)

    def link(u, v, sid, sign, both=True):
        adj[u].append((v, sid))
        directed.append((u, v, sid, sign))
        if both:
            adj[v].append((u, sid))
            directed.append((v, u, sid, -sign))

    link(SRC, plus, "~src", 1, both=False)
    link(minus, GND, "~gnd", 1, both=False)
    sources = {zero.find(plus)}
    for g in gates:
        if outs[g.id]:
            link(SRC, g.pins["out"], f"~out{g.id}", 1, both=False)
            sources.add(zero.find(g.pins["out"]))
        for i, pin in enumerate(g.gate_inputs()):
            link(pin, GND, f"~in{g.id}{i}", 1, both=False)
    for s in circuit.slots:
        if s.is_gate_socket or s.kind is None or s.kind == "battery":
            continue
        r = parts.role(s.kind)
        if r == "switch" and not closed(s):
            continue
        if r == "diode":
            if s.forward:
                link(s.a, s.b, s.id, 1, both=False)
            else:
                link(s.b, s.a, s.id, -1, both=False)
        else:
            link(s.a, s.b, s.id, 1)

    # Reverse adjacency for "can still reach ground" searches
    radj = defaultdict(list)
    for u, v, sid, _sign in directed:
        radj[v].append((u, sid))

    slot_ids = {sid for _u, _v, sid, _s in directed if not sid.startswith("~")}
    cache_f, cache_b = {}, {}
    for sid in slot_ids:
        f = cache_f.setdefault(sid, _reach(adj, SRC, sid))
        bk = cache_b.setdefault(sid, _reach(radj, GND, sid))
        for u, v, did, sign in directed:
            if did == sid and u in f and v in bk:
                result.flow[sid] = sign
                break

    for s in circuit.outputs():
        on = s.id in result.flow
        if on and s.kind == "led":
            anode = s.a if s.forward else s.b
            cathode = s.b if s.forward else s.a
            if zero.find(anode) in sources and zero.find(cathode) == zero.find(minus):
                result.burned.add(s.id)
                on = False
        result.on[s.id] = on
    return result


class Verdict:
    def __init__(self, ok, code="ok", kind=None):
        self.ok = ok
        self.code = code   # key into the i18n "fail_*" messages
        self.kind = kind   # part the message is about

    def __repr__(self):
        return f"Verdict({self.ok}, {self.code}, {self.kind})"


def evaluate(circuit):
    """Try every combination of switch positions and compare with the goal."""
    goal = circuit.goal
    switches = circuit.switches()
    if len(switches) != goal["inputs"]:
        return Verdict(False, "switch_count", goal["inputs"])

    for combo in itertools.product((False, True), repeat=len(switches)):
        if simulate(circuit, {s.id: v for s, v in zip(switches, combo)}).short:
            return Verdict(False, "short")

    present = defaultdict(list)
    for s in circuit.outputs():
        present[s.kind].append(s)
    wanted = {o["kind"]: o for o in goal["outputs"]}
    for kind, spec in wanted.items():
        if len(present[kind]) < spec["count"]:
            return Verdict(False, "missing_output", kind)
        if len(present[kind]) > spec["count"]:
            return Verdict(False, "extra_part", kind)
    for kind in present:
        if kind not in wanted:
            return Verdict(False, "extra_part", kind)

    stats = {kind: {"on": False, "off": False, "wrong": False} for kind in wanted}
    for combo in itertools.product((False, True), repeat=len(switches)):
        states = {s.id: v for s, v in zip(switches, combo)}
        sim = simulate(circuit, states)
        if sim.short:
            return Verdict(False, "short")
        if sim.burned:
            return Verdict(False, "burned", "led")
        for kind, spec in wanted.items():
            expect = bool(spec["fn"](combo))
            for s in present[kind]:
                actual = sim.on.get(s.id, False)
                stats[kind]["on" if actual else "off"] = True
                if actual != expect:
                    stats[kind]["wrong"] = True

    for kind, st in stats.items():
        if not st["wrong"]:
            continue
        if not st["on"]:
            if kind == "led" and _flipping_led_helps(circuit, present["led"]):
                return Verdict(False, "led_backwards", kind)
            return Verdict(False, "never_on", kind)
        if not st["off"]:
            return Verdict(False, "always_on", kind)
        return Verdict(False, "wrong_logic", kind)
    return Verdict(True)


def _flipping_led_helps(circuit, leds):
    for led in leds:
        led.forward = not led.forward
        try:
            states = {s.id: True for s in circuit.switches()}
            if any(simulate(circuit, states).on.values()):
                return True
            for combo in itertools.product((False, True), repeat=len(circuit.switches())):
                st = {s.id: v for s, v in zip(circuit.switches(), combo)}
                if simulate(circuit, st).on.get(led.id):
                    return True
        finally:
            led.forward = not led.forward
    return False


def best_led_direction(circuit, slot):
    """Point a newly dropped LED the way that lets it light (the friendly modes)."""
    for forward in (slot.forward, not slot.forward):
        slot.forward = forward
        for combo in itertools.product((False, True), repeat=len(circuit.switches())):
            st = {s.id: v for s, v in zip(circuit.switches(), combo)}
            sim = simulate(circuit, st)
            if sim.on.get(slot.id) or slot.id in sim.burned:
                return forward
    slot.forward = True
    return True
