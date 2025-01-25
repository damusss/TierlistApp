import pygame
import mili
import datetime
from src import common
from src import alert
from src.tierlist_view import TierlistView


class ScreenshotWindowManager:
    def __init__(self, app: "common.TierlistApp"):
        self.app = app
        self.appdata = self.app.data
        self.screenshot_taking = False
        self.screenshot_window = None
        self.screenshot_framec = 0
        self.screenshot_ready = False
        self.mili = mili.MILI(None)
        self.tiers_scroll = mili.Scroll()
        self.dragging_obj = None
        self.show_numbers = False
        self.drag_origin = -1
        self.highlighted_category = None
        self.selected_obj = None
        self.prev_selected_obj = None
        self.only_marked = False
        self.global_i = 0
        self.image_h = 1
        self.lowest_card_bottom = 0
        self.mili.default_styles(
            image={"smoothscale": True},
            text={
                "growx": True,
                "growy": True,
                "slow_grow": True,
                "sysfont": True,
                "name": "Segoe UI",
            },
            line={"color": "white"},
            rect={"border_radius": 0},
        )

    @property
    def tierlist(self):
        return self.app.tierlist

    @property
    def image_w(self):
        return self.image_h * self.appdata.image_ratio

    @property
    def layer_cache(self):
        return None

    def get_tiers_percentage(self):
        return "100"

    def mult(self, a):
        return self.app.mult(a)

    def category_from_name(self, name):
        return self.app.tierlist_view.category_from_name(name)

    def screenshot_start(self):
        self.screenshot_taking = True
        self.screenshot_framec = 0
        self.screenshot_window = pygame.Window(
            "Screenshot Temporary Window",
            pygame.Vector2(self.app.window.size) * self.appdata.screenshot_window_mult,
        )
        self.mili.canva = self.screenshot_window.get_surface()
        self.mili.canva_offset = self.mili.canva.size
        self.image_h = (
            self.app.tierlist_view.image_h * self.appdata.screenshot_window_mult
        )
        self.screenshot_ready = False

    def screenshot_ui(self):
        self.kmods = pygame.key.get_mods()
        self.lowest_card_bottom = 0
        self.mili.rect({"color": common.BG_COL})
        with self.mili.begin(None, mili.FILL | mili.PADLESS):
            TierlistView.ui_tiers_col(self)
        if self.lowest_card_bottom > self.screenshot_window.size[1]:
            self.image_h -= 1
            self.screenshot_ready = False
        else:
            self.screenshot_ready = True

    def ui_tier_name(self, i):
        TierlistView.ui_tier_name(self, i, self.appdata.screenshot_window_mult)

    def ui_tier(self, i, parent_it):
        TierlistView.ui_tier(self, i, parent_it)

    def ui_tier_card(self, prefixed, tier_i, i, preview=False):
        TierlistView.ui_tier_card(self, prefixed, tier_i, i, False)

    def screenshot_take(self):
        now = datetime.datetime.now()
        date_str = (
            str(now).split(".")[0].replace("-", "_").replace(" ", "_").replace(":", "_")
        )
        surf = self.screenshot_window.get_surface()
        pygame.image.save(
            surf.subsurface((0, 0, surf.width, self.lowest_card_bottom)),
            f"screenshots/{self.tierlist.name}_{date_str}.png",
        )
        alert.message(
            f"Saved screenshot of tierlist {self.tierlist.name} to 'screenshots/{self.tierlist.name}_{date_str}.png'"
        )

    def screenshot_stop(self):
        self.screenshot_take()
        self.screenshot_window.destroy()
        self.screenshot_window = None
        self.screenshot_taking = False

    def screenshot_run(self):
        if self.screenshot_window is None:
            return
        self.mili.canva = self.screenshot_window.get_surface()
        self.screenshot_window.get_surface().fill(0)
        self.mili.start(mili.PADLESS, is_global=False)
        self.screenshot_ui()
        self.mili.update_draw()
        self.screenshot_framec += 1
        self.screenshot_window.flip()
        if self.screenshot_framec >= 3 and self.screenshot_ready:
            self.screenshot_stop()
