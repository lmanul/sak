import datetime
import shlex
import subprocess

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
    event_format = "%s|%e|%m\\n"
    out = []
    cmd = ("calcurse "
           "-r" + str(days) + " "
           "--format-apt='" + event_format + "' "
           "--format-event='" + event_format + "' "
           "--format-recur-apt='" + event_format + "' "
           "--format-recur-event='" + event_format + "'")
    current_date_from_output = None
    for l in subprocess.check_output(shlex.split(cmd)).decode().split("\n"):
        l = l.strip()
        if l == "":
            continue
        if l.count("/") == 2:
            # Date
            if l.endswith(":"):
                l = l[:-1]
            p = l.split("/")
            current_date_from_output = datetime.datetime(
                2000 + int(p[2]), int(p[0]), int(p[1]))
            continue

        (start, end, title) = l.split("|", 2)
        if start == "?":
            day_start = current_date_from_output.replace(hour=0, minute=0)
            start = day_start.timestamp()
        if end == "?":
            day_end = current_date_from_output.replace(hour=23, minute=59)
            end = day_end.timestamp()
        start = int(start)
        end = int(end)
        out.append([start, end, title])
    return out
