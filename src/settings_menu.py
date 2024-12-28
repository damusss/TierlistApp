import mili
import pygame
from src import common
from src import entryline
from src import data
from functools import partial


class SettingsMenu(common.UIComponent):
    name = "settings"

    def init(self):
        self.scroll_left = mili.Scroll("settings_scroll_left")
        self.scroll_right = mili.Scroll("settings_scroll_right")
        self.tbarh_entry = entryline.Entryline(
            "Enter height...",
            True,
            (0, 100),
            self.appdata.taskbar_h,
            self.appdata.taskbar_h_change,
        )
        self.ratio_entry = entryline.Entryline(
            "Enter ratio...",
            True,
            (0.1, 1),
            self.appdata.image_ratio,
        )
        self.screenshot_mult_entry = entryline.Entryline(
            "Enter multiplier...", True, (1, 5), self.appdata.screenshot_window_mult
        )
        self.get_ratio_size_entry = entryline.Entryline("Enter image full path...")
        self.resize_ratio_size_entry = entryline.Entryline("Enter image full path...")
        self.category_entries = {}
        self.color_entries = {}
        self.show_ids = False
        self.rect_l = pygame.Rect()
        self.rect_r = pygame.Rect()

    def update(self):
        self.show_ids = pygame.key.get_pressed()[pygame.K_t]

    def ui(self):
        with self.mili.begin(None, mili.CENTER | mili.FILL | mili.PADLESS):
            self.mili.text_element("General Settings", {"size": self.mult(40)})
            self.uicommon_back(self.app.main_menu)
            with self.mili.begin(
                None,
                {"default_align": "center", "pad": 0, "spacing": 0}
                | mili.FILL
                | mili.X,
            ):
                perc = 35
                with self.mili.begin(
                    None,
                    {
                        "fillx": str(perc),
                        "filly": True,
                        "default_align": "center",
                        "update_id": "settings_scroll_left",
                    },
                ) as cl:
                    self.ui_base_settings()
                    self.ui_action_btns()
                    self.ui_colors()
                    self.ui_utilities()
                    self.rect_l = cl.data.absolute_rect
                self.mili.line_element(
                    [(0, "-100"), (0, "100")],
                    {"size": 1, "color": (50,) * 3},
                    (0, 0, 1, 0),
                    {"filly": True},
                )
                with self.mili.begin(
                    None,
                    {
                        "fillx": str(100 - perc),
                        "filly": True,
                        "default_align": "center",
                        "update_id": "settings_scroll_right",
                    },
                ) as cr:
                    self.ui_categories()
                    self.rect_r = cr.data.absolute_rect

    def ui_base_settings(self):
        self.uicommon_setting(
            "Taskbar Height",
            self.tbarh_entry,
            self.appdata,
            "taskbar_h",
            "57",
            "40",
            buttons=[(30, "refresh", self.action_refresh_tbarh)],
            scroll=self.scroll_left,
        )
        self.uicommon_setting(
            "Image Ratio",
            self.ratio_entry,
            self.appdata,
            "image_ratio",
            "57",
            "40",
            buttons=[(30, "refresh", self.action_refresh_ratio)],
            scroll=self.scroll_left,
        )
        self.uicommon_setting(
            "Screenshot Mult",
            self.screenshot_mult_entry,
            self.appdata,
            "screenshot_window_mult",
            "57",
            "40",
            buttons=[(30, "refresh", self.action_refresh_screenshot_mult)],
            scroll=self.scroll_left,
        )

    def ui_utilities(self):
        self.mili.text_element(
            "Image Utilities",
            {
                "size": self.mult(26),
            },
            None,
            {"offset": self.scroll_left.get_offset()},
        )
        self.uicommon_setting(
            "Get Size Ratio",
            self.get_ratio_size_entry,
            None,
            "",
            "57",
            "40",
            buttons=[(30, "check_circle", self.action_get_size_ratio)],
            scroll=self.scroll_left,
        )
        self.uicommon_setting(
            "Resize Size Ratio",
            self.resize_ratio_size_entry,
            None,
            "",
            "57",
            "40",
            buttons=[(30, "check_circle", self.action_resize_size_ratio)],
            scroll=self.scroll_left,
        )

    def ui_colors(self):
        self.mili.text_element(
            "Color Variables",
            {
                "size": self.mult(26),
            },
            None,
            {"offset": self.scroll_left.get_offset()},
        )
        new_colors = []
        i = 0
        for varname, colvalue in list(self.appdata.color_vars):
            left_entry = self.get_color_entryline(i, varname, "left")
            right_entry = self.get_color_entryline(i, colvalue, "right")
            self.add_next_col = True
            self.uicommon_color(
                left_entry,
                right_entry,
                [(30, "delete", self.action_delete_color)],
                scroll=self.scroll_left,
                small=True,
            )
            if self.add_next_col:
                new_colors.append([left_entry.texts, right_entry.texts])
                i += 1
        it = self.mili.element(
            (0, 0, self.mult(40), self.mult(40)),
            {"offset": self.scroll_left.get_offset()},
        )
        self.mili.image(
            mili.icon.get_google("add", "white"),
            {
                "alpha": common.cond(it, *common.ALPHAS),
                "cache": mili.ImageCache.get_next_cache(),
            },
        )
        if it.left_just_released:
            new_colors.append([f"name_{pygame.time.get_ticks()}", "white"])
        self.appdata.color_vars = new_colors

    def ui_categories(self):
        with self.mili.begin(
            None,
            {"resizey": True, "fillx": True}
            | mili.PADLESS
            | mili.CENTER
            | mili.X
            | {"offset": self.scroll_right.get_offset()},
        ):
            color = "white"
            if any([cat.downloading for cat in self.appdata.categories.values()]):
                color = "orange"
            self.mili.text_element(
                "Categories",
                {"size": self.mult(26), "color": color},
                None,
            )
            it = self.mili.element((0, 0, self.mult(30), self.mult(30)))
            self.mili.rect({"color": (common.cond(it, *common.BTN_COLS),) * 3})
            self.mili.image(
                mili.icon.get_google(
                    "close" if self.appdata.auto_download else "download"
                ),
                {
                    "cache": mili.ImageCache.get_next_cache(),
                    "alpha": common.cond(it, *common.ALPHAS),
                },
            )
            if it.left_just_released:
                self.appdata.auto_download = not self.appdata.auto_download
        downloaded = len(self.appdata.categories[common.ANIMES_UID].downloaded)
        todownload = sum([len(cat.links) for cat in self.appdata.categories.values()])
        self.mili.text_element(
            f"Downloaded {downloaded}/{todownload} anime covers",
            {
                "size": self.mult(22),
                "color": "yellow" if downloaded < todownload else "white",
            },
            None,
            {"offset": self.scroll_right.get_offset()},
        )
        self.mili.line_element(
            [("-100", 0), ("100", 0)],
            {"size": 1, "color": (50,) * 3},
            (0, 0, 0, 5),
            {"fillx": "100", "offset": self.scroll_right.get_offset()},
        )
        first = True
        for category in list(self.appdata.categories.values()):
            if not first:
                self.mili.line_element(
                    [("-100", 0), ("100", 0)],
                    {"size": 1, "color": (50,) * 3},
                    (0, 0, 0, 5),
                    {"fillx": "100", "offset": self.scroll_right.get_offset()},
                )
            if category.uid == common.ANIMES_UID:
                continue
            self.ui_category(category)
            first = False
        it = self.mili.element(
            (0, 0, self.mult(40), self.mult(40)),
            {"offset": self.scroll_right.get_offset()},
        )
        self.mili.image(
            mili.icon.get_google("add", "white"),
            {
                "alpha": common.cond(it, *common.ALPHAS),
                "cache": mili.ImageCache.get_next_cache(),
            },
        )
        if it.left_just_released:
            self.appdata.add_category()

    def ui_category(self, category: data.CategoryData):
        name_entry = self.get_category_entryline(category.uid, category.name, False)
        id_str = (
            f" [id:{category.uid}{", only cover" if category.only_cover else ""}] "
            if self.show_ids
            else ""
        )
        extra_str, downloaded_all = category.get_downloaded_of(None)
        self.uicommon_setting(
            f"Name{id_str} {extra_str}",
            name_entry,
            None,
            "name",
            "60",
            ("35" if self.show_ids else "20"),
            buttons=[
                (30, "add", partial(self.action_add_link, category.uid)),
                (
                    30 if name_entry.texts.lower() != category.name.lower() else None,
                    "sync",
                    partial(
                        self.appdata.rename_category,
                        category,
                        name_entry.texts,
                        name_entry,
                    ),
                ),
                (
                    30,
                    "close" if category.downloading else "download",
                    partial(self.action_stop_download, category.uid)
                    if category.downloading
                    else category.download,
                ),
                (
                    30,
                    "cover" if category.only_cover else "cover_plus",
                    lambda: setattr(category, "only_cover", not category.only_cover),
                ),
                (30, "delete", partial(self.action_delete_category, category.uid)),
            ],
            namecol="orange"
            if category.downloading
            else ("white" if downloaded_all else "yellow"),
            txtcol="yellow"
            if name_entry.texts.lower() != category.name.lower()
            else "white",
            scroll=self.scroll_right,
        )
        if category.downloading:
            name_entry.text = category.name
        for i, link in enumerate(category.links.copy()):
            link_entry = self.get_category_entryline(f"{category.uid}_{i}", link, True)
            extra_str, downloaded_all = category.get_downloaded_of(link)
            self.uicommon_setting(
                f"Link {i+1} {extra_str}",
                link_entry,
                category.links,
                i,
                "85",
                "25",
                [(30, "delete", partial(self.action_remove_link, category.uid, i))],
                "#0EAAFC"
                if link_entry.texts.startswith(r"https://myanimelist.net/anime/")
                else "red",
                ("white" if downloaded_all else "yellow"),
                entrysize=18,
                scroll=self.scroll_right,
            )
            if category.downloading:
                link_entry.text = link

    def ui_action_btns(self):
        for txt, callback in [
            ("Apply Custom Characters", self.appdata.apply_custom_chars),
            ("Create Backup", self.appdata.create_backup),
        ]:
            it = self.mili.element(
                None, {"fillx": "90", "offset": self.scroll_left.get_offset()}
            )
            self.mili.rect({"color": (common.cond(it, *common.BTN_COLS) + 5,) * 3})
            self.mili.text(txt, {"size": self.mult(20)})
            if it.left_just_released:
                callback()

    def action_get_size_ratio(self):
        try:
            res, other = self.appdata.get_size_ratio(self.get_ratio_size_entry.texts)
            self.get_ratio_size_entry.set_text(f"Width: {res}, Offset: {other}")
        except Exception as e:
            self.get_ratio_size_entry.set_text(f"Error: {e}")

    def action_resize_size_ratio(self):
        try:
            self.appdata.resize_size_ratio(self.resize_ratio_size_entry.texts)
            self.resize_ratio_size_entry.set_text("")
        except Exception as e:
            self.resize_ratio_size_entry.set_text(f"Error: {e}")

    def action_refresh_screenshot_mult(self):
        self.appdata.screenshot_window_mult = 2

    def action_delete_category(self, uid):
        cat = self.appdata.categories[uid]
        if cat.downloading:
            return
        if cat.name in self.appdata.categories_uids:
            self.appdata.categories_uids.pop(cat.name)
        del self.appdata.categories[uid]

    def action_add_link(self, uid):
        cat = self.appdata.categories[uid]
        if cat.downloading:
            return
        cat.links.append("")

    def action_stop_download(self, uid):
        cat = self.appdata.categories[uid]
        if cat.downloading:
            cat.abort = True

    def action_remove_link(self, uid, idx):
        cat = self.appdata.categories[uid]
        if cat.downloading:
            return
        cat.links.pop(idx)
        for name in list(self.category_entries.keys()):
            if name.startswith(f"{uid}_"):
                del self.category_entries[name]

    def action_delete_color(self):
        self.add_next_col = False
        self.color_entries = {}

    def action_refresh_tbarh(self):
        self.appdata.taskbar_h = 48
        self.appdata.taskbar_h_change()
        self.tbarh_entry.set_text("48")

    def action_refresh_ratio(self):
        self.ratio_entry.set_text("0.6428571429")
        self.appdata.image_ratio = 0.6428571429

    def can_back(self):
        for cat in self.appdata.categories.values():
            entry = self.get_category_entryline(cat.uid, cat.name, False)
            if entry.text != cat.name:
                return False
        return True

    def can_quit(self):
        if not self.can_back():
            return False
        for cat in self.appdata.categories.values():
            if cat.downloading:
                return False
        return True

    def get_category_entryline(self, uid, text, link=False):
        uid = str(uid)
        if uid in self.category_entries:
            return self.category_entries[uid]
        entry = entryline.Entryline(
            "Enter MAL anime link..." if link else "Enter category name...",
            False,
            None,
            text,
            files=not link,
            lowercase=not link,
        )
        self.category_entries[uid] = entry
        return entry

    def get_color_entryline(self, idx, value, suffix):
        string = f"{idx}_{suffix}"
        if string in self.color_entries:
            return self.color_entries[string]
        entry = entryline.Entryline(
            "Enter name..." if suffix == "left" else "Enter color...",
            False,
            None,
            value,
        )
        self.color_entries[string] = entry
        return entry

    def event(self, e):
        self.event_scroll(e, self.scroll_left, self.rect_l)
        self.event_scroll(e, self.scroll_right, self.rect_r)
        self.tbarh_entry.event(e)
        self.ratio_entry.event(e)
        self.screenshot_mult_entry.event(e)
        self.get_ratio_size_entry.event(e)
        self.resize_ratio_size_entry.event(e)
        for entry in self.category_entries.values():
            entry.event(e)
        for entry in self.color_entries.values():
            entry.event(e)
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                if self.can_back():
                    self.app.menu = self.app.main_menu
