import time
from rtc import RTC
import board

from adafruit_matrixportal.network import Network
from adafruit_matrixportal.matrix import Matrix

import doorbellDisplay_graphics

# Get Wi-Fi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

# Coords MILL
LAT = '38.720'
LON = '-9.141'

# Minimum time to hold each page in the top section
# Notice the scroll is code-blocking so text will scroll to the end of current line
# before evaluating the page change timer
PAGE_HOLD_TIME = 1.5

# --- Display setup ---
matrix = Matrix()
network = Network(status_neopixel=board.NEOPIXEL)

gfx = doorbellDisplay_graphics.doorbellDisplay(matrix.display)

print("gfx loaded")

localtime_refresh = None
doorbell_refresh = None
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
    if (not doorbell_refresh) or (time.monotonic() - doorbell_refresh) > 600:
        try:
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