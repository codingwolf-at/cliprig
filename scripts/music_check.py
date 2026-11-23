"""Flag possible music in a clip or segment before cutting.

Two checks:
1. Loud gaps: stretches between speech that still carry sound (background music, a song, game radio).
2. Hidden words: an unfiltered transcription (no voice-activity filter) finds words the normal
   transcription drops, which is often sung lyrics.

usage: python music_check.py <video-or-audio> [--start SEC] [--end SEC] [--model small] [--floor -50]
Exit code 0 = nothing flagged, 1 = something to listen to. It flags; a person decides.
"""
import argparse
import subprocess
import sys

import numpy as np
from faster_whisper import WhisperModel

SR = 16000


def decode(src):
    """Mono 16 kHz float32 via ffmpeg (avoids PyAV version clashes in faster-whisper's decoder)."""
    raw = subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-i", src, "-ac", "1", "-ar", str(SR),
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def loud_gaps(audio, speech, min_gap=1.0, floor_db=-50.0):
    """Return (start, end, dBFS) for gaps between speech segments louder than floor_db."""
    edges = [0.0] + [t for s, e in speech for t in (s, e)] + [len(audio) / SR]
    out = []
    for a, b in zip(edges[::2], edges[1::2]):
        if b - a < min_gap:
            continue
        chunk = audio[int(a * SR):int(b * SR)]
        db = 20 * np.log10(np.sqrt(np.mean(chunk ** 2)) + 1e-9)
        if db > floor_db:
            out.append((a, b, db))
    return out


def hidden_words(filtered, unfiltered):
    """Unfiltered segments that don't overlap any filtered speech segment."""
    return [u for u in unfiltered if not any(u[0] < e and s < u[1] for s, e, _ in filtered)]


def transcribe(model, audio, vad):
    segs, _ = model.transcribe(audio, vad_filter=vad, condition_on_previous_text=False)
    return [(s.start, s.end, s.text.strip()) for s in segs
            if s.text.strip() and s.no_speech_prob < 0.6 and s.avg_logprob > -1.0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float, default=None)
    ap.add_argument("--model", default="small")
    ap.add_argument("--floor", type=float, default=-50.0, help="gap loudness (dBFS) that counts as sound; raise for noisy rooms")
    a = ap.parse_args()

    audio = decode(a.src)
    audio = audio[int(a.start * SR):int(a.end * SR) if a.end else None]
    model = WhisperModel(a.model, device="auto", compute_type="int8")

    filtered = transcribe(model, audio, vad=True)
    gaps = loud_gaps(audio, [(s, e) for s, e, _ in filtered], floor_db=a.floor)
    hidden = hidden_words(filtered, transcribe(model, audio, vad=False))

    t = lambda x: f"{a.start + x:.1f}s"
    for s, e, db in gaps:
        print(f"LOUD GAP {t(s)}-{t(e)} at {db:.0f} dBFS: listen for music under it")
    for s, e, txt in hidden:
        print(f"HIDDEN WORDS {t(s)}-{t(e)}: \"{txt}\": lyrics?")
    if not gaps and not hidden:
        print("PASS: no loud gaps, no hidden words")
    sys.exit(1 if gaps or hidden else 0)


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        tone = (0.1 * np.sin(np.arange(SR * 3) * 2 * np.pi * 440 / SR)).astype(np.float32)
        quiet = np.zeros(SR * 3, dtype=np.float32)
        gaps = loud_gaps(np.concatenate([quiet, tone]), [(0.0, 1.0)])
        assert [g[:2] for g in gaps] == [(1.0, 6.0)], gaps
        assert loud_gaps(quiet, []) == []
        assert hidden_words([(0, 2, "a")], [(1, 3, "a"), (5, 6, "la la")]) == [(5, 6, "la la")]
        print("self-test ok")
    else:
        main()
