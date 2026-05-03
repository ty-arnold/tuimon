from typing import Optional
from pokemon.pokemon_factory import create_pokemon_from_api
from core.game_print import game_print
from models import Pokemon


def print_actions(trainer):
    while True:
        try:
            game_print(f"{trainer.name}'s {trainer.active().name}:")
            game_print("1. Moves")
            game_print("2. Pokemon")
            game_print("3. Items")
            choice = int(input("Select an action: "))
            if choice not in range(1, 4):
                raise ValueError
            return choice
        except ValueError:
            game_print("Invalid choice, please select again.")


def build_party(trainer_name: str, party_size: int = 2) -> list[Pokemon]:
    party: list[Pokemon] = []
    while len(party) < party_size:
        name    = input(f"Choose pokemon {len(party) + 1}/{party_size}: ")
        pokemon = create_pokemon_from_api(name)
        if pokemon is not None:
            party.append(pokemon)
    return party
