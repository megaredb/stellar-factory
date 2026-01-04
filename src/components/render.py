import arcade
from src.components import component
from src.components.base import BaseComponent


@component
class Renderable(BaseComponent):
    sprite: arcade.Sprite
