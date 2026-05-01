import json
import os

_SAVES_DIR  = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "saves")
_TEAMS_FILE = os.path.join(_SAVES_DIR, "teams.json")
_PARTY_FILE = os.path.join(_SAVES_DIR, "party.json")

_DEFAULT_TEAM_NAMES = ["Team 1", "Team 2", "Team 3", "Team 4", "Team 5", "Team 6"]


def load_teams() -> list[dict]:
    """Return list of {name, party} dicts. Migrates party.json → Team 1 if teams.json missing."""
    if os.path.exists(_TEAMS_FILE):
        with open(_TEAMS_FILE) as f:
            content = f.read().strip()
            teams: list[dict] = json.loads(content) if content else []
        changed = False
        for i, name in enumerate(_DEFAULT_TEAM_NAMES):
            if i >= len(teams):
                teams.append({"name": name, "party": []})
                changed = True
        if changed:
            save_teams(teams)
        return teams

    return _migrate_from_party()


def save_teams(teams: list[dict]) -> None:
    os.makedirs(_SAVES_DIR, exist_ok=True)
    with open(_TEAMS_FILE, "w") as f:
        json.dump(teams, f, indent=2)


def _default_teams() -> list[dict]:
    return [{"name": n, "party": []} for n in _DEFAULT_TEAM_NAMES]


def _migrate_from_party() -> list[dict]:
    """Promote existing party.json into Team 1, create 2 empty teams."""
    existing_party: list[dict] = []
    if os.path.exists(_PARTY_FILE):
        with open(_PARTY_FILE) as f:
            content = f.read().strip()
            existing_party = json.loads(content) if content else []

    teams = [{"name": n, "party": existing_party if i == 0 else []}
              for i, n in enumerate(_DEFAULT_TEAM_NAMES)]
    save_teams(teams)
    return teams
