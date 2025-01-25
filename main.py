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


class TierlistApp(mili.GenericApp):
    def __init__(self):
        assert pygame.vernum >= (2, 5, 2)
        assert mili.VERSION >= (1, 0, 3)
        print(f"MILI {mili.VERSION_STR}")
        pygame.init()
        super().__init__(
            pygame.Window(
                "Tierlist", pygame.display.get_desktop_sizes()[0], borderless=True
            ),
            start_style=mili.CENTER | mili.PADLESS,
            target_framerate=120,
        )
        pygame.key.set_repeat(300, 80)
        mili.icon.setup("appdata", "white", google_size=255)
        mili.InteractionCursor.setup(update_id="cursor")
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
        self.frozen = False
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
        self.settings_back = None
        surf = pygame.Surface((20, 20))
        surf.fill("#9539bf")
        self.window.set_icon(surf)
        pygame.image.save(surf, "appdata/icon.png")
        self.window.minimum_size = (500, 500)
        self.custom_borders = mili.CustomWindowBorders(
            self.window, 2, 3, 30, uniform_resize_key=None
        )

    def on_quit(self):
        self.data.save()

    def update(self):
        if len(self.data.startup_to_load_categories) > 0:
            cat = self.data.startup_to_load_categories.pop()
            self.data.load_category_images(cat)
        if self.data.free_category_uid in self.data.categories:
            self.data.free_category_uid += 1
        self.tierlist_view.layer_cache.active = False
        if pygame.time.get_ticks() - self.last_save >= 1000 * 3 * 60:
            self.data.save()
            self.last_save = pygame.time.get_ticks()
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
        # if not self.custom_borders.update():
        #    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        if self.frozen:
            self.target_framerate = 10
            return
        self.target_framerate = 120
        self.menu.update()
        self.update_auto_download()
        self.update_reload()

    def update_auto_download(self):
        if self.data.auto_download:
            if self.data.downloading_amount == 0:
                found = False
                for category in self.data.categories.values():
                    if category.name.strip() == "" or category.abort:
                        continue
                    _, downloaded_all = category.get_downloaded_of(
                        None, include_covers=True
                    )
                    if not downloaded_all and not category.downloading:
                        category.download()
                        found = True
                        alert.message(
                            f"Started downloading {category.name.replace('_', ' ').title()}"
                        )
                        break
                if not found:
                    self.data.auto_download = False

    def update_reload(self):
        for category in self.data.categories.values():
            if category.to_reload:
                self.data.load_category_images(category)
                category.to_reload = False
                self.data.load_category_images(self.data.categories[common.ANIMES_UID])
        if (
            self.data.to_load_categories is not None
            and self.data.to_load_categories <= 0
        ):
            self.data.to_load_categories = None
            self.data.apply_custom_chars()

    def ui(self):
        if self.frozen:
            self.mili.text("FROZEN (F4)", {"size": self.mult(100), "cache": "auto"})
            self.menu.uicommon_top_btn(
                "close",
                "right",
                self.quit
                if self.menu.can_exit() and self.settings_menu.can_exit()
                else None,
                othercallback=self.exit_alert,
            )
            return
        self.mili.rect({"color": common.BG_COL})
        self.mili.rect(
            {"color": (common.BG_COL[0] + 40,) * 3, "outline": 1, "draw_above": True}
        )
        if self.alert_system.update():
            self.menu.uicommon_top_btn(
                "close",
                "right",
                self.quit
                if self.menu.can_exit() and self.settings_menu.can_exit()
                else None,
                othercallback=self.exit_alert,
            )
            self.menu.ui()
            self.alert_system.ui_message()
        else:
            self.tierlist_view.layer_cache.active = False
        mili.InteractionCursor.apply()

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
            if e.key == pygame.K_F4:
                self.frozen = not self.frozen

    def mult(self, a):
        return a


if __name__ == "__main__":
    TierlistApp().run()
