import arcade
import esper
import math

from src.components import Position, Velocity, Renderable
from src.components.logistics import Collector, ResourceChunk, Drone, Storage, DroneStation
from src.components.gameplay import Inventory, PlayerControl
from src.components.production import Factory
from src.components.map import MapTag
from src.game_data import RECIPES, BLOCK_PROPERTIES
from src.systems.inventory import add_item, remove_resources
from src.systems.audio import AudioSystem


class LogisticsProcessor(esper.Processor):
    def __init__(self, drone_list: arcade.SpriteList):
        super().__init__()
        self.drone_list = drone_list

    def process(self, dt: float):
        self._process_chunks(dt)
        self._process_drones(dt)

    def _process_chunks(self, dt: float):
        chunks_to_destroy = []

        # Get all collectors (including player)
        collectors = []
        for ent, (collector, pos) in esper.get_components(Collector, Position):
            collectors.append(
                (ent, collector, pos, None)
            )  # None for inventory, handled later if needed

        # Player is also a collector (conceptually)
        for ent, (inv, ctrl, pos) in esper.get_components(
            Inventory, PlayerControl, Position
        ):
            # Create a temporary "Collector" component for the player
            player_collector = Collector(range=100.0, pull_speed=400.0)
            collectors.append((ent, player_collector, pos, inv))  # type: ignore

        for chunk_ent, (
            chunk,
            chunk_pos,
            chunk_vel,
            chunk_rend,
        ) in esper.get_components(ResourceChunk, Position, Velocity, Renderable):
            chunk.lifetime -= dt
            if chunk.lifetime <= 0:
                chunks_to_destroy.append((chunk_ent, chunk_rend))
                continue

            # Apply drag
            chunk_vel.dx *= 0.95
            chunk_vel.dy *= 0.95

            # Check attraction
            for col_ent, col, col_pos, col_inv in collectors:
                dist = math.hypot(col_pos.x - chunk_pos.x, col_pos.y - chunk_pos.y)

                if dist < col.range:
                    # Pull towards collector
                    angle = math.atan2(col_pos.y - chunk_pos.y, col_pos.x - chunk_pos.x)
                    chunk_vel.dx += math.cos(angle) * col.pull_speed * dt
                    chunk_vel.dy += math.sin(angle) * col.pull_speed * dt

                    # Collection radius
                    if dist < 20:
                        if self._collect_chunk(chunk_ent, chunk, col_ent, col_inv):
                            chunks_to_destroy.append((chunk_ent, chunk_rend))
                        break  # Collected, stop checking other collectors

        for ent, rend in chunks_to_destroy:
            self._destroy_chunk(ent, rend)

    def _collect_chunk(self, chunk_ent, chunk, col_ent, col_inv):
        # If it's the player, add to inventory directly
        if col_inv:
            add_item(col_inv, chunk.resource_type, chunk.amount)
            # AudioSystem().play_sound("collect") # Need sound
            return True
        else:
            # If it's a block collector, it needs an inventory component to store it.
            if esper.has_component(col_ent, Inventory):
                inv = esper.component_for_entity(col_ent, Inventory)
                add_item(inv, chunk.resource_type, chunk.amount)
                return True

        return False

    def _destroy_chunk(self, ent, renderable):
        renderable.sprite.remove_from_sprite_lists()
        esper.delete_entity(ent)

    def _process_drones(self, dt: float):
        for ent, (drone, pos, renderable) in esper.get_components(Drone, Position, Renderable):
            if drone.state == "IDLE":
                self._handle_idle(ent, drone, pos)
            elif drone.state == "MOVING_TO_SOURCE":
                self._handle_moving_to_source(dt, ent, drone, pos, renderable)
            elif drone.state == "MOVING_TO_TARGET":
                self._handle_moving_to_target(dt, ent, drone, pos, renderable)
            elif drone.state == "RETURNING_TO_STATION":
                self._handle_returning_to_station(dt, ent, drone, pos, renderable)

    def _handle_idle(self, ent, drone, pos):
        # Find source (Collector with items)
        source_id = self._find_source(pos)
        if source_id != -1:
            drone.source_id = source_id
            drone.state = "MOVING_TO_SOURCE"
        else:
            # Return to station if not already there
            if drone.station_id != -1 and esper.entity_exists(drone.station_id):
                station_pos = esper.component_for_entity(drone.station_id, Position)
                dist = math.hypot(station_pos.x - pos.x, station_pos.y - pos.y)
                if dist > 10.0:
                    drone.state = "RETURNING_TO_STATION"

    def _handle_moving_to_source(self, dt, ent, drone, pos, renderable):
        if not esper.entity_exists(drone.source_id):
            drone.state = "IDLE"
            return

        target_pos = esper.component_for_entity(drone.source_id, Position)
        if self._move_towards(dt, pos, target_pos, drone.speed, renderable):
            # Arrived
            self._take_items(drone, drone.source_id)
            
            # Find target (Storage or Factory)
            target_id = self._find_target(pos, drone)
            if target_id != -1:
                drone.target_id = target_id
                drone.state = "MOVING_TO_TARGET"
            else:
                drone.state = "IDLE"

    def _handle_moving_to_target(self, dt, ent, drone, pos, renderable):
        if not esper.entity_exists(drone.target_id):
            drone.state = "IDLE"
            return

        target_pos = esper.component_for_entity(drone.target_id, Position)
        if self._move_towards(dt, pos, target_pos, drone.speed, renderable):
            # Arrived
            self._deposit_items(drone, drone.target_id)
            drone.state = "IDLE"

    def _handle_returning_to_station(self, dt, ent, drone, pos, renderable):
        if not esper.entity_exists(drone.station_id):
            drone.state = "IDLE"
            return

        target_pos = esper.component_for_entity(drone.station_id, Position)
        if self._move_towards(dt, pos, target_pos, drone.speed, renderable):
            drone.state = "IDLE"

    def _move_towards(self, dt, current_pos, target_pos, speed, renderable):
        dx = target_pos.x - current_pos.x
        dy = target_pos.y - current_pos.y
        dist = math.hypot(dx, dy)
        
        if dist < 5.0:
            return True
            
        angle = math.atan2(dy, dx)
        current_pos.x += math.cos(angle) * speed * dt
        current_pos.y += math.sin(angle) * speed * dt
        
        renderable.sprite.center_x = current_pos.x
        renderable.sprite.center_y = current_pos.y
        renderable.sprite.angle = math.degrees(angle) - 90 # -90 because sprite points up usually
        
        return False


    def _find_source(self, pos):
        best_id = -1
        min_dist = float('inf')
        
        # 1. Check Collectors (High Priority)
        for ent, (col, inv, col_pos) in esper.get_components(Collector, Inventory, Position):
            if not inv.resources:
                continue
                
            dist = math.hypot(col_pos.x - pos.x, col_pos.y - pos.y)
            if dist < min_dist:
                min_dist = dist
                best_id = ent
        
        if best_id != -1:
            return best_id

        # 2. Check Factories with Output (Medium Priority)
        for ent, (factory, inv, factory_pos, tag) in esper.get_components(Factory, Inventory, Position, MapTag):
            if not inv.resources:
                continue
                
            machine_type = tag.cell_type
            
            # Determine valid inputs for this machine
            valid_inputs = set()
            for recipe_name, data in RECIPES.items():
                if data["machine"] == machine_type:
                    for input_item in data["inputs"]:
                        valid_inputs.add(input_item)
            
            # Check if there are any items that are NOT valid inputs (i.e., outputs)
            has_output = False
            for res in inv.resources:
                if res not in valid_inputs:
                    has_output = True
                    break
            
            if has_output:
                dist = math.hypot(factory_pos.x - pos.x, factory_pos.y - pos.y)
                if dist < min_dist:
                    min_dist = dist
                    best_id = ent

        if best_id != -1:
            return best_id

        # 3. Check Storage (Low Priority) - Only if factories need resources
        # This is a bit expensive, maybe optimize later
        needed_resources = set()
        for ent, (factory, inv, tag) in esper.get_components(Factory, Inventory, MapTag):
            machine_type = tag.cell_type
            for recipe_name, data in RECIPES.items():
                if data["machine"] == machine_type:
                    for input_item in data["inputs"]:
                        # If factory needs this item (simple check, not checking amount)
                        needed_resources.add(input_item)

        if not needed_resources:
            return -1

        for ent, (store, inv, store_pos) in esper.get_components(Storage, Inventory, Position):
            if not inv.resources:
                continue
            
            # Check if storage has any needed resource
            has_needed = False
            for res in inv.resources:
                if res in needed_resources:
                    has_needed = True
                    break
            
            if not has_needed:
                continue

            dist = math.hypot(store_pos.x - pos.x, store_pos.y - pos.y)
            if dist < min_dist:
                min_dist = dist
                best_id = ent
                
        return best_id

    def _find_target(self, pos, drone):
        best_id = -1
        min_dist = float('inf')
        
        # 1. Check Factories that need inputs
        for ent, (factory, inv, factory_pos, tag) in esper.get_components(Factory, Inventory, Position, MapTag):
            # Check if factory accepts what drone has
            if not drone.inventory:
                continue
                
            # Get machine type and valid inputs
            machine_type = tag.cell_type
            
            # Simple check: does any recipe for this machine use the item?
            accepts_item = False
            input_limit_reached = False
            
            for recipe_name, data in RECIPES.items():
                if data["machine"] == machine_type:
                    for input_item, input_amount in data["inputs"].items():
                        if input_item in drone.inventory:
                            # Check input limit (e.g., 5x recipe cost)
                            current_amount = inv.resources.get(input_item, 0)
                            if current_amount < input_amount * 5:
                                accepts_item = True
                            else:
                                input_limit_reached = True
                            break
                if accepts_item:
                    break
            
            if accepts_item:
                dist = math.hypot(factory_pos.x - pos.x, factory_pos.y - pos.y)
                if dist < min_dist:
                    min_dist = dist
                    best_id = ent

        if best_id != -1:
            return best_id

        # 2. Check Storage
        for ent, (store, inv, store_pos) in esper.get_components(Storage, Inventory, Position):
            # Don't return the same storage we just took from
            if ent == drone.source_id:
                continue

            dist = math.hypot(store_pos.x - pos.x, store_pos.y - pos.y)
            if dist < min_dist:
                min_dist = dist
                best_id = ent
                
        return best_id

    def _take_items(self, drone, source_id):
        if not esper.has_component(source_id, Inventory):
            return

        inv = esper.component_for_entity(source_id, Inventory)
        
        # If source is a Factory, only take OUTPUT items
        if esper.has_component(source_id, Factory) and esper.has_component(source_id, MapTag):
            tag = esper.component_for_entity(source_id, MapTag)
            machine_type = tag.cell_type
            valid_inputs = set()
            for recipe_name, data in RECIPES.items():
                if data["machine"] == machine_type:
                    for input_item in data["inputs"]:
                        valid_inputs.add(input_item)
            
            for res, amount in list(inv.resources.items()):
                if res not in valid_inputs:
                    to_take = min(amount, drone.capacity)
                    remove_resources(inv, {res: to_take})
                    drone.inventory[res] = drone.inventory.get(res, 0) + to_take
                    break
        else:
            # Normal behavior for Collector/Storage
            for res, amount in list(inv.resources.items()):
                to_take = min(amount, drone.capacity)
                remove_resources(inv, {res: to_take})
                drone.inventory[res] = drone.inventory.get(res, 0) + to_take
                break 

    def _deposit_items(self, drone, target_id):
        if not esper.has_component(target_id, Inventory):
            return

        inv = esper.component_for_entity(target_id, Inventory)
        for res, amount in list(drone.inventory.items()):
            add_item(inv, res, amount)
        drone.inventory.clear()
