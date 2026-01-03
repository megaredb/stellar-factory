from dataclasses import dataclass, field
from src.components import component


@component
class PlayerControl:
    speed: float = 200.0


@component
@dataclass
class ResourceSource:
    resource_type: str = "iron"
    amount: int = 10
    max_amount: int = 10


@component
@dataclass
class Inventory:
    resources: dict[str, int] = field(default_factory=dict)

    def add(self, resource_type: str, count: int):
        self.resources[resource_type] = self.resources.get(resource_type, 0) + count

    def has_resources(self, cost: dict[str, int]) -> bool:
        for res, amount in cost.items():
            if self.resources.get(res, 0) < amount:
                return False
        return True

    def remove_resources(self, cost: dict[str, int]):
        for res, amount in cost.items():
            if res in self.resources:
                self.resources[res] -= amount
                if self.resources[res] <= 0:
                    del self.resources[res]
