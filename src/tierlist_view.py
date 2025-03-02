import mili
import pygame
import webbrowser
import sys
import os
from io import BytesIO
from PIL import Image
from src import common
from src import data
from src import alert


class TierlistView(common.UIComponent):
    name = "tierlist_view"

    def init(self):
        self.categories_scroll = mili.Scroll("tierlist_categories_scroll")
        self.category_scroll = mili.Scroll("tierlist_category_scroll")
        self.tiers_scroll = mili.Scroll("tierlist_tiers_scroll")
        self.show_categories = True
        self.selected_category: data.CategoryData = None
        self.categories_rect = pygame.Rect()
        self.category_rect = pygame.Rect()
        self.tiers_rect = pygame.Rect()
        self.selected_obj = None
        self.prev_selected_obj = None
        self.obj_selection_time = -1
        self.obj_selection_locked = False
        self.cache_black = mili.ImageCache()
        self.cache_selected_obj = mili.ImageCache()
        self.cache_dragging = mili.ImageCache()
        self.cache_preview = mili.ImageCache()
        self.obj_selection_search = None
        self.dragging_obj = None
        self.last_hovered_rect = pygame.Rect()
        self.last_hovered_idx = -1
        self.tier_name_w = 0
        self.drag_origin = None
        self.drag_origin_i = None
        self.show_numbers = False
        self.global_i = 0
        self.only_marked = False
        self.highlighted_category = None
        self.prev_highlighted_category = None
        self.highlight_locked = False
        self.highlight_time = 0
        self.lowest_card_bottom = 0
        self.category_count = {}
        self.card_hover_time = 0
        self.card_hovered = None
        self.layer_cache = mili.ImageLayerCache(self.mili, self.app.window.size, (0, 0))
        self.title_h = 0
        self.kmods = 0
        self.animes_only_first = True
        self.menu_change_tierlist = False
        self.show_initials = False
        self.memory_keep_ids = set([10000])
        self.set_image_h(common.IMAGE_H)

    @property
    def tierlist(self):
        return self.app.tierlist

    @property
    def only_category(self):
        id = self.appdata.categories_uids.get(self.tierlist.only_category, -1)
        if id != -1:
            return self.tierlist.only_category
        return ""

    def open(self):
        if self.only_category != "":
            only_category = self.appdata.categories[
                self.appdata.categories_uids[self.only_category]
            ]
            if not only_category.auto and only_category in self.appdata.manual_to_load:
                self.appdata.manual_to_load.remove(only_category)
                self.appdata.load_category_images(only_category)
        self.set_image_h(self.tierlist.default_image_h)
        self.update_category_count()

    def set_image_h(self, v):
        self.image_h = v
        self.image_w = self.image_h * self.appdata.image_ratio

    def update_category_count(self):
        self.category_count = {}
        for item in self.tierlist.tiers_all:
            uid = int(item.split("|")[0])
            if uid in self.category_count:
                self.category_count[uid] += 1
            else:
                self.category_count[uid] = 1

    def get_title(self):
        return f"Tierlist {self.tierlist.name.title()} (FPS:{self.app.clock.get_fps():.0f})"

    def update(self):
        self.kmods = pygame.key.get_mods()
        if pygame.mouse.get_just_released()[2]:
            if not self.obj_selection_locked:
                if self.selected_obj is None:
                    if (
                        pygame.time.get_ticks() - self.obj_selection_time
                        <= common.DOUBLE_CLICK_TIME
                    ):
                        self.selected_obj = self.prev_selected_obj
                        self.obj_selection_locked = True
                else:
                    self.selected_obj = None
            else:
                self.selected_obj = None
            if not self.highlight_locked:
                if self.highlighted_category is None:
                    if (
                        pygame.time.get_ticks() - self.highlight_time
                        <= common.DOUBLE_CLICK_TIME
                    ):
                        self.highlighted_category = self.prev_highlighted_category
                        self.highlight_locked = True
                else:
                    self.highlighted_category = None
            else:
                self.highlighted_category = None
        if self.selected_obj is not None:
            self.dragging_obj = None
        self.global_i = 0
        self.lowest_card_bottom = 0
        self.card_hovered = None
        self.layer_cache.size = (
            self.app.window.size[0],
            self.app.window.size[1] - self.title_h,
        )
        self.layer_cache.offset = (0, self.title_h)
        self.layer_cache.active = True
        self.dragging_category = None
        if (
            pygame.mouse.get_pressed()[pygame.BUTTON_RIGHT - 1]
            and self.dragging_obj is not None
        ):
            self.dragging_category = self.category_from_name(self.dragging_obj)
        if (
            pygame.mouse.get_pressed()[pygame.BUTTON_RIGHT - 1]
            and self.selected_obj is None
            and self.selected_category is not None
            and self.highlighted_category is None
        ):
            self.dragging_category = self.selected_category
        self.show_initials = pygame.key.get_pressed()[pygame.K_g]

    def ui(self):
        was = self.menu_change_tierlist
        with self.mili.begin(None, mili.FILL | mili.PADLESS | {"spacing": 0}) as mainc:
            self.ui_top_btns()
            self.title_h = self.mili.text_element(
                f"Tierlist {self.tierlist.name.upper().replace('_', ' ')} ({len(self.tierlist.tiers_all)})",
                {
                    "size": self.mult(20),
                    "growy": False,
                    "cache": "auto",
                },
                (0, 0, 0, self.mult(30)),
                {"align": "center", "offset": (0, -1)},
            ).data.rect.h
            self.ui_columns()
        self.mili.id_checkpoint(200000)
        if self.menu_change_tierlist:
            self.ui_change_tierlist(mainc)
            if any(pygame.mouse.get_just_released()) and was:
                self.menu_change_tierlist = False
        if self.dragging_obj is None and self.card_hovered is not None:
            self.mili.element(
                (pygame.mouse.get_pos() + pygame.Vector2(10, 10), (0, 0)),
                mili.FLOATING | {"blocking": False},
            )
            self.mili.rect({"color": common.BG_COL})
            self.mili.text(
                self.get_obj_name(
                    self.remove_prefix(self.card_hovered),
                    self.category_from_name(self.card_hovered),
                ),
                {"size": self.mult(20), "cache": "auto", "color": "white"},
            )
        self.ui_selected_obj()
        self.ui_dragging()

    def ui_top_btns(self):
        self.uicommon_back(self.app.main_menu)
        self.uicommon_top_btn("settings", "left", self.action_settings, 1)
        self.uicommon_top_btn("reorder", "left", self.action_toggle_categories, 2)
        self.uicommon_top_btn(
            "numon" if self.show_numbers else "numoff",
            "left",
            self.action_toggle_numbers,
            3,
        )
        self.uicommon_top_btn(
            "bookmark_flag" if self.only_marked else "bookmark",
            "left",
            self.action_toggle_only_marked,
            4,
        )
        self.uicommon_top_btn(
            common.HOURGLASS
            if self.app.screenshot.screenshot_taking
            else "photo_camera",
            "left",
            self.app.screenshot.screenshot_start,
            5,
        )
        self.uicommon_top_btn("manufacturing", "left", self.action_general_settings, 6)
        self.uicommon_top_btn(
            "folder_open", "left", self.action_menu_change_tierlist, 7
        )
        if self.selected_category is not None:
            self.uicommon_top_btn(
                "remove",
                "right",
                lambda: (
                    setattr(self, "selected_category", None),
                    self.mili.clear_memory(),
                ),
                1,
            )

    def ui_change_tierlist(self, mainc):
        with self.mili.begin(
            (
                0,
                self.title_h,
                (
                    (
                        self.appdata.ui_categories_col_percentage
                        if self.tierlist.only_category.strip() == ""
                        else self.tierlist.ui_tier_name_percentage
                    )
                    / 100
                )
                * self.app.window.size[0],
                self.app.window.size[1] - self.title_h,
            ),
            {"ignore_grid": True, "z": 99999, "parent_id": mainc.data.id}
            | mili.PADLESS,
        ):
            self.mili.rect({"color": common.BG_COL})
            self.mili.rect(
                {
                    "color": (common.BG_COL[0] + 40,) * 3,
                    "outline": 1,
                    "draw_above": True,
                }
            )
            for tierlist in self.appdata.tierlists.values():
                if tierlist is self.tierlist:
                    continue
                it = self.mili.element(None, {"fillx": True, "update_id": "cursor"})
                self.mili.rect({"color": (common.cond(it, *common.BTN_COLS),) * 3})
                self.mili.text(
                    tierlist.name.upper().replace("_", " "), {"size": self.mult(20)}
                )
                if it.left_just_released:
                    self.action_back()
                    if self.app.main_menu.tierlist_sanity_check(tierlist):
                        self.app.main_menu.open_tierlist(tierlist)

    def ui_dragging(self):
        if self.dragging_obj is None:
            return
        image = self.appdata.images.get(
            self.dragging_obj, mili.icon.get_google(common.HOURGLASS)
        )
        self.mili.image_element(
            image,
            {"cache": self.cache_dragging},
            pygame.Rect(0, 0, self.image_w, self.image_h).move_to(
                center=pygame.mouse.get_pos()
            ),
            {"ignore_grid": True, "z": 9999},
        )

    def ui_selected_obj(self):
        if self.selected_obj is None:
            return
        with self.mili.begin(
            ((0, 0), self.app.window.size),
            {
                "anchor": "max_spacing",
                "ignore_grid": True,
                "z": 500,
                "default_align": "center",
                "blocking": False,
            },
        ):
            self.mili.image(
                common.SURF,
                {
                    "fill": True,
                    "fill_color": "black",
                    "alpha": 200,
                    "cache": self.cache_black,
                },
            )
            category = self.category_from_name(self.selected_obj)
            name = self.remove_prefix(self.selected_obj)
            if (
                category.uid == common.ANIMES_UID
                or self.tierlist.only_category.strip() != ""
            ):
                txt = self.get_obj_name(name, category)
            else:
                txt = f"{self.get_obj_name(name, category)} ({self.get_obj_name(category.name)})"
            self.mili.text_element(
                txt,
                {"size": self.mult(40)},
                None,
                {"blocking": False, "cache": "auto"},
            )
            image = self.appdata.images.get(
                self.get_image_name(category, self.selected_obj),
                mili.icon.get_google(common.HOURGLASS),
            )
            self.mili.image_element(
                image,
                {"cache": self.cache_selected_obj},
                None,
                {"filly": "80", "fillx": True, "blocking": False},
            )
            self.obj_selection_search = txt.replace("(", "").replace(")", "")
            with self.mili.begin(None, mili.X | mili.CENTER | mili.RESIZE):
                for txt, callback in [
                    ("Search Online (A)", self.action_search),
                    (
                        "Unmark (R)"
                        if self.selected_obj in self.tierlist.marked
                        else "Mark (R)",
                        self.action_toggle_marked,
                    ),
                    ("Copy to Clipboard (I)", self.action_copy_to_clipboard),
                    ("Auto Custom Item (L)", self.action_make_custom_char),
                ]:
                    it = self.mili.element(None, {"update_id": "cursor"})
                    self.mili.rect({"color": (common.cond(it, *common.BTN_COLS),) * 3})
                    self.mili.text(
                        txt,
                        {
                            "size": self.mult(20),
                            "cache": "auto",
                        },
                    )
                    if it.left_just_released:
                        callback()

    def ui_columns(self):
        with self.mili.begin(
            None,
            mili.FILL
            | mili.PADLESS
            | mili.X
            | {"spacing": False, "image_layer_cache": self.layer_cache},
        ):
            if self.show_categories and self.only_category == "":
                self.ui_categories_col()
            else:
                self.categories_rect = pygame.Rect()
            self.mili.id_checkpoint(30000)
            self.ui_tiers_col()
            if self.selected_category is not None:
                self.mili.id_checkpoint(100000)
                self.ui_category_col()
            else:
                prev = self.layer_cache._erase_rects
                self.layer_cache._erase_rects = []
                if self.layer_cache._erase_rects != prev:
                    self.layer_cache._dirty = True
                self.category_rect = pygame.Rect()

    def ui_categories_col(self):
        self.mili.id_checkpoint(10000)
        with self.mili.begin(
            None,
            {
                "filly": True,
                "fillx": str(self.appdata.ui_categories_col_percentage),
                "spacing": 0,
                "flag": mili.PARENT_PRE_ORGANIZE_CHILDREN,
                "update_id": "tierlist_categories_scroll",
            }
            | mili.PADLESS,
        ) as cont:
            self.categories_rect = cont.data.absolute_rect.copy()
            self.mili.rect({"color": (40,) * 3, "outline": 1, "draw_above": True})
            self.ui_label_category(self.appdata.categories[common.ANIMES_UID], 0)
            for i, category in enumerate(self.appdata.categories.values()):
                if category.only_cover:
                    continue
                if category.uid != common.ANIMES_UID:
                    self.ui_label_category(category, i)

    def ui_label_category(self, category: data.CategoryData, i):
        self.mili.id_checkpoint(10010 + i * 10)
        if self.mili.id not in self.memory_keep_ids:
            self.memory_keep_ids.add(self.mili.id)
        it = self.mili.element(
            None,
            {
                "fillx": True,
                "offset": self.categories_scroll.get_offset(),
                "update_id": "cursor",
                "cache_rect_size": True,
            },
        )
        self.mili.rect(
            {
                "color": (
                    (common.BTN_COLS[1] + 20)
                    if self.highlighted_category is category
                    else (
                        common.cond(it, *common.BTN_COLS)
                        if category is not self.selected_category
                        else common.BTN_COLS[1]
                    ),
                )
                * 3
            }
        )
        color = "white"
        amount_in_tierlist = self.category_count.get(category.uid, 0)
        if amount_in_tierlist == 0:
            color = (80,) * 3
        else:
            try:
                color = self.get_category_label_color(amount_in_tierlist)
            except Exception:
                color = "white"
        if category.downloading:
            color = "orange"
        else:
            _, downloaded_all = category.get_downloaded_of(None)
            if not downloaded_all:
                color = "yellow"
        self.mili.text(
            self.get_obj_name(category.name),
            {
                "size": self.mult(17),
                "align": "left",
                "color": color,
                "cache": "auto",
            },
        )
        if any(
            [item.split("|")[0] == str(category.uid) for item in self.tierlist.marked]
        ):
            self.ui_marked()
        if it.left_just_released:
            if self.selected_category is category:
                self.selected_category = None
            else:
                self.selected_category = category
            self.mili.clear_memory(self.memory_keep_ids)
        if it.just_pressed_button == pygame.BUTTON_RIGHT:
            self.highlight_category(category)
        if (
            pygame.mouse.get_pressed()[2]
            and it.absolute_hover
            and self.highlighted_category != category
            and self.prev_highlighted_category != category
        ):
            self.highlight_category(category)

    def ui_category_col(self):
        with self.mili.begin(
            None,
            {
                "filly": True,
                "fillx": str(self.appdata.ui_category_col_percentage),
                "pad": 1,
                "spacing": 1,
            },
        ) as cont:
            self.category_rect = cont.data.absolute_rect.copy()
            self.mili.rect({"color": (40,) * 3, "outline": 1, "draw_above": True})
            self.ui_category_title()
            with self.mili.begin(
                None,
                {
                    "filly": True,
                    "fillx": True,
                    "grid": True,
                    "pad": 1,
                    "spacing": 1,
                    "flag": mili.PARENT_PRE_ORGANIZE_CHILDREN,
                    "update_id": "tierlist_category_scroll",
                }
                | mili.X,
            ) as cont:
                already_added = []
                prev = None
                first = True
                for name in self.selected_category.downloaded:
                    if name in self.selected_category.ignore:
                        continue
                    string = self.selected_category.image_prefixed(name)
                    if string in self.tierlist.tiers_all:
                        already_added.append(name)
                        continue
                    self.ui_category_card(name, prev_name=prev, first=first)
                    prev = name
                    first = False
                for name in already_added:
                    self.ui_category_card(name, already_added=True, first=-1)

    def ui_category_title(self):
        with self.mili.begin(
            None, {"fillx": True, "resizey": True} | mili.PADLESS | mili.X
        ) as it:
            r = it.data.absolute_rect
            r.h *= 2
            r.y -= self.title_h
            prev = self.layer_cache._erase_rects
            if r.h < 200:
                self.layer_cache._erase_rects = [r]
            if [r] != prev:
                self.layer_cache._dirty = True
            self.ui_category_title_name()
            if (
                self.selected_category.uid == common.ANIMES_UID
                or not self.selected_category.auto
            ):
                it = self.mili.element(
                    (0, 0, self.mult(30), self.mult(30)),
                    {"align": "center", "update_id": "cursor"},
                )
                self.mili.image(
                    mili.icon.get_google(
                        (
                            "refresh"
                            if not self.selected_category.auto
                            else (
                                "bookmark_flag"
                                if self.animes_only_first
                                else "bookmark"
                            )
                        )
                    ),
                    {
                        "cache": "auto",
                        "alpha": common.cond(it, *common.ALPHAS),
                    },
                )
                if it.left_just_released:
                    if self.selected_category.uid == common.ANIMES_UID:
                        self.animes_only_first = not self.animes_only_first
                    elif not self.selected_category.auto:
                        self.selected_category.download()
        if len(self.selected_category.downloaded) <= 0 and self.selected_category:
            self.mili.text_element(
                "No images downloaded for this category...",
                {
                    "size": self.mult(18),
                    "color": (180,) * 3,
                    "cache": "auto",
                },
                None,
                {"align": "center"},
            )
            if (
                self.selected_category.uid != common.ANIMES_UID
                and self.selected_category.auto
            ):
                it = self.mili.element(
                    (0, 0, self.mult(30), self.mult(30)),
                    {"align": "center", "update_id": "cursor"},
                )
                self.mili.image(
                    mili.icon.get_google("download"),
                    {
                        "cache": "auto",
                        "alpha": common.cond(it, *common.ALPHAS),
                    },
                )
                if it.left_just_released:
                    self.selected_category.download()

    def ui_category_title_name(self):
        extra_str, downloaded_all = self.selected_category.get_downloaded_of(None)
        self.mili.element(
            None,
            {
                "fillx": True,
            },
        )
        self.mili.text(
            self.get_obj_name(self.selected_category.name)
            + (
                f" {extra_str}"
                if self.selected_category.downloading
                and self.selected_category.uid != common.ANIMES_UID
                else f" ({self.category_count.get(self.selected_category.uid, 0)}/{len(self.selected_category.downloaded)})"
            ),
            {
                "size": self.mult(19),
                "color": "orange"
                if self.selected_category.downloading
                else ("white" if downloaded_all else "yellow"),
                "cache": "auto",
            },
        )
        if any(
            [
                item.split("|")[0] == str(self.selected_category.uid)
                for item in self.tierlist.marked
            ]
        ):
            self.ui_marked(True)

    def ui_category_card(self, name, already_added=False, prev_name=None, first=False):
        string = self.selected_category.image_prefixed(name)
        image = self.appdata.images.get(
            self.get_image_name(self.selected_category, string),
            None,
        )
        if image is None:
            image = mili.icon.get_google(common.HOURGLASS)

        it = self.mili.element(
            (0, 0, self.image_w, self.image_h),
            {"offset": self.category_scroll.get_offset()},
        )
        alpha = 255
        marked = string in self.tierlist.marked
        if it.hovered:
            alpha = 130
        if (
            self.selected_category.uid == common.ANIMES_UID
            and name.rsplit("_")[-1].isdecimal()
            and self.animes_only_first
        ):
            alpha = 10
        if already_added:
            alpha = 40
        if not marked and self.only_marked:
            alpha = 50

        self.mili.image(
            image,
            {
                "cache": "auto",
                "alpha": alpha,
                "layer_cache": self.layer_cache,
            }
            | ({"fill": True} if self.tierlist.use_original else {}),
        )
        if marked:
            self.ui_marked()
        if (
            self.show_initials
            and first != -1
            and ((prev_name is not None and name[0] != prev_name[0]) or first)
        ):
            self.mili.element(
                (it.data.absolute_rect.topleft, (0, 0)),
                {"ignore_grid": True, "blocking": False, "z": 999999, "parent_id": 0},
            )
            if (
                len(self.layer_cache._erase_rects) > 0
                and it.data.absolute_rect.top >= self.layer_cache._erase_rects[0].bottom
            ):
                self.mili.rect({"color": (common.BTN_COLS[1],) * 3})
                self.mili.text(
                    name[0].upper(),
                    {
                        "color": "green",
                        "size": int(self.image_h / 5.5),
                        "padx": 2,
                        "pady": 0,
                    },
                )
        if it.left_just_pressed and self.selected_obj is None and not already_added:
            self.dragging_obj = string
            self.drag_origin = None
            self.drag_origin_i = None
        if it.just_pressed_button == pygame.BUTTON_RIGHT and self.dragging_obj is None:
            self.select_obj(string)
        if (
            it.just_released_button == pygame.BUTTON_MIDDLE
            or it.left_just_released
            and (self.kmods & pygame.KMOD_CTRL or self.kmods & pygame.KMOD_META)
        ) and already_added:
            if string in self.tierlist.tiers_all:
                self.tierlist.tiers_all.remove(string)
            for tier in self.tierlist.tiers:
                if string in tier:
                    tier.remove(string)
        if (
            pygame.mouse.get_pressed()[2]
            and it.absolute_hover
            and self.dragging_obj is None
            and self.selected_obj != string
            and self.prev_selected_obj != string
        ):
            self.select_obj(string)
        if it.just_hovered and self.card_hovered is None:
            self.card_hover_time = pygame.time.get_ticks()
        if it.hovered and pygame.time.get_ticks() - self.card_hover_time >= 400:
            self.card_hovered = string

    def ui_tiers_col(self):
        with self.mili.begin(
            None,
            {
                "filly": True,
                "fillx": self.get_tiers_percentage(),
                "update_id": "tierlist_tiers_scroll",
                "spacing": 0,
            }
            | mili.PADLESS,
        ) as cont:
            self.tiers_rect = cont.data.absolute_rect.copy()
            self.mili.rect({"color": (40,) * 3, "outline": 1, "draw_above": True})
            for i in range(len(self.tierlist.tiers)):
                with self.mili.begin(
                    (0, 0, 0, self.image_h + 2),
                    {
                        "fillx": True,
                        "resizey": True if len(self.tierlist.tiers[i]) > 0 else False,
                        "spacing": 0,
                        "offset": self.tiers_scroll.get_offset(),
                    }
                    | mili.X
                    | mili.PADLESS,
                ) as it:
                    if it.absolute_hover:
                        self.last_hovered_idx = i
                        self.last_hovered_rect = it.data.absolute_rect
                    self.mili.rect(
                        {"color": (40,) * 3, "draw_above": True, "outline": 1}
                    )
                    self.ui_tier_name(i)
                    self.ui_tier(i, it)

    def ui_tier(self, i, parent_it):
        tierobjs = self.tierlist.tiers[i].copy()
        with self.mili.begin(
            None,
            {
                "fillx": str(100 - self.tierlist.ui_tier_name_percentage),
                "resizey": True,
                "padx": 1,
                "pady": 0,
                "spacing": 1,
                "grid": True,
                "flag": mili.PARENT_PRE_ORGANIZE_CHILDREN,
                # "cache_rect_size": True,
            }
            | mili.X,
        ):
            drag_i = -1
            if self.dragging_obj is not None and parent_it.absolute_hover:
                drag_i = self.get_drag_idx()
                if (
                    self.drag_origin_i is not None
                    and self.drag_origin_i < drag_i
                    and self.last_hovered_idx == self.drag_origin
                ):
                    drag_i += 1
            did_preview = False
            for oi, name in enumerate(tierobjs):
                if oi == drag_i:
                    did_preview = True
                    self.ui_tier_card(self.dragging_obj, i, oi, preview=True)
                self.ui_tier_card(name, i, oi)
                self.global_i += 1
            if not did_preview and drag_i != -1:
                self.ui_tier_card(self.dragging_obj, i, -1, preview=True)

    def ui_tier_card(self, prefixed, tier_i, i, preview=False):
        category = self.category_from_name(prefixed)
        image = self.appdata.images.get(
            self.get_image_name(category, prefixed),
            None,
        )
        if image is None:
            image = mili.icon.get_google(common.HOURGLASS)

        it = self.mili.element((0, 0, self.image_w, self.image_h))
        if it.data.absolute_rect.bottom > self.lowest_card_bottom:
            self.lowest_card_bottom = it.data.absolute_rect.bottom
        alpha = 255
        marked = prefixed in self.tierlist.marked and isinstance(self, TierlistView)
        cannumber = self.show_numbers
        if it.hovered:
            alpha = 130
        if prefixed == self.dragging_obj and self.drag_origin == tier_i:
            alpha = 0
            cannumber = False
        if preview:
            alpha = 120
            cannumber = False
        if cannumber:
            alpha = 80
        if (
            self.dragging_category is not None
            and category is not self.dragging_category
        ):
            alpha = 50
        if not marked and self.only_marked:
            alpha = 50
        if (
            self.highlighted_category is not None
            and category is not self.highlighted_category
        ):
            alpha = 50
        self.mili.image(
            image,
            {
                "cache": self.cache_preview if preview else "auto",
                "alpha": alpha,
                "layer_cache": None if preview else self.layer_cache,
            }
            | ({"fill": True} if self.tierlist.use_original else {}),
        )
        if cannumber:
            if tier_i == 0 and self.tierlist.ignore_first:
                i = i - 1
            perc = (
                (self.global_i + (0 if self.tierlist.ignore_first else 1))
                / (
                    len(self.tierlist.tiers_all)
                    - (1 if self.tierlist.ignore_first else 0)
                )
            ) * 100
            self.mili.text(
                f"{self.global_i + (0 if self.tierlist.ignore_first else 1)}\n{i + 1}\n{perc:.3f}%",
                {"size": int(self.image_h / 6), "cache": "auto", "growx": False},
            )
        if marked:
            self.ui_marked()
        if preview:
            return
        ctrl = self.kmods & pygame.KMOD_CTRL or self.kmods & pygame.KMOD_META
        if it.left_just_pressed and self.selected_obj is None and not ctrl:
            self.dragging_obj = prefixed
            self.drag_origin = tier_i
            self.drag_origin_i = i
        if it.just_pressed_button == pygame.BUTTON_RIGHT and self.dragging_obj is None:
            self.select_obj(prefixed)
        if it.just_released_button == pygame.BUTTON_MIDDLE or (
            it.left_just_released and ctrl
        ):
            if prefixed in self.tierlist.tiers_all:
                self.tierlist.tiers_all.remove(prefixed)
            if prefixed in self.tierlist.tiers[tier_i]:
                self.tierlist.tiers[tier_i].remove(prefixed)
            self.update_category_count()
        if (
            pygame.mouse.get_pressed()[2]
            and it.absolute_hover
            and self.dragging_obj is None
            and self.selected_obj != prefixed
            and self.prev_selected_obj != prefixed
        ):
            self.select_obj(prefixed)
        if it.just_hovered and self.card_hovered is None:
            self.card_hover_time = pygame.time.get_ticks()
        if it.hovered and pygame.time.get_ticks() - self.card_hover_time >= 400:
            self.card_hovered = prefixed

    def ui_tier_name(self, i, mult=1):
        data = self.tierlist.tiers_settings[i]
        col = self.appdata.get_color(data["color"])
        if col is None:
            col = (0, 0, 0, 0)
        it = self.mili.element(
            None,
            {
                "filly": True,
                "fillx": str(self.tierlist.ui_tier_name_percentage),
                "update_id": "cursor",
            },
        )
        if it.data.absolute_rect.bottom > self.lowest_card_bottom:
            self.lowest_card_bottom = it.data.absolute_rect.bottom
        self.tier_name_w = it.data.rect.w
        self.mili.rect({"color": col})
        self.mili.text(
            data["name"],
            {
                "size": self.mult(20 * mult),
                "color": data["txtcol"],
                "align": "center",
                "wraplen": "100",
                "cache": "auto",
            },
        )

    def ui_marked(self, nonecache=False):
        layercache = self.layer_cache
        if nonecache:
            layercache = None
        self.mili.image(
            mili.icon.get_google("priority_high", "red"),
            {
                "cache": "auto",
                "layer_cache": layercache,
            },
        )

    def action_make_custom_char(self):
        if not os.path.exists("custom_chars"):
            os.mkdir("custom_chars")
        category = self.category_from_name(self.selected_obj)
        name = self.remove_prefix(self.selected_obj)
        self.appdata.resize_size_ratio(
            f"user_data/categories/{category.uid}/{name}.png",
            f"custom_chars/{category.uid}${name}.png",
        )
        self.appdata.apply_custom_chars(f"{category.uid}${name}")

    def action_search(self):
        webbrowser.open(
            f"https://www.google.com/search?tbm=isch&q={self.obj_selection_search}"
        )

    def action_toggle_marked(self):
        if self.selected_obj in self.tierlist.marked:
            self.tierlist.marked.remove(self.selected_obj)
        else:
            self.tierlist.marked.add(self.selected_obj)

    def select_obj(self, name):
        if (
            self.prev_selected_obj == name
            and pygame.time.get_ticks() - self.obj_selection_time
            <= common.DOUBLE_CLICK_TIME
        ):
            return
        self.selected_obj = name
        self.prev_selected_obj = name
        self.obj_selection_locked = False
        self.obj_selection_time = pygame.time.get_ticks()

    def highlight_category(self, category):
        if (
            self.prev_highlighted_category == category
            and pygame.time.get_ticks() - self.highlight_time
            <= common.DOUBLE_CLICK_TIME
        ):
            return
        self.highlighted_category = category
        self.prev_highlighted_category = category
        self.highlight_time = pygame.time.get_ticks()

    def remove_prefix(self, name):
        return name.split("|")[1]

    def category_from_name(self, name):
        return self.appdata.categories[int(name.split("|")[0])]

    def get_obj_name(self, name, category=None):
        if category is None:
            return name.replace("_", " ").title()
        return category.format_item_name(name).replace("_", " ").title()

    def get_image_name(self, category: data.CategoryData, name):
        if category.uid == common.ANIMES_UID and self.tierlist.use_original:
            split = name.split("|")[1]
            split_ = split.rsplit("_", 1)
            if len(split_) == 1:
                catname = split_[0]
            else:
                if split_[-1].isdecimal():
                    return name
                catname = split
            cat = self.appdata.categories[self.appdata.categories_uids[catname]]
            if len(cat.links) > 1:
                return "original_" + name
        return name

    def get_tiers_percentage(self):
        return str(
            100
            - (
                self.appdata.ui_categories_col_percentage
                if self.show_categories and self.only_category == ""
                else 0
            )
            - (
                self.appdata.ui_category_col_percentage
                if self.selected_category is not None
                else 0
            )
        )

    def action_toggle_categories(self):
        self.show_categories = not self.show_categories
        if self.only_category != "":
            if self.selected_category is None:
                self.selected_category = self.appdata.categories[
                    self.appdata.categories_uids[self.only_category]
                ]
            else:
                self.selected_category = None
        self.mili.clear_memory()

    def action_toggle_numbers(self):
        self.show_numbers = not self.show_numbers

    def action_toggle_only_marked(self):
        self.only_marked = not self.only_marked

    def action_settings(self):
        self.action_back()
        self.app.menu = self.app.tierlist_settings_menu
        self.mili.clear_memory()
        self.app.menu.open()

    def action_general_settings(self):
        self.app.menu = self.app.settings_menu
        self.mili.clear_memory()
        self.app.settings_back = self

    def action_menu_change_tierlist(self):
        self.menu_change_tierlist = True
        self.show_categories = True
        self.mili.clear_memory()

    def action_back(self):
        self.tierlist.save_file()
        self.app.menu = self.app.main_menu
        self.mili.clear_memory()
        self.selected_category = None
        self.selected_obj = None
        self.only_marked = False

    def get_drag_idx(self):
        if self.last_hovered_rect is None:
            return -1
        rect = self.last_hovered_rect.copy()
        rect.x += self.tier_name_w + 1
        rect.w -= self.tier_name_w + 2
        rect.h -= 2
        rect.y += 1
        mouse = pygame.mouse.get_pos()
        if mouse[0] < rect.x:
            return 0
        mouse_rel = mouse - pygame.Vector2(rect.topleft)
        per_row = rect.w // (self.image_w + 1)
        row = mouse_rel.y // (self.image_h + 1)
        column = mouse_rel.x // (self.image_w + 1)
        idx = int(row * per_row + column)
        if (
            self.drag_origin_i is not None
            and self.drag_origin_i < idx
            and self.last_hovered_idx == self.drag_origin
        ):
            return idx - 1
        return idx

    def action_copy_to_clipboard(self):
        if not self.selected_obj:
            return
        obj_img = self.appdata.images.get(self.selected_obj, None)
        if obj_img is None:
            return

        image = Image.frombytes(
            "RGBA", obj_img.size, pygame.image.tobytes(obj_img, "RGBA")
        )

        if "win" in sys.platform.lower():
            self.clipboard_windows(image)
        else:
            self.clipboard_mac(image)

    def clipboard_windows(self, image):
        import win32clipboard

        output = BytesIO()
        image.convert("RGB").save(output, "BMP")
        bmp_data = output.getvalue()[14:]
        output.close()

        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, bmp_data)
        win32clipboard.CloseClipboard()

    def clipboard_mac(self, image):
        from AppKit import NSPasteboard, NSPasteboardTypePNG, NSData  # type: ignore
        import objc  # type: ignore

        buffer = BytesIO()
        image.save(buffer, format="PNG")
        png_data = buffer.getvalue()
        buffer.close()
        pasteboard = NSPasteboard.generalPasteboard()
        pasteboard.clearContents()
        ns_data = NSData.dataWithBytes_length_(png_data, len(png_data))
        pasteboard.setData_forType_(ns_data, NSPasteboardTypePNG)

    def get_category_label_color(self, tierlist_amount):
        colordata, power = self.tierlist.distribution_data.split("|")
        power = float(power)
        modulator = (tierlist_amount / max(self.category_count.values())) ** power
        rdata, gdata, bdata = colordata.split(",")
        out = []
        for dt in [rdata, gdata, bdata]:
            if "-" in dt:
                rl, rr = dt.split("-")
                l, r = int(rl), int(rr)
                value = pygame.math.clamp(pygame.math.lerp(l, r, modulator), 0, r)
                out.append(pygame.math.clamp(value, 0, 255))
            else:
                out.append(pygame.math.clamp(int(dt), 0, 255))
        return out

    def event(self, e):
        self.event_drag(e)
        if e.type == pygame.MOUSEWHEEL and pygame.key.get_pressed()[pygame.K_LCTRL]:
            new_h = pygame.math.clamp(
                self.image_h + e.y * 5, 10, self.app.window.size[1]
            )
            self.set_image_h(new_h)
        else:
            self.event_scroll(e, self.categories_scroll, self.categories_rect)
            self.event_scroll(e, self.category_scroll, self.category_rect)
            self.event_scroll(e, self.tiers_scroll, self.tiers_rect)
        if e.type == pygame.KEYDOWN:
            self.event_resize(e)
            self.event_keys(e)

    def event_drag(self, e):
        if not (
            e.type == pygame.MOUSEBUTTONUP
            and e.button == pygame.BUTTON_LEFT
            and self.dragging_obj is not None
        ):
            return
        if self.last_hovered_rect.collidepoint(e.pos):
            if self.drag_origin is not None:
                if self.dragging_obj in self.tierlist.tiers[self.drag_origin]:
                    self.tierlist.tiers[self.drag_origin].remove(self.dragging_obj)
            index = self.get_drag_idx()
            self.tierlist.tiers[self.last_hovered_idx].insert(index, self.dragging_obj)
            if self.dragging_obj not in self.tierlist.tiers_all:
                self.tierlist.tiers_all.add(self.dragging_obj)
        self.update_category_count()
        self.dragging_obj = None

    def event_resize(self, e):
        d = 0
        if e.key == pygame.K_LEFT:
            d = -1
        elif e.key == pygame.K_RIGHT:
            d = 1
        if d != 0:
            speed = 0.5
            if e.mod & pygame.KMOD_CTRL or e.mod & pygame.KMOD_META:
                if self.selected_category is not None:
                    speed *= -d
                    self.appdata.ui_category_col_percentage = pygame.math.clamp(
                        self.appdata.ui_category_col_percentage + speed, 5, 40
                    )
            elif e.mod & pygame.KMOD_SHIFT:
                speed *= d
                self.tierlist.ui_tier_name_percentage = pygame.math.clamp(
                    self.tierlist.ui_tier_name_percentage + speed, 3, 50
                )
            elif self.show_categories:
                speed *= d
                self.appdata.ui_categories_col_percentage = pygame.math.clamp(
                    self.appdata.ui_categories_col_percentage + speed, 5, 40
                )

    def event_keys(self, e):
        if e.key == pygame.K_a and self.selected_obj is not None:
            self.action_search()
        if e.key == pygame.K_r and self.selected_obj is not None:
            self.action_toggle_marked()
        if e.key == pygame.K_i and self.selected_obj is not None:
            self.action_copy_to_clipboard()
        if e.key == pygame.K_l and self.selected_obj is not None:
            self.action_make_custom_char()
        if e.key == pygame.K_r and self.selected_obj is None:
            self.action_toggle_only_marked()
        if e.key == pygame.K_n:
            self.action_toggle_numbers()
        if e.key == pygame.K_c:
            self.app.screenshot.screenshot_start()
        if e.key == pygame.K_u:
            self.animes_only_first = not self.animes_only_first
        if e.key == pygame.K_t:
            self.action_toggle_categories()
            self.mili.clear_memory()
            if not self.show_categories:
                self.menu_change_tierlist = False
        if e.key == pygame.K_y:
            self.menu_change_tierlist = not self.menu_change_tierlist
            if self.menu_change_tierlist:
                self.show_categories = True
                self.mili.clear_memory()
        if e.key == pygame.K_ESCAPE:
            self.event_escape()

    def event_escape(self):
        if self.dragging_obj is not None:
            self.dragging_obj = None
            return
        if self.selected_obj is not None:
            self.selected_obj = None
            self.obj_selection_locked = False
            return
        if self.highlighted_category is not None:
            self.highlighted_category = None
            self.highlight_locked = False
            self.prev_highlighted_category = None
            return
        if self.only_marked:
            self.only_marked = False
            return
        if self.show_numbers:
            self.show_numbers = False
            return
        if self.selected_category is not None:
            self.selected_category = None
            self.mili.clear_memory()
            return
        if self.show_categories:
            self.show_categories = False
            self.mili.clear_memory()
            return
        self.action_back()
