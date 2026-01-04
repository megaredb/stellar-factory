from src.components import component
from src.components.base import BaseComponent


@component
class GridPosition(BaseComponent):
    x: int
    y: int


@component
class MapTag(BaseComponent):
    cell_type: int
