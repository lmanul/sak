#!/usr/bin/python3

import datetime
import pytz

from colorama import Style, Fore

MAX_WIDTH = 15

TZ = [
    ["US/Hawaii", "Hawaii"],
    ["America/Los_Angeles", "San Francisco"],
    ["America/Denver", "Denver"],
    ["America/Chicago", "Chicago"],
    ["America/New_York", "New York"],
    ["Etc/UTC", "UTC"],
    ["Europe/Paris", "Paris"],
    ["Europe/Tallinn", "Tallinn"],
    ["Asia/Bangkok", "Bangkok"],
    ["Asia/Shanghai", "Shanghai"],
    ["Asia/Tokyo", "Tokyo"],
    ["Australia/Sydney", "Sydney"],
]

if __name__ == "__main__":
    print("-" * (len("| ") + MAX_WIDTH + len("00:00") + len(" |")))
    for i in range(len(TZ)):
        tz = TZ[i]
        filler = " " * (MAX_WIDTH - len(tz[1]))
        try:
            now = datetime.datetime.now(pytz.timezone(tz[0]))
            now_str = str(now).split(" ")
            day_of_week = now.strftime("%a")
            day = day_of_week + " " + now_str[0]
            day_for_next_line = day
            day_for_prev_line = day
            if i < len(TZ) - 1:
                now_in_next_line = datetime.datetime.now(pytz.timezone(TZ[i + 1][0]))
                now_in_next_line_str = str(now_in_next_line).split(" ")
                day_of_week_next_line = now_in_next_line.strftime("%a")
                day_for_next_line = day_of_week_next_line + " " + now_in_next_line_str[0]
            if i > 0:
                now_in_prev_line = datetime.datetime.now(pytz.timezone(TZ[i - 1][0]))
                now_in_prev_line_str = str(now_in_prev_line).split(" ")
                day_of_week_prev_line = now_in_prev_line.strftime("%a")
                day_for_prev_line = day_of_week_prev_line + " " + now_in_prev_line_str[0]
        except pytz.exceptions.UnknownTimeZoneError:
            print("Warning, unknown time zone " + str(tz))
            continue

        # Remove precision after minutes
        time = now_str[1][:-16]
        should_show_date = day_for_next_line != day or day_for_prev_line != day
        print("| ", end="")
        print(
            (Fore.CYAN if "UTC" in tz else Fore.WHITE)
            + tz[1]
            + filler
            + time
            + Style.RESET_ALL, end=""
        )
        print(" |", end="")
        if should_show_date:
            print(
                "   "
                + Style.DIM + day + Style.NORMAL, end=""
            )
        print()
    print("-" * (len("| ") + MAX_WIDTH + len("00:00") + len(" |")))
