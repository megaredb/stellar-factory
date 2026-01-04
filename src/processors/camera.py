import arcade
import esper
from arcade.math import lerp_2d
from pyglet.math import Vec2

from src.components.physics import Position
from src.components.gameplay import PlayerControl
from src.processors.keyboard import KeyboardProcessor
from src.processors.mouse import MouseProcessor

ZOOM_SPEED = 0.1
MIN_ZOOM = 0.2
MAX_ZOOM = 4.0
LERP_SPEED = 5.0


class CameraProcessor(esper.Processor):
    def __init__(
        self,
        camera: arcade.Camera2D,
        keyboard: KeyboardProcessor,
        mouse: MouseProcessor,
    ):
        super().__init__()
        self.camera = camera
        self.keyboard = keyboard
        self.mouse = mouse
        self.target_zoom = camera.zoom

    def process(self, dt: float):
        self._handle_mouse_zoom()

        target_pos = self.camera.position

        player_found = False
        for ent, (pos, ctrl) in esper.get_components(Position, PlayerControl):
            target_pos = Vec2(pos.x, pos.y)
            player_found = True
            break

        if not player_found:
            pass

        lerp_t = min(1.0, LERP_SPEED * dt)

        new_pos = lerp_2d(self.camera.position, target_pos, lerp_t)
        self.camera.position = new_pos

        diff = self.target_zoom - self.camera.zoom
        self.camera.zoom += diff * lerp_t

    def _handle_mouse_zoom(self):
        if self.mouse.scroll_y == 0:
            return

        zoom_change = self.mouse.scroll_y * ZOOM_SPEED
        self.target_zoom += zoom_change

        if self.target_zoom < MIN_ZOOM:
            self.target_zoom = MIN_ZOOM
        if self.target_zoom > MAX_ZOOM:
            self.target_zoom = MAX_ZOOM
