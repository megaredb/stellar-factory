import arcade
import esper
import math

from src.components import Position, Velocity, Renderable
from src.components.combat import Turret, Projectile
from src.components.gameplay import ResourceSource
from src.processors.mining import MiningProcessor
from src.systems.audio import AudioSystem
from src.spatial.quadtree import QuadTree, Point, Rectangle
from src.game_data import MAP_LIMIT_X, MAP_LIMIT_Y


class CombatProcessor(esper.Processor):
    def __init__(self, mining: MiningProcessor, sprite_list: arcade.SpriteList):
        super().__init__()
        self.mining = mining
        self.sprite_list = sprite_list

        boundary = Rectangle(0, 0, MAP_LIMIT_X * 1.5, MAP_LIMIT_Y * 1.5)
        self.asteroid_tree = QuadTree(boundary, capacity=8)

    def process(self, dt: float):
        self._rebuild_asteroid_tree()

        self._process_turrets(dt)
        self._process_projectiles(dt)

    def _rebuild_asteroid_tree(self):
        self.asteroid_tree.clear()

        for ent, (res, pos) in esper.get_components(ResourceSource, Position):
            point = Point(pos.x, pos.y, ent)
            self.asteroid_tree.insert(point)

    def _process_turrets(self, dt: float):
        for ent, (turret, pos, renderable) in esper.get_components(
            Turret, Position, Renderable
        ):
            turret.last_shot_time += dt

            if turret.last_shot_time < turret.cooldown:
                continue

            candidates = self.asteroid_tree.query_radius(pos.x, pos.y, turret.range)

            target_id = -1
            min_dist = turret.range

            for candidate_id in candidates:
                if not esper.entity_exists(candidate_id):
                    continue

                target_pos = esper.component_for_entity(candidate_id, Position)
                dist = math.hypot(target_pos.x - pos.x, target_pos.y - pos.y)
                if dist < min_dist:
                    min_dist = dist
                    target_id = candidate_id

            if target_id != -1:
                self._fire_turret(ent, turret, pos, renderable, target_id)

    @staticmethod
    def _calculate_intercept(
        tx: float,  # turret
        ty: float,
        px: float,  # target position
        py: float,
        vx: float,  # target velocity
        vy: float,
        projectile_speed: float,
    ) -> tuple[float, float] | None:
        dx = px - tx
        dy = py - ty

        a = vx**2 + vy**2 - projectile_speed**2
        b = 2 * (dx * vx + dy * vy)
        c = dx**2 + dy**2

        discriminant = b**2 - 4 * a * c

        if discriminant < 0:
            return None

        if abs(a) < 0.001:
            if abs(b) < 0.001:
                return px, py
            t = -c / b
            if t < 0:
                return None
        else:
            sqrt_discriminant = math.sqrt(discriminant)
            t1 = (-b - sqrt_discriminant) / (2 * a)
            t2 = (-b + sqrt_discriminant) / (2 * a)

            valid_times = [t for t in [t1, t2] if t > 0]
            if not valid_times:
                return None
            t = min(valid_times)

        aim_x = px + vx * t
        aim_y = py + vy * t

        return aim_x, aim_y

    def _fire_turret(self, turret_ent, turret, pos, renderable, target_id):
        turret.last_shot_time = 0.0
        speed = 100.0

        target_pos = esper.component_for_entity(target_id, Position)

        aim_x, aim_y = target_pos.x, target_pos.y

        if esper.has_component(target_id, Velocity):
            target_vel = esper.component_for_entity(target_id, Velocity)

            intercept = self._calculate_intercept(
                pos.x,
                pos.y,
                target_pos.x,
                target_pos.y,
                target_vel.dx,
                target_vel.dy,
                speed,
            )

            if intercept:
                aim_x, aim_y = intercept

        dx = aim_x - pos.x
        dy = aim_y - pos.y
        angle = math.atan2(dy, dx)

        renderable.sprite.angle = -math.degrees(angle)

        sprite = arcade.SpriteCircle(5, arcade.color.YELLOW)
        sprite.center_x = pos.x
        sprite.center_y = pos.y
        self.sprite_list.append(sprite)

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
