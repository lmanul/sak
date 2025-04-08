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

def send_command_to_music_player(cmd, print_reply=False,
        cmd_prefix=CMD_PREFIX, msg_payload=""):

    if cmd == "ToggleMute":
        current_vol = subprocess.check_output(["playerctl", "volume"]).decode().strip()
        if current_vol.startswith("0.0"):
            os.system("playerctl volume 1.0")
        else:
            os.system("playerctl volume 0.0")
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
