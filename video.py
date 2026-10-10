import bisect
import concurrent.futures
import json
import os
import re
import statistics
import struct
import subprocess
import tempfile

SRT_TIME = r"(\d+):(\d\d):(\d\d)[,.](\d\d\d)"
SRT_TIMING_REGEXP = re.compile(SRT_TIME + r"\s*-->\s*" + SRT_TIME)

PGS_CODEC = "HDMV PGS"
# Matroska uses the "bibliographic" ISO 639-2 codes, Tesseract the "terminologic" ones.
TESSERACT_LANGUAGES = {
    "alb": "sqi", "arm": "hye", "baq": "eus", "bur": "mya", "cze": "ces",
    "dut": "nld", "fre": "fra", "geo": "kat", "ger": "deu", "gre": "ell",
    "ice": "isl", "mac": "mkd", "may": "msa", "per": "fas", "rum": "ron",
    "slo": "slk", "tib": "bod", "wel": "cym",
}
# Tracks are only tagged "Chinese", so we have to find out which script it is.
CHINESE_SCRIPTS = ["chi_sim", "chi_tra"]
OCR_LINE_HEIGHT = 32
# (scale, black and white only?, Tesseract page segmentation mode) to try in
# turn. Tesseract sometimes sees nothing at all in a perfectly clean line, and
# a slightly different rendering of that same line is usually enough to wake it
# up. Mode 13 always returns something, but is a bit less accurate than 7.
OCR_ATTEMPTS = [(1, False, 7), (1, True, 7), (.75, False, 7), (1.125, True, 7),
                (1.5, False, 7), (.875, True, 7), (1, False, 13)]
# Characters that are specific to Taiwan and that OpenCC leaves alone.
TAIWANESE_TO_SIMPLIFIED = str.maketrans("妳牠暱", "你它昵")

class OcrError(Exception):
    pass

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
            retval[number]["codec"] = track["codec"]
            # Image-based tracks (PGS, VobSub) need OCR to become text.
            retval[number]["text"] = track["properties"].get("text_subtitles", False)
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

def ocr_pgs_subtitle_track(mkv, track_id, language):
    """Reads the given image-based track (mkvmerge track ID, in the given
    Matroska language) and returns it as a list of (start_ms, end_ms, text)
    cues, same as parse_srt()."""
    with tempfile.TemporaryDirectory() as tmp:
        sup = os.path.join(tmp, "track.sup")
        subprocess.check_call(
            ["mkvextract", "-q", mkv, "tracks", str(track_id) + ":" + sup])
        with open(sup, "rb") as f:
            cues = _parse_pgs(f.read())
    # OCR works much better one line of text at a time.
    lines = [_split_lines(image) for _, _, image in cues]
    height = statistics.median([l.height for ls in lines for l in ls] or [1])
    lines = [_merge_line_fragments(ls, 1.1 * height) for ls in lines]
    # Scaling everything by the same factor, rather than each line to the same
    # height: the odd stray dash must not get blown up to the size of a line.
    flat = [_scale(l, OCR_LINE_HEIGHT / height) for ls in lines for l in ls]
    texts = iter(_ocr_lines(flat, _tesseract_language(language, flat)))
    result = []
    for (start, end, _), ls in zip(cues, lines):
        text = " ".join(t for t in (next(texts) for _ in ls) if t)
        if text:
            result.append((start, end, text))
    return result

def to_simplified_chinese(cues):
    try:
        import opencc
    except ImportError:
        raise OcrError("Converting to simplified Chinese needs OpenCC: "
                       "sudo apt install python3-opencc")
    # Unlike "t2s", "tw2s" also deals with the likes of 看著 (看着).
    converter = opencc.OpenCC("tw2s")
    return [(start, end, converter.convert(text).translate(TAIWANESE_TO_SIMPLIFIED))
            for start, end, text in cues]

