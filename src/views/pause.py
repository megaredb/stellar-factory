import arcade
import arcade.gui
from src.save_manager import save_game, load_game
from src.views.settings import SettingsView


class PauseView(arcade.View):
    def __init__(self, game_view):
        super().__init__()
        self.game_view = game_view
        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        self.v_box = arcade.gui.UIBoxLayout()

        # Resume
        resume_button = arcade.gui.UIFlatButton(text="Resume", width=200)
        self.v_box.add(resume_button.with_padding(bottom=20))
        resume_button.on_click = self.on_click_resume

        # Save
        save_button = arcade.gui.UIFlatButton(text="Save Game", width=200)
        self.v_box.add(save_button.with_padding(bottom=20))
        save_button.on_click = self.on_click_save

        # Load
        load_button = arcade.gui.UIFlatButton(text="Load Game", width=200)
        self.v_box.add(load_button.with_padding(bottom=20))
        load_button.on_click = self.on_click_load

        # Settings
        settings_button = arcade.gui.UIFlatButton(text="Settings", width=200)
        self.v_box.add(settings_button.with_padding(bottom=20))
        settings_button.on_click = self.on_click_settings

        # Exit
        exit_button = arcade.gui.UIFlatButton(text="Exit to Main Menu", width=200)
        self.v_box.add(exit_button)
        exit_button.on_click = self.on_click_exit

        self.manager.add(
            arcade.gui.UIAnchorLayout(
                anchor_x="center_x", anchor_y="center_y", children=[self.v_box]
            )
        )

    def on_click_resume(self, event):
        self.window.show_view(self.game_view)

    def on_click_save(self, event):
        save_game(self.game_view.builder_processor)

    def on_click_load(self, event):
        load_game(self.game_view.builder_processor, self.game_view.render_processor)
        self.window.show_view(self.game_view)

    def on_click_settings(self, event):
        settings_view = SettingsView(self)
        self.window.show_view(settings_view)

    def on_click_exit(self, event):
        from src.views.menu import MenuView

        menu_view = MenuView()
        self.window.show_view(menu_view)

    def on_draw(self):
        self.clear()
        self.game_view.on_draw()

        self.window.default_camera.use()

        arcade.draw_text(
            "PAUSED",
            self.window.width / 2,
            self.window.height - 100,
            arcade.color.WHITE,
            font_size=50,
            anchor_x="center",
        )
        self.manager.draw()

    def on_hide_view(self):
        self.manager.disable()

    def on_show_view(self):
        self.manager.enable()
