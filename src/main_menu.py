import mili
from src import data
from src import common
from src import alert
from functools import partial


class MainMenu(common.UIComponent):
    name = "main"

    def ui(self):
        with self.mili.begin(None, {"fillx": True, "filly": True} | mili.CENTER):
            with self.mili.begin(None, mili.RESIZE | mili.X | mili.PADLESS):
                it = self.mili.element(
                    (0, 0, self.mult(80), self.mult(80)), {"update_id": "cursor"}
                )
                self.mili.image(
                    mili.icon.get_google("settings"),
                    {
                        "alpha": common.cond(it, *common.ALPHAS),
                        "cache": "auto",
                    },
                )
                if it.left_just_released:
                    self.app.menu = self.app.settings_menu
                    self.app.settings_back = None
                it = self.mili.element(
                    (0, 0, self.mult(80), self.mult(80)), {"update_id": "cursor"}
                )
                self.mili.image(
                    mili.icon.get_google("mal", (0, 0, 0, 0)),
                    {
                        "alpha": common.cond(it, *common.ALPHAS),
                        "cache": "auto",
                        "pad": "7",
                    },
                )
                if it.left_just_released:
                    self.app.menu = self.app.mal_menu
                    self.app.settings_back = None
            for tierlist in self.appdata.tierlists.values():
                with self.mili.begin(
                    None,
                    {"resizey": True, "fillx": True}
                    | mili.CENTER
                    | mili.PADLESS
                    | mili.X,
                ):
                    it = self.mili.element(None, {"fillx": "30", "update_id": "cursor"})
                    self.mili.rect(
                        {"color": (common.cond(it, *common.BTN_COLS) + 5,) * 3}
                    )
                    self.mili.text(
                        f"{tierlist.name.upper().replace('_', ' ')}",
                        {
                            "size": self.mult(27),
                            "cache": "auto",
                        },
                    )
                    if it.left_just_released:
                        if self.tierlist_sanity_check(tierlist):
                            self.open_tierlist(tierlist)
                    it = self.mili.element(
                        (0, 0, self.mult(40), self.mult(40)), {"update_id": "cursor"}
                    )
                    self.mili.rect({"color": (common.cond(it, *common.BTN_COLS),) * 3})
                    self.mili.image(
                        mili.icon.get_google("settings"),
                        {
                            "cache": "auto",
                            "alpha": common.cond(it, *common.ALPHAS),
                        },
                    )
                    if it.left_just_released:
                        if self.tierlist_sanity_check(tierlist, True):
                            self.open_tierlist(tierlist, True)
            it = self.mili.element(
                (0, 0, self.mult(60), self.mult(60)), {"update_id": "cursor"}
            )
            self.mili.image(
                mili.icon.get_google("add"),
                {
                    "alpha": common.cond(it, *common.ALPHAS),
                    "cache": "auto",
                },
            )
            if it.left_just_released:
                self.appdata.add_tierlist()

    def open_tierlist(self, tierlist: data.TierlistData, settings=False):
        self.app.tierlist = tierlist
        self.app.menu = self.app.tierlist_view
        self.app.menu.open()
        if settings:
            self.app.menu.action_settings()

    def tierlist_open_callback(self, tierlist, settings, buttonidx):
        if buttonidx == 1:
            return
        self.open_tierlist(tierlist, settings)

    def tierlist_sanity_check(self, tierlist: data.TierlistData, settings=False):
        for item in tierlist.tiers_all:
            category = self.appdata.categories.get(int(item.split("|")[0]), None)
            if category is None:
                alert.alert(
                    "Missing Components Warning",
                    f"This tierlist contains items whos category were not found. Opening it might result in data loss or crashes (the first error found is item {item} not having a category). Do you still wish to proceed?",
                    False,
                    ["Open", "Cancel"],
                    partial(self.tierlist_open_callback, tierlist, settings),
                )
                return False
            if item.split("|")[1] not in category.downloaded:
                alert.alert(
                    "Missing Components Warning",
                    f"This tierlist contains items that don't exist in their category. Opening it might result in data loss or crashes (the first error found is item {item.split('|')[1]} not existing in category {category.name}). Do you still wish to proceed?",
                    False,
                    ["Open", "Cancel"],
                    partial(self.tierlist_open_callback, tierlist, settings),
                )
                return False
        return True
