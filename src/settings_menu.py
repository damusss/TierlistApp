import mili
import pygame
from src import common
from src import entryline
from src import data
from src import alert
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
        self.mal_entry = entryline.Entryline(
            "Enter MAL username...", text=self.appdata.mal_username
        )
        self.get_ratio_size_entry = entryline.Entryline("Enter image full path...")
        self.resize_ratio_size_entry = entryline.Entryline("Enter image full path...")
        self.search_entry = entryline.Entryline("Enter search query...", lowercase=True)
        self.category_entries = {}
        self.color_entries = {}
        self.show_ids = False
        self.rect_l = pygame.Rect()
        self.rect_r = pygame.Rect()

    def get_title(self):
        return f"Tierlist App Settings (FPS:{self.app.clock.get_fps():.0f})"

    def update(self):
        self.search_entry.update()
        self.show_ids = pygame.key.get_pressed()[pygame.K_t] and (
            pygame.key.get_mods() & pygame.KMOD_CTRL
            or pygame.key.get_mods() & pygame.KMOD_META
        )

    def ui(self):
        with self.mili.begin(None, mili.CENTER | mili.FILL | mili.PADLESS):
            self.mili.text_element(
                "General Settings",
                {"size": self.mult(40), "cache": "auto"},
            )
            self.uicommon_back(
                self.app.main_menu
                if self.app.settings_back is None
                else self.app.settings_back
            )
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
                    self.mili.element((0, 0, 0, self.mult(10)))
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
        self.uicommon_setting(
            "MAL Username",
            self.mal_entry,
            self.appdata,
            "mal_username",
            "57",
            "40",
            buttons=[(30, "check_circle", self.appdata.refresh_MAL)],
            scroll=self.scroll_left,
        )

    def ui_utilities(self):
        self.mili.text_element(
            "Image Utilities",
            {"size": self.mult(26), "cache": "auto"},
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
            {"size": self.mult(26), "cache": "auto"},
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
            {"offset": self.scroll_left.get_offset(), "update_id": "cursor"},
        )
        self.mili.image(
            mili.icon.get_google("add", "white"),
            {
                "alpha": common.cond(it, *common.ALPHAS),
                "cache": "auto",
            },
        )
        if it.left_just_released:
            new_colors.append([f"name_{pygame.time.get_ticks()}", "white"])
        self.appdata.color_vars = new_colors

    def ui_categories(self):
        self.ui_categories_title()
        first = True
        stop = prev_oc = prev_manual = False
        done, didamount, totalamount, milid = 0, 0, 0, 5000
        only_oc = self.search_entry.texts == "$oc"
        only_manual = self.search_entry.texts == "$manual"
        for i, category in enumerate(
            sorted(
                sorted(self.appdata.categories.values(), key=lambda c: c.only_cover),
                key=lambda c: not c.auto,
            )
        ):
            if not only_oc and not only_manual:
                if self.search_entry.texts != "" and self.search_entry.texts.replace(
                    "_", " "
                ) not in category.name.replace("_", " "):
                    continue
            if only_oc and not category.only_cover:
                continue
            if only_manual and category.auto:
                continue
            if not stop and category.only_cover and not prev_oc and category.auto:
                self.mili.text_element(
                    "Only Cover Categories",
                    {
                        "cache": "auto",
                        "size": self.mult(22),
                    },
                    None,
                    {"offset": self.scroll_right.get_offset()},
                )
                prev_oc = True
            if not stop and not category.auto and not prev_manual:
                self.mili.text_element(
                    "Manual Categories",
                    {
                        "cache": "auto",
                        "size": self.mult(22),
                    },
                    None,
                    {"offset": self.scroll_right.get_offset()},
                )
                prev_manual = True
            if not first and not stop:
                self.ui_categories_line()
            if category.uid == common.ANIMES_UID:
                continue
            totalamount += 1 + len(category.links)
            if stop:
                continue
            done += 1
            self.mili.id_checkpoint(milid)
            if self.ui_category(category, i):
                stop = True
            milid += 500
            first = False
            didamount += 1 + len(category.links)
        if stop and didamount != totalamount:
            self.mili.element((0, 0, 0, self.mult(40) * (totalamount - didamount)))
            return
        if done == 0 and self.search_entry.texts != "":
            self.mili.text_element(
                "No category matches the search query",
                {
                    "size": self.mult(22),
                    "color": (200,) * 3,
                    "cache": "auto",
                },
            )
        self.ui_categories_footer()

    def ui_categories_footer(self):
        it = self.mili.element(
            (0, 0, self.mult(40), self.mult(40)),
            {"offset": self.scroll_right.get_offset(), "update_id": "cursor"},
        )
        self.mili.image(
            mili.icon.get_google("add", "white"),
            {
                "alpha": common.cond(it, *common.ALPHAS),
                "cache": "auto",
            },
        )
        if it.left_just_released:
            self.appdata.add_category()

    def ui_categories_title(self):
        with self.mili.begin(
            None,
            {"resizey": True, "fillx": True}
            | mili.PADLESS
            | mili.CENTER
            | mili.X
            | {"offset": self.scroll_right.get_offset()},
        ):
            color = "white"
            if self.appdata.downloading_amount > 0:
                color = "orange"
            self.mili.text_element(
                "Categories",
                {
                    "size": self.mult(26),
                    "color": color,
                    "cache": "auto",
                },
                None,
            )
            it = self.mili.element(
                (0, 0, self.mult(30), self.mult(30)), {"update_id": "cursor"}
            )
            self.mili.rect({"color": (common.cond(it, *common.BTN_COLS),) * 3})
            self.mili.image(
                mili.icon.get_google(
                    "close" if self.appdata.auto_download else "download"
                ),
                {
                    "cache": "auto",
                    "alpha": common.cond(it, *common.ALPHAS),
                },
            )
            if it.left_just_released:
                self.appdata.auto_download = not self.appdata.auto_download
            self.search_entry.ui(
                self.mili, (0, 0, 0, self.mult(35)), {"fillx": "25"}, self.mult
            )
        downloaded = len(self.appdata.categories[common.ANIMES_UID].downloaded)
        todownload = sum(
            [
                len(cat.links) if cat.auto else 0
                for cat in self.appdata.categories.values()
            ]
        )
        self.mili.text_element(
            f"Downloaded {downloaded}/{todownload} anime covers",
            {
                "size": self.mult(22),
                "color": "yellow" if downloaded < todownload else "white",
                "cache": "auto",
            },
            None,
            {"offset": self.scroll_right.get_offset()},
        )
        self.ui_categories_line()

    def ui_categories_line(self):
        self.mili.line_element(
            [("-100", 0), ("100", 0)],
            {"size": 1, "color": (50,) * 3},
            (0, 0, 0, 5),
            {"fillx": "100", "offset": self.scroll_right.get_offset()},
        )

    def ui_category(self, category: data.CategoryData, idx):
        name_entry = self.get_category_entryline(category.uid, category.name, False)
        id_str = f" [id:{category.uid}] " if self.show_ids else ""
        extra_str, downloaded_all = category.get_downloaded_of(
            None, include_covers=True
        )
        mainit = [
            self.uicommon_setting(
                f"{idx}.{id_str}",
                name_entry,
                None,
                "name",
                "75",
                ("15" if self.show_ids else "10"),
                buttons=self.get_category_btns(category, name_entry),
                namecol="orange"
                if category.downloading
                else ("white" if downloaded_all else "yellow"),
                txtcol="yellow"
                if name_entry.texts.lower() != category.name.lower()
                else "white",
                scroll=self.scroll_right,
                post_txt=extra_str,
                post_style={
                    "size": self.mult(20),
                    "color": "orange"
                    if category.downloading
                    else ("white" if downloaded_all else "yellow"),
                    "growx": False,
                },
                clickable=None
                if category.downloading
                else (lambda: setattr(category, "collapsed", not category.collapsed))
                if category.auto
                else False,
            )
        ]
        if category.downloading:
            name_entry.focused = False
            name_entry.text = category.name
        if (not category.collapsed and category.auto) or category.downloading:
            for i, link in enumerate(category.links.copy()):
                link_entry = self.get_category_entryline(
                    f"{category.uid}_{i}", link, True
                )
                extra_str, downloaded_all = category.get_downloaded_of(link)
                mainit.append(
                    self.uicommon_setting(
                        f"Link {i + 1}. {extra_str}",
                        link_entry,
                        category.links,
                        i,
                        "90",
                        "20",
                        [
                            (
                                30,
                                None if category.downloading else "delete",
                                partial(self.action_remove_link, category.uid, i),
                            )
                        ],
                        "#0EAAFC"
                        if link_entry.texts.startswith(
                            r"https://myanimelist.net/anime/"
                        )
                        else "red",
                        "orange"
                        if category.downloading
                        else ("white" if downloaded_all else "yellow"),
                        entrysize=18,
                        scroll=self.scroll_right,
                    )
                )
                if category.downloading:
                    link_entry.focused = False
                    link_entry.text = link
        for it in mainit:
            if it.absolute_rect.bottom > self.app.window.size[1] * 1.2:
                return True
        return False

    def get_category_btns(
        self, category: data.CategoryData, name_entry: entryline.Entryline
    ):
        return [
            (
                30 if name_entry.texts.lower() != category.name.lower() else None,
                None if category.downloading else "sync",
                partial(
                    self.appdata.rename_category,
                    category,
                    name_entry.texts,
                    name_entry,
                ),
            ),
            (
                30,
                "refresh"
                if not category.auto
                else ("close" if category.downloading else "download"),
                partial(self.action_stop_download, category.uid)
                if category.downloading
                else category.download,
            ),
            (
                30,
                None
                if category.downloading
                else ("folder_open" if not category.auto else "add"),
                category.open_exporer
                if not category.auto
                else partial(self.action_add_link, category.uid),
            ),
            (
                30,
                None
                if category.downloading
                else (
                    "menu_book"
                    if not category.auto
                    else ("cover" if category.only_cover else "cover_plus")
                ),
                partial(self.action_only_cover_auto, category),
            ),
            (
                30,
                None if category.downloading else "delete",
                partial(self.action_delete_category, category.uid)
                if category.name == ""
                else (
                    partial(
                        alert.alert,
                        "Confirm Deletion",
                        f"Are you sure you want to delete the category {category.name} (uid:{category.uid})? The downloaded covers and items will be deleted and you'll need to download them again if you change your mind.",
                        False,
                        ["Delete", "Cancel"],
                        partial(self.action_delete_category, category.uid),
                    )
                ),
            ),
        ]

    def ui_action_btns(self):
        for txt, callback in [
            ("Apply Custom Characters", self.appdata.apply_custom_chars),
            ("Create Backup", self.appdata.create_backup),
            ("Refresh MyAnimeList", self.appdata.refresh_MAL),
        ]:
            it = self.mili.element(
                None,
                {
                    "fillx": "90",
                    "offset": self.scroll_left.get_offset(),
                    "update_id": "cursor",
                },
            )
            self.mili.rect({"color": (common.cond(it, *common.BTN_COLS) + 5,) * 3})
            self.mili.text(txt, {"size": self.mult(20), "cache": "auto"})
            if it.left_just_released:
                callback()

    def action_only_cover_auto(self, category: data.CategoryData):
        if category.only_cover:
            category.only_cover = False
            category.auto = False
        elif not category.auto:
            category.auto = True
            category.only_cover = False
            category.cached = {}
        else:
            category.auto = True
            category.only_cover = True
            category.cached = {}

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

    def action_delete_category(self, uid, btn=-1):
        if btn == 1:
            return
        cat = self.appdata.categories[uid]
        if cat.downloading:
            return
        cat.remove_old_covers()
        cat.erase_items()
        if cat.name in self.appdata.categories_uids:
            self.appdata.categories_uids.pop(cat.name)
        del self.appdata.categories[uid]
        alert.message(f"Category {cat.name} was deleted")

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
        self.mal_entry.event(e)
        self.screenshot_mult_entry.event(e)
        self.get_ratio_size_entry.event(e)
        self.resize_ratio_size_entry.event(e)
        self.search_entry.event(e)
        for entry in self.category_entries.values():
            entry.event(e)
        for entry in self.color_entries.values():
            entry.event(e)
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                if self.can_back():
                    self.app.menu = self.app.main_menu
