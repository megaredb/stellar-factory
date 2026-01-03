import arcade
import esper
import math

from src.components import Position
from src.components.map import MapTag, GridPosition
from src.components.render import Renderable
from src.components.gameplay import Inventory, PlayerControl
from src.processors import MouseProcessor, KeyboardProcessor
from src.sprites import create_platform_tile, TILE_SIZE
from src.game_data import (
    BlockType,
    BUILDING_RECIPES,
    BLOCK_PROPERTIES,
    BUILD_RANGE,
    MAP_LIMIT_X,
    MAP_LIMIT_Y,
)

SCALE = 3.0
ACTUAL_TILE_SIZE = TILE_SIZE * SCALE
HALF_TILE_SIZE = ACTUAL_TILE_SIZE / 2
CLICK_COOLDOWN = 0.15

NEIGHBOR_OFFSETS = [
    (0, 1, 1),
    (-1, 0, 2),
    (1, 0, 4),
    (0, -1, 8),
]
MASK_TO_TEXTURE_INDEX = {
    0: 15,
    1: 9,
    2: 8,
    4: 13,
    8: 12,
    3: 0,
    5: 1,
    10: 4,
    12: 5,
    6: 10,
    9: 11,
    7: 6,
    11: 7,
    13: 2,
    14: 3,
    15: 14,
}


