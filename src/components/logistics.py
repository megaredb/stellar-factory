from dataclasses import field
from src.components import component
from src.components.base import BaseComponent


@component
class Collector(BaseComponent):
    range: float = 600.0
    pull_speed: float = 300.0
    capacity: int = 100  # Max items it can hold


@component
class ResourceChunk(BaseComponent):
    resource_type: str = "iron"
    amount: int = 1
    value: int = 1
    lifetime: float = 30.0
    claimed_by: int = -1  # Entity ID of collector claiming this chunk


@component
class Storage(BaseComponent):
    capacity: int = 100


@component
class Drone(BaseComponent):
    speed: float = 200.0
    capacity: int = 10
    state: str = "IDLE"  # IDLE, MOVING_TO_SOURCE, MOVING_TO_TARGET
    target_id: int = -1
    source_id: int = -1
    station_id: int = -1
    inventory: dict[str, int] = field(default_factory=dict)


@component
class DroneStation(BaseComponent):
    drone_id: int = -1  # ID of the spawned drone
