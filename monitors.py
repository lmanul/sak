class Monitor:
    "Represents a monitor, with id, orientation, resolution"
    def __init__(self, input_id, rotation="normal", scale=1, resolution=None,
                 primary=False, connected=True):
        self.input_id = input_id
        self.rotation = rotation
        self.scale = scale
        self.resolution = resolution
        self.primary = primary
        self.connected = connected

    def __str__(self):
        return "'" + self.input_id + " -- " + ("" if self.connected else "dis") + "connected"

def get_monitors_x11():
    connected_monitors = []
    disconnected_monitors = []
    try:
        xrandr_output = subprocess.check_output(shlex.split("xrandr")).decode()
        for line in xrandr_output.split("\n"):
            if line.strip() == "":
                continue
            if line.startswith("Screen"):
                continue
            if line.startswith("   "):
                continue
            tokens = line.split(" ")
            id = tokens[0]
            status = tokens[1]
            if status == "connected":
                connected_monitors.append(id)
            elif status == "disconnected":
                disconnected_monitors.append(id)
    except subprocess.CalledProcessError:
        print("Headless mode, not using xrandr")
    return [connected_monitors, disconnected_monitors]

def get_monitors_wayland():
    connected_monitors = []
    disconnected_monitors = []
    randr_output = subprocess.check_output(shlex.split("wlr-randr")).decode()
    current_output = ""
    current_is_disabled = False
    for line in randr_output.split("\n"):
        if line == "":
            continue
        if "Enabled" in line:
            current_is_disabled = ("no" in line)
        if not line.startswith("  "):
            parts = line.split(" ")
            if current_output != "":
                if current_is_disabled:
                    disconnected_monitors.append(current_output)
                else:
                    connected_monitors.append(current_output)
            current_output = parts[0]
            current_is_disabled = False

    if current_is_disabled:
        disconnected_monitors.append(current_output)
    else:
        connected_monitors.append(current_output)
    return [connected_monitors, disconnected_monitors]

# Returns an array of arrays: the first array is connected monitor ids,
# the second is disconnected monitor ids.
def get_monitors():
    if os.environ["XDG_SESSION_TYPE"] == "wayland":
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