class BuilderProcessor(esper.Processor):
    def __init__(
        self,
        floor_list: arcade.SpriteList,
        object_list: arcade.SpriteList,
        camera: arcade.Camera2D,
        mouse: MouseProcessor,
        keyboard: KeyboardProcessor,
    ) -> None:
        super().__init__()
        self.floor_list = floor_list
        self.object_list = object_list
        self.camera = camera
        self.mouse = mouse
        self.keyboard = keyboard

        self.selected_block = BlockType.PLATFORM

        self.floor_data: dict[tuple[int, int], int] = {}
        self.object_data: dict[tuple[int, int], int] = {}
        self.entity_map: dict[tuple[int, int, int], int] = {}

        self.ghost_sprite_list: arcade.SpriteList = arcade.SpriteList()
        self.ghost_sprite = arcade.SpriteSolidColor(
            int(ACTUAL_TILE_SIZE), int(ACTUAL_TILE_SIZE), color=arcade.color.WHITE
        )
        self.ghost_sprite.alpha = 180
        self.ghost_sprite_list.append(self.ghost_sprite)

        self.is_placement_valid = False
        self.cooldown_timer = 0.0

    def process(self, dt: float) -> None:
        self._update_ghost()

        if self.cooldown_timer > 0:
            self.cooldown_timer -= dt

        if self.mouse.handled:
            self.ghost_sprite.visible = False
            return

        self.ghost_sprite.visible = True

        if self.cooldown_timer > 0:
            return

        if self.mouse.is_pressed(arcade.MOUSE_BUTTON_LEFT):
            if self.is_placement_valid:
                self.handle_build()
                self.cooldown_timer = CLICK_COOLDOWN
        elif self.mouse.is_pressed(arcade.MOUSE_BUTTON_RIGHT):
            self.handle_remove()
            self.cooldown_timer = CLICK_COOLDOWN

    def _update_ghost(self):
        gx, gy = self._screen_to_grid()
        pixel_x = gx * ACTUAL_TILE_SIZE + HALF_TILE_SIZE
        pixel_y = gy * ACTUAL_TILE_SIZE + HALF_TILE_SIZE
        self.ghost_sprite.position = (pixel_x, pixel_y)

        valid, reason = self._check_placement_validity(gx, gy)
        self.is_placement_valid = valid
        if valid:
            self.ghost_sprite.color = (100, 255, 100)
        else:
            self.ghost_sprite.color = (255, 100, 100)

    def _check_placement_validity(self, gx, gy) -> tuple[bool, str]:
        world_x = gx * ACTUAL_TILE_SIZE
        world_y = gy * ACTUAL_TILE_SIZE
        if abs(world_x) > MAP_LIMIT_X or abs(world_y) > MAP_LIMIT_Y:
            return False, "Out of bounds"

        player_pos = self._get_player_pos()
        if player_pos:
            dist = math.hypot(world_x - player_pos[0], world_y - player_pos[1])
            if dist > BUILD_RANGE:
                return False, "Too far"

        props = BLOCK_PROPERTIES[self.selected_block]
        layer = props["layer"]

        if layer == 0 and (gx, gy) in self.floor_data:
            return False, "Occupied"
        if layer == 1 and (gx, gy) in self.object_data:
            return False, "Occupied"
        if layer == 1 and (gx, gy) not in self.floor_data:
            return False, "Need floor"

        inv = self._get_player_inventory()
        cost = BUILDING_RECIPES.get(self.selected_block, {})
        if inv and not inv.has_resources(cost):
            return False, "No resources"

        return True, "OK"

    def on_draw(self):
        if self.ghost_sprite.visible:
            self.camera.use()
            self.ghost_sprite_list.draw()

    def _screen_to_grid(self) -> tuple[int, int]:
        world_pos = self.camera.unproject((self.mouse.x, self.mouse.y))
        gx = int(world_pos[0] // ACTUAL_TILE_SIZE)
        gy = int(world_pos[1] // ACTUAL_TILE_SIZE)
        return gx, gy

    @staticmethod
    def _get_player_inventory() -> Inventory | None:
        for ent, (inv, ctrl) in esper.get_components(Inventory, PlayerControl):
            return inv
        return None

    @staticmethod
    def _get_player_pos() -> tuple[float, float] | None:
        for ent, (pos, ctrl) in esper.get_components(Position, PlayerControl):
            return pos.x, pos.y
        return None

    def handle_build(self) -> None:
        gx, gy = self._screen_to_grid()
        cost = BUILDING_RECIPES.get(self.selected_block, {})
        inv = self._get_player_inventory()
        if inv:
            inv.remove_resources(cost)

        layer = BLOCK_PROPERTIES[self.selected_block]["layer"]
        if layer == 0:
            self.floor_data[(gx, gy)] = self.selected_block
            self.update_neighborhood(gx, gy)
        else:
            self.object_data[(gx, gy)] = self.selected_block
            self._create_entity(gx, gy, self.selected_block, layer)

    def handle_remove(self) -> None:
        gx, gy = self._screen_to_grid()
        player_pos = self._get_player_pos()
        if player_pos:
            world_x = gx * ACTUAL_TILE_SIZE
            world_y = gy * ACTUAL_TILE_SIZE
            if (
                math.hypot(world_x - player_pos[0], world_y - player_pos[1])
                > BUILD_RANGE
            ):
                return

        inventory = self._get_player_inventory()
        target_layer = -1
        block_type = None

        if (gx, gy) in self.object_data:
            target_layer = 1
            block_type = self.object_data[(gx, gy)]
        elif (gx, gy) in self.floor_data:
            target_layer = 0
            block_type = self.floor_data[(gx, gy)]

        if target_layer == -1 or block_type is None:
            return

        if inventory:
            cost = BUILDING_RECIPES.get(block_type, {})
            for res, amount in cost.items():
                inventory.add(res, amount)

        self._remove_entity(gx, gy, target_layer)
        if target_layer == 1:
            del self.object_data[(gx, gy)]
        else:
            del self.floor_data[(gx, gy)]
            self.update_neighborhood(gx, gy)

    def _create_entity(self, gx, gy, block_type, layer):
        pixel_x = gx * ACTUAL_TILE_SIZE + HALF_TILE_SIZE
        pixel_y = gy * ACTUAL_TILE_SIZE + HALF_TILE_SIZE

        sprite = None
        target_list = self.floor_list if layer == 0 else self.object_list

        if layer == 0:
            pass  # Обрабатывается update_neighborhood
        elif block_type == BlockType.WALL:
            sprite = arcade.SpriteSolidColor(
                int(ACTUAL_TILE_SIZE), int(ACTUAL_TILE_SIZE), arcade.color.INDIAN_RED
            )
            sprite.center_x = pixel_x
            sprite.center_y = pixel_y
            target_list.append(sprite)

        if sprite:
            ent = esper.create_entity(
                GridPosition(gx, gy), MapTag(block_type), Renderable(sprite=sprite)
            )
            self.entity_map[(gx, gy, layer)] = ent

    def _remove_entity(self, gx, gy, layer):
        key = (gx, gy, layer)
        if key in self.entity_map:
            ent_id = self.entity_map.pop(key)
            if esper.entity_exists(ent_id):
                try:
                    sprite_comp = esper.component_for_entity(ent_id, Renderable)
                    sprite_comp.sprite.remove_from_sprite_lists()
                    esper.delete_entity(ent_id)
                except KeyError:
                    pass

    def update_neighborhood(self, gx, gy) -> None:
        for dx, dy in [(0, 0), (0, 1), (0, -1), (1, 0), (-1, 0)]:
            self._update_single_floor_visuals(gx + dx, gy + dy)

    def _update_single_floor_visuals(self, gx: int, gy: int) -> None:
        if (gx, gy) not in self.floor_data:
            return
        mask = 0
        for dx, dy, bit_val in NEIGHBOR_OFFSETS:
            if (gx + dx, gy + dy) in self.floor_data:
                mask += bit_val

        texture_idx = MASK_TO_TEXTURE_INDEX.get(mask, 0)
        self._remove_entity(gx, gy, 0)

        pixel_x = gx * ACTUAL_TILE_SIZE + HALF_TILE_SIZE
        pixel_y = gy * ACTUAL_TILE_SIZE + HALF_TILE_SIZE

        sprite = create_platform_tile(
            self.floor_list, texture_idx, pixel_x, pixel_y, scale=SCALE
        )
        ent = esper.create_entity(
            GridPosition(gx, gy), MapTag(BlockType.PLATFORM), Renderable(sprite=sprite)
        )
        self.entity_map[(gx, gy, 0)] = ent

    def get_map_state(self) -> dict:
        return {
            "floor": [
                {"x": k[0], "y": k[1], "type": v} for k, v in self.floor_data.items()
            ],
            "objects": [
                {"x": k[0], "y": k[1], "type": v} for k, v in self.object_data.items()
            ],
        }

    def load_map_state(self, data: dict):
        for _, ent_id in list(self.entity_map.items()):
            if esper.entity_exists(ent_id):
                esper.delete_entity(ent_id)
        self.entity_map.clear()
        self.floor_data.clear()
        self.object_data.clear()

        for item in data.get("floor", []):
            self.floor_data[(item["x"], item["y"])] = item["type"]

        for item in data.get("objects", []):
            self.object_data[(item["x"], item["y"])] = item["type"]

        for gx, gy in self.floor_data.keys():
            self._update_single_floor_visuals(gx, gy)

        for (gx, gy), type_id in self.object_data.items():
            self._create_entity(gx, gy, type_id, layer=1)
