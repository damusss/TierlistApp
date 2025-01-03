import pygame
import mili
from src import common
from src import main_menu
from src import settings_menu
from src import tierlist_view
from src import tierlist_settings_menu
from src import data
from src import alert
from src import screenshot

# todo: delete covers when delete category


class TierlistApp(mili.GenericApp):
    def __init__(self):
        assert pygame.vernum >= (2, 5, 2)
        assert mili.VERSION >= (1, 0, 3)
        print(f"MILI {mili.VERSION_STR}")
        pygame.init()
        super().__init__(
            pygame.Window("Tierlist", pygame.display.get_desktop_sizes()[0]),
            start_style=mili.CENTER | mili.PADLESS,
            target_framerate=120,
        )
        pygame.key.set_repeat(300, 80)
        mili.icon.setup("appdata", "white", google_size=255)
        self.mili.default_styles(
            image={"smoothscale": True},
            text={
                "growx": True,
                "growy": True,
                "sysfont": True,
                "name": "Segoe UI",
            },
            line={"color": "white"},
            rect={"border_radius": 0},
        )
        self.data = data.Data(self)
        self.main_menu = main_menu.MainMenu(self)
        self.settings_menu = settings_menu.SettingsMenu(self)
        self.tierlist_view = tierlist_view.TierlistView(self)
        self.tierlist_settings_menu = tierlist_settings_menu.TierlistSettingsMenu(self)
        self.tierlist: data.TierlistData = None
        self.alert_system = alert.AlertSystem(self)
        self.screenshot = screenshot.ScreenshotWindowManager(self)
        self.last_save = pygame.time.get_ticks()
        self.menu: common.UIComponent = self.main_menu
        surf = pygame.Surface((20, 20))
        surf.fill("#9539bf")
        self.window.set_icon(surf)
        pygame.image.save(surf, "appdata/icon.png")

    def on_quit(self):
        self.data.save()

    def update(self):
        self.tierlist_view.layer_cache.active = False
        if pygame.time.get_ticks() - self.last_save >= 1000 * 3 * 60:
            self.data.save()
            self.last_save = pygame.time.get_ticks()
        if (
            self.data.to_load_categories is not None
            and self.data.to_load_categories <= 0
        ):
            self.data.to_load_categories = None
            self.data.apply_custom_chars()
        self.window.title = (
            f"Tierlist {self.tierlist.name.title()} {self.clock.get_fps():.0f}"
            if self.menu in [self.tierlist_view, self.tierlist_settings_menu]
            else f"Tierlist App {self.clock.get_fps():.0f}"
        )
        if self.screenshot.screenshot_taking:
            self.window.focus()
            self.screenshot.screenshot_run()
            self.window.focus()
            return
        self.menu.update()
        if self.data.auto_download:
            if not any([cat.downloading for cat in self.data.categories.values()]):
                found = False
                for category in self.data.categories.values():
                    if category.name.strip() == "":
                        continue
                    _, downloaded_all = category.get_downloaded_of(
                        None, include_covers=True
                    )
                    if not downloaded_all and not category.downloading:
                        category.download()
                        found = True
                        break
                if not found:
                    self.data.auto_download = False
        for category in self.data.categories.values():
            if category.to_reload:
                self.data.load_category_images(category)
                category.to_reload = False
                self.data.load_category_images(self.data.categories[common.ANIMES_UID])

    def ui(self):
        self.mili.rect({"color": common.BG_COL})
        if self.alert_system.update():
            self.menu.uicommon_top_btn(
                "close",
                "right",
                self.quit if self.menu.can_exit() else None,
                othercallback=self.exit_alert,
            )
            self.menu.ui()

    def exit_alert(self):
        alert.alert(
            "Cannot Exit Yet",
            "Something is stopping the app from quitting. This can be caused from not syncing tierlist/category names or if something is downloading. It is suggested to complete or stop those actions before exiting.",
            False,
        )

    def event(self, e):
        self.menu.event(e)
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_s and (
                e.mod & pygame.KMOD_CTRL or e.mod & pygame.KMOD_META
            ):
                self.data.save()

    def mult(self, a):
        return a


if __name__ == "__main__":
    TierlistApp().run()
