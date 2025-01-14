import os
import shlex
import subprocess

import monitors

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

def focus_workspace_with_name(name):
    if is_bspwm():
        os.system("bspc desktop -f " + str(name))
    elif is_hyprland():
        cmd = "hyprctl dispatch workspace " + str(name)
        print(cmd)
        os.system(cmd)

def notify(text, icon_path=None):
    time_ms = 500
    if is_bspwm() or is_hyprland():
        # Should work for both as long as "dunst" is running.
        icon_option = "" if icon_path is None else "--icon " + icon_path
        # In BSPWM, the icon is enough, no need for text for now.
        cmd = f"notify-send --urgency=low --expire-time={time_ms} '{text}' " + icon_option
        print(cmd)
        os.system(cmd)
    # elif is_hyprland():
    #     # No custom icons?
    #     icon_option = "-1"
    #     color = "888888"
    #     # icon_option = "-1" if not icon_path else '--icon "' + icon_path + '"'
    #     # print(f'hyprctl notify {icon_option} {time_ms} "rgb(ff1ea3)" "{text} + Hello everyone!"')
    #     os.system(f'hyprctl notify {icon_option} {time_ms} "rgb({color})" "{text}"')

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
