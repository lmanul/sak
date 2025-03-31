import json
import os
import shlex
import subprocess

def get_mkv_audio_tracks(mkv):
    retval = {}
    j = subprocess.check_output(shlex.split("mkvmerge -J " + mkv)).decode()
    for track in json.loads(j)['tracks']:
        if track["type"] == "audio":
            lang_id = track["properties"]["language"]
            retval[lang_id] = {}
            retval[lang_id]["number"] = track["properties"]["number"]
            if "track_name" in track["properties"]:
                retval[lang_id]["name"] = track["properties"]["track_name"]
    return retval
