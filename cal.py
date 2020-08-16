import datetime
import os
import shlex
import subprocess
import sys

from datetime import timedelta

DEBUG = False

HOME = os.path.expanduser("~")
CALCURSE_DATETIME_FORMAT = "%m/%d/%Y @ %H:%M"

def datetime_to_date_tuple(dt):
    return (dt.year, dt.month, dt.day)

def parse_non_repeated_timing(timing):
    """
    Takes an input of the form:

        10/28/2020 @ 16:30 -> 10/28/2020 @ 17:30

    and returns (start_date, end_date) where each date is of time
    datetime.datetime.
    """

    if "->" not in timing:
        # Not parsing this type of event yet
        return (None, None)
    (start, end) = timing.split("->", 1)
    if "@" not in start:
        # Not parsing full-day events yet
        return (None, None)
    start_date = datetime.datetime.strptime(
        start.strip(), CALCURSE_DATETIME_FORMAT)
    end_date = datetime.datetime.strptime(
        end.strip(), CALCURSE_DATETIME_FORMAT)
    return (start_date, end_date)

def parse_repeated_timing(timing):
    repeat_str_start = timing.index("{")
    repeat_str_end = timing.index("}")
    repeat_str = timing[repeat_str_start + 1:repeat_str_end]
    remainder = timing[:repeat_str_start] + timing[repeat_str_end + 1:]
    remainder = remainder.strip()
    (base_event_start, base_event_end) = parse_non_repeated_timing(remainder)
    return (base_event_start, base_event_end, repeat_str)

class Event:
    def __init__(self, l):
        (timing, title) = l.split("|", 1)
        repeated = "{" in timing and "}" in timing
        self.title = title.strip()
        # "Hands off" when there are things I can't parse, don't modify
        self.handsoff = False
        # Only start times
        self.futures = []
        if repeated:
            (start, end, repeat_str) = parse_repeated_timing(timing)
            self.repeat_str = repeat_str
            self.futures = self.populate_futures(start, self.repeat_str)
        else:
            (start, end) = parse_non_repeated_timing(timing)
            self.repeat_str = ""
        if start and end:
            self.valid = True
        else:
            self.valid = False
            return
        self.start = start
        self.end = end
        self.orig_line = l.strip()

    def repeated(self):
        return self.repeat_str != ""

    def includes(self, other):
        if not self.repeated():
            return False
        if self.title.lower() != other.title.lower():
            return False
        if self.orig_line == other.orig_line:
            # Same event
            return False
        if other.start < self.start:
            return False
        if self.start.hour != other.start.hour or \
           self.start.minute != other.start.minute:
            return False

        # If the other event is also repeated, it can still be included in this
        # one, if this one's 'futures' include all others'.
        if other.repeated():
            if len(other.futures) >= len(self.futures):
                return False
            for f in other.futures:
                if f not in self.futures:
                    return False
            return True

        for f in self.futures:
            if datetime_to_date_tuple(other.start) == f:
                return True
        return False

    def sort_key(self):
        m = str(self.start.month).zfill(2)
        d = str(self.start.day).zfill(2)
        return "-".join([str(self.start.year), m, d]) + "|" + \
            ":".join([str(self.start.hour).zfill(2),
                      str(self.start.minute).zfill(2)]) + "|" + \
            self.title[0]

    def populate_futures(self, start, repeat_str):
        max_calc_date = start + timedelta(days=3650)
        parts = repeat_str.split(" ")
        freq_str = parts[0][-1]
        cur = 0
        if freq_str == "W":
            freq = timedelta(weeks=int(parts[cur][:-1]))
        elif freq_str == "M":
            print("Warning: I don't support month repeats yet "
                  "('" + self.title + "')")
            self.handsoff = True
            return []
            # freq = timedelta(months=int(parts[cur][:-1]))
        elif freq_str == "D":
            freq = timedelta(days=int(parts[cur][:-1]))
        else:
            print("Sorry but I can't make sense of this frequency: " + parts[cur])
            sys.exit(1)
        cur += 1
        until = None
        if len(parts) > cur and parts[cur] == "->":
            until = parts[cur + 1]
            until_parts = until.split("/")
            until = datetime.datetime(
                int(until_parts[2]), int(until_parts[0]), int(until_parts[1]))
            cur += 2
        raw_excepts = []
        if len(parts) > cur:
            raw_excepts = parts[cur:]
        for e in raw_excepts:
            if not e.startswith("!"):
                print("Should be an 'except' but doesn't start with '!': " + e)
                sys.exit(1)
        raw_excepts = [e[1:] for e in raw_excepts]
        excepts = []
        for e in raw_excepts:
            if e.count("/") != 2:
                print("Unexpected 'except format': " + e)
            (m, d, y) = e.split("/")
            excepts.append([int(y), int(m), int(d)])
        cur_start = start
        futures = [datetime_to_date_tuple(start)]
        while True:
            cur_start += freq
            if cur_start > max_calc_date or (until and cur_start > until):
                break
            futures.append(datetime_to_date_tuple(cur_start))
        return futures

    def __str__(self):
        if not self.valid:
            return "<invalid event>"
        return "<" + self.title + ">"

    def __eq__(self, other):
        if self.start != other.start or self.end != other.end:
            return False
        if self.title.lower() != other.title.lower():
            return False
        if not self.repeated and not other.repeated:
            return True
        if self.repeat_str != other.repeat_str:
            return False
        return True

    def __ne__(self, other):
        return self != other

    def __lt__(self, other):
        self_key = self.sort_key()
        other_key = other.sort_key()
        if self_key == other_key:
            if self.title.lower() == other.title.lower():
                return self.repeat_str < other.repeat_str
            return self.title < other.title
        return self.sort_key() < other.sort_key()

    def __hash__(self):
        if not self.valid:
            return hash("<invalid>")
        return int(self.start.timestamp()) + int(self.end.timestamp()) + \
            hash(self.title.lower()) + hash(self.repeat_str)

