import pygame
import mili
import json
import os
import typing
from src import entryline


if typing.TYPE_CHECKING:
    from main import TierlistApp

BG_COL = (15,) * 3
ANIMES_UID = 0
ALPHAS = 160, 255, 100
BTN_COLS = 15, 30, 10
DOWNLOAD_SLEEP = 0.8
SURF = pygame.Surface((10, 10), pygame.SRCALPHA)
IMAGE_H = 70
DOUBLE_CLICK_TIME = 300
HOURGLASS = "hourglass_top"
DISTRIBUTION = "50-100,5-180,180|0.25"
THREADED = True
RATED_NAMES = {
    10: "Masterpiece (10/10)",
    9.5: "Peak (9.5/10)",
    9: "Great (9/10)",
    8: "Good (8/10)",
    7: "Alright (7/10)",
    6: "Decent (6/10)",
    5: "Bad (<=5/10)",
    2: "Dogshit (2/10)",
    0: "Unrated (-/10)",
}
RATED_NAMES_SHORT = {
    10: "Masterpiece",
    9.5: "Peak",
    9: "Great",
    8: "Good",
    7: "Alright",
    6: "Decent",
    5: "Bad",
    2: "Dogshit",
    0: "Unrated",
}
RATED_COLORS = {
    10: "#FFC000",
    9.5: "#ce8100",
    9: "#BE93E4",
    8: "#17B169",
    7: "#6CB4EE",
    6: "#fd5c63",
    5: "#ff0000",
    2: "#8b0000",
    0: "white",
}


