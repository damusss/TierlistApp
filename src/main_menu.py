import mili
import pygame
from src import common


class MainMenu(common.UIComponent):
    name = "main"

    def ui(self):
        with self.mili.begin(None, {"fillx": True, "filly": True} | mili.CENTER):
            it = self.mili.element((0, 0, self.mult(80), self.mult(80)))
            self.mili.image(
                mili.icon.get_google("settings"),
                {
                    "alpha": common.cond(it, *common.ALPHAS),
                    "cache": "auto",
                },
            )
            if it.left_just_released:
                self.app.menu = self.app.settings_menu
            for tierlist in self.appdata.tierlists.values():
                with self.mili.begin(
                    None,
                    {"resizey": True, "fillx": True}
                    | mili.CENTER
                    | mili.PADLESS
                    | mili.X,
                ):
                    it = self.mili.element(None, {"fillx": "30"})
                    self.mili.rect(
                        {"color": (common.cond(it, *common.BTN_COLS) + 5,) * 3}
                    )
                    self.mili.text(
                        f"{tierlist.name.upper().replace("_", " ")}",
                        {
                            "size": self.mult(27),
                            "cache": "auto",
                        },
                    )
                    if it.left_just_released:
                        self.app.tierlist = tierlist
                        self.app.menu = self.app.tierlist_view
                        self.app.menu.open()
                    it = self.mili.element((0, 0, self.mult(40), self.mult(40)))
                    self.mili.rect({"color": (common.cond(it, *common.BTN_COLS),) * 3})
                    self.mili.image(
                        mili.icon.get_google("settings"),
                        {
                            "cache": "auto",
                            "alpha": common.cond(it, *common.ALPHAS),
                        },
                    )
                    if it.left_just_released:
                        self.app.tierlist = tierlist
                        self.app.menu = self.app.tierlist_view
                        self.app.menu.open()
                        self.app.menu.action_settings()
            it = self.mili.element((0, 0, self.mult(60), self.mult(60)))
            self.mili.image(
                mili.icon.get_google("add"),
                {
                    "alpha": common.cond(it, *common.ALPHAS),
                    "cache": "auto",
                },
            )
            if it.left_just_released:
                self.appdata.add_tierlist()
