import os
import pygame
import time
import requests
import bs4
import random
import shutil
import pathlib
import platform
import subprocess
from datetime import datetime, timedelta
from xml.etree import ElementTree as XMLTree
from src import common
from src import alert

if common.THREADED:
    import threading

for folder in ["user_data", "backups", "custom_chars", "screenshots"]:
    if not os.path.exists(folder):
        os.mkdir(folder)
for folder in ["tierlists", "categories"]:
    if not os.path.exists(f"user_data/{folder}"):
        os.mkdir(f"user_data/{folder}")


def request_wrapper(action_message, *args, get=True, **kwargs):
    try:
        response = (requests.get if get else requests.post)(*args, **kwargs)
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
        elif response.status_code == 404:
            return alert.alert(f"400 {response.reason}")
        else:
            return alert.alert("HTTP Error", f"{action_message}: {http_err}")
    except requests.exceptions.RequestException as err:
        return alert.alert("Unexpected Error", f"{action_message}: {err}")
    return response


class CategoryData:
    def __init__(self, data: "Data", uid=-1):
        self.data = data
        self.name, self.uid, self.links = "", uid, [""]
        self.downloading, self.only_cover = False, False
        self.cached = {}
        self.downloaded = []
        self.abort = False
        self.to_reload = False
        self.no_image = []
        self.covers_downloaded = 0
        self.collapsed = True
        self.auto = True
        self.subtitles = {}
        self.score_categories = dict.fromkeys(common.SCORE_CATEGORIES, "-")
        self.ignore = set()

    def load(self, uid, data):
        self.name = data["name"]
        self.uid = uid
        self.links = data["links"]
        self.only_cover = data["only_cover"]
        cached = data["cached"]
        for key, value in cached.items():
            self.cached[key] = set(value)
        self.no_image = data.get("no_image", [])
        self.auto = data.get("auto", True)
        self.ignore = set(data.get("ignore", set()))
        self.score_categories = data.get("score_categories", {})
        for cat in common.SCORE_CATEGORIES:
            if cat not in self.score_categories:
                self.score_categories[cat] = "-"
        self.check_subtitles()
        self.update_downloaded()
        return self

    def save(self):
        return {
            "name": self.name,
            "links": self.links,
            "only_cover": self.only_cover,
            "cached": self.cached,
            "no_image": self.no_image,
            "auto": self.auto,
            "ignore": self.ignore,
            "score_categories": self.score_categories,
        }

    def format_item_name(self, item):
        if self.uid != common.ANIMES_UID:
            return item.replace("_039", "")
        index = 0
        if "_" in item:
            parts = item.split("_")
            if parts[-1].isdecimal():
                index = int(parts[-1]) - 1
                parts.pop(-1)
                cat_name = "_".join(parts).strip()
                if cat_name in self.data.categories_uids:
                    cat_uid = self.data.categories_uids[cat_name]
                    category = self.data.categories[cat_uid]
                    subtitle = category.subtitles.get(
                        index, f"{index + 1 if index != 0 else ''}"
                    )
                    return f"{cat_name}_{subtitle}"
        return item

    def open_exporer(self):
        system = platform.system()
        path = pathlib.Path(f"user_data/categories/{self.uid}").absolute()

        if system == "Windows":
            subprocess.Popen(
                ["explorer", path],
                creationflags=subprocess.CREATE_NO_WINDOW
                | subprocess.CREATE_NEW_CONSOLE,
            )
        elif system == "Darwin":
            subprocess.Popen(["open", path])
        elif system == "Linux":
            subprocess.Popen(["xdg-open", path])
        else:
            pygame.display.message_box(
                "Operation failed",
                "Could not show file in explorer due to unsupported OS.",
                "error",
                None,
                ("Understood"),
            )

    def check_subtitles(self):
        self.subtitles = {}
        for i, link in enumerate(self.links):
            if "," in link:
                subtitle = link.split(",")[-1].strip()
                self.subtitles[i] = subtitle

    def remove_old_covers(self):
        if self.name.strip() == "":
            return
        cover_files = [
            f"{self.name}" if i == 0 else f"{self.name}_{i + 1}"
            for i in range(len(self.links))
        ]
        for file in cover_files:
            path = f"user_data/categories/{common.ANIMES_UID}/{file}"
            if os.path.exists(path):
                os.remove(path)

    def erase_items(self):
        if self.uid == common.ANIMES_UID:
            return
        path = f"user_data/categories/{self.uid}"
        if os.path.exists(path):
            for file in os.listdir(path):
                try:
                    os.remove(f"{path}/{file}")
                except OSError:
                    ...

    def image_prefixed(self, name):
        return f"{self.uid}|{name}"

    def get_raw_link(self, link):
        if "," in link:
            return link.split(",")[0].strip()
        return link

    def get_downloaded_of(self, link, include_covers=False):
        if not self.auto:
            return f"({len(self.downloaded)})", True
        if self.uid == common.ANIMES_UID:
            return "", True
        unknown = False
        if link is None:
            to_download = set()
            for lk in self.links:
                lk = self.get_raw_link(lk)
                if lk in self.cached:
                    to_download |= self.cached[lk]
                else:
                    unknown = True
        else:
            link = self.get_raw_link(link)
        if (link in self.cached or link is None) and not unknown:
            if link is not None:
                to_download = self.cached[link]
            remaining = to_download.difference(set(self.downloaded))
            if self.only_cover:
                string = f"({self.covers_downloaded}/{len(self.links)})"
            else:
                string = f"({len(to_download) - len(remaining)}{f'+{self.covers_downloaded}' if include_covers else ''}/{len(to_download)}{f'+{len(self.links)}' if include_covers else ''})"
            return (
                string,
                (
                    len(remaining) == 0
                    and (
                        not include_covers or len(self.links) == self.covers_downloaded
                    )
                ),
            )
        else:
            return (
                f"({len(self.downloaded)}{f'+{self.covers_downloaded}' if include_covers else ''}/?)",
                False,
            )

    def download(self):
        self.abort = False
        if not self.auto:
            if not os.path.exists(f"user_data/categories/{self.uid}"):
                os.mkdir(f"user_data/categories/{self.uid}")
            if not os.path.exists(f"user_data/categories/{self.name}"):
                os.symlink(
                    pathlib.Path(f"user_data/categories/{self.uid}").resolve(),
                    f"user_data/categories/{self.name}",
                    True,
                )
            self.update_downloaded()
            self.data.load_category_images(self, True)
            return
        if self.name.strip() == "":
            alert.alert(
                "Empty Category Name Error",
                f"The category you are trying to download (UID: {self.uid}) has no name and cannot be downloaded. Did you forget to sync your changes?",
            )
            return
        self.downloading = True
        self.data.downloading_amount += 1
        if common.THREADED:
            thread = threading.Thread(target=self.thread_download)
            thread.start()
        else:
            self.thread_download()

    def thread_download(self):
        self.update_downloaded()
        cancel = False
        try:
            character_links = set()
            for i, link in enumerate(self.links):
                link = self.get_raw_link(link)
                if link not in self.cached:
                    self.cached[link] = set()
                character_links.update(
                    self.async_download_anime_characters(self.name, link, i)
                )
            for char_link in character_links:
                self.async_download_anime_character(char_link, self.name)
        except SystemExit:
            alert.message(f"Download of {self.name} canceled")
            cancel = True
        except Exception as e:
            alert.alert(
                "Unexpected Download Error",
                f"An error in the code occurred so the category {self.name} could not download properly: '{e}'",
            )
        self.downloading = False
        self.to_reload = True
        self.data.downloading_amount -= 1
        if not cancel:
            alert.message(f"Finished downloading {self.name.replace('_', ' ').title()}")

    def async_download_image(self, img_url, save_path, try_large=False):
        if self.abort:
            raise SystemExit
        try:
            try:
                if not try_large:
                    raise requests.HTTPError
                left, right = img_url.rsplit(".", 1)
                img_response = requests.get(left + "l." + right)
                img_response.raise_for_status()
                with open(save_path, "wb") as img_file:
                    img_file.write(img_response.content)
            except requests.HTTPError:
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
        if self.uid != common.ANIMES_UID and self.auto:
            self.data.categories[common.ANIMES_UID].update_downloaded()
        if not os.path.exists(f"user_data/categories/{common.ANIMES_UID}"):
            self.covers_downloaded = 0
            return
        self.covers_downloaded = 0
        if not self.auto:
            return
        cover_files = [
            f"{self.name}" if i == 0 else f"{self.name}_{i + 1}"
            for i in range(len(self.links))
        ]
        for file in os.listdir(f"user_data/categories/{common.ANIMES_UID}"):
            file = file.split(".")[0]
            for cover in cover_files:
                if file == cover:
                    self.covers_downloaded += 1

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
        self.async_download_image(img_url, path, is_anime)
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
            alert.message(
                f"Character {char_name} of {anime_name} has no image (or unsupported image) on MAL!"
            )
            if char_name not in self.no_image:
                self.no_image.append(char_name)
            for link, cont in self.cached.items():
                if char_name in cont:
                    cont.remove(char_name)

    def async_download_anime_characters(self, name, raw_link, idx=0):
        if self.abort:
            raise SystemExit
        only_anime = False or self.only_cover
        chars_link = raw_link + "/characters"
        cname = name if idx == 0 else f"{name}_{idx + 1}"
        if not only_anime and not os.path.exists(f"user_data/categories/{self.uid}"):
            os.mkdir(f"user_data/categories/{self.uid}")
        if not os.path.exists(f"user_data/categories/{common.ANIMES_UID}"):
            os.mkdir(f"user_data/categories/{common.ANIMES_UID}")

        if (
            os.path.exists(f"user_data/categories/{common.ANIMES_UID}/{cname}.png")
            and only_anime
        ):
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
        if not os.path.exists(f"user_data/categories/{common.ANIMES_UID}/{cname}.png"):
            cover = soup.find("div", {"class": "leftside"})
            if "manga" in raw_link:
                cover_link = list(list(list(cover.children)[0].children)[0])[0].attrs[
                    "data-src"
                ]
            else:
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
                cword = "manga" if "manga" in raw_link else "anime"
                cached = set()
                container = soup.find(
                    "div",
                    {
                        "class": f"{cword}-character-container js-{cword}-character-container"
                    },
                )
                to_download = set()
                for child in container.children:
                    if child.name == "article":
                        continue
                    if self.abort:
                        raise SystemExit
                    if "manga" in raw_link:
                        if isinstance(child, bs4.NavigableString):
                            continue
                    child: bs4.element.Tag = self.async_recursive_get_first_children(
                        child, 4
                    )
                    character_link = child.attrs["href"]
                    thischarname = character_link.split("/")[-1]
                    if thischarname not in self.no_image:
                        if thischarname not in self.cached[raw_link]:
                            self.cached[raw_link].add(thischarname)
                        cached.add(thischarname)
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
                if raw_link in self.cached:
                    for item in self.cached[raw_link].difference(cached):
                        self.cached[raw_link].remove(item)
                return to_download
            except Exception:
                alert.alert(
                    "Error Getting Characters",
                    f"An error was raised while trying to get the characters of {raw_link}. This probably happened because the link provided has an unsupported layout. Make sure the link follows the format https://myanimelist.net/anime|manga/<NUMBER>/<ANIME NAME>",
                )
        return set()


