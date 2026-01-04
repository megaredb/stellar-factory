import arcade
import esper

from src.components.gameplay import Inventory, PlayerControl
from src.components.map import MapTag
from src.components.logistics import Storage
from src.processors import KeyboardProcessor
from src.processors.mouse import MouseProcessor
from src.processors.builder import BuilderProcessor
from src.game_data import (
    TOOLBAR_ITEMS,
    TOOLBAR_SLOT_SIZE,
    TOOLBAR_PADDING,
    TOOLBAR_SELECTED_COLOR,
    BLOCK_PROPERTIES,
    RECIPES,
)
from src.components.production import Factory


class UIProcessor(esper.Processor):
    def __init__(
        self,
        window: arcade.Window,
        mouse: MouseProcessor,
        keyboard: KeyboardProcessor,
        builder: BuilderProcessor,
    ):
        super().__init__()
        self.window = window
        self.mouse = mouse
        self.keyboard = keyboard
        self.builder = builder

    def process(self, dt: float):
        for i in range(10):
            key = arcade.key.KEY_1 + i
            if not self.keyboard.is_pressed(key):
                continue

            if i < len(TOOLBAR_ITEMS):
                self.builder.selected_block = TOOLBAR_ITEMS[i]

        if self.mouse.is_pressed(arcade.MOUSE_BUTTON_LEFT):
            self._handle_click()

    def _handle_click(self):
        screen_w = self.window.width

        total_width = (
            len(TOOLBAR_ITEMS) * (TOOLBAR_SLOT_SIZE + TOOLBAR_PADDING) + TOOLBAR_PADDING
        )
        start_x = (screen_w - total_width) // 2
        y = TOOLBAR_PADDING

        for i, block_type in enumerate(TOOLBAR_ITEMS):
            x = start_x + TOOLBAR_PADDING + i * (TOOLBAR_SLOT_SIZE + TOOLBAR_PADDING)

            if (
                x <= self.mouse.x <= x + TOOLBAR_SLOT_SIZE
                and y <= self.mouse.y <= y + TOOLBAR_SLOT_SIZE
            ):
                self.builder.selected_block = block_type
                self.mouse.mark_handled()
                return

        if (
            start_x <= self.mouse.x <= start_x + total_width
            and 0 <= self.mouse.y <= y + TOOLBAR_SLOT_SIZE + TOOLBAR_PADDING
        ):
            self.mouse.mark_handled()

    def on_draw_ui(self):
        self.window.default_camera.use()

        self._draw_inventory_text()

        self._draw_toolbar()
        self._draw_hover_info()

    def _draw_hover_info(self):
        # Convert mouse to world
        world_x, world_y, _ = self.builder.camera.unproject(
            (self.mouse.x, self.mouse.y)
        )

        # Grid coords
        from src.processors.builder import ACTUAL_TILE_SIZE

        gx = int(world_x // ACTUAL_TILE_SIZE)
        gy = int(world_y // ACTUAL_TILE_SIZE)

        # Find entity at this location
        world_map = self.builder.get_world_map()
        if not world_map:
            return

        ent_id = world_map.entity_map.get((gx, gy, 1))  # Check object layer
        if not ent_id:
            ent_id = world_map.entity_map.get((gx, gy, 0))  # Check floor layer

        if not ent_id or not esper.entity_exists(ent_id):
            return

        # Gather info
        info_lines = []

        # Name
        if esper.has_component(ent_id, MapTag):
            tag = esper.component_for_entity(ent_id, MapTag)
            props = BLOCK_PROPERTIES.get(tag.cell_type, {})
            name = props.get("name", "Unknown")
            info_lines.append(f"Block: {name}")

        # Inventory / Storage
        if esper.has_component(ent_id, Inventory):
            inv = esper.component_for_entity(ent_id, Inventory)
            if inv.resources:
                info_lines.append("Inventory:")
                for res, amount in inv.resources.items():
                    info_lines.append(f" - {res}: {amount}")
            else:
                info_lines.append("Inventory: Empty")

        if esper.has_component(ent_id, Storage):
            store = esper.component_for_entity(ent_id, Storage)
            info_lines.append(f"Capacity: {store.capacity}")

        if esper.has_component(ent_id, Factory):
            factory = esper.component_for_entity(ent_id, Factory)
            status = "Working" if factory.is_working else "Idle"
            info_lines.append(f"Status: {status}")
            if factory.is_working:
                progress = int((factory.progress / factory.processing_time) * 100)
                info_lines.append(f"Progress: {progress}%")
            else:
                # Show missing inputs if idle
                # Need to find potential recipe
                if esper.has_component(ent_id, MapTag):
                    tag = esper.component_for_entity(ent_id, MapTag)
                    machine_type = tag.cell_type

                    # Check recipes
                    for name, data in RECIPES.items():
                        if data["machine"] == machine_type:
                            # Check inputs
                            missing = []
                            inv = esper.component_for_entity(ent_id, Inventory)
                            for res, amount in data["inputs"].items():
                                current = inv.resources.get(res, 0)
                                if current < amount:
                                    missing.append(f"{res} ({current}/{amount})")

                            if missing:
                                info_lines.append(f"Missing: {', '.join(missing)}")

        if not info_lines:
            return

        # Draw tooltip
        x = self.mouse.x + 15
        y = self.mouse.y - 15

        line_height = 16
        padding = 5
        width = 150
        height = len(info_lines) * line_height + padding * 4

        # Background
        arcade.draw_rect_filled(
            arcade.rect.XYWH(x + width / 2, y - height / 2, width, height),
            (0, 0, 0, 200),
        )

        # Text
        for i, line in enumerate(info_lines):
            arcade.draw_text(
                line,
                x + padding,
                y - padding - (i + 1) * line_height + 4,
                arcade.color.WHITE,
                12,
            )

    def _draw_inventory_text(self):
        player_inv = None
        for ent, (inv, ctrl) in esper.get_components(Inventory, PlayerControl):
            player_inv = inv
            break

        if player_inv:
            text = ""
            for resource, amount in player_inv.resources.items():
                text += f"{resource}: {amount} | "
            arcade.draw_text(text, 10, self.window.height - 30, arcade.color.WHITE, 14)

    def _draw_toolbar(self):
        screen_w = self.window.width
        num_items = len(TOOLBAR_ITEMS)

        total_width = (
            num_items * (TOOLBAR_SLOT_SIZE + TOOLBAR_PADDING) + TOOLBAR_PADDING
        )
        start_x = (screen_w - total_width) // 2

        for i, block_type in enumerate(TOOLBAR_ITEMS):
            x = start_x + TOOLBAR_PADDING + i * (TOOLBAR_SLOT_SIZE + TOOLBAR_PADDING)
            y = TOOLBAR_PADDING

            is_selected = self.builder.selected_block == block_type
            color = TOOLBAR_SELECTED_COLOR if is_selected else (100, 100, 100, 255)

            arcade.draw_rect_outline(
                arcade.rect.XYWH(x, y, TOOLBAR_SLOT_SIZE, TOOLBAR_SLOT_SIZE),
                color=color,
                border_width=2 if is_selected else 1,
            )

            props = BLOCK_PROPERTIES.get(block_type, {})
            name = props.get("name", "?")[0]
            arcade.draw_text(
                name,
                x + TOOLBAR_SLOT_SIZE / 2,
                y + TOOLBAR_SLOT_SIZE / 2,
                arcade.color.WHITE,
                14,
                anchor_x="center",
                anchor_y="center",
            )

            arcade.draw_text(str(i + 1), x + 2, y + 2, arcade.color.GRAY, 10)
