import os
import shlex
import subprocess

def get_focused_monitor():
    session = os.getenv("XDG_SESSION_DESKTOP")
    if session == "bspwm":
        return subprocess.check_output(shlex.split(
            "bspc query -M -d focused --names")).decode().strip()
