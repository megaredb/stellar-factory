import arcade
import esper
import math

from src.components import Position, Velocity, Renderable
from src.components.combat import Turret, Projectile
from src.components.logistics import ResourceChunk
from src.components.gameplay import ResourceSource
from src.processors.mining import MiningProcessor
from src.systems.audio import AudioSystem
import random


class CombatProcessor(esper.Processor):
    def __init__(self, mining: MiningProcessor, sprite_list: arcade.SpriteList):
        super().__init__()
        self.mining = mining
        self.sprite_list = sprite_list

    def process(self, dt: float):
        self._process_turrets(dt)
        self._process_projectiles(dt)

    def _process_turrets(self, dt: float):
        for ent, (turret, pos, renderable) in esper.get_components(
            Turret, Position, Renderable
        ):
            turret.last_shot_time += dt

            if turret.last_shot_time < turret.cooldown:
                continue

            # Find closest target
            target_id = -1
            min_dist = turret.range

            for target_ent, (res, target_pos) in esper.get_components(
                ResourceSource, Position
            ):
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

        speed = 600.0
        vel_x = math.cos(angle) * speed
        vel_y = math.sin(angle) * speed

        esper.create_entity(
            Position(pos.x, pos.y),
            Velocity(vel_x, vel_y),
            Renderable(sprite=sprite),
            Projectile(target_id=target_id, speed=speed, damage=turret.damage),
        )

        AudioSystem().play_sound("laser")

    def _process_projectiles(self, dt: float):
        for ent, (proj, pos, vel, renderable) in esper.get_components(
            Projectile, Position, Velocity, Renderable
        ):
            proj.lifetime -= dt
            if proj.lifetime <= 0:
                self._destroy_projectile(ent, renderable)
                continue

            if esper.entity_exists(proj.target_id):
                target_pos = esper.component_for_entity(proj.target_id, Position)
                dist = math.hypot(target_pos.x - pos.x, target_pos.y - pos.y)

                if dist < 20:
                    self._handle_hit(ent, proj, renderable)
            else:
                # Target dead, destroy projectile
                self._destroy_projectile(ent, renderable)

    def _handle_hit(self, proj_ent, proj, renderable):
        if esper.entity_exists(proj.target_id):
            try:
                res = esper.component_for_entity(proj.target_id, ResourceSource)
                res.amount -= proj.damage

                to_receive = (
                    proj.damage if res.amount <= 0 else res.amount + proj.damage
                )

                target_pos = esper.component_for_entity(proj.target_id, Position)
                self.mining.spawn_chunk(
                    target_pos.x, target_pos.y, res.resource_type, to_receive
                )

                if res.amount <= 0 and esper.entity_exists(proj.target_id):
                    try:
                        target_rend = esper.component_for_entity(
                            proj.target_id, Renderable
                        )
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
