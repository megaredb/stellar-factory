import json
from typing import Any

import esper
from src.components import Position, Velocity
from src.components.gameplay import Inventory, PlayerControl, ResourceSource
from src.processors.builder import BuilderProcessor
from src.processors.render import RenderProcessor
from src.entities.player import create_player
from src.entities.asteroids import create_asteroid

SAVE_FILE = "savegame.json"


def save_game(builder: BuilderProcessor):
    print("Saving game...")
    data: dict[str, Any] = {}

    for ent, (pos, inv, ctrl) in esper.get_components(
        Position, Inventory, PlayerControl
    ):
        data["player"] = {"x": pos.x, "y": pos.y, "inventory": inv.resources}
        break

    data["map"] = builder.get_map_state()

    asteroids_data = []
    for ent, (pos, res, vel) in esper.get_components(
        Position, ResourceSource, Velocity
    ):
        asteroids_data.append(
            {
                "x": pos.x,
                "y": pos.y,
                "dx": vel.dx,
                "dy": vel.dy,
                "resource_type": res.resource_type,
                "amount": res.amount,
                "max_amount": res.max_amount,
            }
        )
    data["asteroids"] = asteroids_data

    try:
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f, indent=4)
        print("Game saved successfully!")
    except Exception as e:
        print(f"Error saving game: {e}")


def load_game(builder: BuilderProcessor, render_processor: RenderProcessor):
    print("Loading game...")
    try:
        with open(SAVE_FILE, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Save file not found.")
        return
    except Exception as e:
        print(f"Error loading save file: {e}")
        return

    esper.clear_database()
    render_processor.clear_all_sprites()

    player_data = data.get("player")
    if player_data:
        ent_list = render_processor.sprite_lists["entities"]
        pid = create_player(player_data["x"], player_data["y"], ent_list)

        inv = esper.component_for_entity(pid, Inventory)
        inv.resources = player_data.get("inventory", {})

    builder.load_map_state(data.get("map", {}))

    asteroid_list = render_processor.sprite_lists["asteroids"]
    for ast_data in data.get("asteroids", []):
        aid = create_asteroid(
            x=ast_data["x"],
            y=ast_data["y"],
            dx=ast_data.get("dx", 0),
            dy=ast_data.get("dy", 0),
            sprite_list=asteroid_list,
        )

        res = esper.component_for_entity(aid, ResourceSource)
        res.resource_type = ast_data["resource_type"]
        res.amount = ast_data["amount"]
        res.max_amount = ast_data["max_amount"]

    print("Game loaded successfully!")
