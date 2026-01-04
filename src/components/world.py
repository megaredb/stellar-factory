from dataclasses import dataclass, field
from src.components import component


@component
class WorldMap:
    floor_data: dict[tuple[int, int], int] = field(default_factory=dict)
    object_data: dict[tuple[int, int], int] = field(default_factory=dict)
    entity_map: dict[tuple[int, int, int], int] = field(default_factory=dict)
