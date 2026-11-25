"""Find the best clip moments in a long video, podcast, stream VOD or local file.

Signals per second: loudness spikes (laughter, applause, shouting), YouTube "most replayed" heatmap,
live-chat spikes (YouTube VOD chat replay or a TwitchDownloader chat.json) and hook phrases in the transcript.
Windows start on a sentence start and end on a sentence end where the transcript allows.
Writes jobs/<id>/candidates.md + candidates.json.

usage: python moments.py <url-or-file> [--top 8] [--min 15] [--max 40] [--hype "phrase|phrase"] [--chat chat.json] [--max-minutes 90]
       python moments.py --self-test
"""
import argparse, bisect, json, math, re, sys, wave
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
from common import ffprobe, is_url, job_dir, load_json, run, save_json, tool, ytdlp_base, ytdlp_json

# reactions and hook phrases that work across niches; add niche words with --hype
HYPE = (r"no way|oh my (god|gosh)|omg|let'?s go|holy|insane|crazy|wtf|are you serious|i can'?t believe|"
        r"the truth is|here'?s the thing|nobody (knows|talks about)|biggest mistake|never again|plot twist")
CHAT_HYPE = re.compile(r"(LMAO|LOL|KEKW|OMEGALUL|W+\b|CLIP|💀|😂|🔥|NO WAY|HOLY)", re.I)


def fetch(src, d, max_min):
    info = {}
    if is_url(src):
        info = ytdlp_json(src)
        save_json(d / "info.json", {k: info.get(k) for k in ("id", "title", "uploader", "channel", "uploader_id", "webpage_url",
                                                             "duration", "view_count", "upload_date", "heatmap", "is_live", "was_live")})
        vid = d / "source.mp4"
        if not vid.exists():
            args = ytdlp_base() + ["-f", "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[height<=1080]/b", "--merge-output-format", "mp4",
                                   "-o", str(vid)]
            if (info.get("duration") or 0) > max_min * 60:
                print(f"source is {info['duration'] / 60:.0f} min; using the first {max_min} (raise --max-minutes for more)")
                args += ["--download-sections", f"*0-{max_min * 60}"]
            run(args + [src])
        if info.get("was_live") and not (d / "chat.json").exists():  # YouTube chat replay
            run(ytdlp_base() + ["--skip-download", "--write-subs", "--sub-langs", "live_chat", "-o", str(d / "chat"), src], check=False)
    else:
        vid = Path(src).resolve()
        save_json(d / "info.json", {"title": vid.stem, "webpage_url": str(vid)})
    return vid, info


def audio_rms(vid, d, max_min):
    wav = d / "audio.wav"
    if not wav.exists():
        run([tool("ffmpeg"), "-y", "-v", "error", "-i", str(vid), "-t", str(max_min * 60), "-ac", "1", "-ar", "16000", str(wav)])
    with wave.open(str(wav)) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    n = len(x) // 16000
    rms = np.sqrt((x[: n * 16000].reshape(n, 16000) ** 2).mean(1) + 1e-9)
    return wav, 20 * np.log10(rms)


def transcribe(wav, d):
    """Words with timestamps; b/eos mark the first/last word of each transcript segment (roughly a sentence)."""
    out = d / "transcript.json"
    if out.exists():
        return load_json(out)
    from faster_whisper import WhisperModel
    try:
        import ctranslate2
        cuda = ctranslate2.get_cuda_device_count() > 0
    except Exception:
        cuda = False
    with wave.open(str(wav)) as w:  # pass samples directly (16 kHz mono), no extra decoder needed
        pcm = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768

    def run_on(device):
        model = WhisperModel("small", device=device, compute_type="float16" if device == "cuda" else "int8")
        segs, _ = model.transcribe(pcm, word_timestamps=True, vad_filter=True)
        words = []
        for s in segs:
            ws = [{"w": w.word.strip(), "s": round(w.start, 2), "e": round(w.end, 2)} for w in (s.words or []) if w.word.strip()]
            if ws:
                ws[0]["b"] = ws[-1]["eos"] = True
                words += ws
        return words
    try:
        words = run_on("cuda" if cuda else "cpu")
    except RuntimeError as e:  # GPU present but CUDA libraries missing: fall back to CPU
        print(f"GPU transcription unavailable ({str(e)[:80]}), using CPU")
        words = run_on("cpu")
    save_json(out, words)
    return words


