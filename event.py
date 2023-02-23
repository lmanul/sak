import datetime

import pytz

import util
import timezones

def is_past(d):
    now_utc = datetime.datetime.now(pytz.timezone("Etc/UTC"))
    return now_utc > d

def format_timedelta(minutes, prefix, suffix, highlight_color):
    color = "white"
    prefix = "(" + prefix + " "
    suffix = suffix + ")"
    if minutes > 24 * 60:
        color = "dim"
        infix = "> 1 day"
    elif minutes > 60:
        hours = int(minutes / 60)
        remaining_minutes = minutes - hours * 60
        infix = str(hours) + " h " + str(remaining_minutes) + " mn"
    elif minutes < 60:
        infix = str(minutes) + " mn"
        if minutes < 30:
            color = highlight_color
    else:
        infix = str(minutes) + " mn"
    return util.color(prefix + infix + suffix, color)

class Event:
    def __init__(self, start, end, text):
        self.start = start
        self.end = end
        self.text = text

    def print(self, timezone):
        result = (self.get_displayed_time(self.start, timezone) + ""
                  " — "
                  "" + self.get_displayed_time(self.end, timezone) + ""
                  "  " + self.get_displayed_text())
        if not is_past(self.start):
            minutes_until_start = int(self.get_time_to_start().total_seconds() / 60)
            result = result + " " + format_timedelta(
                minutes_until_start, "in", "", "yellow")
        if is_past(self.start) and not is_past(self.end):
            minutes_until_end = int(self.get_time_to_end().total_seconds() / 60)
            result = result + " " + format_timedelta(
                minutes_until_end, "end in", "", "cyan")
        elif is_past(self.end):
            minutes_since_end = int(self.get_time_since_end().total_seconds() / 60)
            result = result + " " + format_timedelta(
                minutes_since_end, "ended ", " ago", "green")
        print("\t" + result)

    def get_displayed_time(self, d, timezone="UTC"):
        color = "dim" if is_past(d) else "white"
        tz = timezones.TIMEZONES[timezone]
        d_with_tz = d.astimezone(pytz.timezone(tz))
        return util.color(str(d_with_tz.hour).zfill(2) + ":"
                          "" + str(d_with_tz.minute).zfill(2),
                          color)

    def get_displayed_text(self):
        color = "white"
        if is_past(self.start) and is_past(self.end):
            color = "dim"
        return util.color(self.text, color)

    def get_time_to_start(self):
        now_utc = datetime.datetime.now(pytz.timezone("Etc/UTC"))
        return self.start - now_utc

    def get_time_to_end(self):
        now_utc = datetime.datetime.now(pytz.timezone("Etc/UTC"))
        return self.end - now_utc

    def get_time_since_end(self):
        now_utc = datetime.datetime.now(pytz.timezone("Etc/UTC"))
        return now_utc - self.end
