import arcade
from pyglet import media


class AudioSystem:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AudioSystem, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        self._initialized: bool

        if self._initialized:
            return

        self._initialized = True

        self.sounds: dict[str, arcade.Sound] = {}
        self.music: arcade.Sound | None = None
        self.music_player: media.Player | None = None

        self.master_volume = 0.5
        self.music_volume = 0.5

        self.load_sound("laser", "sounds/laser.wav")
        self.load_sound("build", "sounds/build.wav")
        self.load_sound("remove", "sounds/remove.wav")

    def load_sound(self, name: str, path: str):
        try:
            self.sounds[name] = arcade.load_sound(path)
        except Exception as e:
            print(f"Failed to load sound {name}: {e}")

    def play_sound(self, name: str):
        if name in self.sounds:
            arcade.play_sound(self.sounds[name], volume=self.master_volume)

    def play_music(self, path: str):
        if self.music_player:
            self.music_player.pause()

        try:
            self.music = arcade.load_sound(path)
            if self.music:
                self.music_player = self.music.play(volume=self.music_volume, loop=True)
        except Exception as e:
            print(f"Failed to load music {path}: {e}")

    def set_volume(self, master: float, music: float):
        self.master_volume = master / 100.0
        self.music_volume = music / 100.0

        if self.music_player:
            self.music_player.volume = self.music_volume
