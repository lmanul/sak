import os
import shlex
import subprocess

def get_size(f):
    raw = subprocess.check_output(shlex.split("file " + f)).decode().strip()
    for part in raw.split(", "):
        if " x " in part:
            (w, h) = part.split(" x ")
            return (int(w), int(h))

    return (0, 0)
