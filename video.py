import bisect
import json
import os
import re
import subprocess
import tempfile

SRT_TIME = r"(\d+):(\d\d):(\d\d)[,.](\d\d\d)"
SRT_TIMING_REGEXP = re.compile(SRT_TIME + r"\s*-->\s*" + SRT_TIME)

def get_mkv_audio_tracks(mkv):
    retval = {}
    j = subprocess.check_output(["mkvmerge", "-J", mkv]).decode()
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
    j = subprocess.check_output(["mkvmerge", "-J", mkv]).decode()
    for track in json.loads(j)['tracks']:
        if track["type"] == "subtitles":
            number = track["properties"]["number"]
            retval[number] = {}
            retval[number]["id"] = track["id"]
            retval[number]["language"] = track["properties"]["language"]
            if "track_name" in track["properties"]:
                retval[number]["name"] = track["properties"]["track_name"]
    return retval

def extract_subtitle_track_as_srt(video_file, track_id):
    """Returns the contents of the given track (ffmpeg stream index) as SRT."""
    with tempfile.TemporaryDirectory() as tmp:
        srt = os.path.join(tmp, "track.srt")
        subprocess.check_call(
            ["ffmpeg", "-loglevel", "error", "-i", video_file,
             "-map", "0:" + str(track_id), "-c:s", "srt", srt])
        with open(srt, encoding="utf-8-sig") as f:
            return f.read()

def parse_srt(srt):
    """Turns SRT text into a list of (start_ms, end_ms, text) cues."""
    cues = []
    for block in re.split(r"\n\s*\n", srt.strip()):
        lines = block.strip().splitlines()
        timing = None
        for i, line in enumerate(lines):
            timing = SRT_TIMING_REGEXP.search(line)
            if timing:
                lines = lines[i + 1:]
                break
        if not timing:
            continue
        text = " ".join(l.strip() for l in lines if l.strip())
        if text:
            cues.append((_srt_time_to_ms(timing.groups()[:4]),
                         _srt_time_to_ms(timing.groups()[4:]),
                         text))
    return cues

def merge_srt_cues(top_cues, bottom_cues, tolerance_ms=200):
    """Interleaves two cue lists so that at any moment the text from the first
    one is on the first line and the text from the second one right below.

    The two tracks rarely agree on exact timings even when they are subtitling
    the same moment, so boundaries less than tolerance_ms apart are snapped
    together first. Without that, every small disagreement becomes its own
    sliver of a cue and the result flickers between one and two lines."""
    boundaries = sorted({t for c in top_cues + bottom_cues for t in c[:2]})
    snapped = {}
    anchor = boundaries[0] if boundaries else 0
    for t in boundaries:
        if t - anchor > tolerance_ms:
            anchor = t
        snapped[t] = anchor
    top_cues = _snap_cues(top_cues, snapped)
    bottom_cues = _snap_cues(bottom_cues, snapped)

    boundaries = sorted(set(snapped.values()))
    merged = []
    for start, end in zip(boundaries, boundaries[1:]):
        text = "\n".join(t for t in (_text_between(top_cues, start, end),
                                     _text_between(bottom_cues, start, end)) if t)
        if not text:
            continue
        if merged and merged[-1][1] == start and merged[-1][2] == text:
            merged[-1] = (merged[-1][0], end, text)
        else:
            merged.append((start, end, text))
    return merged

def format_srt(cues):
    return "".join(
        "%d\n%s --> %s\n%s\n\n" % (i, _ms_to_srt_time(start), _ms_to_srt_time(end), text)
        for i, (start, end, text) in enumerate(cues, start=1))

def _snap_cues(cues, snapped):
    anchors = sorted(set(snapped.values()))
    result = []
    for start, end, text in cues:
        start, end = snapped[start], snapped[end]
        if end <= start:
            # A cue shorter than the tolerance would otherwise collapse to
            # nothing, so give it the next slot rather than dropping it.
            following = bisect.bisect_right(anchors, start)
            if following >= len(anchors):
                continue
            end = anchors[following]
        result.append((start, end, text))
    return result

def _text_between(cues, start, end):
    return " ".join(c[2] for c in cues if c[0] < end and c[1] > start)

def _srt_time_to_ms(groups):
    hours, minutes, seconds, ms = [int(g) for g in groups]
    return ((hours * 60 + minutes) * 60 + seconds) * 1000 + ms

def _ms_to_srt_time(ms):
    seconds, ms = divmod(ms, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return "%02d:%02d:%02d,%03d" % (hours, minutes, seconds, ms)
