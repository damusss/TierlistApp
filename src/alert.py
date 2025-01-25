from src import common
import mili
import pygame


class AlertData:
    def __init__(self, system, title, details, error=True, options=None, callback=None):
        self.system = system
        self.title = title
        self.details = details
        self.error = error
        self.mili: mili.MILI = self.system.mili
        if options is None:
            options = ["OK"]
        self.options = options
        self.callback = callback

    def ui(self):
        with self.mili.begin(
            ((0, 0), self.system.app.window.size),
            mili.CENTER | mili.PADLESS | {"ignore_grid": True},
        ):
            self.mili.image(
                common.SURF,
                {
                    "alpha": 180,
                    "fill": True,
                    "fill_color": "black",
                    "cache": "auto",
                },
            )
            with self.mili.begin(
                None, {"fillx": "30", "filly": "30", "anchor": "max_spacing"}
            ) as parent:
                self.mili.rect({"color": (20,) * 3, "border_radius": "5"})
                self.mili.text_element(
                    self.title,
                    {
                        "size": self.system.app.menu.mult(30),
                        "color": "red" if self.error else "white",
                        "align": "center",
                        "cache": "auto",
                    },
                    None,
                    {"align": "center"},
                )
                self.mili.text_element(
                    self.details,
                    {
                        "size": self.system.app.menu.mult(20),
                        "color": "white",
                        "wraplen": "100",
                        "slow_grow": True,
                        "growx": False,
                        "cache": "auto",
                    },
                    (0, 0, parent.data.rect.w, 0),
                )
                with self.mili.begin(
                    None, mili.RESIZE | mili.PADLESS | mili.CENTER | mili.X
                ):
                    for i, option in enumerate(self.options):
                        it = self.mili.element(None, {"align": "center", "update_id": "cursor"})
                        self.mili.rect(
                            {"color": (common.cond(it, *common.BTN_COLS),) * 3}
                        )
                        self.mili.text(
                            option,
                            {
                                "size": self.system.app.menu.mult(25),
                                "cache": "auto",
                            },
                        )
                        if it.left_just_released:
                            self.system.current_alert = None
                            if self.callback:
                                self.callback(i)


def alert(title, details, error=True, options=None, callback=None):
    print(title, details, sep=": ")
    _instance.alerts.append(
        AlertData(_instance, title, details, error, options, callback)
    )


def message(message):
    print(f"[info] {message}")
    _instance.messages.append(message)


_instance: "AlertSystem" = None


class AlertSystem:
    def __init__(self, app):
        self.app: "common.TierlistApp" = app
        self.mili: mili.MILI = app.mili
        self.alerts = []
        self.messages = []
        self.current_message = None
        self.current_alert = None
        self.message_start = 0
        global _instance
        _instance = self

    def ui_message(self):
        if self.current_message is None:
            return
        r = pygame.Rect(
            0, 0, self.app.window.size[0] * 0.15, self.app.window.size[1] * 0.07
        ).move_to(
            midbottom=(
                self.app.window.size[0] / 2,
                self.app.window.size[1] - self.app.mult(50),
            )
        )
        with self.mili.begin(r, {"ignore_grid": True, "z": 99999, "parent_id": 0}):
            self.mili.rect(
                {"border_radius": "7", "color": (common.BG_COL[0] + 10,) * 3}
            )
            perc = (pygame.time.get_ticks() - self.message_start) / 3000
            self.mili.rect(
                {
                    "border_radius": "7",
                    "color": (50,) * 3,
                    "outline": 2,
                    "dash_size": [str((1 - perc) * 100), str(perc * 100)],
                }
            )
            self.mili.text(
                self.current_message,
                {
                    "wraplen": "92",
                    "align": "center",
                    "font_align": pygame.FONT_CENTER,
                    "slow_grow": True,
                    "size": self.app.mult(20),
                    "growx": False,
                    "pady": 5,
                },
            )

    def update(self):
        if self.current_message is not None:
            if pygame.time.get_ticks() - self.message_start >= 3000:
                self.current_message = None
        else:
            if len(self.messages) > 0:
                self.current_message = self.messages.pop(0)
                self.message_start = pygame.time.get_ticks()
        if self.current_alert is not None:
            self.current_alert.ui()
            return False
        if len(self.alerts) > 0:
            alert = self.alerts.pop(0)
            self.current_alert = alert
            return False
        return True
