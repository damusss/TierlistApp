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
        self.parent = None
        self.parent_cache = mili.ImageCache()
        self.parent_fullscreen = False
        self.layer_cache = mili.ImageLayerCache(
            self.mili, (self.app.window.size[0], self.app.window.size[1] - 30), (0, 30)
        )
        self.entrylines = {
            label: mili.EntryLine(
                "-",
                {
                    "bg_rect_style": {"color": (25,) * 3},
                    "outline_rect_style": {
                        "color": (40,) * 3,
                        "outline": 1,
                        "draw_above": True,
                    },
                    "text_anchor": "right",
                },
            )
            for label in common.SCORE_CATEGORIES
        }

    def update(self):
        self.search_entry.update()
        self.prev_count = self.count
        self.count = 0
        self.layer_cache.active = True

    def get_title(self):
        return f"{self.appdata.mal_username}'s Anime List (FPS:{self.app.clock.get_fps():.0f})"

    def ui(self):
        if not self.parent_fullscreen or self.parent is None:
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
                    },
                ) as rcond:
                    self.mili.image_layer_renderer(self.layer_cache)
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
        if self.parent is not None:
            self.layer_cache.active = False
            self.mili.id_checkpoint(500 * 1000)
            self.ui_parent(rcond.data.rect.size)

    def ui_parent(self, size):
        color = common.RATED_COLORS[self.parent.score]
        bar_col = {
            "completed": (25,) * 3,
            "watching": "#002203",
            "reading": "#002203",
            "dropped": "#270109",
            "on-hold": "#282000",
            "plan_to_watch": "gray30",
        }[self.parent.status]
        with self.mili.begin(
            ((0, 0), self.app.window.size if self.parent_fullscreen else size),
            {"ignore_grid": True, "update_id": "cursor"}
            | mili.CENTER
            | mili.PADLESS
            | ({"parent_id": 0} if self.parent_fullscreen else {}),
        ) as shadow:
            self.mili.image(
                common.SURF,
                {"cache": "auto", "alpha": 230, "fill": True, "fill_color": "black"},
            )
            if shadow.left_clicked:
                self.parent = None
                return
            with self.mili.begin(
                None,
                {
                    "fillx": "100" if self.parent_fullscreen else "85",
                    "filly": "100" if self.parent_fullscreen else "85",
                    "axis": "x",
                    "pad": 5,
                    "spacing": 1,
                },
            ) as cont:
                self.mili.rect(
                    {
                        "color": (20,) * 3,
                        "border_radius": 0 if self.parent_fullscreen else "2",
                    }
                )
                ret = self.ui_parent_close(cont)
                if ret:
                    return
                h = cont.data.rect.h - cont.data.grid.pady * 2
                w = h * self.appdata.image_ratio
                image = self.appdata.images.get(f"0|{self.parent.category.name}", None)
                if image is None:
                    image = mili.icon.get_google(common.HOURGLASS)
                self.mili.image_element(
                    image,
                    {"cache": self.parent_cache, "border_radius": "2"},
                    (0, 0, w, h),
                )
                with self.mili.begin(None, mili.FILL) as right:
                    self.ui_anime_name(self.parent, color, right.data.rect.w, 43)
                    self.mili.element(None, {"filly": "3"})
                    self.ui_parent_infobar(color, bar_col, right)
                    if self.parent.best_char is None:
                        self.ui_parent_scores()
                    else:
                        with self.mili.begin(
                            None,
                            {
                                "filly": True,
                                "fillx": True,
                                "pad": 0,
                                "align": "center",
                                "default_align": "center",
                                "anchor": "center",
                                "axis": "x",
                            },
                        ):
                            self.ui_parent_scores()
                            image = self.appdata.images.get(self.parent.best_char, None)
                            if image:
                                iheight = cont.data.rect.h / (2.2 if not self.parent_fullscreen else 1.8)
                                iw = self.appdata.image_ratio * iheight
                                with self.mili.begin(
                                    None,
                                    {
                                        "resizex": True,
                                        "filly": True,
                                        "pad": 0,
                                        "default_align": "center",
                                        "anchor": "center"
                                    },
                                ):
                                    self.mili.text_element(
                                        self.parent.category.format_item_name(
                                            self.parent.best_char.split("|")[-1]
                                        ).replace("_", " "), {"size": self.mult(20), "color": common.RATED_COLORS[10]}
                                    )
                                    self.mili.image_element(
                                        image,
                                        {"smoothscale": True, "cache": "auto"},
                                        (0, 0, iw, iheight),
                                    )
                    if len(self.parent.animes) > 1:
                        self.ui_parent_animes()

    def ui_parent_scores(self):
        if self.show_filters:
            return
        with self.mili.begin(
            None,
            {
                "fillx": "60" if self.parent.best_char is None else "85",
                "filly": True,
                "axis": "x",
                "pady": 0,
                "align": "center",
                "default_align": "center",
                "anchor": "center",
            },
        ):
            for half in [
                common.SCORE_CATEGORIES[: len(common.SCORE_CATEGORIES) // 2],
                common.SCORE_CATEGORIES[len(common.SCORE_CATEGORIES) // 2 :],
            ]:
                with self.mili.begin(None, {"fillx": True, "resizey": True, "pad": 0}):
                    for label in half:
                        cur_label = self.parent.category.score_categories.get(
                            label, "-"
                        )
                        entry = self.entrylines[label]
                        if cur_label == "-":
                            color = "white"
                        else:
                            try:
                                if "." in cur_label:
                                    intlabel = float(cur_label)
                                else:
                                    intlabel = int(cur_label)
                                color = common.RATED_COLORS[intlabel]
                            except Exception:
                                color = "white"
                        with self.mili.begin(
                            None,
                            {
                                "fillx": True,
                                "resizey": True,
                                "pad": 0,
                                "spacing": 1,
                                "axis": "x",
                                "default_align": "center",
                            },
                        ):
                            h = self.mult(35)
                            self.mili.circle_element(
                                {
                                    "color": (120,) * 3,
                                    "antialias": True,
                                    "pad": self.mult(15),
                                },
                                (0, 0, h, h),
                            )
                            self.mili.text_element(
                                common.SCORE_CATEGORIES_LABELS[label],
                                {"size": self.mult(20)},
                            )
                            self.mili.element(None, {"fillx": True})
                            self.mili.image_element(
                                mili.icon.get_google("star", color),
                                {"pad": self.mult(6)},
                                (0, 0, h, h),
                            )
                            with self.mili.begin(
                                (0, 0, self.mult(50), h),
                            ) as econt:
                                entry.style["text_style"] = {"color": color}
                                entry.ui(econt)
                                if entry.text_strip != cur_label:
                                    self.parent.category.score_categories[label] = (
                                        entry.text_strip
                                    )
                            self.mili.text_element(
                                "/10",
                                {
                                    "size": self.mult(22),
                                    "color": color,
                                    "font_align": pygame.FONT_RIGHT,
                                    "align": "right",
                                },
                            )

    def ui_parent_infobar(self, color, bar_col, right):
        with self.mili.begin(
            None, {"fillx": True, "resizey": True, "padx": 0, "pady": 10}
        ):
            self.mili.rect({"color": bar_col, "border_radius": "5"})
            self.ui_anime_infobar(
                self.parent,
                bar_col,
                right.data.rect.w,
                25,
                35,
                add_score=True,
                col=color,
            )
            self.mili.element((0, 0, 0, self.mult(30)))
            self.mili.text_element(
                "  ".join([f"#{tag}" for tag in self.parent.tags]),
                {
                    "color": (120,) * 3,
                    "size": self.mult(20),
                    "wraplen": right.data.rect.w / 1.5,
                    "slow_grow": True,
                },
                None,
                {"fillx": True},
            )

    def ui_parent_close(self, cont):
        with self.mili.element(
            pygame.Rect(0, 0, self.mult(30), self.mult(30)).move_to(
                topright=(cont.data.rect.w - 5, 5)
            ),
            {"ignore_grid": True, "z": 9999, "update_id": "cursor"},
        ) as cbtn:
            self.mili.rect(
                {
                    "color": (common.cond(cbtn, 25, 40, 20),) * 3,
                    "border_radius": "50",
                }
            )
            self.mili.image(mili.icon.get_google("close"), {"pad": 2})
            if cbtn.left_clicked:
                self.parent = None
                return True
        return False

    def ui_parent_animes(self):
        with self.mili.begin(
            None,
            {"fillx": True, "resizey": True, "axis": "x"} | mili.CENTER,
        ):
            self.mili.rect({"color": (25,) * 3, "border_radius": "5"})
            animes_sorted = sorted(self.parent.animes.items(), key=lambda i: i[0])
            for i, (_, anime) in enumerate(animes_sorted):
                self.ui_anime_anime(anime, self.parent, self.mult(150), i, 16, 12)

    def ui_anime(self, parent: data.MALParent):
        self.count += 1
        H = self.mult(280)
        if self.appdata.mal_small:
            H = self.mult(120)
        diff = 0.3
        if self.app.window.size[0] < 1800:
            diff = 0.5
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
                    - diff
                ),
                "axis": "x",
                "pad": 0,
                "spacing": 0,
                "update_id": "cursor",
                "blocking": True,
            },
        ) as main:
            if main.left_clicked:
                self.parent = parent
                self.parent_update_entries()
            r = main.data.absolute_rect
            if r.top >= self.app.window.size[1] or r.bottom <= self.mult(30):
                return
            color = common.RATED_COLORS[parent.score]
            bar_col = {
                "completed": (25,) * 3,
                "watching": "#002203",
                "reading": "#002203",
                "dropped": "#270109",
                "on-hold": "#282000",
                "plan_to_watch": "gray30",
            }[parent.status]
            br = "0"
            image = self.appdata.images.get(f"0|{parent.category.name}", None)
            if image is None:
                image = mili.icon.get_google(common.HOURGLASS)
            self.mili.rect({"color": (20,) * 3, "border_radius": br})
            self.mili.image_element(
                image,
                {
                    "cache": "auto",
                    "layer_cache": None if self.parent else self.layer_cache,
                },
                (0, 0, H * self.appdata.image_ratio, H),
                {"blocking": False},
            )
            with self.mili.begin(
                ((0, 0), (r.size[0] - H * self.appdata.image_ratio, r.size[1])),
                mili.PADLESS
                | {"spacing": 0, "anchor": "max_spacing", "blocking": False},
            ) as cont:
                w = cont.data.rect.w
                self.ui_anime_name(parent, color, w)
                self.mili.element(None, {"filly": "10", "blocking": False})
                self.ui_anime_infobar(parent, bar_col, w)
                if not self.appdata.mal_small:
                    self.mili.element(None, {"filly": True, "blocking": False})
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
                "blocking": False,
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
                    "blocking": False,
                },
            ):
                for _, anime in animes_sorted[first_batch:]:
                    self.ui_anime_anime(anime, parent, H, i)
                    i += 1

    def ui_anime_anime(
        self, anime: data.MALAnime, parent: data.MALParent, H, i, ssize=13, stsize=10
    ):
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
                    "blocking": False,
                }
                | mili.CENTER,
            ):
                self.mili.image_element(
                    mili.icon.get_google("star", color=color),
                    {"cache": "auto"},
                    (0, 0, self.mult(stsize), self.mult(stsize)),
                    {"blocking": False},
                )
                self.mili.text_element(
                    f"{anime.score if anime.score != 0 else '-'}  ",
                    {
                        "size": self.mult(ssize),
                        "color": color,
                        "padx": 0,
                        "pady": 1,
                        "bold": True,
                        "cache": "auto",
                    },
                    None,
                    {"blocking": False},
                )
            image = self.appdata.images.get(
                f"original_0|{parent.category.name}{f'_{i + 1}' if i > 0 else ''}", None
            )
            if image is None:
                image = mili.icon.get_google(common.HOURGLASS)
            self.mili.image_element(
                image,
                {
                    "cache": "auto",
                    "layer_cache": None if self.parent else self.layer_cache,
                    "fill": True,
                },
                (0, 0, H * self.appdata.image_ratio, H),
                {"blocking": False},
            )

    def ui_anime_infobar(
        self,
        parent: data.MALParent,
        bar_col,
        w,
        size=18,
        h=30,
        add_score=False,
        col=None,
    ):
        with self.mili.begin(
            (0, 0, w, self.mult(h)),
            {
                "fillx": True,
                "axis": "x",
                "spacing": 0,
                "anchor": "max_spacing",
                "blocking": False,
            }
            | mili.CENTER,
        ):
            self.mili.rect({"color": bar_col})
            self.mili.text_element(
                f"#{parent.global_i}",
                {"size": self.mult(size), "bold": True, "cache": "auto"},
                None,
                {"blocking": False},
            )
            self.mili.element(None, {"fillx": True, "blocking": False})
            if add_score:
                self.mili.image_element(
                    mili.icon.get_google("star", col),
                    {},
                    (0, 0, self.mult(h - 10), self.mult(h - 10)),
                    {"blocking": False},
                )
                self.mili.text_element(
                    f"{parent.score}/10",
                    {"size": self.mult(size), "color": col},
                    None,
                    {"blocking": False},
                )
                self.mili.element(None, {"fillx": True, "blocking": False})
            if parent.elapsed_time is not None:
                self.mili.text_element(
                    f"{parent.elapsed_time} Day{'s' if parent.elapsed_time > 1 else ''}",
                    {"size": self.mult(size - 2), "color": (150,) * 3, "cache": "auto"},
                    None,
                    {"blocking": False},
                )
                self.mili.element(None, {"fillx": True, "blocking": False})
            self.mili.image_element(
                mili.icon.get_google("movie"),
                {"cache": "auto", "alpha": 190},
                (0, 0, self.mult(22), self.mult(22)),
                {"blocking": False},
            )
            self.mili.text_element(
                f"{parent.episodes_str.replace(' + ', ('+' if self.appdata.mal_small else ' + '))}",
                {"size": self.mult(size), "cache": "auto"},
                None,
                {"blocking": False},
            )

    def ui_anime_name(self, parent: data.MALParent, color, w, size=22):
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
                "size": self.mult(size),
                "slow_grow": True,
                "growx": False,
                "color": color,
                "wraplen": "100",
                "cache": "auto",
            },
            (0, 0, w, 0),
            {"blocking": False},
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
                "offset": self.scroll_right.get_offset(),
            },
        ) as it:
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
            (
                "Filters",
                self.filters,
                [
                    "TV",
                    "Movie",
                    "Manga",
                    "Couple",
                    "Trilogy",
                    "Saga",
                    "Watching",
                    "Reading",
                    "Dropped",
                    "On Hold",
                ],
            ),
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
                adder = 0 if len(totlist) % 2 == 0 else 1
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

    def parent_update_entries(self):
        for label, entry in self.entrylines.items():
            entry.text = self.parent.category.score_categories.get(label, "-")

    def filter_anime(self, anime: data.MALAnime):
        if self.filters_and:
            if "Movie" in self.filters and not anime.movie:
                return False
            if "Manga" in self.filters and not anime.manga:
                return False
            if "TV" in self.filters and anime.movie:
                return False
            for status in ["Watching", "Reading", "Dropped", "On Hold"]:
                if (
                    status in self.filters
                    and anime.status != status.replace(" ", "_").lower()
                ):
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
            if "Manga" in self.filters and anime.manga:
                return True
            if "TV" in self.filters and not anime.movie:
                return True
            for status in ["Watching", "Reading", "Dropped", "On Hold"]:
                if (
                    status in self.filters
                    and anime.status == status.replace(" ", "_").lower()
                ):
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
        self.parent = None

    def action_back(self):
        self.action_clear_filters()

    def event(self, e: pygame.Event):
        if self.show_filters:
            self.search_entry.event(e)
        self.event_scroll(e, self.scroll_left, self.sl_rect)
        focused = False
        if self.parent is None:
            self.event_scroll(e, self.scroll_right, self.sr_rect)
        else:
            for entry in self.entrylines.values():
                entry.event(e)
                if entry.focused:
                    focused = True
        if e.type == pygame.KEYDOWN:
            if not self.search_entry.focused and not focused:
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
            if e.key == pygame.K_F11:
                self.parent_fullscreen = not self.parent_fullscreen
            if e.key == pygame.K_ESCAPE:
                if self.parent:
                    self.parent = None
                    return
                if self.show_filters:
                    self.show_filters = False
                    self.parent = None
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