class TierlistData:
    def __init__(self):
        self.name = f"new_tierlist_{pygame.time.get_ticks()}"
        self.tiers = [list() for i in range(9)]
        self.tiers_settings = [
            {"name": "S+", "color": "$purple", "txtcol": "white"},
            {"name": "S", "color": "$red", "txtcol": "white"},
            {"name": "A", "color": "$orange", "txtcol": "white"},
            {"name": "B", "color": "$yellow", "txtcol": "black"},
            {"name": "C", "color": "$lightgreen", "txtcol": "black"},
            {"name": "D", "color": "$darkgreen", "txtcol": "white"},
            {"name": "E", "color": "$lightblue", "txtcol": "black"},
            {"name": "F", "color": "$blue", "txtcol": "white"},
            {"name": "F-", "color": "$darkblue", "txtcol": "white"},
        ]
        self.tiers_all = set()
        self.only_category = ""
        self.default_image_h = common.IMAGE_H
        self.marked = set()
        self.ui_tier_name_percentage = 10
        self.distribution_data = common.DISTRIBUTION
        self.ignore_first = False
        self.use_original = False

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
        self.ignore_first = data.get("ignore_first", False)
        self.use_original = data.get("use_original", False)
        all = []
        for t in self.tiers:
            all += t
        for item in set(all).difference(self.tiers_all):
            self.tiers_all.add(item)
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
            "ignore_first": self.ignore_first,
            "use_original": self.use_original,
        }

    def save_file(self):
        common.write_json(f"tierlists/{self.name}.json", self.save())


