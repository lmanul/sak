import datetime
import os
import shlex
import subprocess

DEBUG = False

HOME = os.path.expanduser("~")
CALCURSE_DATETIME_FORMAT = "%m/%d/%Y @ %H:%M"

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

def sort_by_date(line):
    date_chunk = line.split(" ")[0]
    if date_chunk.count("/") != 2:
        raise ValueError("Invalid date: " + date_chunk)
    (m, d, y) = date_chunk.split("/")
    return "-".join([y, m, d])

def sort_calcurse_apts_by_date():
    os.chdir(HOME)
    os.chdir("bus/config/calcurse")
    lines = []
    i = 0
    with open("apts") as f:
        try:
            for l in f:
                lines.append(l)
                i += 1
        except UnicodeDecodeError as error:
            print("One line I can't decode. Last line number was " + str(i))
            print(str(error))

        f.close()
    cleaned_up_lines = []
    for l in lines:
        l = l.strip()
        if l == "":
            continue
        cleaned_up_lines.append(l)
    sorted_lines = sorted(cleaned_up_lines, key=sort_by_date, reverse=True)
    output = "\n".join(sorted_lines)
    with open("apts_sorted_by_date", "w") as f:
        f.write(output)
        f.close()
    os.system("mv apts_sorted_by_date apts")

def remove_duplicated_with_repeated():
    """
    Parses repeated events and removes one-time events that represent the same
    as one instance.
    """
    os.chdir(HOME)
    os.chdir("bus/config/calcurse")
    with open("apts") as f:
        lines = f.readlines()

    # Dictionary whose keys are the start date, and the values are
    # a list of [end date, title].
    non_repeated = {}
    repeated = {}

    for l in lines:
        l = l.strip()
        if l == "":
            continue
        if "|" not in l:
            # Ignoring full-day events for now
            continue
        if "->" not in l:
            print("Warning, line without '->': '" + l + "'")
            continue
        (timing, title) = l.split("|", 1)
        if "{" in timing and "}" in timing:
            # Repeated event
            continue
        # Nonrepeated event
        (start, end) = timing.split("->", 1)
        if "@" not in start:
            print("Warning, ignoring line with '@': '" + start + "'")
            continue
        start_date = datetime.datetime.strptime(
            start.strip(), CALCURSE_DATETIME_FORMAT)
        end_date = datetime.datetime.strptime(
            end.strip(), CALCURSE_DATETIME_FORMAT)
        if start_date not in non_repeated:
            non_repeated[start_date] = []
        non_repeated[start_date].append([end_date, title])
    print("Parsed " + str(len(non_repeated)) + " nonrepeated events")

def remove_duplicates():
    os.chdir(HOME)
    os.chdir("bus/config/calcurse")
    os.system("sort -u apts > new")
    os.system("mv new apts")
    os.chdir(HOME)
