from src.components import component


@component
class Position:
    x: float
    y: float


@component
class Velocity:
    dx: float
    dy: float
