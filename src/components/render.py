import arcade
from src.components import component


@component
class Renderable:
    sprite: arcade.Sprite
