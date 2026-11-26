"""CI smoke test: cut real clips with ffmpeg, captions, the per-shot crop and the shot sheet.

The script self-tests never call ffmpeg, so a broken filter or a Windows path only shows up here.
usage: python .github/smoke_cut.py   (needs ffmpeg with libass on PATH, or Homebrew's ffmpeg-full)
"""
import json, os, subprocess, sys, tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
from cut import ffmpeg_with_libass  # noqa: E402

page = Path(tempfile.mkdtemp(prefix="cliprig-smoke-"))
env = dict(os.environ, CLIPRIG_HOME=str(page))
ff = ffmpeg_with_libass()
job = page / "jobs" / "smoke"
job.mkdir(parents=True)

# 10 s source: two different test patterns (a camera cut at 5 s) and a tone
src = job / "source.mp4"
subprocess.run([ff, "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=1280x720:d=5:r=30", "-f", "lavfi",
                "-i", "smptebars=s=1280x720:d=5:r=30", "-f", "lavfi", "-i", "sine=f=440:d=10",
                "-filter_complex", "[0:v][1:v]concat=n=2:v=1[v]", "-map", "[v]", "-map", "2:a",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(src)], check=True)
words = [{"w": w, "s": 1.0 + i * 0.6, "e": 1.5 + i * 0.6} for i, w in enumerate("one two three four five six seven eight nine ten.".split())]
words[0]["b"] = words[-1]["eos"] = True
(job / "transcript.json").write_text(json.dumps(words))
(job / "candidates.json").write_text(json.dumps({"source": str(src), "info": {"channel": "Smoke Pod"},
                                                 "candidates": [{"n": 1, "start": 1.0, "end": 9.0}]}))
(page / "playbook.md").write_text("4. Word-by-word captions. Caption style: clean\n")


def py(script, *args):
    r = subprocess.run([sys.executable, str(SCRIPTS / script), *args], env=env, cwd=page, capture_output=True, text=True)
    print(r.stdout, r.stderr, sep="", end="")
    assert r.returncode == 0, f"{script} failed ({r.returncode})"
    return r.stdout


def meta(n):
    return json.loads((page / "media" / "edits" / f"smoke_clip{n}.json").read_text())


# fill, crop following faces (none here, so centred), style from playbook.md
py("cut.py", str(job), "--pick", "1", "--layout", "fill", "--hook", "Smoke test")
assert meta(1)["style"] == "clean" and meta(1)["focus"] == 0.5, meta(1)
# blur with an explicit style, and a custom range with an unused pick number
py("cut.py", str(job), "--pick", "2", "--layout", "blur", "--style", "box", "--start", "2", "--end", "9.5")
assert meta(2)["style"] == "box", meta(2)
for n in (1, 2):
    out = py("check.py", str(page / "media" / "edits" / f"smoke_clip{n}.mp4"), "--caption", "Smoke test. Clip from Smoke Pod.")
    assert "RESULT: PASS" in out and "LOOK  2 shots" in out, out
    assert (page / "media" / "edits" / f"smoke_clip{n}_shots.png").stat().st_size > 1000
print("smoke ok")
