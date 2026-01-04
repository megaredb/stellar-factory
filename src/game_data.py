import arcade

MAP_LIMIT_X = 2000
MAP_LIMIT_Y = 2000

BUILD_RANGE = 300.0


class BlockType:
    PLATFORM = 1
    TURRET = 2
    COLLECTOR = 3
    STORAGE = 4
    DRONE_STATION = 5
    SMELTER = 6
    ASSEMBLER = 7


BUILDING_RECIPES = {
    BlockType.PLATFORM: {"iron": 1},
    BlockType.TURRET: {"iron": 10, "gold": 5},
    BlockType.COLLECTOR: {"iron": 5, "silicon": 5},
    BlockType.STORAGE: {"iron": 20},
    BlockType.DRONE_STATION: {"iron": 20, "gold": 10, "silicon": 10},
    BlockType.SMELTER: {"iron": 10, "gold": 5},
    BlockType.ASSEMBLER: {"iron": 20, "silicon": 10},
}

BLOCK_PROPERTIES = {
    BlockType.PLATFORM: {
        "layer": 0,
        "name": "Platform",
        "color": arcade.color.GRAY,
    },
    BlockType.TURRET: {
        "layer": 1,
        "name": "Turret",
        "color": arcade.color.ROCKET_METALLIC,
    },
    BlockType.COLLECTOR: {
        "layer": 1,
        "name": "Collector",
        "color": arcade.color.ORANGE_PEEL,
    },
    BlockType.STORAGE: {
        "layer": 1,
        "name": "Storage",
        "color": arcade.color.DARK_BROWN,
    },
    BlockType.DRONE_STATION: {
        "layer": 1,
        "name": "Drone Station",
        "color": arcade.color.AIR_FORCE_BLUE,
    },
    BlockType.SMELTER: {
        "layer": 1,
        "name": "Smelter",
        "color": arcade.color.RED_DEVIL,
    },
    BlockType.ASSEMBLER: {
        "layer": 1,
        "name": "Assembler",
        "color": arcade.color.GREEN,
    },
}

TOOLBAR_SLOT_SIZE = 50
TOOLBAR_PADDING = 10
TOOLBAR_COLOR = (50, 50, 50, 200)
TOOLBAR_SELECTED_COLOR = (100, 200, 100, 200)

TOOLBAR_ITEMS = [
    BlockType.PLATFORM,
    BlockType.TURRET,
    BlockType.COLLECTOR,
    BlockType.STORAGE,
    BlockType.DRONE_STATION,
    BlockType.SMELTER,
    BlockType.ASSEMBLER,
]

RECIPES = {
    "iron_bar": {
        "inputs": {"iron": 1},
        "outputs": {"iron_bar": 1},
        "time": 2.0,
        "machine": BlockType.SMELTER,
    },
    "gold_bar": {
        "inputs": {"gold": 1},
        "outputs": {"gold_bar": 1},
        "time": 2.0,
        "machine": BlockType.SMELTER,
    },
    "silicon_wafer": {
        "inputs": {"silicon": 1},
        "outputs": {"silicon_wafer": 1},
        "time": 3.0,
        "machine": BlockType.SMELTER, # Or maybe a different machine? Let's stick to Smelter for now or add Furnace
    },
    "circuit": {
        "inputs": {"iron_bar": 1, "silicon_wafer": 1},
        "outputs": {"circuit": 1},
        "time": 5.0,
        "machine": BlockType.ASSEMBLER,
    },
}