def fallback_serializer(obj):
    if isinstance(obj, set):
        return list(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def cond(it, normal, hover, press, abs=False):
    if it.left_pressed:
        return press
    if it.hovered or (abs and it.absolute_hover):
        return hover
    return normal


def load_json(rel_path, default):
    path = f"user_data/{rel_path}"
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8", errors="replace") as file:
            json.dump(default, file, default=fallback_serializer)
        return default
    with open(path, "r", encoding="utf-8", errors="replace") as file:
        data = default.copy()
        data.update(json.loads(file.read()))
        return data


def write_json(rel_path, data):
    path = f"user_data/{rel_path}"
    with open(path, "w", encoding="utf-8", errors="replace") as file:
        json.dump(data, file, default=fallback_serializer)


class UIComponent:
    name: str

    def __init__(self, app: "TierlistApp"):
        self.app = app
        self.mili = self.app.mili
        self.appdata = self.app.data
        self.scroll = None
        self.init()

    def init(self): ...

    def update(self): ...

    def ui(self): ...

    def event(self, e): ...

    def event_scroll(
        self, e, scroll: mili.Scroll | None = None, rect: pygame.Rect = None
    ):
        if e.type == pygame.MOUSEWHEEL:
            if scroll is None:
                scroll = self.scroll
            if rect is None or rect.collidepoint(pygame.mouse.get_pos()):
                scroll.scroll(0, -e.y * 40)

    def uicommon_back(self, menu_back):
        it = self.mili.element(
            (0, 0, self.mult(30), self.mult(30)),
            {"ignore_grid": True, "z": 9999, "update_id": "cursor"},
        )
        self.mili.rect({"color": (cond(it, *BTN_COLS),) * 3})
        self.mili.image(
            mili.icon.get_google("arrow_back", "white"),
            {"alpha": cond(it, *ALPHAS), "cache": "auto"},
        )
        if it.left_just_released:
            if self.can_back():
                self.action_back()
                self.mili.clear_memory()
                self.app.menu = menu_back

    def uicommon_top_btn(self, iconname, side, callback, offset=0, othercallback=None):
        mult30 = self.mult(30)
        it = self.mili.element(
            (
                mult30 * offset
                if side == "left"
                else self.app.window.size[0] - (mult30 * (offset + 1)),
                0,
                mult30,
                mult30,
            ),
            {"ignore_grid": True, "z": 9999, "update_id": "cursor"},
        )
        self.mili.rect({"color": (cond(it, *BTN_COLS),) * 3})
        self.mili.image(
            mili.icon.get_google(iconname),
            {"alpha": cond(it, *ALPHAS), "cache": "auto"},
        )
        if it.left_just_released:
            if callback:
                callback()
            elif othercallback:
                othercallback()

    def get_title(self):
        return f"Tierlist App (FPS:{self.app.clock.get_fps():.0f})"

    def can_back(self):
        return True

    def action_back(self): ...

    def can_exit(self):
        return self.can_back()

    def uicommon_color(
        self,
        left_entry: entryline.Entryline,
        right_entry: entryline.Entryline,
        buttons=None,
        scroll=None,
        small=False,
        longer=False,
    ):
        if scroll is None:
            scroll = self.scroll
        left_entry.update()
        right_entry.update()
        with self.mili.begin(
            None,
            {
                "fillx": "100" if small else "40",
                "resizey": True,
                "default_align": "center",
                "anchor": "center",
                "offset": scroll.get_offset() if scroll else (0, 0),
            }
            | mili.X
            | mili.PADLESS,
        ):
            self.mili.element(None)
            left_entry.ui(
                self.mili,
                (0, 0, 0, self.mult(35)),
                {"fillx": "55" if longer else "45"},
                self.mult,
                txtcol="white",
            )
            col = self.appdata.get_color(right_entry.texts)
            right_entry.ui(
                self.mili,
                (0, 0, 0, self.mult(35)),
                {"fillx": "55" if longer else "45"},
                self.mult,
                txtcol=("white" if col is not None else "red"),
            )
            self.mili.image_element(
                pygame.Surface((10, 10), pygame.SRCALPHA),
                {
                    "fill": True,
                    "fill_color": col if col else 0,
                    "alpha": 255 if col else 0,
                },
                (0, 0, self.mult(35), self.mult(35)),
            )
            self.uicommon_buttons(buttons)

    def uicommon_setting(
        self,
        text,
        entryline_: entryline.Entryline,
        obj,
        varname,
        entryfillx="50",
        namefillx="50",
        buttons=None,
        txtcol="white",
        namecol="white",
        entrysize=None,
        scroll=None,
        post_txt=None,
        post_style=None,
        clickable=False,
        rightclickable=False,
    ):
        if scroll is None:
            scroll = self.scroll
        entryline_.update()
        with self.mili.begin(
            None,
            {
                "fillx": True,
                "resizey": True,
                "default_align": "center",
                "offset": scroll.get_offset() if scroll else (0, 0),
                "update_id": "cursor" if clickable else None,
            }
            | mili.X
            | mili.PADLESS,
        ) as cont:
            cdata = cont.data
            if cdata.absolute_rect.bottom < 0 or cdata.absolute_rect == (0, 0, 0, 0):
                self.mili.element((0, 0, 0, self.mult(40)))
                entryline_.entry_rect = pygame.Rect()
                entryline_.focused
                return cdata
            self.mili.text_element(
                text,
                {
                    "size": 20,
                    "align": "right",
                    "font_align": pygame.FONT_RIGHT,
                    "color": namecol,
                    "cache": "auto",
                },
                None,
                {"fillx": namefillx, "blocking": False},
            )
            entryline_.ui(
                self.mili,
                (0, 0, 0, self.mult(40)),
                {"fillx": entryfillx},
                self.mult,
                txtcol=txtcol,
                txtsize=entrysize,
            )
            if obj:
                if isinstance(varname, str):
                    if entryline_.only_numbers:
                        if entryline_.texts != "":
                            setattr(
                                obj,
                                varname,
                                pygame.math.clamp(
                                    (
                                        float
                                        if isinstance(entryline_.minmax[0], float)
                                        else int
                                    )(entryline_.texts),
                                    *entryline_.minmax,
                                ),
                            )
                    else:
                        setattr(obj, varname, entryline_.texts)
                else:
                    try:
                        obj[varname] = entryline_.texts
                    except IndexError:
                        ...
            entryline_.trigger_callback()
            self.uicommon_buttons(buttons)
            if post_txt:
                self.mili.text_element(
                    post_txt,
                    post_style | {"cache": "auto"},
                    None,
                    {"blocking": False, "fillx": "20"},
                )
            if clickable or rightclickable:
                if cont.hovered:
                    self.mili.rect(
                        {"color": (BG_COL[0] + 5,) * 3, "element_id": cdata.id}
                    )
                if clickable and cont.left_just_released:
                    clickable()
                if rightclickable and cont.just_released_button == pygame.BUTTON_RIGHT:
                    rightclickable()
        return cdata

    def uicommon_buttons(self, buttons):
        if buttons is not None:
            for size, iconname, onclick in buttons:
                if size is None:
                    continue
                if onclick == "color":
                    surf = pygame.Surface((size, size), pygame.SRCALPHA)
                    col = self.appdata.get_color(iconname)
                    if col is None:
                        col = (0, 0, 0, 0)
                    self.mili.image_element(
                        surf,
                        {
                            "fill_color": col,
                            "fill": True,
                            "cache": "auto",
                        },
                        (0, 0, size, size),
                    )
                else:
                    it = self.mili.element(
                        (0, 0, self.mult(size), self.mult(size)),
                        {"update_id": "cursor"},
                    )
                    if iconname is not None:
                        self.mili.rect({"color": (cond(it, *BTN_COLS),) * 3})
                    self.mili.image(
                        SURF
                        if iconname is None
                        else mili.icon.get_google(iconname, "white"),
                        {
                            "alpha": cond(it, *ALPHAS),
                            "cache": "auto",
                        },
                    )
                    if it.left_just_released and iconname is not None:
                        onclick()

    def mult(self, a):
        return self.app.mult(a)
