from dataclasses import field
from src.components import component


@component
class PlayerControl:
    speed: float = 200.0


@component
class ResourceSource:
    resource_type: str = "iron"
    amount: int = 10
    max_amount: int = 10


@component
class Inventory:
    resources: dict[str, int] = field(default_factory=dict)
