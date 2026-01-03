import arcade
import esper
import random
import math
from src.components import Renderable, Position, Velocity
from src.components.gameplay import ResourceSource, Inventory, PlayerControl
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


class MiningProcessor(esper.Processor):
    def __init__(self, camera: arcade.Camera2D, mouse: MouseProcessor):
        super().__init__()
        self.camera = camera
        self.mouse = mouse

        self.mining_timer = 0.0

        # Для визуализации лазера
        self.is_mining_active = False
        self.laser_start = (0.0, 0.0)
        self.laser_end = (0.0, 0.0)

        # Список частиц
        self.particles: list[Particle] = []

    def process(self, dt: float):
        self.is_mining_active = False
        self._update_particles(dt)

        if not self.mouse.is_pressed(arcade.MOUSE_BUTTON_LEFT):
            self.mining_timer = 0  # Сбрасываем таймер, если отпустили кнопку
            return

        # 1. Получаем координаты мыши в мире
        world_x, world_y, world_z = self.camera.unproject((self.mouse.x, self.mouse.y))

        # 2. Ищем астероид под курсором
        target_entity = None
        target_pos = None

        # Оптимизация: Сначала проверяем, попадаем ли мы вообще в какой-то астероид
        # Можно было бы использовать пространственный хеш, но для <1000 объектов перебор ок
        for ent, (res_source, renderable, pos) in esper.get_components(
            ResourceSource, Renderable, Position
        ):
            if renderable.sprite.collides_with_point((world_x, world_y)):
                target_entity = ent
                target_pos = (pos.x, pos.y)
                break

        if target_entity is None or target_pos is None:
            return

        # АСТЕРОИД НАЙДЕН - БЛОКИРУЕМ СТРОИТЕЛЬСТВО
        self.mouse.mark_handled()

        # 3. Ищем игрока (источник лазера и получатель ресурсов)
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

        # 4. Визуализация лазера (рисуем всегда, когда зажато на астероиде)
        self.is_mining_active = True
        self.laser_start = player_pos
        self.laser_end = (
            world_x,
            world_y,
        )  # Лазер бьет в точку клика, а не в центр астероида

        # 5. Логика периодической добычи
        self.mining_timer += dt
        if self.mining_timer >= MINING_RATE:
            self.mining_timer = 0
            self._mine_step(target_entity, player_inventory, target_pos)

    def _mine_step(
        self, entity_id: int, inventory: Inventory, pos: tuple[float, float]
    ):
        """Один тик добычи"""
        res_source = esper.component_for_entity(entity_id, ResourceSource)

        amount_to_take = min(MINING_AMOUNT, res_source.amount)
        res_source.amount -= amount_to_take
        inventory.add(res_source.resource_type, amount_to_take)

        # Эффекты
        self._spawn_particles(
            self.laser_end[0], self.laser_end[1], res_source.resource_type
        )

        try:
            renderable = esper.component_for_entity(entity_id, Renderable)
            # Легкая тряска
            renderable.sprite.angle += random.randint(-5, 5)
            # Можно чуть уменьшать спрайт по мере добычи
            # renderable.sprite.scale = 0.5 + 0.5 * (res_source.amount / res_source.max_amount)
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

        for _ in range(3):  # 3 искры за тик
            angle = random.uniform(0, 6.28)
            speed = random.uniform(30, 100)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed
            life = random.uniform(0.3, 0.6)
            self.particles.append(Particle(x, y, dx, dy, color, life))

    def _update_particles(self, dt):
        for p in self.particles:
            p.life -= dt
            p.x += p.dx * dt
            p.y += p.dy * dt
            # Замедление частиц
            p.dx *= 0.9
            p.dy *= 0.9

        # Удаляем мертвые частицы
        self.particles = [p for p in self.particles if p.life > 0]

    def on_draw(self):
        # Рисуем лазер
        if self.is_mining_active:
            arcade.draw_line(
                self.laser_start[0],
                self.laser_start[1],
                self.laser_end[0],
                self.laser_end[1],
                LASER_COLOR,
                3,
            )
            # Вторая линия для эффекта свечения
            arcade.draw_line(
                self.laser_start[0],
                self.laser_start[1],
                self.laser_end[0],
                self.laser_end[1],
                (255, 255, 255, 100),
                1,
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
