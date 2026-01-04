import arcade
import esper
from src.views.menu import MenuView

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Stellar Factory"


def main() -> None:
    esper.clear_database()
    window = arcade.Window(
        SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, vsync=True, resizable=True
    )
    menu_view = MenuView()
    window.show_view(menu_view)
    window.center_window()
    arcade.run()


if __name__ == "__main__":
    main()
