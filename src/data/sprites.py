_SPRITES: dict[str, dict[str, list[str]]] = {
    "Pikachu": {
        "front": [
            r" /\ /\ ",
            r"( o  o)",
            r" \  = /",
            r" /|  |\ ",
            r"(_|  |_)",
        ],
        "back": [
            r"  _____",
            r" / . . \\",
            r"|  ===  |",
            r" \_____/",
            r"  /   \\ ",
        ],
    },
    "Blastoise": {
        "front": [
            r"  _____  ",
            r" /o   o\ ",
            r"|  ___  |",
            r"|_|   |_|",
            r"  |___|  ",
        ],
        "back": [
            r"  _____  ",
            r" /     \ ",
            r"| [===] |",
            r"|_______|",
            r"  /   \  ",
        ],
    },
    "Charizard": {
        "front": [
            r"  /\  /\ ",
            r" / \/ o) ",
            r"|  /\  | ",
            r" \/  \/ ",
            r"  \__/  ",
        ],
        "back": [
            r"  /\  /\ ",
            r" /  \/  \ ",
            r"|  (())  |",
            r" \______/ ",
            r"  /    \  ",
        ],
    },
    "Pidgeot": {
        "front": [
            r"  _  _ ",
            r" (o)(o)",
            r"  \  / ",
            r"  /\/\ ",
            r" / || \ ",
        ],
        "back": [
            r" ______",
            r"/      \\",
            r"|  ~~  |",
            r"\______/",
            r"  /  \  ",
        ],
    },
}

_GENERIC_FRONT = [
    r"  .---.  ",
    r" (o   o) ",
    r"  > - <  ",
    r"  |___|  ",
    r" /     \ ",
]

_GENERIC_BACK = [
    r"  _____  ",
    r" /     \ ",
    r"|  ~~~  |",
    r" \_____/ ",
    r"  /   \  ",
]


def get_sprite(name: str, view: str = "front") -> list[str]:
    entry = _SPRITES.get(name, {})
    lines = entry.get(view)
    if lines:
        return lines
    return _GENERIC_FRONT if view == "front" else _GENERIC_BACK