def mark_sentences(words):
    """Sentence edges from . ? ! when the transcript has punctuation: Whisper's segment edges often fall mid-sentence."""
    if not any(w["w"][-1:] in ".?!" for w in words):
        return words
    for i, w in enumerate(words):
        w["b"] = i == 0 or words[i - 1]["w"][-1:] in ".?!"
        w["eos"] = w["w"][-1:] in ".?!" or i == len(words) - 1
    return words


def chat_series(d, n, chat_arg):
    """Messages per second from YouTube live_chat json lines or a TwitchDownloader chat.json."""
    c = np.zeros(n)
    yt = list(d.glob("chat*.live_chat.json"))
    if yt:
        for line in yt[0].read_text(encoding="utf-8", errors="ignore").splitlines():
            try:
                a = json.loads(line)["replayChatItemAction"]
                t = int(a["videoOffsetTimeMsec"]) / 1000
                txt = json.dumps(a["actions"], ensure_ascii=False)
            except Exception:
                continue
            if 0 <= t < n:
                c[int(t)] += 2 if CHAT_HYPE.search(txt) else 1
    elif chat_arg:
        js = load_json(chat_arg)
        for m in js.get("comments", []):
            t = m.get("content_offset_seconds", 0)
            body = (m.get("message") or {}).get("body", "")
            if 0 <= t < n:
                c[int(t)] += 2 if CHAT_HYPE.search(body) else 1
    return c


def hype_series(words, n, pattern):
    """Phrase hits per second. Matches run over the joined transcript so multi-word phrases count."""
    rx = re.compile(rf"\b({pattern})\b", re.I)
    offsets, text = [], ""
    for w in words:
        offsets.append(len(text))
        text += w["w"] + " "
    out = np.zeros(n)
    for m in rx.finditer(text):
        t = int(words[bisect.bisect_right(offsets, m.start()) - 1]["s"])
        if t < n:
            out[t] += 1
    return out


def z(a):
    a = np.asarray(a, dtype=float)
    if a.std() < 1e-9:
        return np.zeros_like(a)
    return (a - np.median(a)) / (a.std() + 1e-9)


def smooth(a, k):
    k = max(1, int(k))
    return np.convolve(a, np.ones(k) / k, mode="same")


