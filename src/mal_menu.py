import mili
import pygame
from src import common
from src import entryline
from src import data


class MALMenu(common.UIComponent):
    name = "MAL"

    def init(self):
        self.scroll_right = mili.Scroll("MAL_scroll_right")
        self.scroll_left = mili.Scroll("MAL_scroll_left")
        self.search_entry = entryline.Entryline("Enter query filter...", lowercase=True)
        self.sr_rect = pygame.Rect()
        self.sl_rect = pygame.Rect()
        self.show_filters = False
        self.filters_full = False
        self.tag_filters = []
        self.score_filters = []
        self.filters = []
        self.filters_and = True
        self.filters_pos = True
        self.count = 0
        self.prev_count = 0
        self.layer_cache = mili.ImageLayerCache(
            self.mili, (self.app.window.size[0], self.app.window.size[1] - 30), (0, 30)
        )

    def update(self):
        self.search_entry.update()
        self.prev_count = self.count
        self.count = 0
        self.layer_cache.active = True

    def get_title(self):
        return f"{self.appdata.mal_username}'s Anime List (FPS:{self.app.clock.get_fps():.0f})"

    def ui(self):
        self.uicommon_back(self.app.main_menu)
        self.uicommon_top_btn("reorder", "left", self.action_toggle_filters, 1)
        self.uicommon_top_btn("clear_filters", "left", self.action_clear_filters, 2)
        self.uicommon_top_btn(
            "mask_add" if self.filters_and else "mask",
            "left",
            self.action_toggle_filter_op,
            3,
        )
        self.uicommon_top_btn(
            "full" if self.filters_full else "partial",
            "left",
            self.action_toggle_filter_full,
            4,
        )
        self.uicommon_top_btn(
            "filter_pos" if self.filters_pos else "filter_neg",
            "left",
            self.action_toggle_filter_sign,
            5,
        )
        self.uicommon_top_btn(
            "unfold_more" if self.appdata.mal_small else "unfold_less",
            "left",
            self.action_toggle_size,
            6,
        )
        self.uicommon_top_btn("settings", "left", self.action_settings, 7)
        self.uicommon_top_btn("refresh", "left", self.appdata.refresh_MAL, 8)
        self.uicommon_top_btn("find_replace", "left", self.appdata.load_MAL, 9)
        self.ui_filters_preview()
        self.ui_main_cont()
        if self.count != self.prev_count:
            self.layer_cache._dirty = True

    def ui_main_cont(self):
        self.mili.id_checkpoint(1000)
        with self.mili.begin(
            ((0, 0), self.app.window.size), mili.PADLESS | {"spacing": 0}
        ):
            self.mili.element((0, 0, 0, self.mult(30)))
            self.mili.line_element(
                [("-100", 0), ("100", 0)],
                {"size": 1, "color": (40,) * 3},
                (0, self.mult(30), self.app.window.size[0], 1),
                {"ignore_grid": True, "blocking": False},
            )
            with self.mili.begin(
                None, mili.FILL | mili.PADLESS | mili.X | {"spacing": 0}
            ):
                with self.mili.begin(
                    None,
                    {
                        "filly": True,
                        "fillx": "20" if self.show_filters else "0",
                        "pad": 0,
                        "spacing": 0,
                        "update_id": "MAL_scroll_left",
                    },
                ) as lcont:
                    with self.mili.begin(
                        None, mili.FILL | mili.PADLESS | {"spacing": 1}
                    ):
                        if self.show_filters:
                            self.ui_filters()
                    self.sl_rect = lcont.data.absolute_rect
                with self.mili.begin(
                    None,
                    mili.FILL
                    | mili.PADLESS
                    | mili.CENTER
                    | {
                        "update_id": "MAL_scroll_right",
                        "anchor": "first",
                        "image_layer_cache": self.layer_cache,
                    },
                ) as rcond:
                    self.ui_right_cond(rcond)

    def ui_right_cond(self, rcond):
        self.mili.text_element(
            f"{self.appdata.mal_username}'s Anime List",
            {"size": self.mult(40), "cache": "auto"},
            element_style={"offset": self.scroll_right.get_offset()},
        )
        if self.appdata.mal_episodes_str is not None:
            self.mili.text_element(
                f"Statistics: {self.appdata.mal_episodes_str}",
                {"size": self.mult(20), "color": (160,) * 3, "cache": "auto"},
                element_style={"offset": self.scroll_right.get_offset()},
            )
        self.sr_rect = rcond.data.absolute_rect
        amount = 0
        tot_amount = 0
        all_parents = []
        for score, parents in self.appdata.mal_sorted.items():
            tot_amount += len(parents)
            parents = [parent for parent in parents if self.filter(parent)]
            amount += len(parents)
            if len(parents) <= 0:
                continue
            all_parents.append((score, parents))
        if amount != tot_amount and amount > 0:
            self.mili.text_element(
                f"Search Stats: {(amount / (tot_amount if tot_amount else 1000000)) * 100:.2f}% of animes match filters",
                {"size": self.mult(20), "color": (160,) * 3},
                element_style={"offset": self.scroll_right.get_offset()},
            )
        for score, parents in all_parents:
            self.ui_category(score, parents)
            self.layer_cache.active = True
        if amount <= 0:
            self.mili.text_element(
                "No animes match the provided filters, try changing/clearing them",
                {"size": self.mult(25), "color": (180,) * 3},
            )
            self.layer_cache.active = False

    def ui_anime(self, parent: data.MALParent):
        self.count += 1
        H = self.mult(280)
        if self.appdata.mal_small:
            H = self.mult(120)
        self.mili.id_checkpoint(10000 + parent.global_i * 1000)
        with self.mili.begin(
            (0, 0, 0, H),
            {
                "fillx": str(
                    100
                    / (
                        (3 if self.show_filters else 4)
                        + (2 if self.appdata.mal_small else 0)
                    )
                    - 0.3
                ),
                "axis": "x",
                "pad": 0,
                "spacing": 0,
            },
        ) as main:
            r = main.data.absolute_rect
            if r.top >= self.app.window.size[1] or r.bottom <= self.mult(30):
                return
            color = common.RATED_COLORS[parent.score]
            bar_col = {
                "completed": (25,) * 3,
                "watching": "#002203",
                "dropped": "#270109",
                "on-hold": "#282000",
            }[parent.status]
            br = "0"
            image = self.appdata.images.get(f"0|{parent.category.name}", None)
            if image is None:
                image = mili.icon.get_google(common.HOURGLASS)
            self.mili.rect({"color": (20,) * 3, "border_radius": br})
            self.mili.image_element(
                image,
                {"cache": "auto", "layer_cache": self.layer_cache},
                (0, 0, H * self.appdata.image_ratio, H),
            )
            with self.mili.begin(
                ((0, 0), (r.size[0] - H * self.appdata.image_ratio, r.size[1])),
                mili.PADLESS | {"spacing": 0, "anchor": "max_spacing"},
            ) as cont:
                w = cont.data.rect.w
                self.ui_anime_name(parent, color, w)
                self.mili.element(None, {"filly": "10"})
                self.ui_anime_infobar(parent, bar_col, w)
                if not self.appdata.mal_small:
                    self.mili.element(None, {"filly": True})
                if len(parent.animes) > 1 and not self.appdata.mal_small:
                    self.ui_anime_animes(parent, w, H)

    def ui_anime_animes(self, parent: data.MALParent, w, h):
        first_batch = len(parent.animes)
        match len(parent.animes):
            case 2:
                W = w / 3.5
                H = W * (1 / self.appdata.image_ratio)
            case 3:
                W = w / 3.5
                H = W * (1 / self.appdata.image_ratio)
            case 4:
                W = w / 4 - 1
                H = W * (1 / self.appdata.image_ratio)
            case 5 | 6:
                H = h / 3.5
                first_batch = 3
            case 7 | 8:
                H = h / 3.5
                first_batch = 4
        animes_sorted = sorted(parent.animes.items(), key=lambda i: i[0])
        i = 0
        with self.mili.begin(
            (0, 0, w, 0),
            {
                "resizey": True,
                "axis": "x",
                "padx": 1,
                "pady": 0,
                "spacing": 1,
            },
        ):
            for _, anime in animes_sorted[:first_batch]:
                self.ui_anime_anime(anime, parent, H, i)
                i += 1
        if len(parent.animes) > 4:
            with self.mili.begin(
                (0, 0, w, 0),
                {
                    "resizey": True,
                    "axis": "x",
                    "padx": 1,
                    "pady": 0,
                    "spacing": 1,
                },
            ):
                for _, anime in animes_sorted[first_batch:]:
                    self.ui_anime_anime(anime, parent, H, i)
                    i += 1

    def ui_anime_anime(self, anime: data.MALAnime, parent: data.MALParent, H, i):
        color = common.RATED_COLORS[anime.score]
        with self.mili.begin(None, mili.RESIZE | mili.PADLESS | {"spacing": 0}):
            with self.mili.begin(
                None,
                {
                    "fillx": True,
                    "resizey": True,
                    "pad": 0,
                    "spacing": 0,
                    "axis": "x",
                }
                | mili.CENTER,
            ):
                self.mili.image_element(
                    mili.icon.get_google("star", color=color),
                    {"cache": "auto"},
                    (0, 0, self.mult(10), self.mult(10)),
                )
                self.mili.text_element(
                    f"{anime.score if anime.score != 0 else '-'}  ",
                    {
                        "size": self.mult(13),
                        "color": color,
                        "padx": 0,
                        "pady": 1,
                        "bold": True,
                        "cache": "auto",
                    },
                )
            image = self.appdata.images.get(
                f"original_0|{parent.category.name}{f'_{i + 1}' if i > 0 else ''}", None
            )
            if image is None:
                image = mili.icon.get_google(common.HOURGLASS)
            self.mili.image_element(
                image,
                {"cache": "auto", "layer_cache": self.layer_cache, "fill": True},
                (0, 0, H * self.appdata.image_ratio, H),
            )

    def ui_anime_infobar(self, parent: data.MALParent, bar_col, w):
        with self.mili.begin(
            (0, 0, w, self.mult(30)),
            {"fillx": True, "axis": "x", "spacing": 0, "anchor": "max_spacing"}
            | mili.CENTER,
        ):
            self.mili.rect({"color": bar_col})
            self.mili.text_element(
                f"#{parent.global_i}",
                {"size": self.mult(18), "bold": True, "cache": "auto"},
            )
            self.mili.element(None, {"fillx": True})
            if parent.elapsed_time is not None:
                self.mili.text_element(
                    f"{parent.elapsed_time} Day{'s' if parent.elapsed_time > 1 else ''}",
                    {"size": self.mult(16), "color": (150,) * 3, "cache": "auto"},
                )
                self.mili.element(None, {"fillx": True})
            self.mili.image_element(
                mili.icon.get_google("movie"),
                {"cache": "auto", "alpha": 190},
                (0, 0, self.mult(22), self.mult(22)),
            )
            self.mili.text_element(
                f"{parent.episodes_str.replace(' + ', ('+' if self.appdata.mal_small else ' + '))}",
                {"size": self.mult(18), "cache": "auto"},
            )

    def ui_anime_name(self, parent: data.MALParent, color, w):
        name = parent.category.name.replace("_", " ").title()
        if name.lower() == "fmab":
            name = "FMAB"
        if name.lower().startswith("iwanttoeat"):
            name = "I Want to Eat Your Pancreas"
        if name.lower().startswith("thedreaming"):
            name = "The Dreaming Boy is a Realist"
        self.mili.text_element(
            name,
            {
                "size": self.mult(22),
                "slow_grow": True,
                "growx": False,
                "color": color,
                "wraplen": "100",
                "cache": "auto",
            },
            (0, 0, w, 0),
        )

    def ui_category(self, score, parents: list[data.MALParent]):
        name = common.RATED_NAMES[score]
        it = self.mili.text_element(
            name,
            {
                "size": self.mult(30),
                "align": "left",
                "color": common.RATED_COLORS[score],
                "cache": "auto",
            },
            None,
            {"fillx": True, "offset": self.scroll_right.get_offset()},
        )
        if it.data.absolute_rect.top > self.app.window.size[1]:
            return
        with self.mili.begin(
            None,
            {
                "fillx": True,
                "resizey": True,
                "axis": "x",
                "grid": True,
                "flag": mili.PARENT_PRE_ORGANIZE_CHILDREN,
                "offset": self.scroll_right.get_offset(),
            },
        ):
            for parent in parents:
                self.ui_anime(parent)

    def ui_filter(self, item, flist):
        itemstr = item
        if isinstance(item, int | float):
            itemstr = common.RATED_NAMES_SHORT[item]
        it = self.mili.element(
            (0, 0, 0, self.mult(24)), {"fillx": True, "update_id": "cursor"}
        )
        active = item in flist or it.hovered
        self.mili.rect({"color": (28 if active else 18,) * 3})
        self.mili.text(
            itemstr.replace("_", " ").replace("fs0", "fs 0"),
            {
                "size": self.mult(16),
                "align": "left",
                "growy": False,
                "color": (255 if active else 200,) * 3,
                "cache": "auto",
            },
        )
        if it.left_just_released:
            if item in flist:
                flist.remove(item)
            else:
                flist.append(item)

    def ui_filters(self):
        self.mili.rect({"color": (40,) * 3, "outline": 1, "draw_above": True})
        with self.mili.begin(None, {"resizey": True, "fillx": True, "axis": "x"}):
            self.mili.image_element(
                mili.icon.get_google("search"),
                {"cache": "auto"},
                (0, 0, self.mult(25), self.mult(25)),
            )
            self.search_entry.ui(
                self.mili, (0, 0, 0, self.mult(30)), {"fillx": True}, self.mult
            )
        for title, flist, totlist in [
            ("Filters", self.filters, ["TV", "Movie", "Couple", "Trilogy", "Saga"]),
            ("Tag Filters", self.tag_filters, self.appdata.mal_tags),
            (
                "Score Filters",
                self.score_filters,
                list(common.RATED_NAMES_SHORT.keys()),
            ),
        ]:
            self.mili.text_element(
                title,
                {"size": self.mult(21), "cache": "auto"},
                None,
                {"offset": self.scroll_left.get_offset()},
            )
            with self.mili.begin(
                None,
                {
                    "fillx": True,
                    "resizey": True,
                    "spacing": 1,
                    "offset": self.scroll_left.get_offset(),
                }
                | mili.PADLESS
                | mili.X,
            ):
                adder = 0 if len(totlist) <= 2 else 1
                with self.mili.begin(
                    None, {"fillx": True, "resizey": True, "spacing": 1} | mili.PADLESS
                ):
                    for item in totlist[: len(totlist) // 2 + adder]:
                        self.ui_filter(item, flist)
                with self.mili.begin(
                    None, {"fillx": True, "resizey": True, "spacing": 1} | mili.PADLESS
                ):
                    for item in totlist[len(totlist) // 2 + adder :]:
                        self.ui_filter(item, flist)

    def ui_filters_preview(self):
        x = self.mult(30) * 10
        with self.mili.begin(
            (x, 0, self.app.window.size[0] - (x + self.mult(30)), self.mult(30)),
            mili.X
            | {
                "pady": 4,
                "spacing": 2,
                "anchor": "first",
                "ignore_grid": True,
                "padx": 10,
                "z": 99999,
            },
        ):
            first = True
            for list in [
                self.filters,
                self.tag_filters,
                self.score_filters,
                [f"Query:'{self.search_entry.texts}'"]
                if self.search_entry.texts
                else [],
            ]:
                for item in list.copy():
                    if not first:
                        self.mili.text_element(
                            "and" if self.filters_and else "or",
                            {
                                "size": self.mult(12),
                                "color": (120,) * 3,
                                "padx": 0,
                                "cache": "auto",
                            },
                        )
                    first = False
                    with self.mili.begin(
                        None,
                        {
                            "resizex": True,
                            "filly": True,
                            "pady": 0,
                            "padx": 4,
                            "update_id": "cursor",
                        }
                        | mili.X
                        | mili.CENTER,
                    ) as it:
                        white = common.cond(it, 180, 255, 150)
                        self.mili.rect(
                            {
                                "color": (common.BG_COL[0] + 15,) * 3,
                                "border_radius": "0",
                            }
                        )
                        if it.hovered:
                            self.mili.rect(
                                {
                                    "color": (common.BG_COL[0] + 15 * 2.5,) * 3,
                                    "border_radius": "0",
                                    "outline": 1,
                                }
                            )
                        itemstr = item
                        if isinstance(item, int | float):
                            itemstr = common.RATED_NAMES_SHORT[item]
                        self.mili.text_element(
                            itemstr.replace("_", " ").replace("fs0", "fs 0"),
                            {
                                "size": self.mult(14),
                                "color": (white,) * 3,
                                "padx": 0,
                                "growy": False,
                                "cache": "auto",
                            },
                            None,
                            {"blocking": False, "filly": True},
                        )
                        self.mili.image_element(
                            mili.icon.get_google("close"),
                            {"alpha": white, "cache": "auto"},
                            (0, 0, self.mult(15), self.mult(15)),
                            {"blocking": False, "offset": (0, 2)},
                        )
                        if it.left_just_released:
                            if item.startswith("Query:'"):
                                self.search_entry.set_text("")
                            else:
                                list.remove(item)

    def filter_anime(self, anime: data.MALAnime):
        if self.filters_and:
            if "Movie" in self.filters and not anime.movie:
                return False
            if "TV" in self.filters and anime.movie:
                return False
            for tag in self.tag_filters:
                if tag not in anime.tags:
                    return False
            for score in self.score_filters:
                if anime.score != score:
                    return False
            return True
        else:
            if "Movie" in self.filters and anime.movie:
                return True
            if "TV" in self.filters and not anime.movie:
                return True
            for tag in self.tag_filters:
                if tag in anime.tags:
                    return True
            for score in self.score_filters:
                if anime.score == score:
                    return True
            return False

    def filter(self, parent: data.MALParent):
        if (
            len(self.filters + self.score_filters + self.tag_filters)
            + len(self.search_entry.texts)
            <= 0
        ):
            return True
        if len(self.search_entry.texts) > 0:
            has_search = self.search_entry.texts.replace("_", "").replace(
                " ", ""
            ) in parent.category.name.replace("_", "").replace(" ", "")
            if self.filters_and and not has_search:
                return self.filter_invert(False)
            if not self.filters_and and has_search:
                return self.filter_invert(True)
        alen = len(parent.animes)
        rlens = []
        if "Couple" in self.filters:
            rlens.append([2])
        if "Trilogy" in self.filters:
            rlens.append([3])
        if "Saga" in self.filters:
            rlens.append(range(4, 1000))
        for rlen in rlens:
            if self.filters_and and alen not in rlen:
                return self.filter_invert(False)
            if not self.filters_and and alen in rlen:
                return self.filter_invert(True)
        for anime in parent.animes.values():
            filtered = self.filter_anime(anime)
            if not filtered and self.filters_full:
                return self.filter_invert(False)
            if filtered and not self.filters_full:
                return self.filter_invert(True)
        return self.filter_invert(self.filters_full)

    def filter_invert(self, value):
        return value if self.filters_pos else not value

    def action_toggle_filter_op(self):
        self.filters_and = not self.filters_and

    def action_toggle_filter_full(self):
        self.filters_full = not self.filters_full

    def action_toggle_filter_sign(self):
        self.filters_pos = not self.filters_pos

    def action_toggle_size(self):
        self.appdata.mal_small = not self.appdata.mal_small

    def action_clear_filters(self):
        self.tag_filters = []
        self.score_filters = []
        self.filters = []
        self.search_entry.set_text("")

    def action_settings(self):
        self.app.menu = self.app.settings_menu
        self.mili.clear_memory()
        self.app.settings_back = self

    def action_toggle_filters(self):
        self.show_filters = not self.show_filters

    def action_back(self):
        self.action_clear_filters()

    def event(self, e: pygame.Event):
        if self.show_filters:
            self.search_entry.event(e)
        self.event_scroll(e, self.scroll_left, self.sl_rect)
        self.event_scroll(e, self.scroll_right, self.sr_rect)
        if e.type == pygame.KEYDOWN:
            if not self.search_entry.focused:
                if e.key == pygame.K_t:
                    self.action_toggle_filters()
                if e.key == pygame.K_a:
                    self.action_toggle_filter_op()
                if e.key == pygame.K_f:
                    self.action_toggle_filter_full()
                if e.key == pygame.K_s:
                    self.action_toggle_filter_sign()
                if e.key == pygame.K_c:
                    self.action_clear_filters()
                if e.key == pygame.K_f:
                    self.action_toggle_size()
            if e.key == pygame.K_ESCAPE:
                if self.show_filters:
                    self.show_filters = False
                    return
                if (
                    len(self.filters + self.tag_filters + self.score_filters)
                    + len(self.search_entry.texts)
                    > 0
                ):
                    self.action_clear_filters()
                    return
                self.app.menu = self.app.main_menu
                self.mili.clear_memory()
