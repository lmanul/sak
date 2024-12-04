import os
import re
import shlex
import subprocess
import time
import xmltodict

BOUNDS_PATTERN = re.compile(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]')

def get_screen_size():
    raw = subprocess.check_output(shlex.split("adb shell wm size")).decode()
    # Example: Physical size: 1220x2712
    return [int(n) for n in raw.split(":")[1].strip().split("x")]

def get_view_hierarchy_as_dict():
    os.system("adb shell uiautomator dump")
    xml = subprocess.check_output(shlex.split("adb shell cat /sdcard/window_dump.xml")).decode()
    return xmltodict.parse(xml)

def swipe(x1, y1, x2, y2):
    os.system(f"adb shell input swipe {x1} {y1} {x2} {y2}")
    time.sleep(0.2)

def swipe_up():
    (w, h) = get_screen_size()
    x = int(w / 2)
    y1 = int(2 / 3 * h)
    y2 = int(1 / 3 * h)
    swipe(x, y1, x, y2)

def swipe_down():
    (w, h) = get_screen_size()
    x = int(w / 2)
    y1 = int(1 / 3 * h)
    y2 = int(2 / 3 * h)
    swipe(x, y1, x, y2)

def swipe_left():
    (w, h) = get_screen_size()
    y = int(h / 2)
    x1 = int(2 / 3 * w)
    x2 = int(1 / 3 * w)
    swipe(x1, y, x2, y)

def swipe_right():
    (w, h) = get_screen_size()
    y = int(h / 2)
    x1 = int(1 / 3 * w)
    x2 = int(2 / 3 * w)
    swipe(x1, y, x2, y)

def go_home():
    os.system("adb shell input keyevent KEYCODE_HOME")
    time.sleep(0.1)

def go_back():
    os.system("adb shell input keyevent KEYCODE_BACK")
    time.sleep(0.1)

def tap_on_view(view):
    key = "@bounds"
    if key not in view:
        return
    bounds = view[key]
    m = BOUNDS_PATTERN.match(bounds)
    left = int(m.group(1))
    top = int(m.group(2))
    right = int(m.group(3))
    bottom = int(m.group(4))
    center_x = int((left + right) / 2)
    center_y = int((top + bottom) / 2)
    os.system(f"adb shell input tap {center_x} {center_y}")

# f is a function taking a value as argument and returning true or false.
def recursively_find_dict_with_key_and_value_predicate(d, k, f):
    if k in d and f(d[k]):
        return d
    for local_key in d:
        if isinstance(d[local_key], dict):
            found = recursively_find_dict_with_key_and_value_predicate(d[local_key], k, f)
            if found is not None:
                return found
        if isinstance(d[local_key], list):
            for el in d[local_key]:
                if isinstance(el, dict):
                    found = recursively_find_dict_with_key_and_value_predicate(el, k, f)
                    if found is not None:
                        return found
    return None
