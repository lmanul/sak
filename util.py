# coding=utf-8
"Various 'Swiss-army knife' utilities"

import os
import re
import shlex

import subprocess
import sys

from datetime import date
from datetime import datetime

try:
    from colorama import Fore, Style
    has_colorama = True
except (ModuleNotFoundError, ImportError):
    has_colorama = False

def is_android():
    uname = subprocess.check_output(["uname", "-a"]).decode("utf-8")
    return "android" in uname.lower()


def is_mac():
    uname = subprocess.check_output(["uname", "-a"]).decode("utf-8")
    return "darwin" in uname.lower()


def is_linux():
    uname = subprocess.check_output(["uname", "-a"]).decode("utf-8")
    return "linux" in uname.lower() and "android" not in uname.lower()


def get_platform():
    if is_android():
        return "android"
    if is_mac():
        return "mac"
    if is_linux():
        return "linux"
    return "unknown"

def is_screen_session():
    env_var = os.getenv("STY")
    return env_var != None and env_var.strip() != ""

def instances_of_process_running(process, apart_from=None):
    s = subprocess.Popen(["ps", "aux"], stdout=subprocess.PIPE)
    instances = []
    for x in s.stdout:
        l = x.decode().strip()
        if re.search(process, l):
            if apart_from != None and str(apart_from) in l:
                continue
            if not "defunct" in l:
                instances.append(l)
    return instances

# Returns whether a process containing the given name is running.
def is_process_running(process, apart_from=None):
    instances = instances_of_process_running(process, apart_from)
    return len(instances) != 0

def spawn(cmd):
    subprocess.Popen(shlex.split(cmd), stdin=None, stdout=None, stderr=None)

def get_image_dimensions(img):
    if img.endswith(".xcf"):
        output = (
            subprocess.check_output(shlex.split("xcfinfo '" + img + "'"))
            .decode()
            .strip()
            .split("\n")[0]
        )
    else:
        output = (
            subprocess.check_output(shlex.split("identify '" + img + "'"))
            .decode()
            .strip()
        )
    parsed = re.match(r".*\s(\d+)x(\d+)\s.*", output)
    width = int(parsed.group(1))
    height = int(parsed.group(2))
    return (width, height)


def get_image_resolution(img):
    "Returns the resolution of the given image."
    if img.endswith(".png"):
        return "0x0"
    x_res = "unknown"
    y_res = "unknown"
    command = "exiftool " + img
    lines = subprocess.check_output(shlex.split(command)).decode().split("\n")
    for l in lines:
        if "Resolution" in l:
            if l.startswith("X Res"):
                x_res = re.search(r"(\d+)", l).group(1)
            if l.startswith("Y Res"):
                y_res = re.search(r"(\d+)", l).group(1)
    return str(x_res) + "x" + y_res


def get_pdf_pages(pdf_path):
    "Returns the number of pages in the given PDF file"
    output = subprocess.check_output(["pdfinfo", pdf_path]).decode()
    lines = output.split("\n")
    for l in lines:
        if "Pages:" in l:
            value = l.replace("Pages:", "").strip()
            return int(value)
    return None


def get_pdf_dimension(pdf_path):
    "Returns the dimensions of the given PDF file"
    output = subprocess.check_output(["pdfinfo", pdf_path]).decode()
    lines = output.split("\n")
    for l in lines:
        if "Page size:" in l:
            parsed = re.match(r".*:\s+([\d\.]+)\s+x\s+([\d\.]+)\s+.*", l)
            return (float(parsed.group(1)), float(parsed.group(2)))
    return None


def get_ram_gb():
    "Returns the amount of RAM in gigabytes"
    output = subprocess.check_output(shlex.split("free -g")).decode()
    lines = output.split("\n")
    for l in lines:
        if l.startswith("Mem:"):
            parsed = re.match(r"Mem:\s+([\d]+)\s+.*", l)
            return int(parsed.group(1))
    return None


