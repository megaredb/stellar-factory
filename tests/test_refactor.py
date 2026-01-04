import unittest
import esper
import os
import json
from src.components.gameplay import Inventory
from src.systems.inventory import add_item, has_resources, remove_resources
from src.components.world import WorldMap
from src.save_manager import save_game, load_game, SAVE_FILE

# Mock BuilderProcessor
class MockBuilder:
    def get_map_state(self):
        return {}
    def load_map_state(self, data):
        pass
    def refresh_visuals(self):
        pass

class MockRenderProcessor:
    def __init__(self):
        self.sprite_lists = {"entities": [], "asteroids": []}
    def clear_all_sprites(self):
        pass

class TestRefactor(unittest.TestCase):
    def setUp(self):
        esper.clear_database()
        self.world_ent = esper.create_entity(WorldMap())
        self.builder = MockBuilder()

    def tearDown(self):
        if os.path.exists(SAVE_FILE):
            os.remove(SAVE_FILE)

    def test_inventory_system(self):
        inv = Inventory()
        add_item(inv, "iron", 10)
        self.assertEqual(inv.resources["iron"], 10)
        
        self.assertTrue(has_resources(inv, {"iron": 5}))
        self.assertFalse(has_resources(inv, {"iron": 15}))
        
        remove_resources(inv, {"iron": 5})
        self.assertEqual(inv.resources["iron"], 5)

    def test_world_map(self):
        world_map = esper.component_for_entity(self.world_ent, WorldMap)
        world_map.floor_data[(0, 0)] = 1
        self.assertEqual(world_map.floor_data[(0, 0)], 1)

    def test_save_load(self):
        # Setup data
        world_map = esper.component_for_entity(self.world_ent, WorldMap)
        world_map.floor_data[(1, 1)] = 2
        
        # Save
        save_game(self.builder)
        
        # Clear data
        world_map.floor_data.clear()
        
        # Load
        load_game(self.builder, MockRenderProcessor())
        
        # Verify
        # Fetch the new world map component
        for ent, (new_world_map,) in esper.get_components(WorldMap):
            self.assertEqual(new_world_map.floor_data.get((1, 1)), 2)
            break
        else:
            self.fail("WorldMap component not found after load") 
        # Wait, JSON keys are always strings. save_manager loads them. 
        # Let's check save_manager.py again. It loads keys as tuples? 
        # No, json.load returns dict with string keys. 
        # save_manager needs to convert keys back to tuples if it expects tuples.
        # Let's check save_manager.py implementation.

if __name__ == "__main__":
    unittest.main()
