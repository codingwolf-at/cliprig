"""Cut one candidate into a finished vertical clip.

1080x1920, 30 fps, word-by-word burned captions (slurs always masked, swears masked unless allowed),
hook box in the first seconds, loudness normalised to -14 LUFS.
Writes media/edits/<job>_clip<n>.mp4 + .json (metadata for rule checks).

usage: python cut.py jobs/<id> --pick 1 [--layout fill|blur|facecam] [--focus 0.5] [--cam x:y:w:h]
                     [--hook "TEXT"] [--captions word|none] [--allow-profanity] [--start SEC --end SEC]
       python cut.py --self-test
"""
import argparse, re, shutil, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import ROOT, load_json, run, save_json, tool

W, H = 1080, 1920
CAP_Y = {"fill": 1380, "blur": 1460, "facecam": 1120}
CAM_H = 730  # facecam layout: top panel height (~38%); must be even or yuv420p loses a row per panel

SLURS = re.compile(r"\b(nigg\w*|n[i1]gg?a\w*|f[a@]gg?\w*|retard\w*|tranny\w*|chink\w*|spic\w*|kike\w*)\b", re.I)
SWEARS = re.compile(r"\b(fuck\w*|motherfuck\w*|shit\w*|bitch\w*|cunt\w*|dick\w*|pussy\w*|asshole\w*|bastard\w*|whore\w*|slut\w*)\b", re.I)


