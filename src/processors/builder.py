import arcade
import esper
import math

from src.components import Position
from src.components.map import MapTag, GridPosition
from src.components.world import WorldMap
from src.components.combat import Turret
from src.components.logistics import Collector, Storage, DroneStation, Drone
from src.components.production import Factory
from src.systems.audio import AudioSystem
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
from src.systems.inventory import add_item, has_resources, remove_resources

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
        drone_list: arcade.SpriteList,
        camera: arcade.Camera2D,
        mouse: MouseProcessor,
        keyboard: KeyboardProcessor,
    ) -> None:
        super().__init__()
        self.floor_list = floor_list
        self.object_list = object_list
        self.drone_list = drone_list
        self.camera = camera
        self.mouse = mouse
        self.keyboard = keyboard

        self.selected_block = BlockType.PLATFORM

        self.selected_block = BlockType.PLATFORM

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

        world_map = self.get_world_map()
        if not world_map:
            return False, "No World"

        if layer == 0 and (gx, gy) in world_map.floor_data:
            return False, "Occupied"
        if layer == 1 and (gx, gy) in world_map.object_data:
            return False, "Occupied"
        if layer == 1 and (gx, gy) not in world_map.floor_data:
            return False, "Need floor"

        inv = self._get_player_inventory()
        cost = BUILDING_RECIPES.get(self.selected_block, {})
        if inv and not has_resources(inv, cost):
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

    @staticmethod
    def get_world_map() -> WorldMap | None:
        for ent, world_map in esper.get_component(WorldMap):
            return world_map
        return None

    def handle_build(self) -> None:
        gx, gy = self._screen_to_grid()
        cost = BUILDING_RECIPES.get(self.selected_block, {})
        inv = self._get_player_inventory()
        if inv:
            remove_resources(inv, cost)

        world_map = self.get_world_map()
        if not world_map:
            return

        layer = BLOCK_PROPERTIES[self.selected_block]["layer"]
        if layer == 0:
            world_map.floor_data[(gx, gy)] = self.selected_block
            self.update_neighborhood(gx, gy)
        else:
            world_map.object_data[(gx, gy)] = self.selected_block
            self._create_entity(gx, gy, self.selected_block, layer)

        AudioSystem().play_sound("build")

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

        world_map = self.get_world_map()
        if not world_map:
            return

        if (gx, gy) in world_map.object_data:
            target_layer = 1
            block_type = world_map.object_data[(gx, gy)]
        elif (gx, gy) in world_map.floor_data:
            target_layer = 0
            block_type = world_map.floor_data[(gx, gy)]

        if target_layer == -1 or block_type is None:
            return

        if inventory:
            cost = BUILDING_RECIPES.get(block_type, {})
            for res, amount in cost.items():
                add_item(inventory, res, amount)

        self._remove_entity(gx, gy, target_layer)
        if target_layer == 1:
            del world_map.object_data[(gx, gy)]
        else:
            del world_map.floor_data[(gx, gy)]
            self.update_neighborhood(gx, gy)
        AudioSystem().play_sound("remove")

    def _create_entity(self, gx, gy, block_type, layer):
        target_list = self.floor_list if layer == 0 else self.object_list
        sprite = None
        if layer == 0:
            pass
        elif block_type == BlockType.TURRET:
            sprite = arcade.SpriteSolidColor(
                int(ACTUAL_TILE_SIZE * 0.8),  # Narrower
                int(ACTUAL_TILE_SIZE * 0.4),  # Shorter/Narrower
                color=arcade.color.ROCKET_METALLIC,
            )
            sprite.center_x = gx * ACTUAL_TILE_SIZE + HALF_TILE_SIZE
            sprite.center_y = gy * ACTUAL_TILE_SIZE + HALF_TILE_SIZE
            target_list.append(sprite)
        elif block_type == BlockType.COLLECTOR:
            sprite = arcade.SpriteSolidColor(
                int(ACTUAL_TILE_SIZE),
                int(ACTUAL_TILE_SIZE),
                color=arcade.color.ORANGE_PEEL,
            )
            sprite.center_x = gx * ACTUAL_TILE_SIZE + HALF_TILE_SIZE
            sprite.center_y = gy * ACTUAL_TILE_SIZE + HALF_TILE_SIZE
            sprite.center_x = gx * ACTUAL_TILE_SIZE + HALF_TILE_SIZE
            sprite.center_y = gy * ACTUAL_TILE_SIZE + HALF_TILE_SIZE
            target_list.append(sprite)
        elif block_type == BlockType.STORAGE:
            sprite = arcade.SpriteSolidColor(
                int(ACTUAL_TILE_SIZE),
                int(ACTUAL_TILE_SIZE),
                color=arcade.color.DARK_BROWN,
            )
            sprite.center_x = gx * ACTUAL_TILE_SIZE + HALF_TILE_SIZE
            sprite.center_y = gy * ACTUAL_TILE_SIZE + HALF_TILE_SIZE
            target_list.append(sprite)
        elif block_type == BlockType.DRONE_STATION:
            sprite = arcade.SpriteSolidColor(
                int(ACTUAL_TILE_SIZE),
                int(ACTUAL_TILE_SIZE),
                color=arcade.color.AIR_FORCE_BLUE,
            )
            sprite.center_x = gx * ACTUAL_TILE_SIZE + HALF_TILE_SIZE
            sprite.center_y = gy * ACTUAL_TILE_SIZE + HALF_TILE_SIZE
            target_list.append(sprite)
        elif block_type == BlockType.SMELTER:
            sprite = arcade.SpriteSolidColor(
                int(ACTUAL_TILE_SIZE),
                int(ACTUAL_TILE_SIZE),
                color=arcade.color.RED_DEVIL,
            )
            sprite.center_x = gx * ACTUAL_TILE_SIZE + HALF_TILE_SIZE
            sprite.center_y = gy * ACTUAL_TILE_SIZE + HALF_TILE_SIZE
            target_list.append(sprite)
        elif block_type == BlockType.ASSEMBLER:
            sprite = arcade.SpriteSolidColor(
                int(ACTUAL_TILE_SIZE),
                int(ACTUAL_TILE_SIZE),
                color=arcade.color.GREEN,
            )
            sprite.center_x = gx * ACTUAL_TILE_SIZE + HALF_TILE_SIZE
            sprite.center_y = gy * ACTUAL_TILE_SIZE + HALF_TILE_SIZE
            target_list.append(sprite)

        if sprite:
            components = [
                GridPosition(gx, gy),
                Position(sprite.center_x, sprite.center_y),
                MapTag(block_type),
                Renderable(sprite=sprite),
            ]
            if block_type == BlockType.TURRET:
                components.append(Turret())
            elif block_type == BlockType.COLLECTOR:
                components.append(Collector())
                components.append(Inventory())
            elif block_type == BlockType.STORAGE:
                components.append(Storage())
                components.append(Inventory())
            elif block_type == BlockType.DRONE_STATION:
                components.append(DroneStation())
            elif block_type == BlockType.SMELTER or block_type == BlockType.ASSEMBLER:
                components.append(Factory())
                components.append(Inventory())

            ent = esper.create_entity(*components)

            if block_type == BlockType.DRONE_STATION:
                self._spawn_drone(gx, gy, ent)

            world_map = self.get_world_map()
            if world_map:
                world_map.entity_map[(gx, gy, layer)] = ent

    def _remove_entity(self, gx, gy, layer):
        world_map = self.get_world_map()
        if not world_map:
            return

        key = (gx, gy, layer)
        if key in world_map.entity_map:
            ent_id = world_map.entity_map.pop(key)
            if esper.entity_exists(ent_id):
                try:
                    sprite_comp = esper.component_for_entity(ent_id, Renderable)
                    sprite_comp.sprite.remove_from_sprite_lists()

                    # Check for linked drone
                    if esper.has_component(ent_id, DroneStation):
                        station = esper.component_for_entity(ent_id, DroneStation)
                        if station.drone_id != -1 and esper.entity_exists(
                            station.drone_id
                        ):
                            # Remove drone sprite
                            if esper.has_component(station.drone_id, Renderable):
                                drone_rend = esper.component_for_entity(
                                    station.drone_id, Renderable
                                )
                                drone_rend.sprite.remove_from_sprite_lists()
                            esper.delete_entity(station.drone_id)

                    esper.delete_entity(ent_id)
                except KeyError:
                    pass

    def update_neighborhood(self, gx, gy) -> None:
        for dx, dy in [(0, 0), (0, 1), (0, -1), (1, 0), (-1, 0)]:
            self._update_single_floor_visuals(gx + dx, gy + dy)

    def _update_single_floor_visuals(self, gx: int, gy: int) -> None:
        world_map = self.get_world_map()
        if not world_map:
            return

        if (gx, gy) not in world_map.floor_data:
            return
        mask = 0
        for dx, dy, bit_val in NEIGHBOR_OFFSETS:
            if (gx + dx, gy + dy) in world_map.floor_data:
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
        world_map.entity_map[(gx, gy, 0)] = ent

    def refresh_visuals(self):
        world_map = self.get_world_map()
        if not world_map:
            return

        for _, ent_id in list(world_map.entity_map.items()):
            if esper.entity_exists(ent_id):
                esper.delete_entity(ent_id)
        world_map.entity_map.clear()

        for gx, gy in world_map.floor_data.keys():
            self._update_single_floor_visuals(gx, gy)

        for (gx, gy), type_id in world_map.object_data.items():
            self._create_entity(gx, gy, type_id, layer=1)

    def _spawn_drone(self, gx, gy, station_id):
        x = gx * ACTUAL_TILE_SIZE + HALF_TILE_SIZE
        y = gy * ACTUAL_TILE_SIZE + HALF_TILE_SIZE

        sprite = arcade.SpriteCircle(5, arcade.color.WHITE)
        sprite.center_x = x
        sprite.center_y = y
        self.drone_list.append(sprite)

        drone_ent = esper.create_entity(
            Position(x, y), Renderable(sprite=sprite), Drone(station_id=station_id)
        )

        # Link station to drone
        if esper.has_component(station_id, DroneStation):
            station = esper.component_for_entity(station_id, DroneStation)
            station.drone_id = drone_ent
