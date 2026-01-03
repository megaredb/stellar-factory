import esper
import random

from src.components import Position, Velocity, Renderable
from src.components.gameplay import ResourceSource
from src.sprites import SpriteListType, create_asteroid_sprite

RESOURCE_TYPES = ["iron", "gold", "silicon"]


def create_asteroid(
    x: float, y: float, dx: float, dy: float, sprite_list: SpriteListType
) -> int:
    # Случайный ресурс и количество
    res_type = random.choice(RESOURCE_TYPES)
    amount = random.randint(5, 50)

    asteroid = esper.create_entity(
        Position(x=x, y=y),
        Velocity(dx=dx, dy=dy),
        Renderable(sprite=create_asteroid_sprite(sprite_list)),
        ResourceSource(resource_type=res_type, amount=amount, max_amount=amount),
    )

    return asteroid
