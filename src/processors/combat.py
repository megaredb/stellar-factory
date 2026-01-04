import arcade
import esper
import math

from src.components import Position, Velocity, Renderable
from src.components.combat import Turret, Projectile
from src.components.logistics import ResourceChunk
from src.components.gameplay import ResourceSource
from src.systems.audio import AudioSystem
import random

class CombatProcessor(esper.Processor):
    def __init__(self, sprite_list: arcade.SpriteList, chunk_list: arcade.SpriteList):
        super().__init__()
        self.sprite_list = sprite_list
        self.chunk_list = chunk_list

    def process(self, dt: float):
        self._process_turrets(dt)
        self._process_projectiles(dt)

    def _process_turrets(self, dt: float):
        for ent, (turret, pos, renderable) in esper.get_components(Turret, Position, Renderable):
            turret.last_shot_time += dt
            
            if turret.last_shot_time < turret.cooldown:
                continue

            # Find closest target
            target_id = -1
            min_dist = turret.range
            
            for target_ent, (res, target_pos) in esper.get_components(ResourceSource, Position):
                dist = math.hypot(target_pos.x - pos.x, target_pos.y - pos.y)
                if dist < min_dist:
                    min_dist = dist
                    target_id = target_ent

            if target_id != -1:
                self._fire_turret(ent, turret, pos, renderable, target_id)

    def _fire_turret(self, turret_ent, turret, pos, renderable, target_id):
        turret.last_shot_time = 0.0
        
        # Calculate angle
        target_pos = esper.component_for_entity(target_id, Position)
        dx = target_pos.x - pos.x
        dy = target_pos.y - pos.y
        angle = math.atan2(dy, dx)
        
        # Rotate turret
        renderable.sprite.angle = math.degrees(angle)

        # Spawn projectile
        sprite = arcade.SpriteCircle(5, arcade.color.YELLOW)
        sprite.center_x = pos.x
        sprite.center_y = pos.y
        self.sprite_list.append(sprite)
        
        speed = 400.0
        vel_x = math.cos(angle) * speed
        vel_y = math.sin(angle) * speed
        
        esper.create_entity(
            Position(pos.x, pos.y),
            Velocity(vel_x, vel_y),
            Renderable(sprite=sprite),
            Projectile(target_id=target_id, speed=speed, damage=turret.damage)
        )
        
        AudioSystem().play_sound("laser")

    def _process_projectiles(self, dt: float):
        for ent, (proj, pos, vel, renderable) in esper.get_components(Projectile, Position, Velocity, Renderable):
            proj.lifetime -= dt
            if proj.lifetime <= 0:
                self._destroy_projectile(ent, renderable)
                continue

            # Move projectile (handled by MovementProcessor? No, let's do it here or rely on MovementProcessor)
            # If we rely on MovementProcessor, we just update velocity. 
            # But we might want homing missiles later. For now, linear is fine.
            # MovementProcessor updates Position based on Velocity. 
            # So we just need to check collisions.

            # Check collision with target
            if esper.entity_exists(proj.target_id):
                target_pos = esper.component_for_entity(proj.target_id, Position)
                dist = math.hypot(target_pos.x - pos.x, target_pos.y - pos.y)
                
                if dist < 20: # Hit radius
                    self._handle_hit(ent, proj, renderable)
            else:
                # Target dead, destroy projectile
                self._destroy_projectile(ent, renderable)

    def _handle_hit(self, proj_ent, proj, renderable):
        if esper.entity_exists(proj.target_id):
            try:
                res = esper.component_for_entity(proj.target_id, ResourceSource)
                res.amount -= proj.damage
                
                # Visual feedback?
                
                if res.amount <= 0:
                    # Spawn chunks
                    target_pos = esper.component_for_entity(proj.target_id, Position)
                    chunks_count = 10
                    amount_per_chunk = max(1, res.amount // chunks_count)
                    self._spawn_chunks(target_pos.x, target_pos.y, res.resource_type, chunks_count, amount_per_chunk)

                    # Destroy target
                    if esper.entity_exists(proj.target_id):
                        try:
                            target_rend = esper.component_for_entity(proj.target_id, Renderable)
                            target_rend.sprite.remove_from_sprite_lists()
                            esper.delete_entity(proj.target_id)
                        except KeyError:
                            pass
            except KeyError:
                pass
        
        self._destroy_projectile(proj_ent, renderable)

    def _destroy_projectile(self, ent, renderable):
        renderable.sprite.remove_from_sprite_lists()
        esper.delete_entity(ent)

    def _spawn_chunks(self, x, y, res_type, count, amount_per_chunk):
        for _ in range(count):
            sprite = arcade.SpriteCircle(3, arcade.color.YELLOW)
            if res_type == "iron":
                sprite.color = arcade.color.GRAY
            elif res_type == "gold":
                sprite.color = arcade.color.GOLD
            elif res_type == "silicon":
                sprite.color = arcade.color.BLUE_GRAY
                
            sprite.center_x = x
            sprite.center_y = y
            self.chunk_list.append(sprite)
            
            angle = random.uniform(0, 6.28)
            speed = random.uniform(20, 100)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed
            
            esper.create_entity(
                Position(x, y),
                Velocity(dx, dy),
                Renderable(sprite=sprite),
                ResourceChunk(resource_type=res_type, amount=amount_per_chunk)
            )
