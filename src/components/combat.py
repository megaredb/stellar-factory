from src.components import component
from src.components.base import BaseComponent


@component
class Turret(BaseComponent):
    range: float = 300.0
    cooldown: float = 1.0
    damage: int = 10
    last_shot_time: float = 0.0


@component
class Projectile(BaseComponent):
    target_id: int = -1
    speed: float = 400.0
    damage: int = 10
    lifetime: float = 5.0
