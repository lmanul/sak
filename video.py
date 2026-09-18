import json
import os
import shlex
import subprocess

def get_mkv_audio_tracks(mkv):
    retval = {}
    j = subprocess.check_output(shlex.split("mkvmerge -J " + mkv)).decode()
    for track in json.loads(j)['tracks']:
        if track["type"] == "audio":
            number = track["properties"]["number"]
            retval[number] = {}
            retval[number]["language"] = track["properties"]["language"]
            if "track_name" in track["properties"]:
                retval[number]["name"] = track["properties"]["track_name"]
    return retval

def get_mkv_subtitle_tracks(mkv):
    retval = {}
    j = subprocess.check_output(shlex.split("mkvmerge -J " + mkv)).decode()
    for track in json.loads(j)['tracks']:
        if track["type"] == "subtitles":
            number = track["properties"]["number"]
            retval[number] = {}
            retval[number]["language"] = track["properties"]["language"]
            if "track_name" in track["properties"]:
                retval[number]["name"] = track["properties"]["track_name"]
    return retval
