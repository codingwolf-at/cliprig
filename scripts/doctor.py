"""Check a page's setup: Python, packages, yt-dlp age, ffmpeg captions, speech model, page files, cookies, self-tests.

Prints PASS / WARN / FAIL per check with the fix. Exit code 1 on any FAIL.
usage: python doctor.py          (run in the page folder with the page's .venv python)
       python doctor.py --self-test
"""
import importlib.util, re, shutil, subprocess, sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

HERE = Path(__file__).parent
SELF_TESTS = ["music_check", "moments", "cut", "check", "review", "trends", "translate", "questions"]
PAGE_FILES = ["CLAUDE.md", "playbook.md", "campaigns.md", "scoreboard.csv", "yt-dlp.conf", ".gitignore"]
PY = f'"{Path(sys.executable).as_posix()}"'  # the interpreter running this, right on every OS
# venvs made with uv have no pip
UPDATE_YTDLP = (f'uv pip install --python {PY} -U "yt-dlp[default]"' if shutil.which("uv")
                else f'{PY} -m pip install -U "yt-dlp[default]"')


def ytdlp_age(version, today):
    """Days since a yt-dlp release, from its YYYY.MM.DD version string. None if unreadable."""
    m = re.match(r"(\d{4})\.(\d{1,2})\.(\d{1,2})", version or "")
    return (today - date(*map(int, m.groups()))).days if m else None


def cookie_checks(conf, gitignore, cookies_exist):
    """(status, name, detail) for how the page handles YouTube cookies."""
    on = any(l.strip().startswith("--cookies") for l in conf.splitlines())
    ignored = any(l.strip() in ("cookies.txt", "*cookies*.txt") for l in gitignore.splitlines())
    out = [("PASS" if ignored else "FAIL", "cookies.txt is gitignored", "" if ignored else "add cookies.txt to .gitignore")]
    if on:
        out.append(("WARN", "yt-dlp.conf uses cookies", "only needed for a YouTube bot check; comment the line out once downloads work"))
    if cookies_exist:
        out.append(("WARN", "cookies.txt is on disk", "it works like a password; delete it once downloads work"))
    return out


def run_checks(root):
    res = []
    v = sys.version_info
    res.append(("PASS" if (3, 10) <= v[:2] <= (3, 12) else "FAIL", f"Python {v.major}.{v.minor}",
                "" if (3, 10) <= v[:2] <= (3, 12) else "use Python 3.10-3.12 for .venv (faster-whisper has no wheels for newer ones)"))
    missing = [p for p in ("faster_whisper", "numpy", "requests", "yt_dlp") if importlib.util.find_spec(p) is None]
    res.append(("FAIL" if missing else "PASS", "packages installed", f"missing {', '.join(missing)}: reinstall requirements.txt" if missing else ""))
    if "yt_dlp" not in missing:
        from yt_dlp.version import __version__ as ver
        age = ytdlp_age(ver, date.today())
        res.append(("WARN" if age is None or age > 30 else "PASS", f"yt-dlp {ver}",
                    f"{age} days old; update: {UPDATE_YTDLP}" if age and age > 30 else ""))
    try:
        from cut import ffmpeg_with_libass
        res.append(("PASS", "ffmpeg with captions (libass)", ffmpeg_with_libass()))
    except SystemExit as e:
        res.append(("FAIL", "ffmpeg with captions (libass)", str(e)))
    try:
        from huggingface_hub import try_to_load_from_cache
        cached = isinstance(try_to_load_from_cache("Systran/faster-whisper-small", "model.bin"), str)
    except ImportError:
        cached = False
    res.append(("PASS" if cached else "WARN", "speech model downloaded", "" if cached else
                f"first moment-finder run will download ~500 MB; get it now: {PY} -c \"from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8')\""))
    gone = [f for f in PAGE_FILES if not (root / f).exists()]
    res.append(("WARN" if gone else "PASS", "page files", f"missing {', '.join(gone)}: run this in the page folder, or re-run setup" if gone else ""))
    read = lambda f: (root / f).read_text(encoding="utf-8", errors="ignore") if (root / f).exists() else ""
    if (root / ".gitignore").exists():
        res += cookie_checks(read("yt-dlp.conf"), read(".gitignore"), (root / "cookies.txt").exists())
    failed = [s for s in SELF_TESTS
              if subprocess.run([sys.executable, str(HERE / f"{s}.py"), "--self-test"], capture_output=True).returncode != 0]
    res.append(("FAIL" if failed else "PASS", f"self-tests ({len(SELF_TESTS)})", f"failing: {', '.join(failed)}" if failed else ""))
    return res


def main():
    res = run_checks(Path.cwd())
    for status, name, detail in res:
        print(f"{status:4}  {name}" + (f"  [{detail}]" if detail else ""))
    worst = "FAIL" if any(r[0] == "FAIL" for r in res) else "WARN" if any(r[0] == "WARN" for r in res) else "PASS"
    print(f"RESULT: {worst}")
    sys.exit(1 if worst == "FAIL" else 0)


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        assert ytdlp_age("2026.11.23", date(2026, 11, 26)) == 3
        assert ytdlp_age("2026.10.01.232412", date(2026, 11, 26)) == 56, "nightly versions have a time suffix"
        assert ytdlp_age("unknown", date(2026, 11, 26)) is None
        off = "# Only when...\n# --cookies cookies.txt\n--sleep-requests 1.5\n"
        assert cookie_checks(off, "cookies.txt\n", False) == [("PASS", "cookies.txt is gitignored", "")]
        r = cookie_checks("--cookies cookies.txt\n", "jobs/\n", True)
        assert [s for s, _, _ in r] == ["FAIL", "WARN", "WARN"], r
        print("self-test ok")
    else:
        main()
