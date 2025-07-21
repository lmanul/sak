import ast
import audio
import os
import shlex
import subprocess
import sys
import util

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

def seconds_to_ffmpeg_time(seconds: float) -> str:
    minutes = int(seconds // 60)
    hours = int(minutes // 60)
    remaining_minutes = int(minutes % 60)
    remaining_seconds = int(seconds % 60)
    milliseconds = int((seconds % 1) * 1000)
    return f"{hours}:{remaining_minutes:02}:{remaining_seconds:02}.{milliseconds:03}"

def media_player_is_muted():
    current_vol = subprocess.check_output(
         ["playerctl", "--player=vlc", "volume"]).decode().strip()
    return current_vol.startswith("0.0")

def media_player_set_muted(muted):
    os.system("playerctl --player=vlc volume " + ("0.0" if muted else "1.0"))

def get_file_duration_seconds(f):
    return float(subprocess.check_output(shlex.split(
      "ffprobe -v error -show_entries format=duration -of csv=p=0 "
      "" + f + ""
    )).decode())

# Returns (longest_duration_seconds, file_with_longest_duration)
def find_longest_file(files):
    longest_duration = 0
    file_with_longest_duration = None
    for f in files:
        d = get_file_duration_seconds(f)
        if d > longest_duration:
            longest_duration = d
            file_with_longest_duration = f
    return [longest_duration, file_with_longest_duration]

SILENCE_MIN_DURATION_SECONDS = 1.5
LEVEL_DB = "-30"
TOO_CLOSE_TO_START_PERCENT = 10
TOO_CLOSE_TO_END_PERCENT = 90

# Returns [silence_start_seconds, silence_end_seconds,
#     percentage_of_file, silence_duration_seconds]
def find_longest_silence(f):
    total_duration_seconds = get_file_duration_seconds(f)
    output = subprocess.check_output(shlex.split(
      "ffmpeg "
      "-i " + f + " "
      f"-af \"silencedetect=n={LEVEL_DB}dB:d={SILENCE_MIN_DURATION_SECONDS}\" -f null -"
    ), stderr=subprocess.STDOUT).decode()

    # Triplet of start, end, percent of file, duration
    current = []
    last_start = 0
    max_duration = 0
    for l in output.split("\n"):
        if "] " not in l:
            continue
        (_, main) = l.split("] ", 1)
        main = main.strip()
        if main.startswith("silence_start"):
            (_, value) = main.split(": ")
            last_start = float(value)
        elif main.startswith("silence_end"):
            (end, duration) = [s.strip() for s in main.split(" | ")]
            end = float(end.split(": ")[1].strip())
            duration = float(duration.split(": ")[1].strip())
            if duration > max_duration:
                percent = int(last_start / total_duration_seconds * 100)
                if percent < TOO_CLOSE_TO_START_PERCENT or percent > TOO_CLOSE_TO_END_PERCENT:
                    continue
                max_duration = duration
                current = [last_start, end, percent, duration]
    return current


def split_file_on_longest_silence(f, delete_backup=False):
    retval = find_longest_silence(f)
    if len(retval) == 0:
        print("Didn't find longest silence, skipping " + f)
        return
    end = retval[1]
    percent = retval[2]
    split_point_seconds = end - 0.5
    split_point = seconds_to_ffmpeg_time(split_point_seconds)
    print("Splitting " + f + " at " + split_point + f" ({percent}%)")

    part_1 = f.replace(".mp3", "_1.mp3")
    part_2 = f.replace(".mp3", "_2.mp3")
    util.silent(f"ffmpeg -i {f} -to {split_point} -c copy {part_1}")
    util.silent(f"ffmpeg -i {f} -ss {split_point} -c copy {part_2}")
    if delete_backup:
        os.system("rm " + f)
    else:
        os.system("mv " + f + " " + f + ".bup")


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
