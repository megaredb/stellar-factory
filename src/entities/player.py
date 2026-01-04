import esper
from src.components.gameplay import PlayerControl, Inventory
from src.components.physics import Position, Velocity
from src.components.render import Renderable
from src.sprites import SpriteListType, create_ship_sprite


def create_player(x: float, y: float, sprite_list: SpriteListType) -> int:
    player = esper.create_entity(
        Position(x=x, y=y),
        Velocity(dx=0.0, dy=0.0),
        Renderable(sprite=create_ship_sprite(sprite_list)),
        PlayerControl(speed=300.0),
        Inventory(),
    )
    return player
