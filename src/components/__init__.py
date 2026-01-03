from dataclasses import dataclass as component
from src.components.physics import Velocity, Position
from src.components.render import Renderable

__all__ = [
    "component",
    "Position",
    "Velocity",
    "Renderable",
]
