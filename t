#!/usr/bin/python3

import datetime
import pytz

from colorama import Style, Fore

TZ = [
    ["US/Hawaii", "Hawaii"],
    ["America/Los_Angeles", "San Francisco"],
    ["America/Denver", "Denver"],
    ["America/New_York", "New York"],
    ["Etc/UTC", "UTC"],
    ["Europe/Paris", "Paris"],
    ["Europe/Tallinn", "Tallinn"],
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
    day = now[0].replace("-", ".")
    day_for_next_line = day
    day_for_prev_line = day
    if i < len(TZ) - 1:
        now_in_next_line = str(datetime.datetime.now(pytz.timezone(TZ[i + 1][0]))).split(" ")
        day_for_next_line = now_in_next_line[0].replace("-", ".")
    if i > 0:
        now_in_prev_line = str(datetime.datetime.now(pytz.timezone(TZ[i - 1][0]))).split(" ")
        day_for_prev_line = now_in_prev_line[0].replace("-", ".")

    # Remove precision after minutes
    time = now[1][:-16]
    should_show_date = day_for_next_line != day or day_for_prev_line != day
    print(
        (Fore.CYAN if "UTC" in tz else Fore.WHITE)
        + tz[1]
        + filler
        + time, end=""
    )
    if should_show_date:
        print(
            "   "
            + Style.DIM + day + Style.NORMAL, end=""
        )
    print(Style.RESET_ALL)
