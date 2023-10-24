import math
import time
import displayio

from adafruit_bitmap_font import bitmap_font
from adafruit_display_text.label import Label

import helper

HAND_COLOR = 0xFFC0CB
TEXT_COLOR = 0xFFFFFF
OPEN_COLOR = 0x00FF00
CLOSE_COLOR = 0xFF0000

cwd = ("/" + __file__).rsplit("/", 1)[
    0
]  # the current working directory (where this file is)

tiny_font = cwd + "/fonts/ie9x14u.bdf"
small_font = cwd + "/fonts/helvB12.bdf"
medium_font = cwd + "/fonts/Arial-14.bdf"

class doorbellDisplay(displayio.Group):
    def __init__(self, display):
        super().__init__()
        self.display = display

        # splash = displayio.Group()
        # background = displayio.OnDiskBitmap("loading.bmp")
        # bg_sprite = displayio.TileGrid(background, pixel_shader=background.pixel_shader)

        # splash.append(bg_sprite)
        # display.show(splash)

        self.root_group = displayio.Group()
        self.root_group.append(self)

        # Paged top row
        self._page_group = displayio.Group()
        self.append(self._page_group)

        # Scrolling bottom row
        self._scrolling_group = displayio.Group()
        self.append(self._scrolling_group)

        # The page index we're currently on
        self._current_page = None
        # The label index we're currently scrolling
        self._current_label = None

        # self.set_icon(None)
        self._paged_texts = []
        self._scrolling_texts = []

        self.tiny_font = bitmap_font.load_font(tiny_font)
        self.small_font = bitmap_font.load_font(small_font)
        self.medium_font = bitmap_font.load_font(medium_font)

        # Paged text
        # -----------------------------------------------------------------

        # DATE
        self.date = Label(self.small_font)
        self.date.color = TEXT_COLOR
        self.date.x = 5
        self.date.y = 8
        self._paged_texts.append(self.date)

        # HORA
        self.clock = Label(self.small_font)
        self.clock.color = TEXT_COLOR
        self.clock.x = 8
        self.clock.y = 8
        self._paged_texts.append(self.clock)

        # DESCRIPTION
        self.description_text = Label(self.tiny_font, text="MILL - Makers In Little Lisbon")
        self.description_text.color = TEXT_COLOR
        self._paged_texts.append(self.description_text)
        self._scrolling_texts.append(self.description_text)

    def update_clock(self, time_struct):
        self.clock.text = helper.hh_mm(time_struct)
        self.date.text = helper.date(time_struct)

    def scroll_next_label(self):
        # Start by scrolling current label off if not set to None
        if self._current_label is not None and self._scrolling_group:
            current_text = self._scrolling_texts[self._current_label]
            text_width = current_text.bounding_box[2]
            for _ in range(text_width + 1):
                self._scrolling_group.x = self._scrolling_group.x - 1
                time.sleep(self.speed)

        if self._current_label is not None:
            self._current_label += 1
        if self._current_label is None or self._current_label >= len(
            self._scrolling_texts
        ):
            self._current_label = 0

        # Setup the scrolling group by removing any existing
        if self._scrolling_group:
            self._scrolling_group.pop()
        # Then add the current label
        current_text = self._scrolling_texts[self._current_label]
        self._scrolling_group.append(current_text)

        # Set the position of the group to just off screen and centered vertically for lower half
        self._scrolling_group.x = self.display.width
        self._scrolling_group.y = 23

        # Run a loop until the label is offscreen again and leave function
        for _ in range(self.display.width):
            self._scrolling_group.x = self._scrolling_group.x - 1
            time.sleep(self.speed)
        # By blocking other code we will never leave the label half way scrolled

    def show_next_page(self):
        # Move page fwd
        if self._current_page is not None:
            self._current_page += 1

        # Reset page to 0 if None or exceeded available paged texts
        if self._current_page is None or self._current_page >= len(self._paged_texts):
            self._current_page = 0

        # Setup the scrolling group by removing any existing
        if self._page_group:
            self._page_group.pop()

        # Then add the current page
        current_text = self._paged_texts[self._current_page]
        self._page_group.append(current_text)
