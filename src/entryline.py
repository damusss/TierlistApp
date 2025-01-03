import mili
import pygame
import functools

FILE_FORBIDDEN = [
    "<",
    ">",
    ":",
    '"',
    "/",
    "\\",
    "|",
    "?",
    "*",
    ".",
]


class Entryline:
    def __init__(
        self,
        placeholder="Enter text...",
        only_numbers=False,
        minmax=None,
        text="",
        onchange=None,
        files=False,
        lowercase=False,
    ):
        self.placeholder = placeholder
        self.cursor_on = True
        self.cursor_time = pygame.time.get_ticks()
        self.only_numbers = only_numbers
        self.minmax = minmax
        self.focused = False
        self.text = str(text)
        self.cursor = len(self.text)
        self.onchange = onchange
        self.changed = False
        self.files = files
        self.entry_rect = pygame.Rect()
        self.lowercase = lowercase
        self.cache = mili.TextCache()
        self.check()

    @property
    def texts(self):
        return self.text.strip()

    def check(self):
        if self.only_numbers:
            if self.text != "":
                try:
                    float(self.text)
                except ValueError:
                    self.text = "0"
        if self.cursor < 0:
            self.cursor = 0
        if self.cursor > len(self.text):
            self.cursor = len(self.text)

    def add(self, char):
        left, right = self.text[: self.cursor], self.text[self.cursor :]
        self.text = left + char + right
        self.cursor += len(char)
        self.check()
        self.changed = True

    def trigger_callback(self):
        if not self.changed:
            return
        if self.onchange and (not self.only_numbers or self.text != ""):
            self.onchange()
        self.changed = False

    def remove(self):
        if self.cursor > 0:
            left, right = self.text[: self.cursor], self.text[self.cursor :]
            self.text = left[:-1] + right
            self.cursor -= 1
        self.check()
        self.changed = True

    def canc(self):
        if self.cursor <= len(self.text):
            left, right = self.text[: self.cursor], self.text[self.cursor :]
            self.text = left[: self.cursor] + right[1:]
        self.check()
        self.changed = True

    def move(self, dir):
        self.cursor += dir
        self.check()

    def set_text(self, text):
        self.text = str(text)
        self.cursor = len(self.text)

    def event(self, event):
        if self.focused:
            if event.type == pygame.TEXTINPUT:
                evtxt = event.text
                if self.lowercase:
                    evtxt = evtxt.lower()
                if self.only_numbers and evtxt != ".":
                    try:
                        float(evtxt)
                    except ValueError:
                        return
                if self.files and evtxt in FILE_FORBIDDEN:
                    return
                self.set_cursor_on()
                self.add(evtxt)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE and (
                    event.mod & pygame.KMOD_CTRL or event.mod & pygame.KMOD_META
                ):
                    self.text = ""
                    self.cursor = 0
                elif event.key == pygame.K_v and (
                    event.mod & pygame.KMOD_CTRL or event.mod & pygame.KMOD_META
                ):
                    txt = pygame.scrap.get_text().strip()
                    if self.lowercase:
                        txt = txt.lower()
                    if self.files:
                        for char in FILE_FORBIDDEN:
                            txt = txt.replace(char, "")
                    self.add(txt)
                elif event.key == pygame.K_c and (
                    event.mod & pygame.KMOD_CTRL or event.mod & pygame.KMOD_META
                ):
                    pygame.scrap.put_text(self.texts)
                elif event.key == pygame.K_BACKSPACE and (
                    event.mod & pygame.KMOD_CTRL or event.mod & pygame.KMOD_META
                ):
                    self.set_text("")
                else:
                    self.set_cursor_on()
                    if event.key == pygame.K_LEFT:
                        self.move(-1)
                    elif event.key == pygame.K_RIGHT:
                        self.move(1)
                    elif event.key == pygame.K_BACKSPACE:
                        self.remove()
                    elif event.key == pygame.K_DELETE:
                        self.canc()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT:
            self.focused = False

    def update(self):
        if pygame.time.get_ticks() - self.cursor_time >= 350:
            self.cursor_on = not self.cursor_on
            self.cursor_time = pygame.time.get_ticks()

    def set_cursor_on(self):
        self.cursor_on = True
        self.cursor_time = pygame.time.get_ticks()

    def draw_cursor(self, csize, offset, canva, element_data, rect):
        if not self.cursor_on or not self.focused:
            return
        curs = rect.h / 1.5
        xpos = rect.x + csize - offset + 5
        if offset != 0:
            xpos += 5
        pygame.draw.line(
            canva,
            (255,) * 3,
            (xpos, rect.y + rect.h / 2 - curs / 2),
            (xpos, rect.y + rect.h / 2 + curs / 2),
        )

    def ui(
        self,
        mili_: mili.MILI,
        rect,
        style,
        mult,
        bgcol=20,
        outlinecol=40,
        txtcol="white",
        txtsize=None,
    ):
        with mili_.begin(rect, style | {"axis": "x"}) as interaction:
            rect = interaction.data.rect
            mili_.rect({"color": (bgcol,) * 3, "border_radius": 0})
            mili_.rect(
                {
                    "color": (outlinecol,) * 3,
                    "outline": 1,
                    "border_radius": 0,
                    "draw_above": True,
                }
            )

            txtocursor = self.text[: self.cursor]
            size = mili_.text_size(
                txtocursor,
                {"size": mult(20 if txtsize is None else txtsize), "color": txtcol},
            )
            offsetx = size.x - (rect.w - 15)
            if offsetx < 0:
                offsetx = 0

            if mili_.element(
                (0, 0, 0, 0),
                {
                    "align": "center",
                    "offset": (-offsetx, 0),
                    "blocking": False,
                    "post_draw_func": functools.partial(
                        self.draw_cursor, size.x, offsetx
                    ),
                },
            ):
                text = self.text
                if len(self.text) == 1:
                    text = f"{text} "
                mili_.text(
                    text if self.text else self.placeholder,
                    {
                        "color": (txtcol if self.text else (120, 120, 120)),
                        "size": mult(20 if txtsize is None else txtsize),
                        "cache": self.cache,
                    },
                )
            if interaction.left_just_released:
                self.focused = True
                self.set_cursor_on()
            self.entry_rect = interaction.data.absolute_rect.copy()
