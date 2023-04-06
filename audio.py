import os

import dbus

PREFIX = "/org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player."

def send_command_to_music_player(cmd):

    destination = ""
    for service in dbus.SessionBus().list_names():
        if "vlc" in service or "lollypop" in service.lower():
            destination = service
            # Target the first service we find
            break

    if destination:
        os.system("dbus-send --type=method_call --dest='" + destination + "' " + PREFIX + cmd)
