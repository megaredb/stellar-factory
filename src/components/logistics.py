from dataclasses import field
from src.components import component


@component
class Collector:
    range: float = 600.0
    pull_speed: float = 300.0


@component
class ResourceChunk:
    resource_type: str = "iron"
    amount: int = 1
    value: int = 1
    lifetime: float = 30.0


@component
class Storage:
    capacity: int = 100


@component
class Drone:
    speed: float = 200.0
    capacity: int = 10
    state: str = "IDLE"  # IDLE, MOVING_TO_SOURCE, MOVING_TO_TARGET
    target_id: int = -1
    target_id: int = -1
    source_id: int = -1
    station_id: int = -1
    inventory: dict[str, int] = field(default_factory=dict)


@component
class DroneStation:
    drone_id: int = -1  # ID of the spawned drone
