#!/usr/bin/python3

import argparse
import datetime
import pytz

from colorama import Style, Fore

TZ = [
    # TZ, City name, Short name, Icon, Include in mini
    ["Pacific/Honolulu", "Hawaii", "HWI", "", False],
    ["America/Los_Angeles", "San Francisco", "SFO", "🇺🇸", True],
    ["America/Denver", "Denver", "DNV", "🇺🇸", False],
    ["America/Chicago", "Chicago", "CHI", "🇺🇸", False],
    ["America/New_York", "New York", "NYC", "🇺🇸", True],
    ["Etc/UTC", "UTC", "UTC", "🌍", True],
    ["Europe/Paris", "Paris", "PAR", "🇫🇷", True],
    ["Europe/Tallinn", "Tallinn", "TAL", "🇪🇪", False],
    ["Asia/Bangkok", "Bangkok", "BKK", "🇹🇭", False],
    ["Asia/Shanghai", "Shanghai", "SHA", "🇨🇳", True],
    ["Asia/Tokyo", "Tokyo", "TOK", "🇯🇵", True],
    ["Australia/Sydney", "Sydney", "SYD", "🇦🇺", False],
]

parser = argparse.ArgumentParser()
parser.add_argument('-i', '--icons', action='store_true')
parser.add_argument('-l', '--inline', action='store_true')
parser.add_argument('-s', '--short', action='store_true')
parser.add_argument('-m', '--mini', action='store_true')
parser.add_argument('-n', '--nocolor', action='store_true')

def get_label(tz, args):
    return tz[3 if args.icons else 2 if args.short else 1]

def print_horizontal_line(width):
    print("+" + "-" * (len("| ") + width + len("00:00") + len(" |") - 2) + "+")

if __name__ == "__main__":
    args = parser.parse_args()
    max_width = 2 + max([len(get_label(tz, args)) for tz in TZ])
    last_row_index = len([tz for tz in TZ if not args.mini or tz[4]]) - 1
    row = 0
    if not args.inline:
        print_horizontal_line(max_width)
    for i in range(len(TZ)):
        tz = TZ[i]
        if args.mini and not tz[4]:
            continue
        filler = " " if args.inline else (" " * (max_width - len(get_label(tz, args))))
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
        label = get_label(tz, args)
        print(
            ("" if args.nocolor else Fore.CYAN if "UTC" in tz else Fore.WHITE)
            + label
            + filler
            + time
            + ("" if args.nocolor else Style.RESET_ALL), end=""
        )
        if not args.inline:
            print(" |", end="")
        if should_show_date:
            print(
                "   "
                + Style.DIM + day + Style.NORMAL, end=""
            )
        if args.inline and row != last_row_index:
            print(" | ", end="")
        if not args.inline:
            print()
        row += 1
    if not args.inline:
        print_horizontal_line(max_width)