class MALParent:
    def __init__(self, category: "CategoryData"):
        self.category = category
        self.animes: dict[int, "MALAnime"] = {}
        self.tags = set()
        self.score = 0
        self.episodes_str = ""
        self.status = "completed"
        self.global_i = 0
        self.elapsed_time = 0

    def __str__(self):
        return f"{self.category.name}"

    __repr__ = __str__


class MALAnime:
    def __init__(
        self,
        index,
        movie,
        total_amount,
        watched_amount,
        start_date,
        end_date,
        status,
        score,
        tags,
    ):
        def get_date(date):
            year, month, day = date.split("-")
            year = int(year.strip())
            month = int(month.strip())
            day = int(day.strip())
            if year == 0:
                return None
            return datetime(year, month, day)

        self.index = index
        self.movie = movie
        self.total_amount = int(total_amount)
        self.watched_amount = int(watched_amount)
        self.status = status.replace(" ", "_").lower()
        self.score = int(score)
        self.start_date = get_date(start_date)
        self.end_date = get_date(end_date)
        if self.end_date is None and self.status == "watching":
            self.end_date = datetime.now()
        self.elapsed_time = None
        if self.start_date is not None and self.end_date is not None:
            self.elapsed_time = (self.end_date - self.start_date) + timedelta(1)
        self.tags = set([tag.strip() for tag in tags.split(",")]) if tags else set()
        if "almost10" in self.tags:
            self.score = 9.5
        if "film" in self.tags:
            self.movie = True


