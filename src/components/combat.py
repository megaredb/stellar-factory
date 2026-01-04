from dataclasses import field
from src.components import component

@component
class Turret:
    range: float = 300.0
    cooldown: float = 1.0
    damage: int = 10
    last_shot_time: float = 0.0

@component
class Projectile:
    target_id: int = -1
    speed: float = 400.0
    damage: int = 10
    lifetime: float = 5.0
