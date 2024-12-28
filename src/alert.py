from src import common
import mili


class AlertData:
    def __init__(self, system, title, details, error=True, options=None, callback=None):
        self.system = system
        self.title = title
        self.details = details
        self.error = error
        self.mili: mili.MILI = self.system.app.mili
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
                    "cache": mili.ImageCache.get_next_cache(),
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
                    },
                    (0, 0, parent.data.rect.w, 0),
                )
                with self.mili.begin(
                    None, mili.RESIZE | mili.PADLESS | mili.CENTER | mili.X
                ):
                    for i, option in enumerate(self.options):
                        it = self.mili.element(None, {"align": "center"})
                        self.mili.rect(
                            {"color": (common.cond(it, *common.BTN_COLS),) * 3}
                        )
                        self.mili.text(option, {"size": self.system.app.menu.mult(25)})
                        if it.left_just_released:
                            self.system.current_alert = None
                            if self.callback:
                                self.callback(i)


def alert(title, details, error=True, options=None, callback=None):
    print(title, details, sep=": ")
    _instance.alert(AlertData(_instance, title, details, error, options, callback))


_instance: "AlertSystem" = None


class AlertSystem:
    def __init__(self, app):
        self.app = app
        self.alerts = []
        self.current_alert = None
        global _instance
        _instance = self

    def alert(self, alert):
        self.alerts.append(alert)

    def update(self):
        if self.current_alert is not None:
            self.current_alert.ui()
            return False
        if len(self.alerts) > 0:
            alert = self.alerts.pop(0)
            self.current_alert = alert
            return False
        return True