def sanitize_for_filename_one_pass(input):
    output = ""
    for c in input:
        next = ""
        if c in [
                " ", "~", "(", ")", ",", ";", ":", "?", "!", "'", '"',
                "/", "|", "[", "]", "{", "}", "&", "#", "@", "$", "+",
        ]:
            if output[-1:] != "_":
                next = "_"
        elif ord(c) < 128:
            next += c
        elif c in ["é", "è", "ê", "ë"]:
            next = "e"
        elif c in ["à", "á", "â"]:
            next = "a"
        output += next
        if len(output) > 256:
            break
    if output[-1:] in ["_", "."]:
        output = output[:-1]
    if len(output) > 0 and output[0] in ["_"]:
        output = output[1:]
    # Standard image extensions
    if output.endswith(".jpeg"):
        output = output.replace(".jpeg", ".jpg")
    if output.endswith(".JPG"):
        output = output.replace(".JPG", ".jpg")
    if output.endswith(".PNG"):
        output = output.replace(".PNG", ".png")
    output = output.replace("._", "_")
    output = output.replace("_.", ".")
    output = output.replace("-_", "_")
    output = output.replace("__", "_")
    output = output.replace("..", ".")
    output = output.replace("--", "-")
    if output.startswith("-"):
        output = output[1:]
    return output


def sanitize_for_filename(in_filename):
    current = in_filename
    while True:
        new = sanitize_for_filename_one_pass(current)
        if new == current:
            return new
        current = new
    return current

def get_date_prefix():
    now = datetime.now()
    return str(now.year) + "-" + str(now.month).zfill(2) + "-" + str(now.day).zfill(2)


def remove_extension(f):
    last_dot = f.rfind(".")
    return f[:last_dot]


def add_suffix_before_extension(f, suffix):
    last_dot = f.rfind(".")
    return f[:last_dot] + suffix + "." + f[last_dot + 1 :]


def get_extension(f):
    last_dot = f.rfind(".")
    return f[last_dot + 1 :]


def change_extension(f, new_ext):
    last_dot = f.rfind(".")
    return f[:last_dot] + "." + new_ext


def get_git_branches():
    "Returns a list of git branch names in the current directory"
    raw = subprocess.check_output(shlex.split("git branch")).decode()
    branches = []
    for line in raw.split("\n"):
        line = line.strip()
        if line == "":
            continue
        if line.startswith("* "):
            line = line[2:]
        branches.append(line)
    return branches


def get_busy_lock_path():
    return os.path.join(os.path.expanduser("~"), "busy")

def is_busy():
    return os.path.exists(get_busy_lock_path())

def set_busy(flag):
    p = get_busy_lock_path()
    if flag:
        os.system("touch " + p)
    else:
        if is_busy():
            os.system("rm " + p)

def run_bin_cmd(cmd, args=None, detach=False):
    locations = [
        os.path.join(os.getcwd()),
        os.path.join(os.path.expanduser("~"), "bus", "bin"),
        os.path.join(os.path.expanduser("~"), "bus", "bin", "browsers"),
        os.path.join(os.path.expanduser("~"), "repos", "sak"),
        os.path.join("/usr", "bin"),
    ]

    good_path = ""
    for l in locations:
        if os.path.exists(os.path.join(l, cmd)):
            good_path = os.path.join(l, cmd)
            break

    if good_path == "":
        print("Couldn't find '" + cmd + "', sorry!")
        return

    if args:
        cmd = good_path + " " + args
    else:
        cmd = good_path
    if detach:
        spawn(cmd)
        return None
    # print(cmd)
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output = ""
    for l in iter(process.stdout.readline, b""):
        l = l.decode()
        sys.stdout.write(l)
        output += l
    return output

def run_bin_cmd_if_not_running(cmd, args=None, detach=False):
    bin_name = cmd
    if " " in cmd:
        bin_name = cmd.split(" ")[1]
    if is_process_running(cmd):
        return
    run_bin_cmd(cmd, args=args, detach=detach)


def run_bin_cmd_kill_existing(cmd, args=None):
    bin_name = cmd
    if " " in cmd:
        bin_name = cmd.split(" ")[1]
    run_bin_cmd("killgrep", args=bin_name)
    run_bin_cmd(cmd, args=args)


