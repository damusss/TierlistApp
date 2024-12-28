import os
import pygame
import threading
import time
import requests
import bs4
import random
import shutil
import datetime
import pathlib
from src import common
from src import alert

for folder in ["user_data", "backups", "custom_chars"]:
    if not os.path.exists(folder):
        os.mkdir(folder)
for folder in ["tierlists", "categories", "screenshots"]:
    if not os.path.exists(f"user_data/{folder}"):
        os.mkdir(f"user_data/{folder}")


def request_wrapper(action_message, *args, **kwargs):
    try:
        response = requests.get(*args, **kwargs)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        return alert.alert("Connection/Network Error", action_message)
    except requests.exceptions.Timeout:
        return alert.alert("Timeout Error", action_message)
    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 404:
            return alert.alert("404 Bad/Missing Link Error", action_message)
        elif response.status_code == 503:
            return alert.alert("503 Unavailable Server Error", action_message)
        else:
            return alert.alert("Generic HTTP Error", f"{action_message}: {http_err}")
    except requests.exceptions.RequestException as err:
        return alert.alert("Unexpected Error", f"{action_message}: {err}")
    return response


class CategoryData:
    def __init__(self, data, uid=-1):
        self.data = data
        self.name, self.uid, self.links = "", uid, [""]
        self.downloading, self.only_cover = False, False
        self.cached = {}
        self.downloaded = []
        self.abort = False
        self.to_reload = False
        self.no_image = []

    def load(self, uid, data):
        self.name = data["name"]
        self.uid = uid
        self.links = data["links"]
        self.only_cover = data["only_cover"]
        cached = data["cached"]
        for key, value in cached.items():
            self.cached[key] = set(value)
        self.no_image = data.get("no_image", [])
        self.update_downloaded()
        return self

    def save(self):
        return {
            "name": self.name,
            "links": self.links,
            "only_cover": self.only_cover,
            "cached": self.cached,
            "no_image": self.no_image,
        }

    def image_prefixed(self, name):
        return f"{self.uid}|{name}"

    def get_downloaded_of(self, link):
        if self.uid == common.ANIMES_UID:
            return "", True
        unknown = False
        if link is None:
            to_download = set()
            for lk in self.links:
                if lk in self.cached:
                    to_download |= self.cached[lk]
                else:
                    unknown = True
        if (link in self.cached or link is None) and not unknown:
            if link is not None:
                to_download = self.cached[link]
            remaining = to_download.difference(set(self.downloaded))
            return f"({len(to_download)-len(remaining)}/{len(to_download)})", len(
                remaining
            ) == 0
        else:
            return f"({len(self.downloaded)}/?)", False

    def download(self):
        self.downloading = True
        thread = threading.Thread(target=self.thread_download)
        thread.start()

    def thread_download(self):
        self.update_downloaded()
        try:
            character_links = set()
            for i, link in enumerate(self.links):
                if link not in self.cached:
                    self.cached[link] = set()
                character_links.update(
                    self.async_download_anime_characters(self.name, link, i)
                )
            for char_link in character_links:
                self.async_download_anime_character(char_link, self.name)
        except SystemExit:
            print("DOWNLOAD CANCELED")
        self.downloading = False
        self.to_reload = True

    def async_download_image(self, img_url, save_path):
        if self.abort:
            raise SystemExit
        try:
            img_response = request_wrapper(
                f"Failed to download image from {img_url}, to save in {save_path}",
                img_url,
            )
            if img_response:
                with open(save_path, "wb") as img_file:
                    img_file.write(img_response.content)
            self.update_downloaded()
        except UnicodeError as e:
            alert.alert(
                "Unicode Error",
                f"Failed to download image due to unicode error: '{e}' of {save_path}, {img_url}",
            )

    def update_downloaded(self):
        if os.path.exists(f"user_data/categories/{self.uid}"):
            self.downloaded = [
                name.split(".")[0]
                for name in os.listdir(f"user_data/categories/{self.uid}")
            ]
        else:
            self.downloaded = []
        if self.uid != common.ANIMES_UID:
            self.data.categories[common.ANIMES_UID].update_downloaded()

    def async_download_character_image(
        self, img_url, anime_name, char_name, is_anime=False
    ):
        if self.abort:
            raise SystemExit
        path = f"user_data/categories/{0 if is_anime else self.uid}/{char_name}.png"
        if os.path.exists(path):
            if is_anime:
                print(f"Anime cover {char_name} was already downloaded")
            else:
                print(f"Character {char_name} of {anime_name} was already downloaded")
            return
        if is_anime:
            print(f"Downloading anime cover {char_name} ({img_url})")
        else:
            print(f"Downloading character {char_name} of {anime_name} ({img_url})")
        self.async_download_image(img_url, path)
        self.data.load_recent_image(
            self.data.categories[common.ANIMES_UID] if is_anime else self, path
        )

    def async_recursive_get_first_children(self, first_child, iterations):
        result = first_child
        for i in range(iterations):
            result = list(result.children)[1]
        return result

    def async_download_anime_character(self, char_link, anime_name):
        if self.abort:
            raise SystemExit
        time.sleep(common.DOWNLOAD_SLEEP + random.uniform(-0.3, 0.3))
        char_name = char_link.split("/")[-1]

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = request_wrapper(
            f"Failed to get content of anime character {char_link}",
            char_link,
            headers=headers,
        )
        if not response:
            return

        soup = bs4.BeautifulSoup(response.content, "html.parser")
        images = soup.find_all("img")
        found = False
        for img in images:
            if "class" in img.attrs and img.attrs["class"] == [
                "portrait-225x350",
                "lazyload",
            ]:
                img_link = img.attrs["data-src"]
                if (
                    img_link
                    == r"https://cdn.myanimelist.net/images/questionmark_23.gif"
                ):
                    continue
                found = True
                self.async_download_character_image(img_link, anime_name, char_name)
                break
        if (
            not found
            or img_link == r"https://cdn.myanimelist.net/images/questionmark_23.gif"
        ):
            print(
                f"Character {char_name} of {anime_name} has no image (or unsupported image) on MAL!"
            )
            if char_name not in self.no_image:
                self.no_image.append(char_name)
            for link, cont in self.cached.items():
                if char_name in cont:
                    cont.remove(char_name)

    def async_download_anime_characters(self, name, raw_link, idx=0):
        only_anime = False or self.only_cover
        chars_link = raw_link + "/characters"
        cname = name if idx == 0 else f"{name}_{idx+1}"
        if not only_anime and not os.path.exists(f"user_data/categories/{self.uid}"):
            os.mkdir(f"user_data/categories/{self.uid}")
        if not os.path.exists("user_data/categories/0"):
            os.mkdir("user_data/categories/0")

        if os.path.exists(f"user_data/categories/0/{cname}.png") and only_anime:
            print(f"Skipping only-cover anime {name}")
            return set()

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = request_wrapper(
            f"Failed to get content of anime page {chars_link}",
            chars_link,
            headers=headers,
        )
        if not response:
            return set()

        soup = bs4.BeautifulSoup(response.content, "html.parser")
        if not os.path.exists(f"user_data/categories/0/{cname}.png"):
            cover = soup.find("div", {"class": "leftside"})
            cover_link = list(list(list(cover.children)[1].children)[1].children)[
                1
            ].attrs["data-src"]
            self.async_download_character_image(
                cover_link, "ANIMES", cname, is_anime=True
            )
            if only_anime:
                return set()
        else:
            print(f"Anime cover {cname} was already downloaded")
            if only_anime:
                return set()

        if not only_anime:
            try:
                container = soup.find(
                    "div",
                    {"class": "anime-character-container js-anime-character-container"},
                )
                to_download = set()
                for child in container.children:
                    child: bs4.element.Tag = self.async_recursive_get_first_children(
                        child, 4
                    )
                    character_link = child.attrs["href"]
                    thischarname = character_link.split("/")[-1]
                    if thischarname not in self.no_image:
                        if thischarname not in self.cached[raw_link]:
                            self.cached[raw_link].add(thischarname)
                        if thischarname not in self.downloaded:
                            to_download.add(character_link)
                        else:
                            print(
                                f"Character {thischarname} of {name} was already downloaded"
                            )
                    else:
                        print(
                            f"Character {thischarname} of {name} has no image on MAL!"
                        )
                return to_download
            except Exception:
                alert.alert(
                    "Error Getting Characters",
                    f"An error was raised while trying to get the characters of {raw_link}. This probably happened because the link provided has an unsupported layout. Make sure the link follows the format https://myanimelist.net/anime/<NUMBER>/<ANIME NAME>",
                )
        return set()


