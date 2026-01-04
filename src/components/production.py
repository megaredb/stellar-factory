from dataclasses import field
from src.components import component
from src.components.base import BaseComponent


@component
class Factory(BaseComponent):
    recipe_id: str = ""
    progress: float = 0.0
    is_working: bool = False
    processing_time: float = 1.0
    input_buffer: dict[str, int] = field(default_factory=dict)
    output_buffer: dict[str, int] = field(default_factory=dict)
