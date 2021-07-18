TIMEZONES = {
    "CET": "Europe/Paris",
    "CNT": "Asia/Shanghai",
    "CST": "US/Central",
    "EET": "Europe/Tallinn",
    "EST": "US/Eastern",
    "ICT": "Asia/Bangkok",
    "MST": "US/Mountain",
    "JST": "Asia/Tokyo",
    "PST": "US/Pacific",
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
