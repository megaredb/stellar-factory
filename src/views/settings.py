import arcade
import arcade.gui
from src.systems.audio import AudioSystem

SETTINGS = {
    "master_volume": 50,
    "music_volume": 50,
}


class SettingsView(arcade.View):
    def __init__(self, previous_view: arcade.View):
        super().__init__()
        self.previous_view = previous_view
        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        self.v_box = arcade.gui.UIBoxLayout()

        # Master Volume
        self.v_box.add(
            arcade.gui.UILabel(
                text="Master Volume", font_size=14, text_color=arcade.color.WHITE
            )
        )
        self.master_slider = arcade.gui.UISlider(
            value=SETTINGS["master_volume"], width=300, height=50
        )
        self.master_slider.on_change = self.on_master_volume_change  # type: ignore
        self.v_box.add(self.master_slider)

        # Music Volume
        self.v_box.add(
            arcade.gui.UILabel(
                text="Music Volume", font_size=14, text_color=arcade.color.WHITE
            ).with_padding(top=20)
        )
        self.music_slider = arcade.gui.UISlider(
            value=SETTINGS["music_volume"], width=300, height=50
        )
        self.music_slider.on_change = self.on_music_volume_change  # type: ignore
        self.v_box.add(self.music_slider)

        # Back Button
        back_button = arcade.gui.UIFlatButton(text="Back", width=200)
        self.v_box.add(back_button.with_padding(top=40))
        back_button.on_click = self.on_click_back  # type: ignore

        self.manager.add(
            arcade.gui.UIAnchorLayout(
                anchor_x="center_x", anchor_y="center_y", children=[self.v_box]
            )
        )

    def on_master_volume_change(self, event):
        global SETTINGS
        SETTINGS["master_volume"] = self.master_slider.value
        AudioSystem().set_volume(SETTINGS["master_volume"], SETTINGS["music_volume"])

    def on_music_volume_change(self, event):
        global SETTINGS
        SETTINGS["music_volume"] = self.music_slider.value
        AudioSystem().set_volume(SETTINGS["master_volume"], SETTINGS["music_volume"])

    def on_click_back(self, event):
        self.window.show_view(self.previous_view)

    def on_draw(self):
        self.clear()
        self.manager.draw()

    def on_hide_view(self):
        self.manager.disable()

    def on_show_view(self):
        self.manager.enable()