# Assumes the two arguments are sorted (first element of e is lower than
# first element of f). This also assumes the second element of each even is
# greater than the second.
def overlap_or_contiguous(e, f):
    if not e or not f:
        return False
    return f[0] <= e[1]

# Same assumptions as 'overlap_or_continuous'. This also assumes these two
# elements do overlap.
def merge(e, f):
    return (e[0], e[1] if f[1] < e[1] else f[1])

# Takes a list of pairs (start time, end time, in epoch seconds) and returns
# a list of pairs (start time, end time) where continguous and overlapping
# events have been merged.
def reduce_availability(events):
    sorted_events = sorted(events)
    reduced = []
    while len(sorted_events) != 0:
        current = sorted_events.pop(0)
        head = reduced[-1] if len(reduced) else None
        if overlap_or_contiguous(head, current):
            reduced[-1] = merge(head, current)
        else:
            reduced.append(current)

    return reduced

# Returns a list where each element is itself a list of three elements:
# start time, end time (both in seconds since the epoch) and title.
def get_events_for_next_n_days(days):
    event_format = "%s|%e|%m"
    out = []
    cmd = ("calcurse "
           "-r" + str(days) + " "
           "--format-apt='" + event_format + "\\n' "
           "--format-event='" + event_format + "\\n' "
           "--format-recur-apt='" + event_format + " (recur)\\n' "
           "--format-recur-event='" + event_format + " (recur)\\n'")
    if DEBUG:
        print(cmd)
    current_date_from_output = None
    for l in subprocess.check_output(shlex.split(cmd)).decode().split("\n"):
        l = l.strip()
        if l == "":
            continue
        if l.count("/") == 2 and len(l) == len("12/34/56:"):
            # Date
            if l.endswith(":"):
                l = l[:-1]
            p = l.split("/")
            current_date_from_output = datetime.datetime(
                2000 + int(p[2]), int(p[0]), int(p[1]))
            added_events_for_today = set()
            continue

        try:
            (start, end, title) = l.split("|", 2)
        except ValueError:
            print("Oops, couldn't parse '" + l + "'")
            continue
        if start == "?":
            day_start = current_date_from_output.replace(hour=0, minute=0)
            start = day_start.timestamp()
        if end == "?":
            day_end = current_date_from_output.replace(hour=23, minute=59)
            end = day_end.timestamp()
        start = int(start)
        end = int(end)
        event_fp = str(start) + "|" + str(end) + "|" + str(title)
        if event_fp in added_events_for_today:
            # Don't add duplicates
            continue
        out.append([start, end, title])
        added_events_for_today.add(event_fp)
    return out

def remove_duplicated_with_repeated(events):
    """
    Parses repeated events and removes one-time events that represent the same
    as one instance.
    """
    repeated = []
    nonrepeated = []
    pruned = []
    for e in events:
        if e.repeated():
            repeated.append(e)
        else:
            nonrepeated.append(e)
    print("I have " + str(len(repeated)) + " repeated events and "
          "" + str(len(nonrepeated)) + " non-repeated ones")

    # TODO: not optimal
    for e in events:
        should_add = True
        if not e.handsoff:
            for r in repeated:
                if r.includes(e):
                    should_add = False
                    break
        if should_add:
            pruned.append(e)

    return pruned

def parse_calcurse_file():
    all_events = set()
    os.chdir(HOME)
    os.chdir("bus/config/calcurse")
    with open("apts") as f:
        lines = f.readlines()
        f.close()
    for l in lines:
        l = l.strip()
        if l == "":
            continue
        if "|" not in l:
            # Ignoring full-day events for now
            continue
        e = Event(l)
        if e.valid:
            all_events.add(e)
    return all_events

def consolidate_calcurse_file():
    all_events = parse_calcurse_file()
    events_reduced = remove_duplicated_with_repeated(all_events)
    # Put most recent events at the top
    sorted_events = sorted(events_reduced, reverse=True)
    output = "\n".join([e.orig_line for e in sorted_events])
    with open("apts_consolidated", "w") as f:
        f.write(output)
        f.close()
    os.system("mv apts_consolidated apts")

def remove_duplicates():
    os.chdir(HOME)
    os.chdir("bus/config/calcurse")
    os.system("sort -u apts > new")
    os.system("mv new apts")
    os.chdir(HOME)
