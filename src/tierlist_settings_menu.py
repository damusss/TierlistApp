import mili
import pygame
import os
import datetime
import json
from src import common
from src import entryline
from src import alert
from functools import partial


class TierlistSettingsMenu(common.UIComponent):
    name = "tierlist_settings"

    def init(self):
        self.scroll = mili.Scroll("tierlist_settings_scroll")
        self.name_entry = entryline.Entryline("Enter name...", lowercase=True)
        self.only_category_entry = entryline.Entryline(
            "Enter category name or leave blank...", lowercase=True
        )
        self.image_h_entry = entryline.Entryline(
            "Enter height in pixels...", True, (10, 1000), common.IMAGE_H
        )
        self.distribution_data_entry = entryline.Entryline(
            "Enter data...", False, None, common.DISTRIBUTION
        )
        self.copyfrom_entry = entryline.Entryline(
            "Enter tierlist name...", lowercase=True
        )
        self.settings_entries = {}

    def open(self):
        self.settings_entries = {}
        self.name_entry.set_text(self.tierlist.name)
        self.only_category_entry.set_text(self.tierlist.only_category)
        self.image_h_entry.set_text(self.tierlist.default_image_h)
        self.distribution_data_entry.set_text(self.tierlist.distribution_data)
        self.copyfrom_entry.set_text("")

    @property
    def tierlist(self):
        return self.app.tierlist

    def ui(self):
        with self.mili.begin(None, mili.CENTER | mili.FILL | mili.PADLESS):
            self.mili.text_element(
                "Tierlist Settings",
                {"size": self.mult(40), "cache": "auto"},
            )
            self.uicommon_back(self.app.tierlist_view)
            with self.mili.begin(
                None,
                {"default_align": "center"}
                | mili.FILL
                | {"update_id": "tierlist_settings_scroll"},
            ):
                self.ui_name()
                self.ui_only_category()
                self.ui_image_h()
                self.ui_distribution_color()
                self.ui_copy_from()
                self.ui_tiers_settings()
                self.ui_marked()
                self.mili.element((0, 0, 0, self.mult(10)))
                self.ui_action_btns()
                self.ui_help()

    def ui_help(self):
        self.mili.text_element(
            "Commands Help",
            {"size": self.mult(26), "cache": "auto"},
            None,
            {"offset": self.scroll.get_offset()},
        )
        with self.mili.begin(
            None, {"resizey": True, "fillx": "50", "offset": self.scroll.get_offset()}
        ):
            for helpstr in [
                "Toggle Show Category List: UI Button/T",
                "Toggle Show Numbers: UI Button/N",
                "Only Show Marked: UI Button/R",
                "Take Picture of Tierlist: UI Button/C",
                "Toggle Change Tierlist Menu: UI Button/Y",
                "Mark/Unmark (While Selected): UI Button/R",
                "Search (While Selected): UI Button/A",
                "Copy Image to Clipboard (While Selected): UI Button/I",
                "Auto Custom Character (While Selected): UI Button/L",
                "Select Item: Hold Right Click on Card",
                "Permanently Select Item: Double Right Click on Card",
                "Drag Item: Hold Left Click on Card",
                "Remove Item from Tier: Middle Click/SHIFT+Left Click",
                "Select Category: Left Click on Category Name",
                "Highlight Category: Hold Right Click on Category Name",
                "Permanently Highlight Category: Double Right Click on Category Name",
                "Zoom Cards: CTRL+Mouse Wheel",
                "Resize Category List: LEFT, RIGHT",
                "Resize Selected Category: CTRL + LEFT, RIGHT",
                "Resize Tier Name: SHIFT + LEFT, RIGHT",
                "ESC: Cancel Dragging -> Close Selected Item -> Remove Highlight/Numbers/Only Marked -> Close Selected Category -> Close Category List -> Save & Back to Main Menu",
            ]:
                with self.mili.begin(
                    None, mili.PADLESS | mili.X | {"resizey": True, "fillx": True}
                ):
                    align = [pygame.FONT_LEFT, pygame.FONT_RIGHT]
                    for i, string in enumerate(helpstr.split(":")):
                        it = self.mili.element(None, {"fillx": "50", "update_id": "cursor"})
                        self.mili.text(
                            string,
                            {
                                "size": self.mult(18),
                                "color": (180,) * 3,
                                "align": "left"
                                if align[i] == pygame.FONT_LEFT
                                else "right",
                                "font_align": align[i],
                                "growx": False,
                                "wraplen": it.data.rect.w,
                                "slow_grow": True,
                                "cache": "auto",
                            },
                        )

    def ui_marked(self):
        self.mili.text_element(
            "Marked Preview",
            {"size": self.mult(26), "cache": "auto"},
            None,
            {"offset": self.scroll.get_offset()},
        )
        if len(self.tierlist.marked) <= 0:
            self.mili.text_element(
                "No marked items yet...",
                {
                    "size": self.mult(19),
                    "color": (200,) * 3,
                    "cache": "auto",
                },
                None,
                {"offset": self.scroll.get_offset()},
            )
        with self.mili.begin(
            None,
            {
                "resizey": True,
                "fillx": "65",
                "spacing": 1,
                "pad": 1,
                "anchor": "center",
                "grid_align": "center",
                "axis": "x",
                "offset": self.scroll.get_offset(),
                "grid": True,
            },
        ):
            for name in list(self.tierlist.marked):
                image = self.appdata.images.get(
                    name, mili.icon.get_google(common.HOURGLASS)
                )
                it = self.mili.element((0, 0, 100 * self.appdata.image_ratio, 100), {"update_id": "cursor"})
                self.mili.image(
                    image,
                    {
                        "cache": "auto",
                        "alpha": common.cond(it, 255, 150, 60),
                    },
                )
                if it.left_just_released:
                    self.tierlist.marked.remove(name)

    def ui_tiers_settings(self):
        self.mili.text_element(
            "Tiers Settings",
            {"size": self.mult(26), "cache": "auto"},
            None,
            {"offset": self.scroll.get_offset()},
        )
        new_settings = []
        self.to_move_down = None
        self.to_move_up = None
        self.to_delete = None
        i = 0
        for i, settings in enumerate(list(self.tierlist.tiers_settings)):
            if len(self.tierlist.tiers) <= i:
                self.tierlist.tiers.append([])
            left_entry = self.get_settings_entry(i, settings["name"], "left")
            right_entry = self.get_settings_entry(i, settings["color"], "right")
            self.uicommon_color(
                left_entry,
                right_entry,
                [
                    (
                        30,
                        "light_mode" if settings["txtcol"] == "white" else "dark_mode",
                        lambda: settings.__setitem__(
                            "txtcol",
                            "white" if settings["txtcol"] == "black" else "black",
                        ),
                    ),
                    (30, "delete", lambda: setattr(self, "to_delete", i)),
                    (
                        30 if i > 0 else None,
                        "arrow_drop_up",
                        lambda: setattr(self, "to_move_up", i),
                    ),
                    (
                        30 if i < len(self.tierlist.tiers_settings) - 1 else None,
                        "arrow_drop_down",
                        lambda: setattr(self, "to_move_down", i),
                    ),
                    (
                        30
                        if i <= 0 or i >= len(self.tierlist.tiers_settings) - 1
                        else None,
                        None,
                        lambda: ...,
                    ),
                ],
                longer=True,
            )
            new_settings.append(
                {
                    "name": left_entry.texts,
                    "color": right_entry.texts,
                    "txtcol": settings["txtcol"],
                }
            )
            i += 1
        it = self.mili.element(
            (0, 0, self.mult(40), self.mult(40)), {"offset": self.scroll.get_offset(), "update_id": "cursor"}
        )
        self.mili.image(
            mili.icon.get_google("add", "white"),
            {
                "alpha": common.cond(it, *common.ALPHAS),
                "cache": "auto",
            },
        )
        if it.left_just_released:
            new_settings.append(
                {"name": "tier_name", "color": "white", "txtcol": "white"}
            )
        if self.to_move_down is not None:
            self.action_move_down(self.to_move_down, new_settings)
        if self.to_move_up is not None:
            self.action_move_up(self.to_move_up, new_settings)
        if self.to_delete is not None:
            self.action_delete_tier(self.to_delete, new_settings)
        self.tierlist.tiers_settings = new_settings.copy()

    def ui_action_btns(self):
        for txt, callback, col in [
            ("Create Backup", self.action_create_backup, "white"),
            (
                "Delete Tierlist",
                partial(
                    alert.alert,
                    f"Delete Tierlist {self.tierlist.name}",
                    "Are you sure you want to delete this tierlist? This action cannot be undone. Creating a backup is adviced before proceeding.",
                    False,
                    ["OK", "Cancel"],
                    self.action_delete_tierlist,
                ),
                "red",
            ),
        ]:
            it = self.mili.element(
                None, {"fillx": "30", "offset": self.scroll.get_offset(), "update_id": "cursor"}
            )
            self.mili.rect({"color": (common.cond(it, *common.BTN_COLS) + 5,) * 3})
            self.mili.text(
                txt,
                {
                    "size": self.mult(20),
                    "color": col,
                    "cache": "auto",
                },
            )
            if it.left_just_released:
                callback()

    def ui_name(self):
        self.uicommon_setting(
            "Name",
            self.name_entry,
            None,
            "name",
            "22",
            "46",
            buttons=[
                (
                    30,
                    "sync"
                    if self.name_entry.text.lower() != self.tierlist.name.lower()
                    else None,
                    partial(
                        self.appdata.rename_tierlist,
                        self.tierlist,
                        self.name_entry.text,
                        self.name_entry,
                    ),
                ),
            ],
            txtcol="yellow"
            if self.name_entry.text.lower() != self.tierlist.name.lower()
            else "white",
        )

    def ui_only_category(self):
        color = "white"
        if self.appdata.categories_uids.get(self.only_category_entry.texts, -1) == -1:
            color = "red"
        self.uicommon_setting(
            "Only Category",
            self.only_category_entry,
            self.tierlist,
            "only_category",
            "22",
            "46",
            buttons=[(30, "refresh", self.action_refresh_only_category)],
            txtcol=color,
        )

    def ui_image_h(self):
        prev = self.tierlist.default_image_h
        self.uicommon_setting(
            "Default Image Height",
            self.image_h_entry,
            self.tierlist,
            "default_image_h",
            "22",
            "46",
            buttons=[(30, "refresh", self.action_refresh_image_h)],
        )
        if self.tierlist.default_image_h != prev:
            self.app.tierlist_view.set_image_h(self.tierlist.default_image_h)

    def ui_distribution_color(self):
        self.uicommon_setting(
            "Distribution Data",
            self.distribution_data_entry,
            self.tierlist,
            "distribution_data",
            "22",
            "46",
            buttons=[(30, "refresh", self.action_refresh_distribution_data)],
        )

    def ui_copy_from(self):
        self.uicommon_setting(
            "Copy Tiers Settings From",
            self.copyfrom_entry,
            None,
            "",
            "22",
            "46",
            buttons=[(30, "check_circle", self.action_copy_from)],
        )

    def get_settings_entry(self, i, value, suffix):
        string = f"{i}_{suffix}"
        if string in self.settings_entries:
            return self.settings_entries[string]
        entry = entryline.Entryline(
            "Enter tier name..." if suffix == "left" else "Enter tier color...",
            False,
            None,
            value,
        )
        self.settings_entries[string] = entry
        return entry

    def action_copy_from(self):
        tierlist = self.appdata.tierlists.get(self.copyfrom_entry.texts, None)
        if tierlist is None:
            alert.alert(
                "Inexistent Tierlist Error",
                f"The tiers settings could not be copied from '{self.copyfrom_entry.texts}' because that tierlist doesn't exist. Did you make any typos?",
            )
            self.copyfrom_entry.set_text("")
            return
        self.copyfrom_entry.set_text("")
        self.settings_entries = {}
        for i, other_setting in enumerate(tierlist.tiers_settings):
            if i <= len(self.tierlist.tiers_settings) - 1:
                self.tierlist.tiers_settings[i] = other_setting.copy()
            else:
                self.tierlist.tiers_settings.append(other_setting.copy())
                self.tierlist.tiers.append([])

    def action_move_up(self, i, settings):
        ts = settings.pop(i)
        settings.insert(i - 1, ts)
        dt = self.tierlist.tiers.pop(i)
        self.tierlist.tiers.insert(i - 1, dt)
        self.settings_entries = {}

    def action_move_down(self, i, settings):
        ts = settings.pop(i)
        settings.insert(i + 1, ts)
        dt = self.tierlist.tiers.pop(i)
        self.tierlist.tiers.insert(i + 1, dt)
        self.settings_entries = {}

    def action_refresh_only_category(self):
        self.tierlist.only_category = ""
        self.only_category_entry.set_text("")

    def action_refresh_image_h(self):
        self.tierlist.default_image_h = common.IMAGE_H
        self.image_h_entry.set_text(common.IMAGE_H)

    def action_refresh_distribution_data(self):
        self.tierlist.distribution_data = common.DISTRIBUTION
        self.distribution_data_entry.set_text(common.DISTRIBUTION)

    def action_create_backup(self):
        now = datetime.datetime.now()
        date_str = (
            str(now).split(".")[0].replace("-", "_").replace(" ", "_").replace(":", "_")
        )
        path = f"backups/tierlist_{self.tierlist.name}_{date_str}"
        with open(path, "w", encoding="utf-8", errors="replace") as file:
            json.dump(self.tierlist.save(), file, default=common.fallback_serializer)
        alert.message(
            f"Backup created for {self.tierlist.name.upper().replace('_', ' ')}"
        )

    def action_delete_tier(self, i, settings):
        self.settings_entries = {}
        now = datetime.datetime.now()
        date_str = (
            str(now).split(".")[0].replace("-", "_").replace(" ", "_").replace(":", "_")
        )
        path = f"backups/tierlist_{self.tierlist.name}_autobackup_{date_str}"
        with open(path, "w", encoding="utf-8", errors="replace") as file:
            json.dump(self.tierlist.save(), file, default=common.fallback_serializer)
        alert.message(
            f"Since you deleted a tier, an irreversible action, a backup of the tierlist before this action has been created in '{path}'",
        )
        settings.pop(i)
        self.tierlist.tiers.pop(i)

    def action_delete_tierlist(self, btn_index):
        if btn_index == 1:
            return
        now = datetime.datetime.now()
        date_str = (
            str(now).split(".")[0].replace("-", "_").replace(" ", "_").replace(":", "_")
        )
        path = f"backups/tierlist_{self.tierlist.name}_autobackup_{date_str}"
        with open(path, "w", encoding="utf-8", errors="replace") as file:
            json.dump(self.tierlist.save(), file, default=common.fallback_serializer)
        alert.message(
            f"Since you deleted the tierlist, an irreversible action, a backup of it before this action has been created in '{path}'",
        )
        self.app.menu = self.app.main_menu
        self.appdata.tierlists.pop(self.tierlist.name, None)
        if os.path.exists(f"user_data/tierlists/{self.tierlist.name}.json"):
            os.remove(f"user_data/tierlists/{self.tierlist.name}.json")

    def can_back(self):
        return self.app.tierlist.name.lower() == self.name_entry.text

    def action_back(self):
        self.tierlist.save_file()

    def event(self, e):
        self.event_scroll(e)
        self.name_entry.event(e)
        self.only_category_entry.event(e)
        self.image_h_entry.event(e)
        self.distribution_data_entry.event(e)
        self.copyfrom_entry.event(e)
        for entry in self.settings_entries.values():
            entry.event(e)
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                if self.can_back():
                    self.app.menu = self.app.tierlist_view