def get_current_brightness_and_display_id():
    raw = subprocess.check_output(shlex.split("xrandr --current --verbose")).decode()
    current_display_id = ""
    for l in raw.split("\n"):
        if "connected" in l:
            matches = re.match(r"(.+)\s+connected", l)
            if matches:
                current_display_id = matches.group(1)
        if "Brightness" in l:
            matches = re.match(r"\s*Brightness:\s+(.*)", l)
            if matches:
                brightness = float(matches.group(1))
                return (brightness, current_display_id)
    return None

# Returns an array of arrays: the first array is connected monitor ids,
# the second is disconnected monitor ids.
def get_monitors():
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

def is_online():
    try:
        import httplib
    except:
        import http.client as httplib

        conn = httplib.HTTPConnection("www.google.com", timeout=5)
    try:
        conn.request("HEAD", "/")
        conn.close()
        return True
    except:
        conn.close()
        return False


# Runs the given command and silence stdout and stderr.
def silent(command):
    return os.system(command + " > /dev/null 2>&1")


# Convert back and forth from date object to YYYY.MM.DD
def string_to_date(date_string):
    return date(*([int(c) for c in date_string.split(".")]))


def date_to_string(d):
    return ".".join([str(d.year), str(d.month).zfill(2), str(d.day).zfill(2)])

def color(text, color_name):
    if not has_colorama:
        return text
    colors = {
        "cyan": Fore.CYAN,
        "dim": Style.DIM,
        "green": Fore.GREEN,
        "lightred": Fore.LIGHTRED_EX,
        "red": Fore.RED,
        "white": Fore.WHITE,
        "yellow": Fore.YELLOW,
    }
    if color_name not in colors:
        return text
    return colors[color_name] + text + Style.RESET_ALL

# |values| is a list of series. A series is a list of points. A point is a
# [date, value] pair. A date is formatted as YYYY.MM.DD.
def make_time_graph(values, out_file, names=[]):
    import leather
    leather.theme.legend_font_family = 'Roboto'
    leather.theme.legend_font_size = '12'
    leather.theme.legend_color = '#999999'
    leather.theme.tick_font_family = 'Roboto'
    leather.theme.tick_font_size = '12'
    leather.theme.tick_color = '#aaa'

    colors = [
        "#8c00e2",
        "#1981d4",
        "#00a22c",
        "#ea8500",
        "#e32d14",
        "#ff72db",
        "#00d69e",
        "#1618db",
    ]
    if len(names) != 0:
        if len(names) != len(values):
            print(
                "You've given me " + str(len(values)) + ""
                " series but " + str(len(names)) + " names. Aborting."
            )
            return
    # Find the earliest and latest dates in all series.
    first_date_string = values[0][0][0]
    last_date_string = values[0][-1][0]
    for series in values:
        for point in series:
            if point[0] < first_date_string:
                first_date_string = point[0]
            if point[0] > last_date_string:
                last_date_string = point[0]
    first_date_parts = [int(v) for v in first_date_string.split("-")]
    last_date_parts = [int(v) for v in last_date_string.split("-")]
    first_date = datetime.combine(date(*first_date_parts), datetime.min.time())
    last_date = datetime.combine(date(*last_date_parts), datetime.min.time())
    chart = leather.Chart("")
    chart.add_x_scale(first_date, last_date)
    for i in range(len(values)):
        name = names[i] if len(names) > i else ""
        series = []
        for point in values[i]:
            date_parts = [int(p) for p in point[0].split("-")]
            d = datetime.combine(date(*date_parts), datetime.min.time())
            value = float(point[1])
            series.append([d, value])
        chart.add_line(
            series, name=name, width=0.75, stroke_color=colors[i % len(colors)]
        )
    chart.to_svg("temp.svg")
    if out_file.endswith(".svg"):
        os.system("mv temp.svg " + out_file)
    elif out_file.endswith(".png"):
        os.system("convert -density 800 temp.svg " + out_file)
        os.system("rm temp.svg")
    else:
        print("Sorry, I don't recognize the extension for '" + out_file + "'")
