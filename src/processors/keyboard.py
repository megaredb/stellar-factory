import esper


class KeyboardProcessor(esper.Processor):
    def __init__(self):
        super().__init__()
        self.keys_pressed = set()
        self.modifiers = 0

    def process(self, dt: float):
        pass

    def on_key_press(self, symbol: int, modifiers: int):
        self.keys_pressed.add(symbol)
        self.modifiers = modifiers

    def on_key_release(self, symbol: int, modifiers: int):
        if symbol in self.keys_pressed:
            self.keys_pressed.remove(symbol)
        self.modifiers = modifiers

    def is_pressed(self, symbol: int) -> bool:
        return symbol in self.keys_pressed
