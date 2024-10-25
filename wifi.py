"""
Various utilities related to managing and connecting to wireless networks.
"""

import os
import shlex
import subprocess
import util

DIGITS = [str(d) for d in range(10)]
HEX_LETTERS = ['A', 'B', 'C', 'D', 'E', 'F']

def collapse_spaces(s):
    "Collapses multiple spaces into just one"
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

def get_current_wifi():
    lines = subprocess.check_output(shlex.split("nmcli con")).decode().split("\n")
    current = lines[1].split("  ")[0].strip()
    if current == "lo":
        return ""
    return current

def connect_to_wifi_with_ssid(ssid, debug=False):
    print("Connecting to '" + ssid + "'...")
    cmd = 'nmcli device wifi connect "' + ssid + '"'
    os.system(cmd)

def connect_to_wifi(path_to_known_networks_list, debug=False):
    "Connects to known wifi points"
    online = util.is_online()
    if online and debug:
        print("Online")
    if not online:
        ssids = get_available_ssids()
        wifis_raw = open(path_to_known_networks_list).readlines()
        wifis = []
        target = None
        for l in wifis_raw:
            l = l.strip()
            if not l:
                continue
            if not l.startswith("#") or l.startswith("\\#"):
                if l.startswith("\\#"):
                    l = l[1:]
                wifis.append(l.split(":"))
        for w in wifis:
            if w[0] in ssids:
                target = w
                break
        if not target:
            print("No known SSID found. Found:\n\t" + "\n\t".join(sorted(ssids)))
            # Re-scan for next time? os.system("nmcli device wifi rescan")
        else:
            if debug:
                print("Trying to connect to: " + str(target))
            ssid = target[0]
            cmd = 'nmcli device wifi connect "' + ssid + '"'
            if target[1] != "":
                cmd += " password '" + target[1] + "'"
            if debug:
                cmd += " 2>> ~/throwaway/tick.txt"
            os.system(cmd)
