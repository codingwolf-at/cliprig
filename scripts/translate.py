"""One finished clip in other languages, with the same layout, hook box and captions as the original cut.

Two steps, so the translation is done by a person or Claude, not a machine-translation service:
  1. python translate.py media/edits/<clip>.mp4 --export
     writes <clip>_lines.json: {"hook": "...", "lines": ["spoken sentence", ...]}
  2. Write <clip>_<lang>.json with the same shape: the hook and every line translated, same number of lines.
     python translate.py media/edits/<clip>.mp4 --lang es [--lang pt ...]
     renders <clip>_<lang>.mp4 + .json (for rule-check).
Translated words are spread evenly over each original sentence's timing.
usage: python translate.py <clip.mp4> (--export | --lang LANG ...)
       python translate.py --self-test
"""
import argparse, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import load_json, save_json, video_source
from cut import CAP_Y, build_ass, encode, ffmpeg_with_libass, video_filter


def sentences(words):
    """Split words into sentences on end punctuation or a pause over 0.8 s."""
    out, cur = [], []
    for w in words:
        if cur and w["s"] - cur[-1]["e"] > 0.8:
            out.append(cur); cur = []
        cur.append(w)
        if w["w"][-1:] in ".?!":
            out.append(cur); cur = []
    return out + ([cur] if cur else [])


def spread(sents, lines):
    """Timed words for translated lines, each spread evenly over its original sentence."""
    res = []
    for sent, line in zip(sents, lines):
        new = line.split()
        if not new:
            continue
        a, b = sent[0]["s"], sent[-1]["e"]
        step = (b - a) / len(new)
        res += [{"w": x, "s": a + i * step, "e": a + (i + 1) * step} for i, x in enumerate(new)]
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("clip"); ap.add_argument("--export", action="store_true")
    ap.add_argument("--lang", action="append", default=[], help="language code with a <clip>_<lang>.json next to the clip")
    a = ap.parse_args()
    clip = Path(a.clip)
    side = clip.with_suffix(".json")
    if not side.exists():
        sys.exit(f"{side} not found: cut the clip with clip-cutter first")
    meta = load_json(side)
    s0, e0, d = meta["start"], meta["end"], Path(meta["job"])
    words = [w for w in load_json(d / "transcript.json") if s0 <= w["s"] < e0 and w["w"]]
    sents = sentences(words) if meta.get("captions", "word") == "word" else []
    if a.export:
        out = clip.with_name(f"{clip.stem}_lines.json")
        save_json(out, {"hook": meta.get("hook", ""), "lines": [" ".join(w["w"] for w in s) for s in sents]})
        print(out)
        return
    if not a.lang:
        sys.exit("give --export or --lang <code>")
    ffmpeg = ffmpeg_with_libass()
    src, off = video_source(load_json(d / "candidates.json"), s0, e0, d)
    layout = meta.get("layout", "blur")
    for lang in a.lang:
        tf = clip.with_name(f"{clip.stem}_{lang}.json")
        if not tf.exists():
            sys.exit(f"{tf} not found: run --export, then write the translation there")
        t = load_json(tf)
        if len(t.get("lines", [])) != len(sents):
            sys.exit(f"{tf}: {len(t.get('lines', []))} lines, the clip has {len(sents)}. Translate every line, keep the count.")
        hook = t.get("hook", "") if meta.get("hook") else ""
        ass = d / f"{clip.stem}_{lang}.ass"
        ass.write_text(build_ass(spread(sents, t["lines"]), s0, e0, hook, CAP_Y[layout], meta.get("allow_profanity", False)),
                       encoding="utf-8")
        mp4 = clip.with_name(f"{clip.stem}_{lang}.mp4")
        encode(ffmpeg, src, s0 - off, e0 - off, video_filter(layout, ass, meta.get("focus", 0.5), meta.get("cam")), mp4)
        save_json(mp4.with_suffix(".json"), dict(meta, file=str(mp4), hook=hook, lang=lang, translated_from=str(clip)))
        print(mp4)


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        ws = [{"w": w, "s": s, "e": s + 0.3} for w, s in [("Hi", 0), ("there.", 0.4), ("Wait", 1.0), ("what", 1.4), ("now", 3.0)]]
        ss = sentences(ws)
        assert [[w["w"] for w in s] for s in ss] == [["Hi", "there."], ["Wait", "what"], ["now"]], ss
        sp = spread(ss, ["Hola a todos.", "Espera", ""])
        assert [w["w"] for w in sp] == ["Hola", "a", "todos.", "Espera"], sp
        assert sp[0]["s"] == 0 and abs(sp[2]["e"] - 0.7) < 1e-9 and sp[3]["s"] == 1.0, sp
        print("self-test ok")
    else:
        main()
