from src.components import component


@component
class GridPosition:
    x: int
    y: int


@component
class MapTag:
    cell_type: int
