#!/usr/bin/python3

import argparse
import datetime
import pytz

from colorama import Style, Fore

TZ = [
    ["Pacific/Honolulu", "Hawaii", "🌴"],
    ["America/Los_Angeles", "San Francisco", "🇺🇸"],
    ["America/Denver", "Denver", "🇺🇸"],
    ["America/Chicago", "Chicago", "🇺🇸"],
    ["America/New_York", "New York", "🇺🇸"],
    ["Etc/UTC", "UTC", "🌍"],
    ["Europe/Paris", "Paris", "🇫🇷"],
    #["Europe/Tallinn", "Tallinn", "🇪🇪"],
    # ["Asia/Bangkok", "Bangkok", "🇹🇭"],
    ["Asia/Shanghai", "Shanghai", "🇨🇳"],
    ["Asia/Tokyo", "Tokyo", "🇯🇵"],
    #["Australia/Sydney", "Sydney", "🇦🇺"],
]

parser = argparse.ArgumentParser()
parser.add_argument('-i', '--icons', action='store_true')
parser.add_argument('-l', '--inline', action='store_true')

if __name__ == "__main__":
    args = parser.parse_args()
    max_width = 2 + max([len(tz[2 if args.icons else 1]) for tz in TZ])
    if not args.inline:
        print("-" * (len("| ") + max_width + len("00:00") + len(" |")))
    for i in range(len(TZ)):
        tz = TZ[i]
        filler = " " if args.inline else (" " * (max_width - len(tz[1])))
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
            print("Warning, unknown time zone " + str(tz[0]))
            continue

        # Remove precision after minutes
        time = now_str[1][:-16]
        should_show_date = (day_for_next_line != day or day_for_prev_line != day) and not args.inline
        if not args.inline:
            print("| ", end="")
        label = tz[2 if args.icons else 1]
        print(
            (Fore.CYAN if "UTC" in tz else Fore.WHITE)
            + label
            + filler
            + time
            + Style.RESET_ALL, end=""
        )
        if not args.inline:
            print(" |", end="")
        if should_show_date:
            print(
                "   "
                + Style.DIM + day + Style.NORMAL, end=""
            )
        if args.inline:
            print(" ", end="")
        else:
            print()
    if not args.inline:
        print("-" * (len("| ") + max_width + len("00:00") + len(" |")))
