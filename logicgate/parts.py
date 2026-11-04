"""The catalogue of parts: what each one is electrically and how it is named."""

# role: how the simulator treats the part
#   source    - battery (+ at one end, - at the other)
#   conductor - lets current through with no resistance (wire)
#   resistor  - lets current through but limits it
#   switch    - conductor when closed, gap when open (an input the player controls)
#   load      - does something when current flows (light, sound, motion)
#   diode     - a load that only works one way round (LED)
#   gate      - logic chip with inputs A, B and an output
PARTS = {
    "battery": {"role": "source"},
    "wire": {"role": "conductor"},
    "resistor": {"role": "resistor"},
    "switch": {"role": "switch"},
    "button": {"role": "switch"},
    "bulb": {"role": "load"},
    "led": {"role": "diode"},
    "buzzer": {"role": "load"},
    "motor": {"role": "load"},
    "AND": {"role": "gate", "fn": lambda a, b: a and b},
    "OR": {"role": "gate", "fn": lambda a, b: a or b},
    "NOT": {"role": "gate", "fn": lambda a, b: not a},
    "NAND": {"role": "gate", "fn": lambda a, b: not (a and b)},
    "NOR": {"role": "gate", "fn": lambda a, b: not (a or b)},
    "XOR": {"role": "gate", "fn": lambda a, b: a != b},
}

GATES = ("AND", "OR", "NOT", "NAND", "NOR", "XOR")
TWO_PIN = tuple(k for k, v in PARTS.items() if v["role"] != "gate")
OUTPUT_ROLES = ("load", "diode")

LED_COLORS = {
    "red": (255, 60, 60),
    "green": (60, 255, 110),
    "blue": (70, 150, 255),
    "yellow": (255, 220, 50),
}


def role(kind):
    return PARTS[kind]["role"]


def is_gate(kind):
    return kind in GATES


def is_output(kind):
    return kind is not None and role(kind) in OUTPUT_ROLES


def is_switch(kind):
    return kind is not None and role(kind) == "switch"


def polarized(kind):
    return kind in ("battery", "led")