def _parse_pgs(data):
    """Turns the contents of a .sup file into (start_ms, end_ms, image) cues,
    the images being black text on a white background."""
    cues = []
    palette, objects, unfinished, placements = {}, {}, {}, []
    showing = None
    pos = 0
    while pos + 13 <= len(data) and data[pos:pos + 2] == b"PG":
        pts, _, kind, size = struct.unpack(">IIBH", data[pos + 2:pos + 13])
        segment = data[pos + 13:pos + 13 + size]
        pos += 13 + size
        if kind == 0x16:  # Presentation composition: what goes where.
            now = pts // 90
            if segment[7] & 0xC0:
                palette, objects = {}, {}
            placements = []
            p = 11
            for _ in range(segment[10]):
                object_id, _, flags, x, y = struct.unpack(">HBBHH", segment[p:p + 8])
                p += 16 if flags & 0x80 else 8
                placements.append((object_id, x, y))
        elif kind == 0x14:  # Palette.
            for p in range(2, len(segment) - 4, 5):
                palette[segment[p]] = (segment[p + 1], segment[p + 4])
        elif kind == 0x15:  # Object (a bitmap), possibly in several segments.
            object_id, _, sequence = struct.unpack(">HBB", segment[:4])
            if sequence & 0x80:
                width, height = struct.unpack(">HH", segment[7:11])
                unfinished[object_id] = [width, height, bytearray(segment[11:])]
            elif object_id in unfinished:
                unfinished[object_id][2] += segment[4:]
            if sequence & 0x40 and object_id in unfinished:
                width, height, rle = unfinished.pop(object_id)
                objects[object_id] = (width, height, _decode_pgs_rle(rle, width, height))
        elif kind == 0x80:  # End of display set: what we had on screen goes away.
            if showing:
                cues.append((showing[0], now, showing[1]))
            image = _render_pgs(placements, objects, palette)
            showing = (now, image) if image else None
    if showing:
        cues.append((showing[0], showing[0] + 3000, showing[1]))
    return cues

def _decode_pgs_rle(data, width, height):
    pixels = bytearray(width * height)
    i = x = y = 0
    while i < len(data) and y < height:
        color = data[i]
        i += 1
        length = 1
        if not color:
            flags = data[i]
            i += 1
            if not flags:
                x = 0
                y += 1
                continue
            length = flags & 0x3F
            if flags & 0x40:
                length = (length << 8) | data[i]
                i += 1
            if flags & 0x80:
                color = data[i]
                i += 1
        length = min(length, width - x)
        if color and length > 0:
            pixels[y * width + x:y * width + x + length] = bytes([color]) * length
        x += length
    return bytes(pixels)

def _render_pgs(placements, objects, palette):
    from PIL import Image
    placed = [(x, y) + objects[i] for i, x, y in placements if i in objects]
    if not placed:
        return None
    left = min(x for x, y, w, h, _ in placed)
    top = min(y for x, y, w, h, _ in placed)
    right = max(x + w for x, y, w, h, _ in placed)
    bottom = max(y + h for x, y, w, h, _ in placed)
    # Subtitles are bright text with a dark outline on a transparent background:
    # only the text itself ends up dark here.
    shades = bytes(255 - luma * alpha // 255 for luma, alpha in
                   (palette.get(i, (0, 0)) for i in range(256)))
    image = Image.new("L", (right - left, bottom - top), 255)
    for x, y, w, h, pixels in placed:
        image.paste(Image.frombytes("L", (w, h), pixels.translate(shades)),
                    (x - left, y - top))
    return image

def _split_lines(image):
    """Cuts the image at each fully blank row of pixels."""
    width, height = image.size
    data = image.tobytes()
    lines = []
    top = None
    for y in range(height + 1):
        ink = y < height and min(data[y * width:(y + 1) * width]) < 128
        if ink and top is None:
            top = y
        elif not ink and top is not None:
            lines.append(image.crop((0, top, width, y)))
            top = None
    return lines

def _merge_line_fragments(lines, max_height):
    """Characters such as "二" have blank rows of their own, so a line with not
    much else in it comes out of _split_lines() in several pieces."""
    from PIL import Image
    merged = []
    for line in lines:
        if merged and merged[-1][1] + line.height <= max_height:
            merged[-1] = (merged[-1][0] + [line], merged[-1][1] + line.height)
        else:
            merged.append(([line], line.height))
    result = []
    for parts, height in merged:
        image = Image.new("L", (parts[0].width, height), 255)
        y = 0
        for part in parts:
            image.paste(part, (0, y))
            y += part.height
        result.append(image)
    return result

