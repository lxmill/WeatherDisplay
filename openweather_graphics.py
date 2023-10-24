# SPDX-FileCopyrightText: 2023 Tiago Rosa @MILL
# SPDX-License-Identifier: MIT
#
# Based on the Adafruit weather display example (2020 John Park for Adafruit Industries)
# Altered to support a "paged" top section and a date / clock display

import math
import time
import displayio
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text.label import Label

import helper

TEMP_COLOR = 0xFFA800
TEXT_COLOR = 0xCCCCCC
ALT_COLOR = 0x660000
SCROLL_COLOR = 0xFFA800

cwd = ("/" + __file__).rsplit("/", 1)[
    0
]  # the current working directory (where this file is)

tiny_font = cwd + "/fonts/ie9x14u.bdf"
small_font = cwd + "/fonts/helvB12.bdf"
medium_font = cwd + "/fonts/Arial-14.bdf"

icon_spritesheet = cwd + "/weather-icons.bmp"
icon_width = 16
icon_height = 16
scrolling_text_height = 24


class OpenWeather_Graphics(displayio.Group):
    def __init__(self, display, my_string, textColor, speed):
        super().__init__()
        self.display = display
        # self.my_string = my_string
        # self.color = textColor
        # self.speed = speed

        splash = displayio.Group()
        background = displayio.OnDiskBitmap("loading.bmp")
        bg_sprite = displayio.TileGrid(background, pixel_shader=background.pixel_shader)

        splash.append(bg_sprite)
        display.show(splash)

        self.root_group = displayio.Group()
        self.root_group.append(self)

        # This will store the weather icon to display next to the temp
        self._icon_group = displayio.Group()
        self.append(self._icon_group)

        # Paged top row: Casa -> Branca -> hh:mm -> temperature
        self._page_group = displayio.Group()
        self.append(self._page_group)

        # Scrolling bottom row: text.txt
        self._scrolling_group = displayio.Group()
        self.append(self._scrolling_group)

        # The page index we're currently on
        self._current_page = None
        # The label index we're currently scrolling
        self._current_label = None

        # Load the icon sprite sheet
        icons = displayio.OnDiskBitmap(icon_spritesheet)
        self._icon_sprite = displayio.TileGrid(
            icons,
            pixel_shader=icons.pixel_shader,
            tile_width=icon_width,
            tile_height=icon_height,
        )

        self.my_string = my_string
        self.color = textColor
        self.speed = speed

        self.set_icon(None)
        self._paged_texts = []
        self._scrolling_texts = []

        self.tiny_font = bitmap_font.load_font(tiny_font)
        self.small_font = bitmap_font.load_font(small_font)
        self.medium_font = bitmap_font.load_font(medium_font)
        glyphs = b"0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-,.: "
        self.small_font.load_glyphs(glyphs)
        self.medium_font.load_glyphs(glyphs)
        self.medium_font.load_glyphs(("°",))  # a non-ascii character we need for sure

        # Paged text
        # -----------------------------------------------------------------

        # CASA
        # city_text = displayio.OnDiskBitmap("casabranca.bmp")
        # self.city_sprite = displayio.TileGrid(city_text, pixel_shader=city_text.pixel_shader)
        # self._paged_texts.append(self.city_sprite)

        # DATA
        self.date = Label(self.small_font)
        self.date.color = ALT_COLOR
        self.date.x = 5
        self.date.y = 8
        self._paged_texts.append(self.date)

        # HORA
        self.clock = Label(self.medium_font)
        self.clock.color = TEXT_COLOR
        self.clock.x = 8
        self.clock.y = 8
        self._paged_texts.append(self.clock)

        # TEMP
        # Manually positioned to leave space for icon
        self.temp_text = Label(self.medium_font)
        self.temp_text.x = 20
        self.temp_text.y = 8
        self.temp_text.color = TEMP_COLOR
        self._paged_texts.append(self.temp_text)

        # SCROLLING TEXT
        # -----------------------------------------------------------------

        # Load txt into description field
        # with open("text.txt", "r", encoding="utf-8") as file:
        desc = my_string.split("\n")

        for i, line in enumerate(desc):
            if i < len(desc) - 1:
                modified_line = line[:-1]  # Remove the last character from the line
            else:
                modified_line = line  # Keep the last line unchanged
            self.description_text = Label(self.tiny_font, text=modified_line)
            self.description_text.color = textColor
            self._scrolling_texts.append(self.description_text)

    def descUpdate(self, my_string, textColor, speed):
        self.my_string = my_string
        self.color = textColor
        self.speed = speed

        self._scrolling_texts = []

        desc = my_string.split("\n")

        for i, line in enumerate(desc):
            if i < len(desc) - 1:
                modified_line = line[:-1]  # Remove the last character from the line
            else:
                modified_line = line  # Keep the last line unchanged
            self.description_text = Label(self.tiny_font, text=modified_line)
            self.description_text.color = textColor
            self._scrolling_texts.append(self.description_text)

    def display_weather(self, weather):
        # TEMP
        self.set_icon(weather["weather"][0]["icon"])
        self.temp_text.text = "%d°C" % weather["main"]["temp"]

        self.display.show(self.root_group)

    def update_clock(self, time_struct):
        self.clock.text = helper.hh_mm(time_struct)
        self.date.text = helper.date(time_struct)

    def set_icon(self, icon_name):
        """Use icon_name to get the position of the sprite and update
        the current icon.

        :param icon_name: The icon name returned by openweathermap

        Format is always 2 numbers followed by 'd' or 'n' as the 3rd character
        """

        icon_map = ("01", "02", "03", "04", "09", "10", "11", "13", "50")

        print("Set icon to", icon_name)
        if icon_name is not None:
            row = None
            for index, icon in enumerate(icon_map):
                if icon == icon_name[0:2]:
                    row = index
                    break
            column = 0
            if icon_name[2] == "n":
                column = 1
            if row is not None:
                self._icon_sprite[0] = (row * 2) + column

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

            # Hide the weather icon
            if self._icon_group:
                self._icon_group.pop()

        if self._current_page == len(self._paged_texts) - 1:
            # This means we reached the last page (temp) so we must also show the icon
            self._icon_group.append(self._icon_sprite)

        # Reset page to 0 if None or exceeded available paged texts
        if self._current_page is None or self._current_page >= len(self._paged_texts):
            self._current_page = 0

        # Setup the scrolling group by removing any existing
        if self._page_group:
            self._page_group.pop()

        # Then add the current page
        current_text = self._paged_texts[self._current_page]
        self._page_group.append(current_text)
