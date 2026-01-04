from dataclasses import field
from src.components import component
from src.components.base import BaseComponent


@component
class PlayerControl(BaseComponent):
    speed: float = 200.0


@component
class ResourceSource(BaseComponent):
    resource_type: str = "iron"
    amount: int = 10
    max_amount: int = 10


@component
class Inventory(BaseComponent):
    resources: dict[str, int] = field(default_factory=dict)
