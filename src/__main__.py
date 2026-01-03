import random
import arcade
import esper

from src.processors import (
    MovementProcessor,
    RenderProcessor,
    BuilderProcessor,
    CameraProcessor,
    KeyboardProcessor,
    MouseProcessor,
)
from src.processors.player_control import PlayerControlProcessor
from src.processors.mining import MiningProcessor
from src.processors.ui import UIProcessor

from src.entities.asteroids import create_asteroid
from src.entities.player import create_player


SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Stellar Factory"


class GameView(arcade.Window):
    def __init__(self) -> None:
        super().__init__(
            SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, vsync=True, resizable=True
        )
        self.center_window()

        self.camera = arcade.Camera2D()
        self.default_ui_camera = arcade.Camera2D()

        self.keyboard_processor = KeyboardProcessor()
        self.mouse_processor = MouseProcessor()

        self.player_control = PlayerControlProcessor(self.keyboard_processor)
        self.movement_processor = MovementProcessor()

        self.camera_processor = CameraProcessor(
            self.camera, self.keyboard_processor, self.mouse_processor
        )

        self.render_processor = RenderProcessor(
            self, self.camera, self.default_ui_camera
        )

        self.mining_processor = MiningProcessor(self.camera, self.mouse_processor)

        self.builder_processor = BuilderProcessor(
            self.render_processor.sprite_lists["floor"],
            self.render_processor.sprite_lists["objects"],
            self.camera,
            self.mouse_processor,
            self.keyboard_processor,
        )

        self.ui_processor = UIProcessor(
            self, self.mouse_processor, self.keyboard_processor, self.builder_processor
        )

    def setup(self) -> None:
        self.camera.zoom = 1.0

        if "entities" not in self.render_processor.sprite_lists:
            self.render_processor.sprite_lists["entities"] = arcade.SpriteList()

        create_player(0, 0, self.render_processor.sprite_lists["entities"])

        asteroid_list = self.render_processor.sprite_lists["asteroids"]
        for _ in range(50):
            create_asteroid(
                x=random.randint(-1000, 1000),
                y=random.randint(-1000, 1000),
                dx=random.randint(-10, 10),
                dy=random.randint(-10, 10),
                sprite_list=asteroid_list,
            )

    def on_update(self, delta_time: float) -> None:
        self.keyboard_processor.process(delta_time)

        self.player_control.process(delta_time)

        self.mining_processor.process(delta_time)
        self.builder_processor.process(delta_time)

        self.movement_processor.process(delta_time)

        self.camera_processor.process(delta_time)
        self.render_processor.process(delta_time)
        self.ui_processor.process(delta_time)

        self.mouse_processor.process(delta_time)

    def on_draw(self) -> None:
        self.clear()

        self.render_processor.on_draw()
        self.camera.use()
        self.mining_processor.on_draw()
        self.ui_processor.on_draw_ui()
        self.builder_processor.on_draw()

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)
        self.render_processor.on_resize(width, height)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        self.mouse_processor.on_mouse_press(x, y, button, modifiers)

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        self.mouse_processor.on_mouse_release(x, y, button, modifiers)

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        self.mouse_processor.on_mouse_motion(x, y, dx, dy)

    def on_mouse_drag(
        self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int
    ):
        self.mouse_processor.on_mouse_drag(x, y, dx, dy, buttons, modifiers)

    def on_mouse_scroll(self, x: int, y: int, scroll_x: float, scroll_y: float):
        self.mouse_processor.on_mouse_scroll(x, y, scroll_x, scroll_y)

    def on_key_press(self, symbol: int, modifiers: int):
        self.keyboard_processor.on_key_press(symbol, modifiers)

    def on_key_release(self, symbol: int, modifiers: int):
        self.keyboard_processor.on_key_release(symbol, modifiers)


def main() -> None:
    esper.clear_database()
    window = GameView()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()