def _tesseract_language(language, lines):
    try:
        installed = subprocess.check_output(
            ["tesseract", "--list-langs"], stderr=subprocess.STDOUT).decode().split()
    except FileNotFoundError:
        raise OcrError("Reading image-based subtitles needs tesseract: "
                       "sudo apt install tesseract-ocr")
    candidates = (CHINESE_SCRIPTS if language in ("chi", "zho")
                  else [TESSERACT_LANGUAGES.get(language, language)])
    missing = [c for c in candidates if c not in installed]
    if missing:
        raise OcrError("Tesseract can't read '" + language + "' yet: sudo apt install " +
                       " ".join("tesseract-ocr-" + m.replace("_", "-") for m in missing))
    if len(candidates) == 1:
        return candidates[0]
    # Whichever one Tesseract is the most confident with on a sample of lines.
    sample = [_prepare_line(l, 1, False) for l in lines[::max(1, len(lines) // 40)]]
    return max(candidates, key=lambda c: _tesseract_confidence(sample, c))

def _ocr_lines(lines, language):
    texts = [""] * len(lines)
    for scale, black_and_white, mode in OCR_ATTEMPTS:
        todo = [i for i, text in enumerate(texts) if not text]
        if not todo:
            break
        batches = [todo[i::os.cpu_count()] for i in range(os.cpu_count())]
        def ocr(batch):
            images = [_prepare_line(lines[i], scale, black_and_white) for i in batch]
            return _tesseract(images, language, mode) if images else []
        with concurrent.futures.ThreadPoolExecutor() as pool:
            for batch, found in zip(batches, pool.map(ocr, batches)):
                for i, text in zip(batch, found):
                    texts[i] = text
    return texts

def _scale(image, scale):
    from PIL import Image
    return image.resize((max(1, round(image.width * scale)),
                         max(1, round(image.height * scale))), Image.LANCZOS)

def _prepare_line(line, scale, black_and_white):
    from PIL import ImageOps
    if black_and_white:
        line = line.point(lambda v: 0 if v < 100 else 255)
    return ImageOps.expand(_scale(line, scale), border=8, fill=255)

def _tesseract(images, language, mode=7, output="txt"):
    """Runs Tesseract on images of a single line of text, returns its output for each."""
    with tempfile.TemporaryDirectory() as tmp:
        paths = [os.path.join(tmp, "%06d.png" % i) for i in range(len(images))]
        for image, path in zip(images, paths):
            image.save(path)
        with open(os.path.join(tmp, "list.txt"), "w") as f:
            f.write("\n".join(paths) + "\n")
        # We already run one Tesseract per core, they must not all try to use
        # all the cores as well.
        out = subprocess.check_output(
            ["tesseract", f.name, "stdout", "-l", language, "--psm", str(mode), output],
            stderr=subprocess.DEVNULL, env=dict(os.environ, OMP_THREAD_LIMIT="1")).decode()
    if output != "txt":
        return out
    pages = out.split("\f")
    if len(pages) != len(images):
        # Tesseract silently skips images it can't deal with (too small, say),
        # and then there is no telling which text belongs to which image.
        if len(images) == 1:
            return [""]
        half = len(images) // 2
        return (_tesseract(images[:half], language, mode) +
                _tesseract(images[half:], language, mode))
    # A dash at the start of a line (dialogue) very often comes out as a tilde,
    # or twice.
    return [re.sub(r"^[~_-]+\s*", "- ", " ".join(page.split())) for page in pages]

def _tesseract_confidence(images, language):
    rows = [r.split("\t") for r in _tesseract(images, language, output="tsv").splitlines()]
    confidences = [float(r[10]) for r in rows if len(r) > 11 and r[0] == "5"]
    return statistics.mean(confidences) if confidences else 0

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
