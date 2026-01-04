import arcade
import esper
from src.components import Velocity, Position
from src.components.gameplay import PlayerControl
from src.processors.keyboard import KeyboardProcessor


class PlayerControlProcessor(esper.Processor):
    def __init__(self, keyboard: KeyboardProcessor):
        super().__init__()
        self.keyboard = keyboard

    def process(self, dt: float):
        for ent, (control, vel) in esper.get_components(PlayerControl, Velocity):
            vel.dx = 0.0
            vel.dy = 0.0

            input_x = 0.0
            input_y = 0.0

            if self.keyboard.is_pressed(arcade.key.W) or self.keyboard.is_pressed(
                arcade.key.UP
            ):
                input_y = 1
            elif self.keyboard.is_pressed(arcade.key.S) or self.keyboard.is_pressed(
                arcade.key.DOWN
            ):
                input_y = -1

            if self.keyboard.is_pressed(arcade.key.A) or self.keyboard.is_pressed(
                arcade.key.LEFT
            ):
                input_x = -1
            elif self.keyboard.is_pressed(arcade.key.D) or self.keyboard.is_pressed(
                arcade.key.RIGHT
            ):
                input_x = 1

            if input_x != 0 and input_y != 0:
                input_x *= 0.7071  # sqrt(1/2)
                input_y *= 0.7071  # sqrt(1/2)

            vel.dx = input_x * control.speed
            vel.dy = input_y * control.speed
