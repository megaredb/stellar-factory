from dataclasses import field
from src.components import component
from src.components.base import BaseComponent


@component
class WorldMap(BaseComponent):
    floor_data: dict[tuple[int, int], int] = field(default_factory=dict)
    object_data: dict[tuple[int, int], int] = field(default_factory=dict)
    entity_map: dict[tuple[int, int, int], int] = field(default_factory=dict)
