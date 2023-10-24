# SPDX-FileCopyrightText: 2023 Tiago Rosa @MILL
# SPDX-License-Identifier: MIT
#
# Based on the Adafruit weather display example (2020 John Park for Adafruit Industries)
# Altered to support a "paged" top section and a date / clock display

import time
from rtc import RTC
import board
from adafruit_matrixportal.network import Network
from adafruit_matrixportal.matrix import Matrix

import helper
import openweather_graphics  # pylint: disable=wrong-import-position

# Get Wi-Fi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

# Coords Casa Branca
# LAT = '38.499'
# LON = '-8.158'

# Coords MILL
LAT = '38.720'
LON = '-9.141'

print("Getting weather for {} {}".format(LAT, LON))

DATA_SOURCE = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&units=metric"
DATA_SOURCE += "&appid=" + secrets["openweather_token"]

DATA_LOCATION = []

# Minimum time to hold each page in the top section
# Notice the scroll is code-blocking so text will scroll to the end of current line
# before evaluating the page change timer
PAGE_HOLD_TIME = 1.5

# --- Display setup ---
matrix = Matrix()
network = Network(status_neopixel=board.NEOPIXEL)
gfx = openweather_graphics.OpenWeather_Graphics(matrix.display)

print("gfx loaded")

localtime_refresh = None
weather_refresh = None
page_change = None

while True:
    # only query the online time once per hour (and on first run)
    if (not localtime_refresh) or (time.monotonic() - localtime_refresh) > 3600:
        try:
            print("Getting time from internet!")
            network.get_local_time()
            localtime_refresh = time.monotonic()
        except RuntimeError as e:
            print("Some error occured, retrying! -", e)
            continue

    # only query the weather every 10 minutes (and on first run)
    if (not weather_refresh) or (time.monotonic() - weather_refresh) > 600:
        try:
            value = network.fetch_data(DATA_SOURCE, json_path=(DATA_LOCATION,))
            gfx.display_weather(value)
            weather_refresh = time.monotonic()
        except RuntimeError as e:
            print("Some error occurred, retrying! -", e)
            continue

    # Non-blocking page change timer logic
    if (not page_change) or (time.monotonic() - page_change) > PAGE_HOLD_TIME:
        # update clock text before page changes
        gfx.update_clock(RTC().datetime)
        gfx.show_next_page()
        page_change = time.monotonic()

    # Show next weather label
    gfx.scroll_next_label()

