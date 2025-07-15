import json
import os
import re
import shlex
import subprocess
import util

from enum import IntEnum

MODE_LINE_X11_PATTERN = re.compile(r'^\s+(\d+)x(\d+)\s+(.*)$')
MODE_LINE_WAYLAND_PATTERN = re.compile(r'^\s+(\d+)x(\d+)\s+px,\s.*$')
SINGLE_RESOLUTION_PATTERN = re.compile(r'^(\d+)x(\d+)@(\d+)Hz$')

class MonitorResolution():
    def __init__(self, width, height, frequency):
        self.width = width
        self.height = height
        self.frequency = frequency

    def __str__(self):
        return str(self.width) + "x" + str(self.height) + "@" + str(self.frequency)

    def equals(self, other):
        is_equal = self.equals_without_frequency(other) and \
            int(self.frequency) - 2 <= int(other.frequency) and \
            int(self.frequency) + 2 >= int(other.frequency)
        return is_equal

    def equals_without_frequency(self, other):
        return self.width == other.width and self.height == other.height

    def surface(self):
        return int(self.height * self.width * self.frequency)

class MonitorRotation(IntEnum):
    DEFAULT = 0
    LEFT = 90
    RIGHT = 270
    UPSIDE_DOWN = 180

    def to_xrandr(self):
        if self == MonitorRotation.DEFAULT:
            return "normal"
        if self == MonitorRotation.RIGHT:
            return "right"
        if self == MonitorRotation.LEFT:
            return "left"
        if self == MonitorRotation.UPSIDE_DOWN:
            return "TODO"

    def __str__(self):
        if self == MonitorRotation.DEFAULT:
            return "normal"
        if self == MonitorRotation.RIGHT:
            return "right"
        if self == MonitorRotation.LEFT:
            return "left"
        if self == MonitorRotation.UPSIDE_DOWN:
            return "upside down"

class Monitor:
    "Represents a monitor, with id, orientation, resolution"
    def __init__(self, input_id="unknown_input_id", rotation=MonitorRotation.DEFAULT, scale=1,
                 resolution=(0, 0), force_off=False,
                 description="Generic Monitor", primary=False, connected=True):
        self.input_id = input_id
        self.rotation = rotation
        self.scale = scale
        self.resolution = resolution
        self.supported_resolutions = []
        self.description = description
        self.primary = primary
        self.connected = connected
        self.force_off = force_off

    def get_resolution_str(self):
        return str(self.resolution[0]) + "x" + str(self.resolution[1])

    def get_resolution(self):
        if (len(self.supported_resolutions) == 1):
            return self.supported_resolutions[0]
        return self.get_max_resolution()

    # Returns whether the resolution was actually added
    def add_supported_resolution(self, res):
        for r in self.supported_resolutions:
            if r.equals(res):
                # Already listed
                return False
        self.supported_resolutions.append(res)
        return True

    def get_max_resolution(self):
        max_surface = 0
        current_max = None
        for r in self.supported_resolutions:
            if r.surface() > max_surface:
                current_max = r
                max_surface = r.surface()
        return current_max

    def get_max_resolution_str_no_frequency(self):
        freq = self.get_max_resolution()
        return str(freq.width) + "x" + str(freq.height)

    def to_xrandr_arg(self):
        if self.force_off:
            return "--output " + self.input_id + " --off"
        return " ".join([
            "--output " + self.input_id,
            "--mode " + str(self.get_max_resolution_str_no_frequency()),
            "--scale " + str(self.scale) + "x" + str(self.scale),
            "--rotate " + self.rotation.to_xrandr(),
            "--primary" if self.primary else "",
        ])

    def to_wlrrandr_arg(self):
        if self.force_off:
            return "--output " + self.input_id + " --off"
        return " ".join([
            "--output " + self.input_id,
            "--mode " + self.get_max_resolution_str_no_frequency(),
            "--scale " + str(self.scale),
            "--transform " + str(self.rotation) if self.rotation != 0 else "",
            # TODO: what is the equivalent of "primary"?
        ])

    def __str__(self):
        connected = "connected" if self.connected else "disconnected"
        return (f"[Monitor {self.input_id} \"{self.description}\" | "
                f"max={self.get_max_resolution()} | "
                f"rotation={self.rotation} | "
                f"primary={self.primary} | "
                f"{len(self.supported_resolutions)} supported res | "
                "" + connected + "]"
               )

    def __repr__(self):
        return "\n" + self.__str__()

