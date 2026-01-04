from src.components import component
from src.components.base import BaseComponent


@component
class Position(BaseComponent):
    x: float
    y: float


@component
class Velocity(BaseComponent):
    dx: float
    dy: float
