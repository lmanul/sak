#!/usr/bin/python3

import datetime
import pytz

from colorama import Style, Fore

TZ = [
    ["US/Hawaii", "Hawaii"],
    ["America/Los_Angeles", "San Francisco"],
    ["America/New_York", "New York"],
    ["Etc/UTC", "UTC"],
    ["Europe/Paris", "Paris"],
    ["Asia/Bangkok", "Bangkok"],
    ["Asia/Shanghai", "Shanghai"],
    ["Asia/Tokyo", "Tokyo"],
    ["Australia/Sydney", "Sydney"],
]

date_has_been_shown = False
for i in range(len(TZ)):
    tz = TZ[i]
    filler = " " * (15 - len(tz[1]))
    now = str(datetime.datetime.now(pytz.timezone(tz[0]))).split(" ")
    if i < len(TZ) - 1:
        now_in_next_line = str(datetime.datetime.now(pytz.timezone(TZ[i + 1][0]))).split(" ")
        day_for_next_line = now_in_next_line[0].replace("-", ".")
    day = now[0].replace("-", ".")
    # Remove precision after minutes
    time = now[1][:-16]
    print(
        (Fore.CYAN if "UTC" in tz else Fore.WHITE)
        + tz[1]
        + filler
        + time
        + "   "
        + Style.DIM + day + Style.NORMAL
        + Style.RESET_ALL
    )
