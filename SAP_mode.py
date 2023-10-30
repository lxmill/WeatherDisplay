import board
import busio

import adafruit_requests as requests
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_esp32spi import adafruit_esp32spi
from adafruit_matrixportal.network import Network

from digitalio import DigitalInOut, Pull

import time
from rtc import RTC
from adafruit_matrixportal.matrix import Matrix

import helper
import openweather_graphics  # pylint: disable=wrong-import-position

import adafruit_requests as requests
import adafruit_esp32spi.adafruit_esp32spi_socket as socket

import digitalio
import supervisor


def DesUpdate():
    TEXT_URL = "https://mill.pt/matrix/display_data.php"  # URL to results page

    print("Fetching text from", TEXT_URL)
    # r = requests.get(TEXT_URL)
    r = network.fetch_data(TEXT_URL)

    print("Text recovered: ", r)

    lines = (r).split("<br>")

    # Initialize variables
    text_info = None
    color_info = None
    speed_info = None

    # Loop through each line and extract the values
    for line in lines:
        parts = line.split(":")  # Split each line by ':' to separate key and value
        if len(parts) == 2:
            key = parts[0].strip()
            value = parts[1].strip()
            if key == "Text":
                text_info = value
            elif key == "Hexadecimal":
                result_string = value[1:]
                hex_number = int(result_string, 16)
                color_info = hex_number
                print("Color HEX: ", color_info)
            elif key == "Float":
                speed_info = float(value)  # Convert the value to a float

    # Print the extracted values
    print("Text:", text_info)
    print("Hexadecimal:", color_info)
    print("Float:", speed_info)

    return [text_info, color_info, speed_info]


# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

# If you are using a board with pre-defined ESP32 Pins:
esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)

spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)
# requests.set_socket(socket, esp)

if esp.status == adafruit_esp32spi.WL_IDLE_STATUS:
    print("ESP32 found and in idle mode")
print("Firmware vers.", esp.firmware_version)
print("MAC addr:", [hex(i) for i in esp.MAC_address])

# Scan the networks avaiable
for ap in esp.scan_networks():
    print("\t%s\t\tRSSI: %d" % (str(ap["ssid"], "utf-8"), ap["rssi"]))

while not esp.is_connected:
    try:
        esp.connect_AP(secrets["ssid"], secrets["password"])
        print("Connected to", str(esp.ssid, "utf-8"), "\tRSSI:", esp.rssi)
        print("My IP address is", esp.pretty_ip(esp.ip_address))
    except OSError as e:
        print("could not connect to AP, retrying: ", e)

# Funcionamento de manutenção
network = Network(status_neopixel=board.NEOPIXEL, esp=esp)

text_info, color_info, speed_info = DesUpdate()

# Coords MILL
LAT = "38.720"
LON = "-9.141"

print("Getting weather for {} {}".format(LAT, LON))

DATA_SOURCE = (
    f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&units=metric"
)
DATA_SOURCE += "&appid=" + secrets["openweather_token"]

DATA_LOCATION = []

# Minimum time to hold each page in the top section
# Notice the scroll is code-blocking so text will scroll to the end of current line
# before evaluating the page change timer
PAGE_HOLD_TIME = 1.5

# --- Display setup ---
color = color_info
speed = speed_info
matrix = Matrix()
# network = Network(status_neopixel=board.NEOPIXEL, esp=esp)
gfx = openweather_graphics.OpenWeather_Graphics(matrix.display, text_info, color, speed)
print("gfx loaded")

localtime_refresh = None
weather_refresh = None
page_change = None

# Initialize the button as a digital input with a pull-up resistor
button_up = digitalio.DigitalInOut(board.BUTTON_UP)
button_up.direction = digitalio.Direction.INPUT
button_up.pull = digitalio.Pull.UP

while True:
    if not button_up.value:  # button is pressed
        print("Button pressed")
        text_new, color_new, speed_new = DesUpdate()
        print("Checking!")
        
        gfx.descUpdate(text_new, color_new, speed_new)
        print("gfx loaded")

    # only query the online time once per hour (and on first run)
    if (not localtime_refresh) or (time.monotonic() - localtime_refresh) > 3600:
        try:
            print("Getting time from internet!")
            network.get_local_time()
            localtime_refresh = time.monotonic()
        except RuntimeError as e:
            print("Some error (online time) occured, retrying! -", e)
            continue

    # only query the weather every 10 minutes (and on first run)
    if (not weather_refresh) or (time.monotonic() - weather_refresh) > 600:
        try:
            value = network.fetch_data(DATA_SOURCE, json_path=(DATA_LOCATION,))
            gfx.display_weather(value)
            weather_refresh = time.monotonic()
        except RuntimeError as e:
            print("Some error (weather) occurred, retrying! -", e)
            continue

    # Non-blocking page change timer logic
    if (not page_change) or (time.monotonic() - page_change) > PAGE_HOLD_TIME:
        # update clock text before page changes
        gfx.update_clock(RTC().datetime)
        gfx.show_next_page()
        page_change = time.monotonic()

    gfx.scroll_next_label()
