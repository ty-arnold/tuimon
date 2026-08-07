from dataclasses import dataclass


@dataclass(frozen=True)
class Ability:
    """Pokemon ability. Constructed from cached PokeAPI data."""
    name: str
    description: str = ""
