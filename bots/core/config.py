import json
from pathlib import Path

DEFAULT_MOUSE_X = None
DEFAULT_MOUSE_Y = None
MIN_CLICK_DELAY = None
MAX_CLICK_DELAY = None
KEYBOARD_ADJACENCY = None
STEPS = None
MAX_NON_OVERSHOOT_OFFSET = None
MAX_OVERSHOOT_OFFSET = None


def _unpack_config():
    base_dir = Path(__file__).resolve().parent
    config_path = base_dir / "data" / "config.json"

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def define_config_variables():
    global DEFAULT_MOUSE_X
    global DEFAULT_MOUSE_Y
    global MIN_CLICK_DELAY
    global MAX_CLICK_DELAY
    global KEYBOARD_ADJACENCY
    global STEPS
    global MAX_NON_OVERSHOOT_OFFSET
    global MAX_OVERSHOOT_OFFSET

    data = _unpack_config()

    DEFAULT_MOUSE_Y = data["mouse"]["position"]["DEFAULT_MOUSE_Y"]
    DEFAULT_MOUSE_X = data["mouse"]["position"]["DEFAULT_MOUSE_X"]

    MIN_CLICK_DELAY = data["mouse"]["input"]["MIN_CLICK_DELAY"]
    MAX_CLICK_DELAY = data["mouse"]["input"]["MAX_CLICK_DELAY"]

    KEYBOARD_ADJACENCY = data["keyboard"]["KEYBOARD_ADJACENCY"]

    STEPS = data["movement"]["STEPS"]
    MAX_NON_OVERSHOOT_OFFSET = data["movement"]["MAX_NON_OVERSHOOT_OFFSET"]
    MAX_OVERSHOOT_OFFSET = data["movement"]["MAX_OVERSHOOT_OFFSET"]

define_config_variables() #this needs to run 