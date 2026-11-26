"""Pre-post check of a finished clip: specs, length, caption requirements, banned terms.

Campaign rules are free text in campaigns.md, so the caller reads them and passes them in.
usage: python check.py <clip.mp4> [--min 7] [--max 60] [--caption "text"] [--require "#tag @handle"] [--ban "word|phrase"]
       python check.py --self-test
Reads <clip>.json (written by cut.py) next to the clip if present. Exit code 1 on any FAIL.
Also writes <clip>_shots.png, one frame per shot, to look at for footage the creator doesn't own.
"""
import argparse, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import ffprobe, load_json, run, tool

BANNED = ["leak", "leaked", "free download", "crack", "cracked", "piracy", "pirated", "full episode free"]


def fps_of(s):
    try:
        a, b = s.split("/"); return float(a) / float(b)
    except (ValueError, ZeroDivisionError):
        return 0.0


def checks(probe, meta, caption, mn, mx, require, ban):
    """(name, ok, detail) per check. caption=None means no caption was given."""
    streams = probe.get("streams", [])
    v = next((s for s in streams if s.get("codec_type") == "video"), None)
    au = next((s for s in streams if s.get("codec_type") == "audio"), None)
    dur = float(probe.get("format", {}).get("duration", 0) or 0)
    f = fps_of(v.get("r_frame_rate", "0/1")) if v else 0
    res = [("resolution 1080x1920", bool(v) and (v.get("width"), v.get("height")) == (1080, 1920),
            f"{v.get('width')}x{v.get('height')}" if v else "no video"),
           ("fps about 30", 29 <= f <= 31, f"{f:.2f}"),
           ("has audio", au is not None, ""),
           (f"duration {mn:g}-{mx:g}s", mn <= dur <= mx, f"{dur:.1f}s")]
    text = f"{meta.get('hook', '')} {caption or ''}".lower()
    hits = [b for b in BANNED + [x.strip() for x in (ban or "").split("|") if x.strip()]
            if re.search(rf"\b{re.escape(b.lower())}\b", text)]
    res.append(("no banned terms in hook/caption", not hits, ", ".join(hits)))
    if caption is None:
        res.append(("caption", True, "not given, caption checks skipped"))
        return res
    low = caption.lower()
    miss = [t for t in (require or "").split() if t.lower() not in low]
    if require:
        res.append(("required tags/mentions", not miss, ("missing " + " ".join(miss)) if miss else require))
    channel = (meta.get("source_channel") or "").lower()
    credited = "clip from" in low or (channel and channel in low)
    res.append(("credit in caption", bool(credited), "" if credited else "add 'Clip from <show or channel> with <creator>.'"))
    return res


def shot_sheet(clip):
    """One frame per shot, tiled 6x4, to spot inserted footage (film, TV, other creators): (png, shot start times)."""
    png = clip.with_name(f"{clip.stem}_shots.png")
    r = run([tool("ffmpeg"), "-hide_banner", "-y", "-i", str(clip), "-vf",
             "select='eq(n,0)+gt(scene,0.3)',showinfo,scale=-2:360,tile=6x4:padding=4",
             "-fps_mode", "vfr", "-frames:v", "1", str(png)], capture=True)
    return png, [float(t) for t in re.findall(r"pts_time:([\d.]+)", r.stderr)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("clip")
    ap.add_argument("--min", type=float, default=7); ap.add_argument("--max", type=float, default=60)
    ap.add_argument("--caption", help="the post caption exactly as it will be posted")
    ap.add_argument("--require", default="", help="space-separated hashtags/mentions the campaign requires")
    ap.add_argument("--ban", default="", help="extra banned words or phrases, separated by |")
    a = ap.parse_args()
    clip = Path(a.clip)
    if not clip.exists():
        sys.exit(f"FAIL file not found: {clip}")
    side = clip.with_suffix(".json")
    meta = load_json(side) if side.exists() else {}
    res = checks(ffprobe(clip), meta, a.caption, a.min, a.max, a.require, a.ban)
    for n, ok, d in res:
        print(f"{'PASS' if ok else 'FAIL'}  {n}" + (f"  [{d}]" if d else ""))
    png, starts = shot_sheet(clip)
    more = f" (the sheet shows the first 24 of {len(starts)})" if len(starts) > 24 else ""
    print(f"LOOK  {len(starts)} shots, starting at {', '.join(f'{t:.1f}s' for t in starts)}{more}: view {png} "
          "for film, TV, music video or another creator's footage cut into the source")
    bad = [r for r in res if not r[1]]
    print("RESULT: " + ("FAIL" if bad else "PASS"))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        good = {"streams": [{"codec_type": "video", "width": 1080, "height": 1920, "r_frame_rate": "30/1"},
                            {"codec_type": "audio"}], "format": {"duration": "20.0"}}
        meta = {"hook": "He said no", "source_channel": "Some Pod"}
        r = checks(good, meta, "He said no. Clip from Some Pod with Ann. #somepod", 7, 60, "#somepod", "")
        assert all(ok for _, ok, _ in r), r
        r = dict((n, ok) for n, ok, _ in checks(good, meta, "Leaked clip #x", 7, 15, "#somepod @ann", "brandx"))
        assert not r["duration 7-15s"] and not r["no banned terms in hook/caption"]
        assert not r["required tags/mentions"] and not r["credit in caption"]
        assert all(ok for _, ok, _ in checks(good, meta, None, 7, 60, "", "")), "no caption must not fail"
        bad = {"streams": [{"codec_type": "video", "width": 1080, "height": 1918, "r_frame_rate": "60/1"}], "format": {"duration": "3"}}
        assert sum(not ok for _, ok, _ in checks(bad, {}, None, 7, 60, "", "")) == 4
        assert checks(good, {"hook": "crackdown on rent"}, None, 7, 60, "", "")[4][1], "word match, not substring"
        print("self-test ok")
    else:
        main()
