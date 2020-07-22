import datetime
import shlex
import subprocess

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
        out.append([start, end, title])
    return out
