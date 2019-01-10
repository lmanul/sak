#!/usr/bin/python3

import datetime
import pytz

TZ = [
    ['America/Los_Angeles', 'San Francisco'],
    ['America/New_York', 'New York'],
    ['Etc/UTC', 'UTC'],
    ['Europe/Paris', 'Paris'],
    ['Asia/Bangkok', 'Bangkok'],
    ['Asia/Shanghai', 'Shanghai'],
    ['Asia/Tokyo', 'Tokyo'],
    ['Australia/Sydney', 'Sydney'],
]

for tz in TZ:
  filler = " " * (15 - len(tz[1]))
  print(tz[1] + filler + \
      str(datetime.datetime.now(pytz.timezone(tz[0])))[:-16].replace(" ", "   "))