def pick(score, words, dur, top, mn, mx):
    """Non-overlapping (start, end, peak) windows around the highest peaks, snapped to sentence edges."""
    out, used = [], np.zeros(len(score), bool)
    for p in np.argsort(-score):
        if len(out) >= top or score[p] <= 0:
            break
        s0 = max(0, p - 0.55 * mx); e0 = min(dur, s0 + mx)
        ws = [x for x in words if x["s"] >= s0 and x["e"] <= e0]
        if ws:
            heads = [i for i, x in enumerate(ws) if x.get("b") and x["s"] <= p]
            ws = ws[heads[0]:] if heads else ws
            tails = [i for i, x in enumerate(ws) if x.get("eos") and x["e"] >= p]
            ws = ws[:tails[-1] + 1] if tails else ws
            prev_e = max((x["e"] for x in words if x["e"] <= ws[0]["s"]), default=0)
            next_s = min((x["s"] for x in words if x["s"] >= ws[-1]["e"]), default=dur)
            # pads never take the previous or next sentence's words
            s0 = max(prev_e, ws[0]["s"] - 0.3); e0 = min(dur, next_s, ws[-1]["e"] + 0.6)
        if e0 - s0 < mn:
            e0 = min(dur, s0 + mn)
        e0 = min(e0, s0 + mx)
        if used[int(s0):int(e0)].any():
            continue
        used[int(s0):int(e0)] = True
        out.append((s0, e0, int(p)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--min", type=float, default=15); ap.add_argument("--max", type=float, default=40)
    ap.add_argument("--hype", help="extra niche phrases, regex alternatives: \"buzzer beater|walk-off\"")
    ap.add_argument("--chat"); ap.add_argument("--max-minutes", type=int, default=90)
    a = ap.parse_args()
    d = job_dir(a.src)
    vid, info = fetch(a.src, d, a.max_minutes)
    dur = min(float(ffprobe(vid)["format"]["duration"]), a.max_minutes * 60)
    wav, db = audio_rms(vid, d, a.max_minutes)
    n = len(db)
    words = mark_sentences(transcribe(wav, d))
    # signals
    loud = smooth(np.clip(z(db - smooth(db, 30)), 0, None), 3)          # jumps above the local level
    hype = smooth(hype_series(words, n, HYPE + (f"|{a.hype}" if a.hype else "")), 5)
    heat = np.zeros(n)
    for h in (info.get("heatmap") or []):
        heat[int(h["start_time"]):int(math.ceil(h["end_time"]))] = h["value"]
    chat = chat_series(d, n, a.chat)
    chatz = smooth(np.clip(z(smooth(chat, 10)), 0, None), 3)
    w_heat = 2.0 if heat.any() else 0
    w_chat = 1.5 if chat.any() else 0
    score = 1.0 * loud + 0.8 * z(hype).clip(0) + w_heat * z(heat).clip(0) + w_chat * chatz
    picks = []
    for s0, e0, p in pick(score, words, dur, a.top, a.min, a.max):
        text = " ".join(x["w"] for x in words if s0 <= x["s"] < e0)
        why = []
        if loud[p] > 1: why.append("loudness spike")
        if hype[p] > 0: why.append("hook words")
        if heat[p] > 0.5: why.append(f"most replayed {heat[p]:.2f}")
        if w_chat and chatz[p] > 1: why.append("chat spike")
        picks.append({"start": round(s0, 2), "end": round(e0, 2), "peak": p,
                      "score": round(float(score[p]), 2), "why": why or ["overall energy"], "text": text[:400]})
    picks.sort(key=lambda x: x["start"])
    for i, x in enumerate(picks, 1):
        x["n"] = i
    meta = load_json(d / "info.json")
    save_json(d / "candidates.json", {"source": str(vid), "info": meta, "duration": dur, "candidates": picks,
                                      "signals": {"heatmap": bool(w_heat), "chat": bool(w_chat), "words": len(words)}})
    fmt = lambda t: f"{int(t // 60)}:{int(t % 60):02d}"
    md = [f"# Candidates: {meta.get('title', '')}", f"source: {meta.get('webpage_url', '')}",
          f"signals: loudness, transcript ({len(words)} words)" + (", most replayed" if w_heat else "") + (", chat" if w_chat else ""), ""]
    for x in picks:
        md += [f"## {x['n']}. {fmt(x['start'])}-{fmt(x['end'])} ({x['end'] - x['start']:.0f}s) score {x['score']}",
               f"why: {', '.join(x['why'])}", f"> {x['text']}", ""]
    (d / "candidates.md").write_text("\n".join(md), encoding="utf-8")
    print(f"job: {d}\n{len(picks)} candidates -> {d / 'candidates.md'}")


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        ws = [{"w": w, "s": s, "e": s + 0.3} for w, s in [("oh", 1), ("my", 1.3), ("God!", 1.6), ("what", 3)]]
        h = hype_series(ws, 5, HYPE)
        assert h[1] == 1 and h.sum() == 1, h
        words = [{"w": "x", "s": t, "e": t + 0.5, "b": t in (10, 20, 50), "eos": t in (19, 45, 49)} for t in range(100)]
        score = np.zeros(100); score[30] = 2; score[31] = 1
        got = pick(score, words, 100.0, 2, 15, 40)
        assert [(round(s, 1), round(e, 1), p) for s, e, p in got] == [(9.7, 46.0, 30)], got
        ms = mark_sentences([{"w": "office", "s": 0, "e": 0.9, "b": True}, {"w": "mates", "s": 1, "e": 1.9, "eos": True},
                             {"w": "a", "s": 2, "e": 2.2, "b": True}, {"w": "bit.", "s": 2.3, "e": 2.6}, {"w": "So", "s": 3, "e": 3.4}])
        assert [(x["b"], x["eos"]) for x in ms] == [(True, False), (False, False), (False, False), (False, True), (True, True)], ms
        raw = [{"w": "no", "s": 0, "e": 1, "b": True}, {"w": "punctuation", "s": 1, "e": 2, "eos": True}]
        assert mark_sentences([dict(x) for x in raw]) == raw, "no punctuation: keep Whisper's marks"
        tight = [{"w": "mates", "s": 9.0, "e": 9.95}] + [{"w": "x", "s": t, "e": t + 0.5, "b": t == 10, "eos": t == 30} for t in range(10, 40)]
        sc = np.zeros(60); sc[20] = 1
        assert round(pick(sc, tight, 60.0, 1, 15, 40)[0][0], 2) == 9.95, "lead-in stops at the previous word's end"
        tight.append({"w": "And", "s": 30.6, "e": 31})
        assert round(pick(sc, tight, 60.0, 1, 15, 40)[0][1], 2) == 30.6, "tail stops where the next sentence starts"
        print("self-test ok")
    else:
        main()
