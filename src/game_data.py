import arcade

MAP_LIMIT_X = 2000
MAP_LIMIT_Y = 2000

BUILD_RANGE = 300.0


class BlockType:
    PLATFORM = 1
    WALL = 2


BUILDING_RECIPES = {
    BlockType.PLATFORM: {"iron": 1},
    BlockType.WALL: {"iron": 5, "gold": 1},
}

BLOCK_PROPERTIES = {
    BlockType.PLATFORM: {
        "layer": 0,
        "name": "Platform",
        "color": arcade.color.GRAY,
    },
    BlockType.WALL: {
        "layer": 1,
        "name": "Wall",
        "color": arcade.color.INDIAN_RED,
    },
}

TOOLBAR_SLOT_SIZE = 50
TOOLBAR_PADDING = 10
TOOLBAR_COLOR = (50, 50, 50, 200)
TOOLBAR_SELECTED_COLOR = (100, 200, 100, 200)

TOOLBAR_ITEMS = [BlockType.PLATFORM, BlockType.WALL]