class TierlistData:
    def __init__(self):
        self.name = f"new_tierlist_{pygame.time.get_ticks()}"
        self.tiers = []
        self.tiers_settings = []
        self.tiers_all = set()
        self.only_category = ""
        self.default_image_h = common.IMAGE_H
        self.marked = set()
        self.ui_tier_name_percentage = 10
        self.distribution_data = common.DISTRIBUTION

    def load(self, data):
        self.name = data["name"]
        self.tiers = data["tiers"]
        self.tiers_settings = data["tiers_settings"]
        self.tiers_all = set(data["tiers_all"])
        self.only_category = data["only_category"]
        self.default_image_h = data["default_image_h"]
        self.marked = set(data["marked"])
        self.ui_tier_name_percentage = data["ui_tier_name_percentage"]
        self.distribution_data = data["distribution_data"]
        return self

    def save(self):
        return {
            "name": self.name,
            "tiers": self.tiers,
            "tiers_settings": self.tiers_settings,
            "tiers_all": self.tiers_all,
            "only_category": self.only_category,
            "default_image_h": self.default_image_h,
            "marked": self.marked,
            "ui_tier_name_percentage": self.ui_tier_name_percentage,
            "distribution_data": self.distribution_data,
        }

    def save_file(self):
        common.write_json(f"tierlists/{self.name}.json", self.save())


