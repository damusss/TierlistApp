import mili
import pygame
from src import common
from src import entryline
from src import data


class BestCharsMenu(common.UIComponent):
    name = "MAL"

    def init(self):
        self.scroll_right = mili.Scroll("BC_scroll_right")
        self.scroll_left = mili.Scroll("BC_scroll_left")
        self.sr_rect = pygame.Rect()
        self.sl_rect = pygame.Rect()
        self.selected_category: data.CategoryData = None
        self.image_h = 100
        self.card_hover_time = 0
        self.card_hovered = None
        self.hover_category = None
        self.hover_char = None
        self.hover_i = -1

    def get_title(self):
        return f"Best Characters (FPS:{self.app.clock.get_fps():.0f})"

    def ui(self):
        self.hover_category = None
        self.uicommon_back(self.app.main_menu)
        self.uicommon_top_btn("settings", "left", self.action_settings, 1)
        # self.mili.id_checkpoint(1000)
        with self.mili.begin(
            ((0, 0), self.app.window.size), mili.PADLESS | {"spacing": 0}
        ):
            mult = 1 if common.USE_RENDERER else 2
            self.mili.line_element(
                [("-100", 0), ("100", 0)],
                {"size": 1, "color": (40,) * 3},
                (0, self.mult(15*mult), self.app.window.size[0], 1),
                {"ignore_grid": True, "blocking": False},
            )
            self.mili.element((0, 0, 0, self.mult(15*mult)))
            with self.mili.begin(
                None, mili.FILL | mili.PADLESS | mili.X | {"spacing": 0}
            ):
                with self.mili.begin(
                    None,
                    mili.FILL
                    | mili.PADLESS
                    | mili.SPACELESS
                    | mili.CENTER
                    | {
                        "update_id": "BC_scroll_left",
                        "anchor": "first",
                    },
                ) as lcond:
                    self.ui_main_cont()
                    self.sl_rect = lcond.data.absolute_rect
                with self.mili.begin(
                    None,
                    {
                        "filly": True,
                        "fillx": "30" if self.selected_category else "0",
                        "pad": 0,
                        "spacing": 0,
                    },
                ) as rcont:
                    if self.selected_category:
                        self.ui_category()
                    self.sr_rect = rcont.data.absolute_rect

    def ui_main_cont(self):
        for category in self.appdata.score_sorted_categories:
            category: data.CategoryData
            with self.mili.begin(
                None,
                {
                    "fillx": True,
                    "resizey": True,
                    "spacing": 1,
                    "axis": "x",
                    "pad": 1,
                    "offset": self.scroll_left.get_offset(),
                },
            ):
                mainit = self.ui_card(f"0|{category.name}")
                if mainit.left_clicked:
                    if (
                        self.selected_category is None
                        or self.selected_category != category
                    ):
                        self.selected_category = category
                    else:
                        self.selected_category = None
                self.mili.element((0, 0, self.mult(3), 0))
                for i, charname in enumerate(list(category.best_chars)):
                    res = self.ui_card(category.image_prefixed(charname))
                    if res.left_clicked:
                        category.best_chars.remove(charname)
                    if res.hovered:
                        self.hover_category = category
                        self.hover_char = charname
                        self.hover_i = i

    def ui_card(self, image_name):
        MULT = 1.5
        with self.mili.element(
            (0, 0, self.image_h * self.appdata.image_ratio * MULT, self.image_h * MULT)
        ) as elit:
            image = self.appdata.images.get(image_name, None)
            if image is None:
                image = mili.icon.get_google(common.HOURGLASS)
            alpha = 255
            if elit.hovered:
                alpha = 130
            self.mili.image(image, {"cache": "auto", "alpha": alpha})
            return elit

    def ui_category(self):
        self.mili.rect({"color": (40,) * 3, "outline": 1, "draw_above": True})
        self.mili.element(
            None,
            {
                "fillx": True,
            },
        )
        self.mili.text(
            self.get_obj_name(self.selected_category.name),
            {
                "size": self.mult(19),
                "cache": "auto",
            },
        )
        with self.mili.begin(
            None,
            {
                "filly": True,
                "fillx": True,
                "grid": True,
                "pad": 1,
                "spacing": 1,
                # "flag": mili.PARENT_PRE_ORGANIZE_CHILDREN,
                "update_id": "BC_scroll_right",
            }
            | mili.X,
        ):
            already_added = []
            for name in self.selected_category.downloaded:
                if name in self.selected_category.ignore:
                    continue
                if name in self.selected_category.best_chars:
                    already_added.append(name)
                    continue
                self.ui_category_card(name)
            for name in already_added:
                self.ui_category_card(name, already_added=True)

    def ui_category_card(self, name, already_added=False):
        string = self.selected_category.image_prefixed(name)
        image = self.appdata.images.get(
            string,
            None,
        )
        if image is None:
            image = mili.icon.get_google(common.HOURGLASS)

        it = self.mili.element(
            (0, 0, self.image_h * self.appdata.image_ratio, self.image_h),
            {"offset": self.scroll_right.get_offset()},
        )
        alpha = 255
        if it.hovered:
            alpha = 130
        if already_added:
            alpha = 40

        self.mili.image(
            image,
            {
                "cache": "auto",
                "alpha": alpha,
            },
        )
        if it.left_just_pressed and not already_added:
            self.selected_category.best_chars.append(name)
        if it.just_hovered and self.card_hovered is None:
            self.card_hover_time = pygame.time.get_ticks()
        if it.hovered and pygame.time.get_ticks() - self.card_hover_time >= 400:
            self.card_hovered = string

    def get_obj_name(self, name, category=None):
        if category is None:
            return name.replace("_", " ").title()
        return category.format_item_name(name).replace("_", " ").title()

    def action_settings(self):
        self.app.menu = self.app.settings_menu
        self.mili.clear_memory()
        self.app.settings_back = self

    def event(self, e: pygame.Event):
        if not pygame.key.get_mods() & pygame.KMOD_CTRL:
            self.event_scroll(e, self.scroll_left, self.sl_rect)
            if self.selected_category is not None:
                self.event_scroll(e, self.scroll_right, self.sr_rect)
        elif e.type == pygame.MOUSEWHEEL and self.hover_category is not None:
            name = self.hover_category.best_chars.pop(self.hover_i)
            self.hover_category.best_chars.insert(self.hover_i + e.y * -1, name)
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                if self.selected_category:
                    self.selected_category = None
                    return
                self.app.menu = self.app.main_menu
                self.mili.clear_memory()
