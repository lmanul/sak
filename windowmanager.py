import os
import shlex
import subprocess

import monitors
import util
import virtualdesktops

# Returns true if the XDG session desktop is as expected
def check_desktop(expected):
    return os.getenv("XDG_SESSION_DESKTOP") == expected

def is_bspwm():
    return check_desktop("bspwm")

def is_hyprland():
    return check_desktop("hyprland")

def get_focused_monitor():
    if is_bspwm():
        return subprocess.check_output(shlex.split(
            "bspc query -M -d focused --names")).decode().strip()
    if is_hyprland():
        raw =  subprocess.check_output(shlex.split("hyprctl monitors")).decode().strip()
        current_monitor_id = None
        for line in raw.split("\n"):
            if line.startswith("Monitor "):
                current_monitor_id = line.split(" ")[1]
            line = line.strip()
            if "focused" in line and "yes" in line:
                return current_monitor_id

def get_monitor_ids():
    if is_bspwm():
        # Faster than using xrandr
        return subprocess.check_output(shlex.split(
            "bspc query -M --names")).decode().strip().split("\n")
    connected_monitors = [m for m in monitors.get_monitors() if m.connected]
    return [m.input_id for m in connected_monitors]

def focus_monitor_with_id(monitor_id):
    if is_bspwm():
        os.system("bspc monitor -f " + monitor_id)
    elif is_hyprland():
        cmd = "hyprctl dispatch focusmonitor " + monitor_id
        os.system(cmd)

def get_focused_workspace_name():
    if is_bspwm():
        return subprocess.check_output(shlex.split(
            "bspc query -D -d focused --names")).decode().strip()
    if is_hyprland():
        raw = subprocess.check_output(shlex.split(
            "hyprctl activeworkspace")).decode().strip()
        return raw.split("\n")[0].split(" ")[2]
    return "1"

def toggle_fullscreen():
    if is_bspwm():
        cmd = "bspc query -N -n 'focused.fullscreen'"
        is_fullscreen = False
        try:
            fullscreen_node = subprocess.check_output(shlex.split(cmd)).decode().strip()
            is_fullscreen = fullscreen_node != ""
        except subprocess.CalledProcessError as e:
            pass
        os.system("bspc node -t " + ("tiled" if is_fullscreen else "fullscreen"))
    elif is_hyprland():
        os.system("hyprctl dispatch fullscreen")

def focus_workspace_with_name(name):
    start = util.current_time_milliseconds()
    if is_bspwm():
        os.system("bspc desktop -f " + str(name))
    elif is_hyprland():
        # Name is actually a 1-based index
        name = int(name)
        # The workspace may not exist yet, ensure it lives
        cmd = "hyprctl dispatch workspace " + str(name)
        os.system(cmd)
        util.log_time(start, "Dispatched ws " + str(name))
        ensure_workspace(name, 3, 3) # TODO: configure
        util.log_time(start, "Ensured ws " + str(name))

def ensure_workspace(index, n_rows, n_cols):
    # index is 1-based
    square = n_rows * n_cols
    name = virtualdesktops.name_from_index(index, n_rows, n_cols)
    ms = monitors.get_monitors()
    corresponding_monitor = ms[(index - 1) // square].input_id
    if is_hyprland():
        cmd = f"hyprctl dispatch moveworkspacetomonitor {index} {corresponding_monitor}"
        os.system(cmd)
        cmd = f"hyprctl dispatch renameworkspace {index} {name}"
        os.system(cmd)
        cmd = "hyprctl dispatch workspaceopt persistent"
        os.system(cmd)

def notify(text, icon_path=None):
    time_ms = 500
    if is_bspwm() or is_hyprland():
        # Should work for both as long as "dunst" is running.
        icon_option = "" if icon_path is None else "--icon " + icon_path
        # In BSPWM, the icon is enough, no need for text for now.
        cmd = f"notify-send --urgency=low --expire-time={time_ms} '{text}' " + icon_option
        os.system(cmd)

# Returns a workspace index, 1-based
def select_target_workspace(n_rows, n_cols, current, direction):
    target = current
    if direction == "l":
        is_leftmost = current % n_cols == 1
        if not is_leftmost:
            target = current - 1
    if direction == "r":
        is_rightmost = current % n_cols == 0
        if not is_rightmost:
            target = current + 1
    if direction == "u":
        is_topmost = current <= n_cols
        if not is_topmost:
            target = current - n_cols
    if direction == "d":
        is_bottommost = current > (n_rows - 1) * n_cols
        if not is_bottommost:
            target = current + n_cols

    return target

def move_mouse_to_center_of_monitor(monitor_id):
    """Move the mouse to the center of the specified monitor."""

    offset_x = 0
    connected_monitors = [m for m in monitors.get_monitors() if m.connected]

    monitor_to_focus = None
    for m in connected_monitors:
        if monitor_id == m.input_id:
            monitor_to_focus = m
            break
        else:
            offset_x += m.get_resolution().width
    if not monitor_to_focus:
        print("Could not find monitor " + monitor_id)
    res = monitor_to_focus.get_resolution()

    center_x = offset_x + res.width / 2
    center_y = res.height / 2
    try:
        subprocess.run(['xdotool', 'mousemove', str(center_x), str(center_y)])
    except subprocess.CalledProcessError as e:
        print("Error moving mouse:", e)