class Data:
    def __init__(self, app: "common.TierlistApp"):
        self.app = app
        self.auto_download = False
        self.load()

    def load(self):
        for folder in os.listdir("user_data/categories"):
            if len(os.listdir(f"user_data/categories/{folder}")) <= 0:
                os.rmdir(f"user_data/categories/{folder}")
        categories_data = common.load_json(
            "categories.json",
            {
                "__uid__": 1,
                f"{common.ANIMES_UID}": {
                    "name": "animes",
                    "links": [],
                    "only_cover": False,
                    "cached": {},
                },
            },
        )
        self.free_category_uid = categories_data["__uid__"]
        self.categories: dict[int, CategoryData] = {}
        self.categories_uids: dict[str, int] = {}
        for struid, data in categories_data.items():
            if struid == "__uid__":
                continue
            uid = int(struid)
            category = CategoryData(self).load(uid, data)
            self.categories[category.uid] = category
            self.categories_uids[category.name] = category.uid
        self.tierlists: dict[str, TierlistData] = {}
        for file in os.listdir("user_data/tierlists"):
            tierlist = TierlistData().load(common.load_json(f"tierlists/{file}", {}))
            self.tierlists[tierlist.name] = tierlist
        settings = common.load_json(
            "settings.json",
            {
                "taskbar_h": 52,
                "image_ratio": 0.6428571429,
                "color_vars": [
                    ["purple", "#9539bf"],
                    ["red", "#E32636"],
                    ["orange", "#FF5E0E"],
                    ["yellow", "#FFFD30"],
                    ["lightgreen", "#00FF40"],
                    ["darkgreen", "#008840"],
                    ["lightblue", "#6CB4EE"],
                    ["blue", "#00308F"],
                    ["darkblue", "#002042"],
                ],
                "ui_category_col_percentage": 25,
                "ui_categories_col_percentage": 12,
                "screenshot_window_mult": 2,
            },
        )
        self.taskbar_h = settings["taskbar_h"]
        self.image_ratio = settings["image_ratio"]
        self.color_vars = settings["color_vars"]
        self.ui_category_col_percentage = settings["ui_category_col_percentage"]
        self.ui_categories_col_percentage = settings["ui_categories_col_percentage"]
        self.screenshot_window_mult = settings["screenshot_window_mult"]
        self.taskbar_h_change()

        self.images = {}
        self.to_load_categories = len(self.categories)
        self.loaded_custom_chars = []
        if os.path.exists("custom_chars"):
            self.custom_chars_listdir = os.listdir("custom_chars")
        else:
            self.custom_chars_listdir = []
        for category in self.categories.values():
            self.load_category_images(category)

    def load_category_images(self, category: CategoryData):
        thread = threading.Thread(
            target=self.thread_load_category_images, args=(category,)
        )
        thread.start()

    def thread_load_category_images(self, category: CategoryData):
        folder = f"user_data/categories/{category.uid}"
        if not os.path.exists(folder):
            self.to_load_categories -= 1
            return
        for filename in os.listdir(folder):
            string = category.image_prefixed(filename.split(".")[0])
            if string in self.images:
                continue
            found = False
            for test_str in [
                f"{category.uid}${filename}",
                f"{category.name}${filename}",
                filename,
            ]:
                if os.path.exists(f"custom_chars/{test_str}"):
                    try:
                        image = pygame.image.load(
                            f"custom_chars/{test_str}"
                        ).convert_alpha()
                        self.images[string] = image
                        self.loaded_custom_chars.append(test_str)
                        found = True
                        break
                    except pygame.error as e:
                        self.image_load_error(f"custom_chars/{test_str}", e)
            if found:
                continue
            try:
                image = pygame.image.load(folder + f"/{filename}").convert_alpha()
                self.images[string] = image
            except pygame.error as e:
                self.image_load_error(folder + f"/{filename}", e)
        if self.to_load_categories is not None:
            self.to_load_categories -= 1

    def image_load_error(self, path, e):
        os.remove(path)
        alert.alert(
            "Error Loading Image",
            f"Could not load image {path} due to unexpected error '{e}'. Image has been deleted.",
        )

    def load_recent_image(self, category: CategoryData, save_path):
        path = save_path
        name = path.split("/")[-1].split(".")[0]
        string = category.image_prefixed(name)
        if string in self.images:
            return
        try:
            image = pygame.image.load(path).convert_alpha()
            self.images[string] = image
        except pygame.error as e:
            self.image_load_error(path, e)

    def get_size_ratio(self, path):
        calc_path = str(path).strip().replace('"', "")
        img = pygame.image.load(calc_path)
        res = int(img.height * 0.6428571429)
        return res, int(img.width / 2 - res / 2)

    def resize_size_ratio(self, path, endpath=None):
        path = pathlib.Path(path.strip().replace('"', ""))
        w, left = self.get_size_ratio(path)
        new_file = endpath if endpath else path.with_stem(path.stem + "_")

        img = pygame.image.load(path)
        subsurface = img.subsurface(
            (
                left,
                0,
                w,
                img.height,
            )
        )
        pygame.image.save(subsurface, new_file)

    def get_color(self, value):
        if value.startswith("$"):
            value = value.removeprefix("$")
            for k, v in self.color_vars:
                if k == value:
                    value = v
                    break
            else:
                return None
        try:
            color = eval(f"Color({value})", {"Color": pygame.Color})
            return color
        except Exception:
            try:
                color = eval(f"Color('{value}')", {"Color": pygame.Color})
                return color
            except Exception:
                return None

    def add_category(self):
        category = CategoryData(self, self.free_category_uid)
        self.free_category_uid += 1
        self.categories[category.uid] = category

    def add_tierlist(self):
        tierlist = TierlistData()
        self.tierlists[tierlist.name] = tierlist

    def rename_category(self, category, name, entry):
        if name == "animes":
            entry.set_text("error_name_is_reserved")
            return
        for cat in self.categories.values():
            if cat is not category and cat.name.lower() == name.lower():
                entry.set_text("error_name_is_duplicate")
                return
        if category.name in self.categories_uids:
            del self.categories_uids[category.name]
        category.name = name.lower()
        self.categories_uids[name] = category.uid

    def rename_tierlist(self, tierlist, name, entry):
        name = name.lower()
        for tier in self.tierlists.values():
            if tier is not tierlist and tier.name.lower() == name:
                entry.set_text("error_name_is_duplicate")
        if tierlist.name in self.tierlists:
            del self.tierlists[tierlist.name]
        if os.path.exists(f"user_data/tierlists/{tierlist.name}.json"):
            os.remove(f"user_data/tierlists/{tierlist.name}.json")
        tierlist.name = name
        self.tierlists[tierlist.name] = tierlist
        tierlist.save_file()

    def taskbar_h_change(self):
        desktop = pygame.display.get_desktop_sizes()[0]
        self.app.window.size = (desktop[0], desktop[1] - self.taskbar_h)
        self.app.window.position = (0, 0)

    def save(self):
        common.write_json(
            "categories.json",
            {
                str(cat.uid): cat.save()
                for cat in sorted(list(self.categories.values()), key=lambda c: c.name)
            }
            | {"__uid__": self.free_category_uid},
        )
        common.write_json(
            "settings.json",
            {
                "taskbar_h": self.taskbar_h,
                "image_ratio": self.image_ratio,
                "color_vars": self.color_vars,
                "ui_categories_col_percentage": self.ui_categories_col_percentage,
                "ui_category_col_percentage": self.ui_category_col_percentage,
                "screenshot_window_mult": self.screenshot_window_mult,
            },
        )
        for tierlist in self.tierlists.values():
            tierlist.save_file()
        print("Data Saved")

    def create_backup(self):
        now = datetime.datetime.now()
        folder_name = (
            str(now)
            .replace("-", "_")
            .replace(" ", "_")
            .replace(":", "_")
            .replace(".", "_")
        )
        if not os.path.exists("backups"):
            os.mkdir("backups")
        os.mkdir(f"backups/{folder_name}")
        backup_folder = f"backups/{folder_name}/"
        shutil.copyfile("user_data/categories.json", f"{backup_folder}categories.json")
        shutil.copyfile("user_data/settings.json", f"{backup_folder}settings.json")
        shutil.copytree("user_data/tierlists", f"{backup_folder}tierlists")
        shutil.copytree("user_data/screenshots", f"{backup_folder}screenshots")

    def apply_custom_chars(self, filter=None):
        thread = threading.Thread(target=self.thread_apply_custom_chars, args=(filter,))
        thread.start()

    def thread_apply_custom_chars(self, filter):
        if not os.path.exists("custom_chars"):
            os.mkdir("custom_chars")
            return
        for filename in os.listdir("custom_chars"):
            char = filename.split(".")[0].strip()
            if filter is not None and char != filter:
                continue
            if filename in self.loaded_custom_chars:
                continue
            if "$" in char:
                category, char = char.split("$")
                category = category.strip()
                char = char.strip()
                oricat = category
                if category.isdecimal():
                    category = self.categories.get(int(category), None)
                else:
                    category = self.categories.get(
                        self.categories_uids.get(category, None), None
                    )
                if category is None:
                    alert.alert(
                        "Error Applying Custom Character",
                        f"The category of {filename} '{oricat}' was not found so the custom character could not be applied.",
                    )
                    continue
                if char not in category.downloaded:
                    alert.alert(
                        "Error Applying Custom Character",
                        f"Custom character {char} of category {category.name} does not exist so it could not be applied.",
                    )
                    continue
                itemstring = f"{category.uid}|{char}"
            else:
                found_categories = []
                for category in self.categories.values():
                    if char in category.downloaded:
                        found_categories.append(category)
                if len(found_categories) == 0:
                    alert.alert(
                        "Error Applying Custom Character",
                        f"Custom character {char} was not found in any category so it could not be applied.",
                    )
                    continue
                if len(found_categories) > 1:
                    alert.alert(
                        "Error Applying Custom Character",
                        f"Custom character {char} was found in multiple categories {tuple([f"{cat.name}:{cat.uid}" for cat in found_categories])} so it could not be applied. Prefix it with the category name/ID and a '$' to select the category.",
                    )
                    continue
                category = found_categories[0]
                itemstring = f"{category.uid}|{char}"
            image = pygame.image.load(f"custom_chars/{filename}").convert_alpha()
            self.images[itemstring] = image
        self.loaded_custom_chars = []
