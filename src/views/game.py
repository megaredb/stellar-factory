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
from src.processors.combat import CombatProcessor
from src.processors.logistics import LogisticsProcessor
from src.processors.production import ProductionProcessor
from src.processors.ui import UIProcessor

from src.entities.asteroids import create_asteroid
from src.entities.player import create_player
from src.components.world import WorldMap
from src.views.pause import PauseView
from src.systems.audio import AudioSystem


class GameView(arcade.View):
    def __init__(self) -> None:
        super().__init__()

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
            self.window, self.camera, self.default_ui_camera
        )

        self.mining_processor = MiningProcessor(
            self.camera,
            self.mouse_processor,
            self.render_processor.sprite_lists["chunks"],
        )
        self.combat_processor = CombatProcessor(
            self.mining_processor,
            self.render_processor.sprite_lists["projectiles"],
        )
        self.logistics_processor = LogisticsProcessor(
            self.render_processor.sprite_lists["drones"]
        )
        self.production_processor = ProductionProcessor()

        self.builder_processor = BuilderProcessor(
            self.render_processor.sprite_lists["floor"],
            self.render_processor.sprite_lists["objects"],
            self.render_processor.sprite_lists["drones"],
            self.camera,
            self.mouse_processor,
            self.keyboard_processor,
        )

        self.ui_processor = UIProcessor(
            self.window,
            self.mouse_processor,
            self.keyboard_processor,
            self.builder_processor,
        )

        self.audio_system = AudioSystem()
        self.audio_system.play_music("sounds/background.wav")

    def setup(self) -> None:
        self.camera.zoom = 1.0

        # Create World Entity
        esper.create_entity(WorldMap())

        if "entities" not in self.render_processor.sprite_lists:
            self.render_processor.sprite_lists["entities"] = arcade.SpriteList()

        create_player(0, 0, self.render_processor.sprite_lists["entities"])

        asteroid_list = self.render_processor.sprite_lists["asteroids"]
        # Initial spawn - wider area, faster speed
        for _ in range(50):
            create_asteroid(
                x=random.randint(-2000, 2000),
                y=random.randint(-2000, 2000),
                dx=random.randint(-40, 40),
                dy=random.randint(-40, 40),
                sprite_list=asteroid_list,
            )

        self.asteroid_spawn_timer = 0.0

    def on_update(self, delta_time: float) -> None:
        self._update_asteroid_spawning(delta_time)
        self.keyboard_processor.process(delta_time)

        self.player_control.process(delta_time)

        self.mining_processor.process(delta_time)
        self.combat_processor.process(delta_time)
        self.logistics_processor.process(delta_time)
        self.production_processor.process(delta_time)
        self.builder_processor.process(delta_time)

        self.movement_processor.process(delta_time)

        self.camera_processor.process(delta_time)
        self.render_processor.process(delta_time)
        self.ui_processor.process(delta_time)

        self.mouse_processor.process(delta_time)
        esper.process()

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
        if symbol == arcade.key.ESCAPE:
            pause_view = PauseView(self)
            self.window.show_view(pause_view)
        else:
            self.keyboard_processor.on_key_press(symbol, modifiers)

    def on_key_release(self, symbol: int, modifiers: int):
        self.keyboard_processor.on_key_release(symbol, modifiers)

    def _update_asteroid_spawning(self, dt: float):
        self.asteroid_spawn_timer += dt
        if self.asteroid_spawn_timer > 1.0:  # Spawn every second
            self.asteroid_spawn_timer = 0.0

            # Spawn off-screen
            cx, cy = self.camera.position
            # Viewport size (approximate, assuming window size + buffer)
            w, h = self.window.width, self.window.height
            buffer = 100

            # Pick a random side
            side = random.choice(["top", "bottom", "left", "right"])

            if side == "top":
                x = cx + random.randint(-w, w)
                y = cy + h + buffer
                dx = random.randint(-20, 20)
                dy = random.randint(-40, -10)  # Move down
            elif side == "bottom":
                x = cx + random.randint(-w, w)
                y = cy - h - buffer
                dx = random.randint(-20, 20)
                dy = random.randint(10, 40)  # Move up
            elif side == "left":
                x = cx - w - buffer
                y = cy + random.randint(-h, h)
                dx = random.randint(10, 40)  # Move right
                dy = random.randint(-20, 20)
            elif side == "right":
                x = cx + w + buffer
                y = cy + random.randint(-h, h)
                dx = random.randint(-40, -10)  # Move left
                dy = random.randint(-20, 20)

            create_asteroid(
                x=x,
                y=y,
                dx=dx,
                dy=dy,
                sprite_list=self.render_processor.sprite_lists["asteroids"],
            )
