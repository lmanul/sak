TIMEZONES = {
    "CET": "Europe/Paris",
    "CNT": "Asia/Shanghai",
    "CST": "America/Chicago",
    "EET": "Europe/Tallinn",
    "EST": "America/New_York",
    "HST": "Pacific/Honolulu",
    "ICT": "Asia/Bangkok",
    "MST": "America/Boise",
    "JST": "Asia/Tokyo",
    "PST": "America/Los_Angeles",
    "UTC": "Etc/UTC",
}

TIMEZONES_REVERSE = {}
for t in TIMEZONES:
    TIMEZONES_REVERSE[TIMEZONES[t]] = t

SHORTS = {
    "C": "CET",
    "E": "EST",
    "H": "HST",
    "J": "JST",
    "P": "PST",
    "S": "CNT",
    "U": "UTC",
}
