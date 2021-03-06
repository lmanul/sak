TIMEZONES = {
    "CET": "Europe/Paris",
    "CST": "Asia/Shanghai",
    "EET": "Europe/Tallinn",
    "EST": "US/Eastern",
    "ICT": "Asia/Bangkok",
    "CST": "Asia/Shanghai",
    "MST": "US/Mountain",
    "JST": "Asia/Tokyo",
    "PST": "US/Pacific",
    "UTC": "UTC",
}

TIMEZONES_REVERSE = {}
for t in TIMEZONES:
    TIMEZONES_REVERSE[TIMEZONES[t]] = t

SHORTS = {
    "C": "CET",
    "E": "EST",
    "P": "PST",
    "S": "CST",
    "U": "UTC",
}
