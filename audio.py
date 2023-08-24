import os

import dbus

PREFIX = "/org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player."

MUSIC_PLAYERS = [
  "clementine",
  "lollypop",
  "vlc",
]

def send_command_to_music_player(cmd):

    destination = ""
    for service in dbus.SessionBus().list_names():
        found = False
        for player in MUSIC_PLAYERS:
            if player in service.lower():
                # Target the first service we find
                destination = service
                found = True
                break
            if found:
                break

    if destination:
        os.system("dbus-send --type=method_call --dest='" + destination + "' " + PREFIX + cmd)
