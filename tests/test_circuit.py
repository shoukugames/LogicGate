import random

import pytest

from logicgate import circuit, levels, parts


def build(name, seed=1, **ctx):
    ctx.setdefault("socket_chance", 1.0)
    ctx.setdefault("gates", ["AND"])
    b, *_ = levels.TEMPLATES[name][0](random.Random(seed), ctx)
    c = b.c
    for s in c.slots:
        s.solution_forward = s.forward
    c.place_solution()
    return c


def first(c, kind):
    return next(s for s in c.slots if s.kind == kind)


def test_simple_loop_lights_only_with_switch_closed():
    c = build("simple", load="bulb")
    sw = first(c, "switch")
    sw.closed = False
    assert not any(circuit.simulate(c).on.values())
    sw.closed = True
    assert all(circuit.simulate(c).on.values())


def test_wire_instead_of_load_is_short():
    c = build("simple", load="bulb")
    first(c, "bulb").kind = "wire"
    assert circuit.evaluate(c).code == "short"


def test_led_without_resistor_burns():
    c = build("simple", load="led")
    first(c, "resistor").kind = "wire"
    assert circuit.evaluate(c).code == "burned"


def test_backwards_led_detected():
    c = build("simple", load="led")
    led = first(c, "led")
    led.forward = not led.forward
    assert circuit.evaluate(c).code == "led_backwards"


def test_missing_switch():
    c = build("simple", load="motor")
    first(c, "switch").kind = "wire"
    assert circuit.evaluate(c).code == "switch_count"


def test_wrong_gate_is_wrong_logic():
    c = build("gate", gates=["AND"])
    gate = next(s for s in c.slots if s.is_gate_socket)
    gate.kind = "OR"
    assert circuit.evaluate(c).code == "wrong_logic"
    gate.kind = None
    assert circuit.evaluate(c).code == "never_on"


@pytest.mark.parametrize("gate", parts.GATES)
def test_every_gate_template_solvable(gate):
    c = build("gate", gates=[gate])
    assert circuit.evaluate(c).ok


@pytest.mark.parametrize("difficulty", levels.DIFFICULTIES)
def test_generated_levels_are_solvable_and_not_free(difficulty):
    rng = random.Random(difficulty)
    for n in range(1, 25):
        lv = levels.generate(n, difficulty, rng)
        assert lv.circuit.sockets(), "nothing to do"
        assert circuit.evaluate(lv.circuit).ok is False   # empty board never passes
        lv.circuit.place_solution()
        assert circuit.evaluate(lv.circuit).ok, (n, lv.template)
        assert set(s.solution for s in lv.circuit.sockets()) <= set(lv.palette)


def test_stages_progress():
    assert levels.stage_for(1, "easy") == "full"
    assert levels.stage_for(5, "easy") == "symbols"
    assert levels.stage_for(9, "easy") == "description"
    assert levels.stage_for(4, "hard") == "description"
