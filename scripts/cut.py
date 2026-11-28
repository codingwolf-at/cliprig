"""Cut one candidate into a finished vertical clip.

1080x1920, 30 fps, word-by-word burned captions (slurs always masked, swears masked unless allowed),
hook box in the first seconds, loudness normalised to -14 LUFS.
Writes media/edits/<job>_clip<n>/ with the .mp4, its .json (metadata for rule checks), captions.md and status.md.

usage: python cut.py jobs/<id> --pick 1 [--frame] [--layout fill|blur|facecam] [--focus auto|0.5] [--cam x:y:w:h]
                     [--hook "TEXT"] [--captions word|none] [--style bold|clean|box] [--allow-profanity] [--mask "w|w"] [--start SEC --end SEC]
       python cut.py --self-test
"""
import argparse, hashlib, os, re, shutil, subprocess, sys, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import ROOT, ends_sentence, load_json, read_pcm, run, save_json, tool, video_source, whisper_run

W, H = 1080, 1920
CAP_Y = {"fill": 1380, "blur": 1460, "facecam": 1120}
CAM_H = 730  # facecam layout: top panel height (~38%); must be even or yuv420p loses a row per panel
CAPTIONS_TEMPLATE = """# Post captions

Credit: <creator or show, as the campaign or permission requires>

## Instagram

## YouTube

## X

## TikTok

## Reels

## Shorts
"""
STATUS_TEMPLATE = """# Status

- Instagram:
- YouTube:
- X:
- TikTok:
- Reels:
- Shorts:
"""
# caption presets: ASS Cap and Hook styles (colours are &HAABBGGRR), all caps or not, tags around the spoken word,
# and a small pop on each new group. Fonts missing on a system fall back to a similar one.
STYLES = {
    "bold": dict(  # big white caps, yellow spoken word, thick outline
        cap="Arial Black,92,&H00FFFFFF,&H0000E5FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,7,3",
        hook="Arial Black,68,&H00000000,&H00000000,&H00FFFFFF,&H00FFFFFF,-1,0,0,0,100,100,0,0,3,18,0",
        upper=True, on="{\\c&H0000E5FF&}", off="{\\c&H00FFFFFF&}", pop=True),
    "clean": dict(  # sentence case, soft shadow, the spoken word bright and the rest dimmed
        cap="Helvetica Neue,84,&H00FFFFFF,&H00FFFFFF,&H30000000,&H60000000,-1,0,0,0,100,100,0,0,1,4,3",
        hook="Helvetica Neue,58,&H00FFFFFF,&H00FFFFFF,&H50000000,&H50000000,-1,0,0,0,100,100,0,0,3,16,0",
        upper=False, on="{\\1a&H00&}", off="{\\1a&H50&}", pop=False),
    "box": dict(  # black caps on a white box, red spoken word
        cap="Arial Black,78,&H00000000,&H00000000,&H00FFFFFF,&H00FFFFFF,-1,0,0,0,100,100,0,0,3,14,0",
        hook="Arial Black,68,&H00000000,&H00000000,&H00FFFFFF,&H00FFFFFF,-1,0,0,0,100,100,0,0,3,18,0",
        upper=True, on="{\\c&H002A2AE0&}", off="{\\c&H00000000&}", pop=True),
}
YUNET = ("https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
         "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4")

SLURS = re.compile(r"\b(nigg\w*|n[i1]gg?a\w*|f[a@]gg?\w*|retard\w*|tranny\w*|chink\w*|spic\w*|kike\w*)\b", re.I)
SWEARS = re.compile(r"\b(fuck\w*|motherfuck\w*|shit\w*|bitch\w*|cunt\w*|dick\w*|pussy\w*|asshole\w*|bastard\w*|whore\w*|slut\w*)\b", re.I)


