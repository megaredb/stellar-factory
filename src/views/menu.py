import arcade
import arcade.gui
import esper

from src.views.game import GameView
from src.views.settings import SettingsView


class MenuView(arcade.View):
    def __init__(self):
        super().__init__()
        esper.clear_database()

        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        self.v_box = arcade.gui.UIBoxLayout()

        start_button = arcade.gui.UIFlatButton(text="Start Game", width=200)
        self.v_box.add(start_button.with_padding(bottom=20))

        settings_button = arcade.gui.UIFlatButton(text="Settings", width=200)
        self.v_box.add(settings_button.with_padding(bottom=20))

        exit_button = arcade.gui.UIFlatButton(text="Exit", width=200)
        self.v_box.add(exit_button)

        start_button.on_click = self.on_click_start
        settings_button.on_click = self.on_click_settings
        exit_button.on_click = self.on_click_exit

        self.manager.add(
            arcade.gui.UIAnchorLayout(
                anchor_x="center_x", anchor_y="center_y", children=[self.v_box]
            )
        )

    def on_click_start(self, event):
        game_view = GameView()
        game_view.setup()
        self.window.show_view(game_view)

    def on_click_settings(self, event):
        settings_view = SettingsView(self)
        self.window.show_view(settings_view)

    @staticmethod
    def on_click_exit(event):
        arcade.exit()

    def on_draw(self):
        self.clear()
        self.manager.draw()

    def on_hide_view(self):
        self.manager.disable()

    def on_show_view(self):
        self.manager.enable()