def ts(t):
    t = max(0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def clean(s, profanity=False):
    """Slurs are always masked (first letter kept); hard swears too unless profanity=True."""
    mask = lambda m: m.group(0)[0] + "*" * (len(m.group(0)) - 1)
    s = SLURS.sub(mask, s)
    return s if profanity else SWEARS.sub(mask, s)


def esc(s):
    return s.replace("\\", "").replace("{", "(").replace("}", ")").replace("\n", " ")


def groups_of(words):
    """Caption groups of up to 3 words, broken on punctuation or a pause."""
    groups, cur = [], []
    for w in words:
        if cur and (len(cur) == 3 or w["s"] - cur[-1]["e"] > 0.6 or cur[-1]["w"][-1:] in ".?!,"):
            groups.append(cur); cur = []
        cur.append(w)
    return groups + ([cur] if cur else [])


def build_ass(words, s0, e0, hook, cap_y, profanity=False):
    hdr = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Arial Black,92,&H00FFFFFF,&H0000E5FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,7,3,5,60,60,0,1
Style: Hook,Arial Black,68,&H00000000,&H00000000,&H00FFFFFF,&H00FFFFFF,-1,0,0,0,100,100,0,0,3,18,0,8,70,70,170,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    groups = groups_of([dict(w, w=clean(w["w"], profanity)) for w in words if s0 <= w["s"] < e0 and w["w"]])
    for gi, g in enumerate(groups):
        g_end = groups[gi + 1][0]["s"] if gi + 1 < len(groups) else g[-1]["e"] + 0.4
        g_end = min(g_end, g[-1]["e"] + 0.8)
        for k, w in enumerate(g):
            a = w["s"] - s0; b = (g[k + 1]["s"] - s0) if k + 1 < len(g) else g_end - s0
            if b <= a:
                continue
            parts = [("{\\c&H0000E5FF&}" + esc(x["w"].upper()) + "{\\c&H00FFFFFF&}") if j == k else esc(x["w"].upper())
                     for j, x in enumerate(g)]
            pop = "{\\fscx112\\fscy112\\t(0,90,\\fscx100\\fscy100)}" if k == 0 else ""
            ev.append(f"Dialogue: 0,{ts(a)},{ts(b)},Cap,,0,0,0,,{{\\pos({W // 2},{cap_y})}}{pop}{' '.join(parts)}")
    if hook:
        ev.append(f"Dialogue: 1,{ts(0)},{ts(2.6)},Hook,,0,0,0,,{{\\fad(0,180)\\fscx92\\fscy92\\t(0,120,\\fscx100\\fscy100)}}{esc(hook)}")
    return hdr + "\n".join(ev) + "\n"


def video_filter(layout, ass, focus=0.5, cam=None):
    """Layout + burned-caption filter graph ending in [vo]."""
    if layout == "fill":  # crop the frame to 9:16, centred on `focus` (0 = left edge, 1 = right edge)
        v = f"[0:v]scale=-2:{H},crop={W}:{H}:(iw-{W})*{focus}:0[v]"
    elif layout == "blur":  # whole frame over a blurred copy of itself
        v = (f"[0:v]split[a][b];[a]scale=-2:{H},crop={W}:{H},boxblur=24:2,eq=brightness=-0.08[bg];"
             f"[b]scale={W}:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2-80[v]")
    else:  # facecam: the cam box on top, the rest of the frame below
        x, y, w, h = map(float, cam.split(":"))
        v = (f"[0:v]split[a][b];[a]crop=iw*{w}:ih*{h}:iw*{x}:ih*{y},scale={W}:{CAM_H}:force_original_aspect_ratio=increase,"
             f"crop={W}:{CAM_H}[cam];[b]scale=-2:{H - CAM_H},crop={W}:{H - CAM_H}:(iw-{W})*{focus}:0[main];[cam][main]vstack[v]")
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("job"); ap.add_argument("--pick", type=int, default=1)
    ap.add_argument("--layout", choices=["fill", "blur", "facecam"], default="blur")
    ap.add_argument("--focus", type=float, default=0.5, help="horizontal centre of the crop, 0-1 (fill and facecam)")
    ap.add_argument("--cam", help="facecam box as x:y:w:h fractions of the frame")
    ap.add_argument("--hook", default="")
    ap.add_argument("--captions", choices=["word", "none"], default="word")
    ap.add_argument("--allow-profanity", action="store_true", help="keep swear words in captions (slurs are always masked)")
    ap.add_argument("--start", type=float); ap.add_argument("--end", type=float)
    a = ap.parse_args()
    if a.layout == "facecam" and not a.cam:
        sys.exit("--layout facecam needs --cam x:y:w:h (grab a frame and measure the cam box)")
    if not 0 <= a.focus <= 1:
        sys.exit("--focus must be between 0 and 1")
    ffmpeg = ffmpeg_with_libass()
    d = Path(a.job); c = load_json(d / "candidates.json")
    pick = next((x for x in c["candidates"] if x["n"] == a.pick), None)
    if not pick:
        sys.exit(f"no candidate {a.pick} in {d / 'candidates.json'}")
    s0 = a.start if a.start is not None else pick["start"]; e0 = a.end if a.end is not None else pick["end"]
    words = load_json(d / "transcript.json") if a.captions == "word" else []
    ass = d / f"clip_{a.pick}.ass"
    ass.write_text(build_ass(words, s0, e0, a.hook, CAP_Y[a.layout], a.allow_profanity), encoding="utf-8")
    out = ROOT / "media" / "edits"; out.mkdir(parents=True, exist_ok=True)
    mp4 = out / f"{d.name}_clip{a.pick}.mp4"
    run([ffmpeg, "-y", "-v", "error", "-ss", f"{s0:.2f}", "-to", f"{e0:.2f}", "-i", c["source"],
         "-filter_complex", video_filter(a.layout, ass, a.focus, a.cam), "-map", "[vo]", "-map", "0:a?",
         "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
         "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
         "-ar", "48000", "-movflags", "+faststart", str(mp4)])
    info = c.get("info", {})
    save_json(mp4.with_suffix(".json"), {"file": str(mp4), "job": str(d), "pick": a.pick, "start": s0, "end": e0,
                                         "layout": a.layout, "hook": a.hook, "source_url": info.get("webpage_url"),
                                         "source_title": info.get("title"), "source_channel": info.get("channel") or info.get("uploader")})
    print(mp4)


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        assert clean("what the fuck, retard") == "what the f***, r*****"
        assert clean("holy shit", profanity=True) == "holy shit"
        ws = [{"w": w, "s": s, "e": s + 0.2} for w, s in [("one", 0), ("two,", 0.3), ("three", 0.6), ("four", 0.9), ("five", 2.0)]]
        assert [[x["w"] for x in g] for g in groups_of(ws)] == [["one", "two,"], ["three", "four"], ["five"]]
        ass = build_ass(ws, 0, 3, "HOOK", 1400)
        assert ass.count("Style: Cap") == 1 and ass.count(",Cap,") == 5 and ",Hook," in ass
        print("self-test ok")
    else:
        main()
