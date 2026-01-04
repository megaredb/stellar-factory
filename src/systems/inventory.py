from src.components.gameplay import Inventory


def add_item(inventory: Inventory, item: str, amount: int) -> None:
    inventory.resources[item] = inventory.resources.get(item, 0) + amount


def has_resources(inventory: Inventory, cost: dict[str, int]) -> bool:
    for res, amount in cost.items():
        if inventory.resources.get(res, 0) < amount:
            return False
    return True


def remove_resources(inventory: Inventory, cost: dict[str, int]) -> None:
    for res, amount in cost.items():
        if res in inventory.resources:
            inventory.resources[res] -= amount
            if inventory.resources[res] <= 0:
                del inventory.resources[res]
