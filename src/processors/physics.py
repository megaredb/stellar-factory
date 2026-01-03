import esper
from src.components import Position, Velocity
from src.game_data import MAP_LIMIT_X, MAP_LIMIT_Y


class MovementProcessor(esper.Processor):
    def process(self, dt: float) -> None:
        for ent, (pos, vel) in esper.get_components(Position, Velocity):
            pos.x += vel.dx * dt
            pos.y += vel.dy * dt

            if pos.x < -MAP_LIMIT_X:
                pos.x = -MAP_LIMIT_X
            if pos.x > MAP_LIMIT_X:
                pos.x = MAP_LIMIT_X
            if pos.y < -MAP_LIMIT_Y:
                pos.y = -MAP_LIMIT_Y
            if pos.y > MAP_LIMIT_Y:
                pos.y = MAP_LIMIT_Y
