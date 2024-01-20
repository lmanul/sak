TIMEZONES = {
    "CET": "Europe/Paris",
    "CNT": "Asia/Shanghai",
    "CST": "America/Chicago",
    "EET": "Europe/Tallinn",
    "EST": "America/New_York",
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
    "J": "JST",
    "P": "PST",
    "S": "CNT",
    "U": "UTC",
}