def spoken_words(d, s0, e0):
    """Caption words in the language spoken. moment-finder ranks non-English audio on an English translation,
    whose word times are rough, so the clip's range is transcribed again in its own language (a few seconds)."""
    lang = (d / "lang.txt").read_text().strip() if (d / "lang.txt").exists() else "en"
    if not (d / "audio.wav").exists():
        return load_json(d / "transcript.json")
    if lang == "en":  # moment-finder may have transcribed only the top regions of a long source: fill the clip's range
        from moments import transcribe
        return transcribe(d / "audio.wav", d, [[s0, e0]])

    def go(model):
        segs, _ = model.transcribe(read_pcm(d / "audio.wav", s0, e0), language=lang, word_timestamps=True, vad_filter=True)
        return [{"w": w.word.strip(), "s": round(s0 + w.start, 2), "e": round(s0 + w.end, 2)}
                for s in segs for w in (s.words or []) if w.word.strip()]
    print(f"transcribing the clip in its language ({lang}) for captions", flush=True)
    return whisper_run(go, "medium")


def ts(t):
    t = max(0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def clean(s, profanity=False, extra=()):
    """Slurs are always masked (first letter kept); hard swears too unless profanity=True.
    extra: more words to mask in any language (--mask), compared whole, ignoring case and punctuation."""
    mask = lambda m: m.group(0)[0] + "*" * (len(m.group(0)) - 1)
    core = s.strip(".,!?;:\"'()¿¡…-")
    if core and core.casefold() in extra:
        s = s.replace(core, core[0] + "*" * (len(core) - 1), 1)
    s = SLURS.sub(mask, s)
    return s if profanity else SWEARS.sub(mask, s)


def esc(s):
    return s.replace("\\", "").replace("{", "(").replace("}", ")").replace("\n", " ")


def groups_of(words):
    """Caption groups of up to 3 words, broken on punctuation or a pause."""
    groups, cur = [], []
    for w in words:
        if cur and (len(cur) == 3 or w["s"] - cur[-1]["e"] > 0.6 or ends_sentence(cur[-1]["w"]) or cur[-1]["w"][-1:] == ","):
            groups.append(cur); cur = []
        cur.append(w)
    return groups + ([cur] if cur else [])


def build_ass(words, s0, e0, hook, cap_y, profanity=False, style="bold", extra=()):
    st = STYLES[style]
    hdr = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{st["cap"]},5,60,60,0,1
Style: Hook,{st["hook"]},8,70,70,170,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    groups = groups_of([dict(w, w=clean(w["w"], profanity, extra)) for w in words if s0 <= w["s"] < e0 and w["w"]])
    for gi, g in enumerate(groups):
        g_end = groups[gi + 1][0]["s"] if gi + 1 < len(groups) else g[-1]["e"] + 0.4
        g_end = min(g_end, g[-1]["e"] + 0.8)
        for k, w in enumerate(g):
            a = w["s"] - s0; b = (g[k + 1]["s"] - s0) if k + 1 < len(g) else g_end - s0
            if b <= a:
                continue
            txt = [esc(x["w"].upper() if st["upper"] else x["w"]) for x in g]
            parts = [st["on"] + t + st["off"] if j == k else t for j, t in enumerate(txt)]
            pop = "{\\fscx112\\fscy112\\t(0,90,\\fscx100\\fscy100)}" if k == 0 and st["pop"] else ""
            ev.append(f"Dialogue: 0,{ts(a)},{ts(b)},Cap,,0,0,0,,{{\\pos({W // 2},{cap_y})}}{pop}{st['off']}{' '.join(parts)}")
    if hook:
        ev.append(f"Dialogue: 1,{ts(0)},{ts(2.6)},Hook,,0,0,0,,{{\\fad(0,180)\\fscx92\\fscy92\\t(0,120,\\fscx100\\fscy100)}}{esc(hook)}")
    return hdr + "\n".join(ev) + "\n"


def page_style(text):
    """The caption style a playbook.md names ("Caption style: clean"), or bold."""
    m = re.search(r"caption style:\s*`?(\w+)", text, re.I)
    return m.group(1).lower() if m and m.group(1).lower() in STYLES else "bold"


def crop_x(focus):
    """Crop x for a focus (0 = left edge, 1 = right edge), or per shot as [[t, focus], ...] with t from the clip start."""
    if not isinstance(focus, list):
        return f"(iw-{W})*{focus}"
    e = str(focus[-1][1])
    for (_, f), (t, _) in zip(reversed(focus[:-1]), reversed(focus[1:])):
        e = f"if(lt(t,{t}),{f},{e})"
    return f"'(iw-{W})*{e}'"


def shots(cuts, dur, min_len=1.0):
    """[(start, end), ...] from camera-cut times, folding shots shorter than min_len into the one before."""
    keep = [0.0]
    for t in sorted(cuts):
        if t - keep[-1] >= min_len and dur - t >= min_len:
            keep.append(t)
    return list(zip(keep, keep[1:] + [dur]))


def focus_for(faces, fw, cw, last=0.5, talk=None):
    """Crop focus that keeps the faces in frame. faces: [(x, w), ...] in a frame fw wide; cw: crop width.
    Faces at least half the size of the largest count; if they all fit, centre on them, else on the one
    talking most (talk: a mouth-movement score per face), or the largest."""
    if not faces or fw <= cw:
        return last
    big = max(w for _, w in faces)
    near = [i for i, (_, w) in enumerate(faces) if w >= big / 2]
    a, b = min(faces[i][0] for i in near), max(faces[i][0] + faces[i][1] for i in near)
    if b - a > 0.9 * cw:
        i = max(near, key=lambda i: (talk[i], faces[i][1]) if talk else faces[i][1])
        a, b = faces[i][0], faces[i][0] + faces[i][1]
    return round(float(min(1.0, max(0.0, ((a + b) / 2 - cw / 2) / (fw - cw)))), 3)


def talk_scores(frames, faces, loud):
    """Who is talking: per face, how well its mouth movement follows the audio's loudness (correlation).
    frames: grey frames at a steady rate; loud: audio loudness at the same rate. Moving alone isn't enough:
    listeners laugh and nod, but their mouths don't rise and fall with the talker's voice.
    A mouth area runs from the nose to the chin, between the mouth corners (YuNet's landmarks)."""
    import numpy as np
    out = []
    for f in faces:
        x0, x1 = int(min(f[10], f[12]) - 0.15 * f[2]), int(max(f[10], f[12]) + 0.15 * f[2])
        y0, y1 = int(f[9]), int(f[1] + f[3])
        crops = [g[max(0, y0):max(0, y1), max(0, x0):max(0, x1)].astype(np.float32) for g in frames]
        moves = np.array([np.abs(p - q).mean() for p, q in zip(crops, crops[1:])]) if crops and crops[0].size else np.array([])
        n = min(len(moves), len(loud) - 1)
        ok = n > 4 and moves[:n].std() > 0 and np.std(loud[1:n + 1]) > 0
        out.append(float(np.corrcoef(moves[:n], loud[1:n + 1])[0, 1]) if ok else 0.0)
    return out


def yunet():
    """Path of OpenCV's YuNet face model (230 KB), downloaded once and checked against its hash."""
    p = Path(os.environ.get("LOCALAPPDATA") or Path.home() / ".cache") / "cliprig" / "face_detection_yunet_2023mar.onnx"
    if not p.exists():
        data = urllib.request.urlopen(YUNET[0], timeout=60).read()
        if hashlib.sha256(data).hexdigest() != YUNET[1]:
            sys.exit("the face model download didn't match its checksum; try again, or use --focus 0.5")
        p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(data)
    return str(p)


def auto_focus(ffmpeg, src, s0, e0):
    """Per-shot crop focus that follows faces: [[t, focus], ...], t from the clip start. 0.5 without OpenCV."""
    try:
        import cv2, numpy as np
    except ImportError:
        print("OpenCV is missing (run the doctor skill), so the crop stays centred")
        return 0.5
    r = run([ffmpeg, "-hide_banner", "-ss", f"{s0:.2f}", "-to", f"{e0:.2f}", "-i", str(src), "-an",
             "-vf", "scale=320:-2,select='gt(scene,0.3)',showinfo", "-f", "null", "-"], capture=True)
    det, out, last = cv2.FaceDetectorYN.create(yunet(), "", (320, 320), 0.7), [], 0.5

    def frame(t):
        png = subprocess.run([ffmpeg, "-v", "error", "-ss", f"{t:.2f}", "-i", str(src), "-frames:v", "1",
                              "-vf", "scale=640:-2", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
        return cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_COLOR) if png else None
    for a, b in shots([float(t) for t in re.findall(r"pts_time:([\d.]+)", r.stderr)], e0 - s0):
        img = frame(s0 + (a + b) / 2)
        if img is None:
            continue
        h, w = img.shape[:2]
        det.setInputSize((w, h))
        faces = det.detect(img)[1]
        faces = [] if faces is None else list(faces)
        talk = None
        if len(faces) > 1:  # two or more people: who talks (used only if they don't all fit in the crop)
            t0, dur = s0 + max(a, (a + b) / 2 - 8), min(b - a, 16)  # shortcut: one speaker per shot, from its middle 16 s
            raw = subprocess.run([ffmpeg, "-v", "error", "-ss", f"{t0:.2f}", "-t", f"{dur:.2f}", "-i", str(src), "-vf",
                                  f"fps=10,scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
            pcm = subprocess.run([ffmpeg, "-v", "error", "-ss", f"{t0:.2f}", "-t", f"{dur:.2f}", "-i", str(src), "-ac", "1",
                                  "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
            x = np.frombuffer(pcm[: len(pcm) // 2 * 2], np.int16).astype(np.float32)
            loud = np.sqrt((x[: len(x) // 1600 * 1600].reshape(-1, 1600) ** 2).mean(1)) if len(x) >= 1600 else np.zeros(0)
            talk = talk_scores(np.frombuffer(raw[: len(raw) // (w * h) * w * h], np.uint8).reshape(-1, h, w), faces, loud)
        last = focus_for([(f[0], f[2]) for f in faces], w, h * W / H, last, talk)
        if not out or abs(last - out[-1][1]) > 0.02:
            out.append([round(a, 2), last])
    return out if len(out) > 1 else (out[0][1] if out else 0.5)


def video_filter(layout, ass, focus=0.5, cam=None):
    """Layout + burned-caption filter graph ending in [vo]. focus: a number, or per shot (see crop_x)."""
    if layout == "fill":  # crop the frame to 9:16, centred on `focus` (0 = left edge, 1 = right edge)
        v = f"[0:v]scale=-2:{H},crop={W}:{H}:{crop_x(focus)}:0[v]"
    elif layout == "blur":  # whole frame over a blurred copy of itself
        v = (f"[0:v]split[a][b];[a]scale=-2:{H},crop={W}:{H},boxblur=24:2,eq=brightness=-0.08[bg];"
             f"[b]scale={W}:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2-80[v]")
    else:  # facecam: the cam box on top, the rest of the frame below
        x, y, w, h = map(float, cam.split(":"))
        v = (f"[0:v]split[a][b];[a]crop=iw*{w}:ih*{h}:iw*{x}:ih*{y},scale={W}:{CAM_H}:force_original_aspect_ratio=increase,"
             f"crop={W}:{CAM_H}[cam];[b]scale=-2:{H - CAM_H},crop={W}:{H - CAM_H}:{crop_x(focus)}:0[main];[cam][main]vstack[v]")
    sub = str(ass).replace("\\", "/").replace(":", "\\:")
    return v + f";[v]fps=30,subtitles='{sub}'[vo]"


def ffmpeg_with_libass():
    """Burned captions need libass. Homebrew's plain ffmpeg lacks it; ffmpeg-full has it."""
    for exe in (shutil.which("ffmpeg"), "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg", "/usr/local/opt/ffmpeg-full/bin/ffmpeg"):
        if exe and Path(exe).exists():
            r = subprocess.run([exe, "-hide_banner", "-filters"], capture_output=True, text=True)
            if re.search(r"\bsubtitles\b", r.stdout):
                return exe
    sys.exit("ffmpeg has no subtitles filter (libass). macOS: brew install ffmpeg-full. Linux: apt install ffmpeg.")


def encode(ffmpeg, src, s0, e0, vf, mp4):
    """Render [s0, e0] of src through filter graph vf: H.264 1080x1920 30 fps, AAC, -14 LUFS."""
    run([ffmpeg, "-y", "-v", "error", "-ss", f"{s0:.2f}", "-to", f"{e0:.2f}", "-i", str(src),
         "-filter_complex", vf, "-map", "[vo]", "-map", "0:a?", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
         "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
         "-ar", "48000", "-movflags", "+faststart", str(mp4)])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("job"); ap.add_argument("--pick", type=int, default=1)
    ap.add_argument("--layout", choices=["fill", "blur", "facecam"], default="blur")
    ap.add_argument("--focus", default="auto", help="horizontal centre of the crop, 0-1 (fill and facecam). "
                    "auto (default): fill follows the faces shot by shot; facecam uses 0.5")
    ap.add_argument("--cam", help="facecam box as x:y:w:h fractions of the frame")
    ap.add_argument("--hook", default="")
    ap.add_argument("--captions", choices=["word", "none"], default="word")
    ap.add_argument("--style", choices=list(STYLES), help="caption look for this clip only; default: the style playbook.md names")
    ap.add_argument("--allow-profanity", action="store_true", help="keep swear words in captions (slurs are always masked)")
    ap.add_argument("--mask", default="", help="more words to mask in the captions, any language, separated by |")
    ap.add_argument("--start", type=float); ap.add_argument("--end", type=float)
    ap.add_argument("--frame", action="store_true", help="save one frame from the middle of the clip to choose a layout, then stop")
    a = ap.parse_args()
    if a.layout == "facecam" and not a.cam:
        sys.exit("--layout facecam needs --cam x:y:w:h (grab a frame and measure the cam box)")
    if a.focus != "auto":
        try:
            a.focus = float(a.focus); assert 0 <= a.focus <= 1
        except (ValueError, AssertionError):
            sys.exit("--focus must be auto or a number between 0 and 1")
    ffmpeg = ffmpeg_with_libass()
    d = Path(a.job); c = load_json(d / "candidates.json")
    pick = next((x for x in c["candidates"] if x["n"] == a.pick), None)
    if not pick and (a.start is None or a.end is None):  # a custom range needs no candidate
        sys.exit(f"no candidate {a.pick} in {d / 'candidates.json'}; pass --start and --end for a custom range")
    s0 = a.start if a.start is not None else pick["start"]; e0 = a.end if a.end is not None else pick["end"]
    src, off = video_source(c, s0, e0, d)  # URL jobs keep audio only: this fetches video for just this range
    if a.frame:
        png = d / f"frame_{a.pick}.png"
        run([ffmpeg, "-y", "-v", "error", "-ss", f"{(s0 + e0) / 2 - off:.2f}", "-i", src, "-frames:v", "1", str(png)])
        print(png)
        return
    if not a.style:
        pb = ROOT / "playbook.md"
        a.style = page_style(pb.read_text(encoding="utf-8") if pb.exists() else "")
        print(f"caption style: {a.style} (from playbook.md)")
    words = spoken_words(d, s0, e0) if a.captions == "word" else []
    ass = d / f"clip_{a.pick}.ass"
    extra = {m.strip().casefold() for m in a.mask.split("|") if m.strip()}
    ass.write_text(build_ass(words, s0, e0, a.hook, CAP_Y[a.layout], a.allow_profanity, a.style, extra), encoding="utf-8")
    lang = (d / "lang.txt").read_text().strip() if (d / "lang.txt").exists() else "en"
    if lang != "en" and words:  # the built-in swear and slur lists are English: Claude checks the rest
        said = " ".join(clean(w["w"], a.allow_profanity, extra) for w in words if s0 <= w["s"] < e0)
        print(f"captions ({lang}): {said}\nThe built-in masking is English only. Check these for swears and slurs "
              f"in {lang}, and re-cut with --mask \"word|word\" if any are left.")
    if a.focus == "auto":
        a.focus = auto_focus(ffmpeg, src, s0 - off, e0 - off) if a.layout == "fill" else 0.5
        print(f"crop focus: {a.focus}")
    clip_id = f"{d.name}_clip{a.pick}"  # one folder per clip: the .mp4, its .json record, captions.md and status.md
    folder = ROOT / "media" / "edits" / clip_id; folder.mkdir(parents=True, exist_ok=True)
    mp4 = folder / f"{clip_id}.mp4"
    encode(ffmpeg, src, s0 - off, e0 - off, video_filter(a.layout, ass, a.focus, a.cam), mp4)
    info = c.get("info", {})
    save_json(mp4.with_suffix(".json"), {"file": str(mp4), "job": str(d), "pick": a.pick, "start": s0, "end": e0,
                                         "layout": a.layout, "focus": a.focus, "cam": a.cam, "captions": a.captions, "style": a.style,
                                         "allow_profanity": a.allow_profanity, "mask": sorted(extra), "hook": a.hook, "source_url": info.get("webpage_url"),
                                         "source_title": info.get("title"), "source_channel": info.get("channel") or info.get("uploader")})
    for name, text in (("captions.md", CAPTIONS_TEMPLATE), ("status.md", STATUS_TEMPLATE)):  # never overwrite a caption already written
        if not (folder / name).exists():
            (folder / name).write_text(text, encoding="utf-8")
    print(mp4)


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        assert clean("what the fuck, retard") == "what the f***, r*****"
        assert clean("holy shit", profanity=True) == "holy shit"
        assert clean("¡Joder!", extra={"joder"}) == "¡J****!" and clean("JODER,", extra={"joder"}) == "J****,"
        assert clean("चूतिया", extra={"चूतिया"}) == "च" + "*" * 5 and clean("hola", extra={"joder"}) == "hola"
        ws = [{"w": w, "s": s, "e": s + 0.2} for w, s in [("one", 0), ("two,", 0.3), ("three", 0.6), ("four", 0.9), ("five", 2.0)]]
        assert [[x["w"] for x in g] for g in groups_of(ws)] == [["one", "two,"], ["three", "four"], ["five"]]
        ass = build_ass(ws, 0, 3, "HOOK", 1400)
        assert ass.count("Style: Cap") == 1 and ass.count(",Cap,") == 5 and ",Hook," in ass
        assert "{\\c&H0000E5FF&}ONE{\\c&H00FFFFFF&} TWO," in ass, "bold: caps, the spoken word in yellow"
        clean_ass = build_ass(ws, 0, 3, "", 1400, style="clean")
        assert "{\\1a&H50&}{\\1a&H00&}one{\\1a&H50&} two," in clean_ass and "fscx112" not in clean_ass, "clean: case kept, no pop"
        assert all(f"Style: Cap,{STYLES[k]['cap']}" in build_ass(ws, 0, 3, "", 1400, style=k) for k in STYLES)
        assert shots([0.4, 5.0, 5.6, 9.7], 10.0) == [(0.0, 5.0), (5.0, 10.0)], "short shots fold into the one before"
        assert focus_for([], 1920, 608, 0.3) == 0.3, "no face: keep the last focus"
        assert focus_for([(1700, 200)], 1920, 608) == 1.0 and focus_for([(860, 200)], 1920, 608) == 0.5
        assert focus_for([(760, 180), (980, 180)], 1920, 608) == 0.5, "two faces that fit: centre between them"
        assert focus_for([(200, 200), (1700, 220)], 1920, 608) == 1.0, "too far apart: the larger face"
        assert focus_for([(200, 200), (1500, 40)], 1920, 608) == 0.0, "small background faces don't count"
        assert focus_for([(200, 200), (1700, 220)], 1920, 608, talk=[5.0, 1.0]) == 0.0, "too far apart: the one talking"
        assert focus_for([(760, 180), (980, 180)], 1920, 608, talk=[0.0, 9.0]) == 0.5, "both fit: talk doesn't matter"
        import numpy as np
        rng = np.random.default_rng(0)
        loud = np.abs(np.sin(np.arange(40) / 2)) * 100  # speech rising and falling, 10 values a second
        frames = [np.zeros((100, 200)) for _ in range(40)]
        for k, g in enumerate(frames):
            g[60:90, 20:60] += 40 * k  # left mouth area changes steadily: noise unrelated to the voice
            g[60:90, 20:60] += rng.integers(0, 120, (30, 40))
            g[60:90, 130:170] = 80 * (k % 2) if loud[k] > 50 else 0  # right mouth moves while the voice is loud
        f = lambda x: [x, 20, 60, 75, 0, 0, 0, 0, x + 30, 55, x + 15, 70, x + 45, 70, 0.9]
        t = talk_scores(frames, [f(10), f(120)], loud)
        assert t[1] > 0.3 and t[1] > t[0], t
        assert page_style("4. Captions, large. Caption style: clean (`bold`: white caps; `box`: ...)") == "clean"
        assert page_style("Caption style: `box`") == "box" and page_style("Caption style: neon") == "bold" and page_style("") == "bold"
        assert crop_x(0.5) == "(iw-1080)*0.5"
        assert crop_x([[0, 0.2], [3.5, 0.8], [7, 0.5]]) == "'(iw-1080)*if(lt(t,3.5),0.2,if(lt(t,7),0.8,0.5))'"
        print("self-test ok")
    else:
        main()
