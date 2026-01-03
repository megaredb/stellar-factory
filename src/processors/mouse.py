import esper


class MouseProcessor(esper.Processor):
    def __init__(self) -> None:
        super().__init__()
        self.x: float = 0.0
        self.y: float = 0.0
        self.scroll_x: float = 0.0
        self.scroll_y: float = 0.0

        self.buttons_pressed: set[int] = set()
        self.handled: bool = False

    def process(self, dt: float):
        self.scroll_x = 0
        self.scroll_y = 0
        self.handled = False

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        self.x = x
        self.y = y

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        self.x = x
        self.y = y
        self.buttons_pressed.add(button)

    def on_mouse_release(self, x: float, y: float, button: int, modifiers: int):
        self.x = x
        self.y = y
        if button in self.buttons_pressed:
            self.buttons_pressed.remove(button)

    def on_mouse_drag(
        self, x: float, y: float, dx: float, dy: float, buttons: int, modifiers: int
    ):
        self.x = x
        self.y = y

    def on_mouse_scroll(self, x: int, y: int, scroll_x: float, scroll_y: float):
        self.scroll_x = scroll_x
        self.scroll_y = scroll_y

    def is_pressed(self, button: int) -> bool:
        return button in self.buttons_pressed

    def mark_handled(self):
        self.handled = True
