import os
import shlex
import subprocess

import monitors

def is_bspwm():
    session = os.getenv("XDG_SESSION_DESKTOP")
    return session == "bspwm"

def get_focused_monitor():
    if is_bspwm():
        return subprocess.check_output(shlex.split(
            "bspc query -M -d focused --names")).decode().strip()

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

def get_focused_workspace_name():
    if is_bspwm():
        return subprocess.check_output(shlex.split(
            "bspc query -D -d focused --names")).decode().strip()

def focus_workspace_with_name(name):
    os.system("bspc desktop -f " + str(name))

def select_target_workspace(n_rows, n_cols, current, direction):
    target = current
    if direction == "l":
        is_leftmost = (current % n_cols == 1)
        if not is_leftmost:
            target = current - 1
    if direction == "r":
        is_rightmost = (current % n_cols == 0)
        if not is_rightmost:
            target = current + 1
    if direction == "u":
        is_topmost = (current <= n_cols)
        if not is_topmost:
            target = current - n_cols
    if direction == "d":
        is_bottommost = (current > (n_rows - 1) * n_cols)
        if not is_bottommost:
            target = current + n_cols

    return target
