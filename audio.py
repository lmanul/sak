import os
import util

PREFIX = "/org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player."

def send_command_to_music_player(cmd):

    destination = ""
    # Lollypop is often running and stopped. Let's try to target other players first.
    if util.is_process_running("vlc") or util.is_process_running("cvlc"):
        destination = "org.mpris.MediaPlayer2.vlc"
    elif util.is_process_running("lollypop"):
        destination = "org.gnome.Lollypop"

    if destination:
        os.system("dbus-send --type=method_call --dest='" + destination + "' " + PREFIX + cmd)