def find_best_match_from_supported_resolutions(needle, haystack):
    best_match = None
    best_match_count = 0
    for m in haystack:
        count = 0
        # Only consider matches with the same max res
        if not m.get_max_resolution().equals_without_frequency(needle.get_max_resolution()):
            continue
        for r in m.supported_resolutions:
            for s in needle.supported_resolutions:
                if r.equals(s):
                    count += 1
        if count > best_match_count:
            best_match = m
            best_match_count = count
    return best_match

def get_monitors_from_hwinfo():
    monitors = []
    lines = subprocess.check_output(
        shlex.split("hwinfo --monitor")).decode().split("\n")
    current_monitor = None
    for l in lines:
        if l.strip() == "":
            continue
        if not l.startswith(" "):
            # New monitor
            if current_monitor is not None:
                monitors.append(current_monitor)
            current_monitor = Monitor()
            continue
        if l.startswith("  Model:"):
            value = l.strip().split("Model: ")[1]
            if value.startswith('"'):
                value = value[1:]
            if value.endswith('"'):
                value = value[:-1]
            current_monitor.description = value
        if l.startswith("  Resolution:"):
            value = l.strip().split("Resolution: ")[1]
            matches = SINGLE_RESOLUTION_PATTERN.match(value)
            r = MonitorResolution(
                int(matches.group(1)), int(matches.group(2)), int(matches.group(3)))
            current_monitor.add_supported_resolution(r)

    # Add last leftover
    monitors.append(current_monitor)
    return monitors

def get_monitors_from_xrandr():
    current_monitor = None
    monitors = []
    xrandr_output = subprocess.check_output(shlex.split("xrandr")).decode()
    for line in xrandr_output.split("\n"):
        if line.strip() == "":
            continue
        if "connected" in line:
            tokens = line.split(" ")
            monitor_id = tokens[0]
            connected = "disconnected" not in line
            primary = "primary" in line
            if current_monitor:
                monitors.append(current_monitor)
            current_monitor = Monitor(monitor_id, connected=connected, primary=primary)
            current_max_surface = 0
            continue

        resolution_matches = MODE_LINE_X11_PATTERN.match(line)
        if resolution_matches:
            w = int(resolution_matches.group(1))
            h = int(resolution_matches.group(2))
            # xrandr sees virtual monitors as disconnected, let's tweak that
            if current_monitor.input_id.startswith("DVI-I-"):
                current_monitor.connected = True
            freqs = []
            freqs_raw_str = resolution_matches.group(3)
            freqs_raw = [f for f in freqs_raw_str.split(" ") if f.strip() != ""]
            for freq_raw in freqs_raw:
                if freq_raw.endswith("+"):
                    freq_raw = freq_raw[:-1]
                if freq_raw.endswith("*"):
                    freq_raw = freq_raw[:-1]
                if freq_raw.strip() == "":
                    continue
                freqs.append(freq_raw)
            for freq in freqs:
                candidate = MonitorResolution(w, h, round(float(freq)))
                was_added = current_monitor.add_supported_resolution(candidate)
        if line.startswith("Screen"):
            continue

    # Don't forget the last monitor
    if current_monitor:
        monitors.append(current_monitor)
    return monitors

def get_monitors_x11():
    # Why TF doesn't xrandr include descriptions?
    # To disambuguate, we need to match supported resolutions from both ends.
    # It's not perfect, let's hope it's reasonably unique.

    try:
        monitors_from_hwinfo = get_monitors_from_hwinfo()
        monitors_from_xrandr = get_monitors_from_xrandr()
    except subprocess.CalledProcessError:
        print("Headless mode, not using xrandr or hwinfo")
        return []

    for m in monitors_from_xrandr:
        if not m.connected:
            continue
        best_match = find_best_match_from_supported_resolutions(m, monitors_from_hwinfo)
        # print("Best match for \n" + str(m) + " is \n" + str(best_match))
        if best_match is not None:
            m.description = best_match.description

    return monitors_from_xrandr

