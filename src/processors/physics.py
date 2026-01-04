import esper
from src.components.physics import Position, Velocity
from src.components.gameplay import ResourceSource
from src.components.render import Renderable
from src.game_data import MAP_LIMIT_X, MAP_LIMIT_Y


class MovementProcessor(esper.Processor):
    def __init__(self):
        super().__init__()
        self.entities_to_delete = []

    def process(self, dt: float) -> None:
        self.entities_to_delete.clear()

        for ent, (pos, vel) in esper.get_components(Position, Velocity):
            pos.x += vel.dx * dt
            pos.y += vel.dy * dt

            limit_x: float = MAP_LIMIT_X
            limit_y: float = MAP_LIMIT_Y

            if esper.has_component(ent, ResourceSource):
                limit_x *= 1.5
                limit_y *= 1.5
                if abs(pos.x) > limit_x or abs(pos.y) > limit_y:
                    self.entities_to_delete.append(ent)
                    continue

            if pos.x < -limit_x:
                pos.x = -limit_x
            if pos.x > limit_x:
                pos.x = limit_x
            if pos.y < -limit_y:
                pos.y = -limit_y
            if pos.y > limit_y:
                pos.y = limit_y

        for ent in self.entities_to_delete:
            if esper.entity_exists(ent):
                try:
                    if esper.has_component(ent, Renderable):
                        renderable = esper.component_for_entity(ent, Renderable)
                        renderable.sprite.remove_from_sprite_lists()
                    esper.delete_entity(ent)
                except KeyError:
                    pass
