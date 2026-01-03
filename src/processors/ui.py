import arcade
import esper
from arcade.types import AnchorPoint

from src.components.gameplay import Inventory, PlayerControl
from src.processors import KeyboardProcessor
from src.processors.mouse import MouseProcessor
from src.processors.builder import BuilderProcessor
from src.game_data import (
    TOOLBAR_ITEMS,
    TOOLBAR_SLOT_SIZE,
    TOOLBAR_PADDING,
    TOOLBAR_COLOR,
    TOOLBAR_SELECTED_COLOR,
    BLOCK_PROPERTIES,
)


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
        if self.mouse.is_pressed(arcade.MOUSE_BUTTON_LEFT):
            self._handle_click()

        if self.keyboard.is_pressed(arcade.key.KEY_1):
            self.builder.selected_block = TOOLBAR_ITEMS[0]

        if self.keyboard.is_pressed(arcade.key.KEY_2):
            self.builder.selected_block = TOOLBAR_ITEMS[1]

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

    def _draw_inventory_text(self):
        player_inv = None
        for ent, (inv, ctrl) in esper.get_components(Inventory, PlayerControl):
            player_inv = inv
            break

        if player_inv:
            text = f"Res: {player_inv.resources}"
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
