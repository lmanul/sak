import os
import shlex
import subprocess

import dbus

CMD_PREFIX = "org.mpris.MediaPlayer2.Player"
OBJECT = "/org/mpris/MediaPlayer2"

# TODO: Use 'playerctl' for more stuff
COMMANDS = [
  "ToggleMute"
]

MUSIC_PLAYERS = [
  "clementine",
  "lollypop",
  "vlc",
]

def media_player_is_muted():
    current_vol = subprocess.check_output(
         ["playerctl", "--player=vlc", "volume"]).decode().strip()
    return current_vol.startswith("0.0")

def media_player_set_muted(muted):
    os.system("playerctl --player=vlc volume " + ("0.0" if muted else "1.0"))

def send_command_to_music_player(cmd, print_reply=False,
        cmd_prefix=CMD_PREFIX, msg_payload=""):

    if cmd == "ToggleMute":
        if media_player_is_muted():
            media_player_set_muted(False)
        else:
            media_player_set_muted(True)
        return

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
        cmd = (
            "dbus-send "
            "--type=method_call "
            "" + ("--print-reply " if print_reply else "") + ""
            "--dest='" + destination + "' "
            "" + OBJECT + " "
            "" + cmd_prefix +  "." + cmd + " "
            "" + msg_payload + ""
        )
        #print(cmd)
        output = subprocess.check_output(shlex.split(cmd)).decode()
        return output
