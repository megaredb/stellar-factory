import arcade
import esper
import random
import math
from src.components import Renderable, Position
from src.components.gameplay import Inventory, ResourceSource, PlayerControl
from src.components.logistics import ResourceChunk
from src.components.physics import Velocity
from src.systems.inventory import add_item
from src.systems.audio import AudioSystem
from src.processors.mouse import MouseProcessor

MINING_AMOUNT = 1
MINING_RATE = 0.2
LASER_COLOR = (100, 255, 255, 200)


class Particle:
    def __init__(self, x, y, dx, dy, color, life):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.color = color
        self.life = life
        self.max_life = life
        self.time = 0


class MiningProcessor(esper.Processor):
    def __init__(
        self,
        camera: arcade.Camera2D,
        mouse: MouseProcessor,
        chunk_list: arcade.SpriteList,
    ):
        super().__init__()
        self.time = 0.0
        self.camera = camera
        self.mouse = mouse
        self.chunk_list = chunk_list

        self.mining_timer = 0.0

        self.is_mining_active = False
        self.laser_start = (0.0, 0.0)
        self.laser_end = (0.0, 0.0)

        self.particles: list[Particle] = []

    def process(self, dt: float):
        self.time += dt % math.pi
        self.is_mining_active = False
        self._update_particles(dt)

        if not self.mouse.is_pressed(arcade.MOUSE_BUTTON_RIGHT):
            self.mining_timer = 0
            return

        world_x, world_y, world_z = self.camera.unproject((self.mouse.x, self.mouse.y))

        target_entity = None
        target_pos = None

        for ent, (res_source, renderable, pos) in esper.get_components(
            ResourceSource, Renderable, Position
        ):
            if res_source.amount > 0 and renderable.sprite.collides_with_point((world_x, world_y)):
                target_entity = ent
                target_pos = (pos.x, pos.y)
                break

        if target_entity is None or target_pos is None:
            return

        self.mouse.mark_handled()

        player_inventory = None
        player_pos = None
        for ent, (inv, ctrl, pos) in esper.get_components(
            Inventory, PlayerControl, Position
        ):
            player_inventory = inv
            player_pos = (pos.x, pos.y)
            break

        if player_inventory is None or player_pos is None:
            return

        self.is_mining_active = True
        self.laser_start = player_pos
        self.laser_end = (
            world_x,
            world_y,
        )

        self.mining_timer += dt
        if self.mining_timer >= MINING_RATE:
            self.mining_timer = 0
            self._mine_step(target_entity, player_inventory, target_pos)

    def _mine_step(
        self, entity_id: int, inventory: Inventory, pos: tuple[float, float]
    ):
        res_source = esper.component_for_entity(entity_id, ResourceSource)

        amount_to_take = min(MINING_AMOUNT, res_source.amount)
        res_source.amount -= amount_to_take

        # Spawn chunk
        self._spawn_chunk(pos[0], pos[1], res_source.resource_type, amount_to_take)

        AudioSystem().play_sound("laser")

        self._spawn_particles(
            self.laser_end[0], self.laser_end[1], res_source.resource_type
        )

        renderable: Renderable | None = None

        try:
            renderable = esper.component_for_entity(entity_id, Renderable)
            renderable.sprite.angle += random.randint(-10, 10)
            renderable.sprite.scale = 0.7 + 0.3 * (
                res_source.amount / res_source.max_amount
            )
        except KeyError:
            pass

        if res_source.amount <= 0:
            if renderable:
                renderable.sprite.remove_from_sprite_lists()
            esper.delete_entity(entity_id)

    def _spawn_particles(self, x, y, res_type):
        color = arcade.color.WHITE
        if res_type == "gold":
            color = arcade.color.GOLD
        elif res_type == "iron":
            color = arcade.color.GRAY
        elif res_type == "silicon":
            color = arcade.color.BLUE_GRAY

        for _ in range(3):
            angle = random.uniform(0, 6.28)
            speed = random.uniform(30, 100)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed
            life = random.uniform(0.3, 0.6)
            self.particles.append(Particle(x, y, dx, dy, color, life))

    def _spawn_chunk(self, x, y, res_type, amount):
        sprite = arcade.SpriteCircle(3, arcade.color.YELLOW)  # Placeholder color
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
        speed = random.uniform(20, 50)
        dx = math.cos(angle) * speed
        dy = math.sin(angle) * speed

        esper.create_entity(
            Position(x, y),
            Velocity(dx, dy),
            Renderable(sprite=sprite),
            ResourceChunk(resource_type=res_type, amount=amount),
        )

    def _update_particles(self, dt):
        for p in self.particles:
            p.life -= dt
            p.x += p.dx * dt
            p.y += p.dy * dt

            p.dx *= 0.9
            p.dy *= 0.9

        self.particles = [p for p in self.particles if p.life > 0]

    def on_draw(self):
        if self.is_mining_active:
            time_sin = math.sin(self.time * 4)

            arcade.draw_line(
                self.laser_start[0],
                self.laser_start[1],
                self.laser_end[0],
                self.laser_end[1],
                LASER_COLOR,
                3 + time_sin,
            )

            arcade.draw_line(
                self.laser_start[0],
                self.laser_start[1],
                self.laser_end[0],
                self.laser_end[1],
                (255, 255, 255, 180),
                1 + time_sin,
            )

        for p in self.particles:
            alpha = int(255 * (p.life / p.max_life))
            # Arcade colors are (r, g, b) or (r, g, b, a).
            # If color is 3-tuple, add alpha. If 4, replace alpha.
            c = p.color
            if len(c) == 3:
                draw_color = c + (alpha,)
            else:
                draw_color = (c[0], c[1], c[2], alpha)

            arcade.draw_point(p.x, p.y, draw_color, 4)
