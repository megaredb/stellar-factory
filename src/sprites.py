import arcade
from arcade import SpriteList

type SpriteListType = SpriteList[arcade.Sprite]


TILE_SIZE = 16
GRID_WIDTH = 4
TOTAL_TILES = 16

# Загружаем ресурсы
try:
    asteroid_texture = arcade.load_texture("sprites/asteroids/asteroid.png")
    platform_textures = arcade.load_spritesheet(
        "sprites/platform.png",
    ).get_texture_grid((16, 16), 4, 16)
except FileNotFoundError:
    print("Warning: Some sprites not found. Using fallbacks.")
    asteroid_texture = arcade.make_circle_texture(16, arcade.color.GRAY)
    platform_textures = []


def create_asteroid_sprite(target_list: SpriteListType) -> arcade.Sprite:
    new_sprite = arcade.Sprite(asteroid_texture)
    target_list.append(new_sprite)
    return new_sprite


def create_platform_tile(
    target_list: SpriteListType,
    texture_index: int,
    center_x: float,
    center_y: float,
    scale: float = 1.0,
) -> arcade.Sprite:
    if platform_textures and 0 <= texture_index < len(platform_textures):
        tex = platform_textures[texture_index]
        new_sprite = arcade.Sprite(tex, scale=scale)
    else:
        new_sprite = arcade.SpriteSolidColor(
            int(16 * scale), int(16 * scale), color=arcade.color.DARK_GRAY
        )

    new_sprite.center_x = center_x
    new_sprite.center_y = center_y

    target_list.append(new_sprite)

    return new_sprite


def create_ship_sprite(target_list: SpriteListType) -> arcade.Sprite:
    new_sprite = arcade.SpriteSolidColor(24, 24, color=arcade.color.CYAN)

    target_list.append(new_sprite)
    return new_sprite