def get_monitors_wayland():
    monitors = []
    randr_output = subprocess.check_output(shlex.split("wlr-randr")).decode()
    current_output = ""
    current_monitor = None
    current_max_surface = 0
    current_make = "Generic"
    current_model = "Monitor"
    current_is_disabled = False
    for line in randr_output.split("\n"):
        resolution_matches = MODE_LINE_WAYLAND_PATTERN.match(line)

        if line.strip() == "":
            continue
        elif not line.startswith("  "):
            parts = line.split(" ")
            current_output = parts[0]
            if current_monitor:
                monitors.append(current_monitor)
            current_monitor = Monitor(current_output)
            current_is_disabled = False
            current_max_surface = 0

        elif "Enabled" in line:
            current_is_disabled = ("no" in line)
            current_monitor.connected = not current_is_disabled

        elif resolution_matches:
            w = int(resolution_matches.group(1))
            h = int(resolution_matches.group(2))
            surface = w * h
            if surface > current_max_surface:
                current_monitor.max_resolution = (w, h)
                current_max_surface = surface

        elif line.strip().startswith("Make:"):
            current_make = line.split(": ")[1]

        elif line.strip().startswith("Model:"):
            current_model = line.split(": ")[1]
            current_monitor.description = current_make + " " + current_model

    if current_monitor:
        monitors.append(current_monitor)
    return monitors

def monitor_from_bspwm_monitor_object(obj):
    monitor = Monitor()
    monitor.input_id = obj["name"]
    if "wired" in obj:
        monitor.connected = obj["wired"]
    monitor.add_supported_resolution(MonitorResolution(obj["rectangle"]["width"], obj["rectangle"]["height"], 60))
    return monitor

def get_monitors_bspwm():
    monitors = []
    monitor_ids = subprocess.check_output(shlex.split("bspc query -M --names")).decode().strip().split("\n")
    for monitor_id in monitor_ids:
        json_str = subprocess.check_output(shlex.split("bspc query -T -m '" + monitor_id + "'")).decode()
        obj = json.loads(json_str)
        monitors.append(monitor_from_bspwm_monitor_object(obj))
    return monitors

def get_monitors():
    if os.getenv("XDG_SESSION_DESKTOP") == "bspwm":
        # This is faster, bspwm caches stuff
        return get_monitors_bspwm()
    if util.is_wayland():
        return get_monitors_wayland()
    else:
        return get_monitors_x11()

# Returns an array of tuples. There is one tuple per screen, and each tuple is
# (id, width_px, width_mm, height_px, height_mm)
def get_monitor_data():
    raw = subprocess.check_output(shlex.split("xrandr --listactivemonitors")).decode()
    data = []
    for i in range(10):
        for l in raw.split("\n"):
            l = l.strip()
            parts = l.split(" ")
            if parts[0] == str(i) + ":":
                monitor_id = parts[-1]
                matches = re.match(r"(\d+)/(\d+)x(\d+)/(\d+)", parts[2])
                (w_px, w_mm, h_px, h_mm) = (
                    int(matches.group(1)),
                    int(matches.group(2)),
                    int(matches.group(3)),
                    int(matches.group(4)),
                )
                data.append([monitor_id, w_px, w_mm, h_px, h_mm])
    return data

def get_screen_dpi(index=None):
    monitor_data = get_monitor_data()
    dpis = []
    for monitor in monitor_data:
        (_, w_px, w_mm, h_px, h_mm) = monitor
        w_in = float(w_mm) / 25.4
        h_in = float(h_mm) / 25.4
        dpi_x = int(float(w_px) / w_in)
        dpi_y = int(float(h_px) / h_in)
        dpi = int(float((dpi_x + dpi_y) / 2))
        dpis.append(dpi)

    if index is not None:
        return dpis[index]
    else:
        return dpis

def get_id_of_largest_monitor():
    monitor_data = get_monitor_data()
    largest_monitor_id = "Unknown"
    largest_pixel_count = 0
    for monitor in monitor_data:
        (monitor_id, width_px, _, height_px, _) = monitor
        pixels = width_px * height_px
        if pixels > largest_pixel_count:
            largest_pixel_count = pixels
            largest_monitor_id = monitor_id
    return largest_monitor_id
