import os
import shlex
import subprocess

DIGITS = [str(d) for d in range(10)]
HEX_LETTERS = ['A', 'B', 'C', 'D', 'E', 'F']

def collapse_spaces(s):
    parts = s.split(" ")
    final_parts = []
    for p in parts:
        if p != "":
            final_parts.append(p)
    return " ".join(final_parts)

def is_hex_char(c):
    return c in DIGITS or c in HEX_LETTERS

def is_hex_code(s):
    if len(s) != 2:
        return False
    return is_hex_char(s[0]) and is_hex_char(s[1])

def get_available_ssids():
    os.system("nmcli device wifi rescan")
    cmd = "nmcli --terse device wifi list"
    available_ssids_raw = subprocess.check_output(shlex.split(cmd)).decode()
    available_ssids = set()
    for l in available_ssids_raw.split("\n"):
        parts = collapse_spaces(l).split(":")
        for p in parts:
            p = p.replace("\\", "")
            if len(p) < 2:
                continue
            if is_hex_code(p):
                continue
            # Assume the first field that gets through to here is the SSID.
            available_ssids.add(p)
            break
    return sorted(list(available_ssids))
