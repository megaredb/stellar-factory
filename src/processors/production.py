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
        # Find a valid recipe based on inputs
        # For now, let's assume the factory is set to a specific recipe or auto-detects
        # Auto-detect: check all recipes for this machine type
        
        # We need to know the machine type. We can get it from MapTag if we query it, 
        # or store it in Factory component. 
        # Let's assume we can infer it or just check all recipes.
        # Checking all recipes is inefficient but fine for now.
        
        possible_recipe = None
        for name, data in RECIPES.items():
            # Check if inputs match what's in inventory
            inputs = data["inputs"]
            has_inputs = True
            for res, amount in inputs.items():
                if inv.resources.get(res, 0) < amount:
                    has_inputs = False
                    break
            
            if has_inputs:
                possible_recipe = name
                break
        
        if possible_recipe:
            factory.recipe_id = possible_recipe
            factory.processing_time = RECIPES[possible_recipe]["time"]
            factory.progress = 0.0
            factory.is_working = True
            
            # Consume inputs immediately? Or at end?
            # Usually consume at start to reserve them.
            inputs = RECIPES[possible_recipe]["inputs"]
            remove_resources(inv, inputs)

    def _process_production(self, dt: float, factory: Factory, inv: Inventory):
        factory.progress += dt
        if factory.progress >= factory.processing_time:
            # Finish
            recipe = RECIPES.get(factory.recipe_id)
            if recipe:
                outputs = recipe["outputs"]
                for res, amount in outputs.items():
                    add_item(inv, res, amount)
            
            factory.is_working = False
            factory.progress = 0.0
            factory.recipe_id = ""