class Data:
    def __init__(self, app: "common.TierlistApp"):
        self.app = app
        self.auto_download = False
        self.load()

    def load(self):
        self.downloading_amount = 0
        for folder in os.listdir("user_data/categories"):
            if pathlib.Path(f"user_data/categories/{folder}").is_dir():
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
                "mal_username": "",
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
                "mal_small": False,
                "mal_tags": [],
            },
        )
        self.taskbar_h = settings["taskbar_h"]
        self.image_ratio = settings["image_ratio"]
        self.color_vars = settings["color_vars"]
        self.ui_category_col_percentage = settings.get("ui_category_col_percentage", 25)
        self.ui_categories_col_percentage = settings.get(
            "ui_categories_col_percentage", 12
        )
        self.screenshot_window_mult = settings.get("screenshot_window_mult", 2)
        self.mal_username = settings.get("mal_username", "")
        self.mal_small = settings.get("mal_small", False)
        self.mal_tags = settings.get("mal_tags", [])
        self.taskbar_h_change()

        self.images = {}
        self.to_load_categories = len(self.categories)
        self.loaded_custom_chars = []
        if os.path.exists("custom_chars"):
            self.custom_chars_listdir = os.listdir("custom_chars")
        else:
            self.custom_chars_listdir = []
        self.startup_to_load_categories = [
            cat for cat in self.categories.values() if cat.auto
        ]
        self.manual_to_load = [cat for cat in self.categories.values() if not cat.auto]
        self.loaded_amount = 0
        self.should_load_amount = 0

        self.load_MAL()

    def refresh_MAL(self):
        if common.THREADED:
            thread = threading.Thread(target=self.thread_refresh_MAL)
            thread.start()
        else:
            self.thread_refresh_MAL()

    def thread_refresh_MAL(self):
        if self.mal_username.strip() == "":
            return alert.alert(
                "Empty MAL Username", "Cannot retrieve MAL data with empty username!"
            )
        response = request_wrapper(
            "Could not refresh MyAnimeList data",
            "https://malscraper.azurewebsites.net/scrape",
            get=False,
            data={"username": self.mal_username, "listtype": "anime"},
        )
        if response is None:
            return
        with open("user_data/mal.xml", "w", encoding="utf-8") as file:
            file.write(response.text)
        self.load_MAL()
        alert.message("Refreshed MyAnimeList")

    def MAL_process_element(self, element: XMLTree.Element):
        status = element.find("my_status").text
        if status in ["Plan To Watch"]:
            return
        start, end = (
            element.find("my_start_date").text,
            element.find("my_finish_date").text,
        )
        movie = element.find("series_type").text == "Movie"
        score = element.find("my_score").text
        uid = element.find("series_animedb_id").text
        episodes, watched = (
            element.find("series_episodes").text,
            element.find("my_watched_episodes").text,
        )
        tags = element.find("my_tags").text
        category = None
        index = -1
        for cat in self.categories.values():
            dobreak = False
            for i, link in enumerate(cat.links):
                link_uid = (
                    link.replace("https://myanimelist.net/anime/", "")
                    .replace("https://myanimelist.net/manga/", "")
                    .split("/")[0]
                )
                if link_uid == uid:
                    category = cat
                    index = i
                    dobreak = True
                    break
            if dobreak:
                break
        if category is None:
            return
        if category.uid not in self.mal_data:
            self.mal_data[category.uid] = MALParent(category)
        parent = self.mal_data[category.uid]
        anime = MALAnime(
            index, movie, episodes, watched, start, end, status, score, tags
        )
        parent.animes[index] = anime

    def get_episodes_str(self, watched_eps, eps, movies):
        return f"{f'{watched_eps}{f"/{eps}" if watched_eps != eps else ""}' if eps > 0 else ''}{f'{" + " if eps > 0 and movies > 0 else ""}{movies} Movie{"s" if movies > 1 else ""}' if movies > 0 else ''}"

    def load_MAL(self):
        self.mal_data: dict[int, MALParent] = {}
        self.mal_episodes_str = None
        g_eps = g_seasons = g_movies = g_series = 0
        self.mal_sorted = {}
        if not os.path.exists("user_data/mal.xml"):
            return
        with open("user_data/mal.xml", "r", encoding="utf-8") as file:
            tree = XMLTree.fromstring(file.read())
            for element in tree.findall("anime"):
                self.MAL_process_element(element)
        tierlist = self.tierlists.get("fav_animes", None)
        keys = [10, 9.5, 9, 8, 7, 6, 5, 2]
        if tierlist is None:
            self.mal_sorted = {key: [] for key in keys} | {0: []}
        else:
            self.mal_sorted = {
                key: [None] * len(tierlist.tiers[i]) for i, key in enumerate(keys)
            } | {0: []}
        for parent in self.mal_data.values():
            tags = set()
            eps = 0
            watched_eps = 0
            movies = 0
            last_end = None
            for anime in parent.animes.values():
                tags |= anime.tags
                if anime.elapsed_time is not None:
                    parent.elapsed_time += anime.elapsed_time.days
                    if anime.start_date == last_end:
                        parent.elapsed_time -= 1
                last_end = anime.end_date
                if anime.status != "completed":
                    parent.status = anime.status
                if anime.movie:
                    movies += 1
                else:
                    g_seasons += 1
                    eps += anime.total_amount
                    watched_eps += anime.watched_amount
            if parent.status == "completed":
                watched_eps = eps
            g_series += 1
            g_eps += watched_eps
            g_movies += movies
            if len(parent.animes) == 1 and parent.animes[0].movie:
                g_series -= 1
            parent.episodes_str = self.get_episodes_str(watched_eps, eps, movies)
            parent.tags = tags
            if tierlist is None:
                if "almost10" in tags:
                    parent.score = 9.5
                parent.score = max([anime.score for anime in parent.animes.values()])
                self.mal_sorted[parent.score].append(parent)
            else:
                tname = "0|" + parent.category.name
                if tname not in tierlist.tiers_all:
                    parent.score = max(
                        [anime.score for anime in parent.animes.values()]
                    )
                    self.mal_sorted[parent.score].append(parent)
                else:
                    for i, tier in enumerate(tierlist.tiers):
                        if tname in tier:
                            parent.score = keys[i]
                            idx = tier.index(tname)
                            self.mal_sorted[parent.score][idx] = parent
        if tierlist is None:
            self.mal_sorted = {
                key: sorted(value, key=lambda p: p.category.name[0])
                for key, value in self.mal_sorted.items()
            }
        global_i = 1
        for parents in self.mal_sorted.values():
            for parent in parents:
                if parent.elapsed_time == 0:
                    parent.elapsed_time = None
                parent.global_i = global_i
                global_i += 1

        self.mal_episodes_str = f"{len(self.mal_data)} Animes, {g_series} TV Series, {g_seasons} Seasons, {g_eps} Episodes, {g_movies} Movies"

    def load_category_images(self, category: CategoryData, force=False):
        if common.THREADED:
            thread = threading.Thread(
                target=self.thread_load_category_images, args=(category, force)
            )
            thread.start()
        else:
            self.thread_load_category_images(category, force)

    def thread_load_category_images(self, category: CategoryData, force=False):
        folder = f"user_data/categories/{category.uid}"
        if not os.path.exists(folder):
            self.to_load_categories -= 1
            return
        for filename in os.listdir(folder):
            name = filename.split(".")[0]
            self.should_load_amount += 1
            if name in category.ignore:
                continue
            string = category.image_prefixed(name)
            if string in self.images and not force:
                continue
            found = False
            for test_str in [
                f"{category.uid}${filename}",
                f"{category.name}${filename}",
                f"_{category.name}${filename}",
                filename,
            ]:
                if os.path.exists(f"custom_chars/{test_str}"):
                    try:
                        image = pygame.image.load(
                            f"custom_chars/{test_str}"
                        ).convert_alpha()
                        self.images[string] = image
                        if category.uid == common.ANIMES_UID:
                            image2 = pygame.image.load(
                                folder + f"/{filename}"
                            ).convert_alpha()
                            self.images["original_" + string] = image2
                        self.loaded_custom_chars.append(test_str)
                        found = True
                        break
                    except pygame.error as e:
                        self.image_load_error(f"custom_chars/{test_str}", e)
            if found:
                continue
            try:
                image = pygame.image.load(folder + f"/{filename}")

            except pygame.error as e:
                self.image_load_error(folder + f"/{filename}", e)
                continue
            img = image.convert_alpha()
            self.images[string] = img
            if category.uid == common.ANIMES_UID:
                self.images["original_" + string] = img
        if self.to_load_categories is not None:
            self.to_load_categories -= 1

    def image_load_error(self, path, e):
        alert.alert(
            "Error Loading Image",
            f"Could not load image {path} due to unexpected error '{e}'. Press 'Delete' to delete it.",
            options=("Delete", "Understood"),
            callback=lambda *args: os.remove(path),
        )

    def confirm_delete(self, btn, path):
        if btn == 1:
            return
        os.remove(path)

    def load_recent_image(self, category: CategoryData, save_path):
        path = save_path
        name = path.split("/")[-1].split(".")[0]
        string = category.image_prefixed(name)
        if string in self.images:
            return
        try:
            image = pygame.image.load(path)
        except pygame.error as e:
            self.image_load_error(path, e)
            return
        img = image.convert_alpha()
        self.images[string] = img
        if category.uid == common.ANIMES_UID:
            self.images["original_" + string] = img

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
        category.collapsed = False
        self.free_category_uid += 1
        self.categories[category.uid] = category

    def add_tierlist(self):
        tierlist = TierlistData()
        self.tierlists[tierlist.name] = tierlist

    def rename_category(self, category: CategoryData, name, entry):
        if name == "animes":
            entry.set_text("error_name_is_reserved")
            return
        for cat in self.categories.values():
            if cat is not category and cat.name.lower() == name.lower():
                entry.set_text("error_name_is_duplicate")
                return
        category.remove_old_covers()
        oldname = category.name
        if category.name in self.categories_uids:
            del self.categories_uids[category.name]
        category.name = name.lower()
        self.categories_uids[name] = category.uid
        if oldname != "":
            alert.message(f"Category was renamed from {oldname} to {category.name}")

    def rename_tierlist(self, tierlist, name, entry):
        name = name.lower()
        for tier in self.tierlists.values():
            if tier is not tierlist and tier.name.lower() == name:
                entry.set_text("error_name_is_duplicate")
        if tierlist.name in self.tierlists:
            del self.tierlists[tierlist.name]
        if os.path.exists(f"user_data/tierlists/{tierlist.name}.json"):
            os.remove(f"user_data/tierlists/{tierlist.name}.json")
        oldname = tierlist.name
        tierlist.name = name
        self.tierlists[tierlist.name] = tierlist
        tierlist.save_file()
        alert.message(f"Tierlist was renamed from {oldname} to {tierlist.name}")

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
                "mal_username": self.mal_username,
                "mal_small": self.mal_small,
                "color_vars": self.color_vars,
                "ui_categories_col_percentage": self.ui_categories_col_percentage,
                "ui_category_col_percentage": self.ui_category_col_percentage,
                "screenshot_window_mult": self.screenshot_window_mult,
                "mal_tags": self.mal_tags,
            },
        )
        for tierlist in self.tierlists.values():
            tierlist.save_file()
        alert.message("All data was saved")

    def create_backup(self):
        now = datetime.now()
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
        alert.message(f"Backup created at backups/{folder_name}/")

    def apply_custom_chars(self, filter=None):
        if common.THREADED:
            thread = threading.Thread(
                target=self.thread_apply_custom_chars, args=(filter,)
            )
            thread.start()
        else:
            self.thread_apply_custom_chars(filter)

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
                    if category.startswith("_"):
                        category = category.removeprefix("_")
                    category = self.categories.get(
                        self.categories_uids.get(category, None), None
                    )
                if category is None:
                    alert.alert(
                        "Error Applying Custom Item",
                        f"The category of {filename} '{oricat}' was not found so the custom item could not be applied.",
                    )
                    continue
                if char not in category.downloaded:
                    alert.alert(
                        "Error Applying Custom Item",
                        f"Custom item {char} of category {category.name} does not exist so it could not be applied.",
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
                        "Error Applying Custom Item",
                        f"Custom item {char} was not found in any category so it could not be applied.",
                    )
                    continue
                if len(found_categories) > 1:
                    alert.alert(
                        "Error Applying Custom Item",
                        f"Custom item {char} was found in multiple categories {tuple([f'{cat.name}:{cat.uid}' for cat in found_categories])} so it could not be applied. Prefix it with the category name/ID and a '$' to select the category.",
                    )
                    continue
                category = found_categories[0]
                itemstring = f"{category.uid}|{char}"
            image = pygame.image.load(f"custom_chars/{filename}").convert_alpha()
            self.images[itemstring] = image
        self.loaded_custom_chars = []
        if filter is None:
            alert.message("Custom items applied")
