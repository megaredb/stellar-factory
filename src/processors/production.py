import esper
from src.components.production import Factory
from src.components.gameplay import Inventory
from src.game_data import RECIPES
from src.systems.inventory import remove_resources, add_item


class ProductionProcessor(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self, dt: float):
        for ent, (factory, inv) in esper.get_components(Factory, Inventory):
            if not factory.is_working:
                self._check_start_production(factory, inv)
            else:
                self._process_production(dt, factory, inv)

    def _check_start_production(self, factory: Factory, inv: Inventory):
        possible_recipe = None
        for name, data in RECIPES.items():
            # Check if inputs match what's in inventory
            inputs = data["inputs"]
            has_inputs = True
            for res, amount in inputs.items():  # type: ignore
                if inv.resources.get(res, 0) < amount:
                    has_inputs = False
                    break

            if has_inputs:
                possible_recipe = name
                break

        if possible_recipe:
            factory.recipe_id = possible_recipe
            factory.processing_time = RECIPES[possible_recipe]["time"]  # type: ignore
            factory.progress = 0.0
            factory.is_working = True

            inputs = RECIPES[possible_recipe]["inputs"]
            remove_resources(inv, inputs)  # type: ignore

    def _process_production(self, dt: float, factory: Factory, inv: Inventory):
        factory.progress += dt
        if factory.progress >= factory.processing_time:
            # Finish
            recipe = RECIPES.get(factory.recipe_id)
            if recipe:
                outputs = recipe["outputs"]
                for res, amount in outputs.items():  # type: ignore
                    add_item(inv, res, amount)

            factory.is_working = False
            factory.progress = 0.0
            factory.recipe_id = ""
