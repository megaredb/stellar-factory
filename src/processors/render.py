import arcade
import esper

from src.components import Renderable, Position
from src.sprites import SpriteListType


class RenderProcessor(esper.Processor):
    def __init__(
        self, window: arcade.Window, camera: arcade.Camera2D, ui_camera: arcade.Camera2D
    ) -> None:
        super().__init__()

        self.window = window
        self.camera = camera
        self.ui_camera = ui_camera

        self.quad_fs = arcade.gl.geometry.quad_2d_fs()
        self.program = window.ctx.load_program(
            fragment_shader="shaders/stars.frag",
            vertex_shader="shaders/default_vs.glsl",
        )
        self.program["u_resolution"] = (window.width, window.height)
        self.total_time = 0.0

        self.sprite_lists: dict[str, SpriteListType] = {
            "floor": arcade.SpriteList(),
            "objects": arcade.SpriteList(),
            "asteroids": arcade.SpriteList(),
            "entities": arcade.SpriteList(),
            "projectiles": arcade.SpriteList(),
            "chunks": arcade.SpriteList(),
            "drones": arcade.SpriteList(),
        }

    def process(self, dt: float) -> None:
        for ent, (renderable, pos) in esper.get_components(Renderable, Position):
            renderable.sprite.position = pos.x, pos.y

        self.total_time += dt

    def on_draw(self) -> None:
        self.window.clear()

        self.camera.use()

        self.program["u_time"] = self.total_time
        self.quad_fs.render(self.program)

        for sprite_list in self.sprite_lists.values():
            sprite_list.draw(pixelated=True)

    def on_resize(self, width: int, height: int) -> None:
        self.program["u_resolution"] = (width, height)

        self.camera.match_window()
        self.ui_camera.match_window()

    def clear_all_sprites(self):
        for sl in self.sprite_lists.values():
            sl.clear()
