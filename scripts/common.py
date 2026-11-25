"""Shared helpers: paths, tool lookup, yt-dlp and ffmpeg wrappers."""
import hashlib, json, os, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(os.environ.get("CLIPRIG_HOME", Path.cwd()))
JOBS = ROOT / "jobs"


def tool(name):
    p = shutil.which(name)
    if not p:
        sys.exit(f"{name} not found. Run the setup skill first (it installs ffmpeg and yt-dlp).")
    return p


def run(cmd, check=True, capture=False):
    r = subprocess.run(cmd, check=False, text=True, encoding="utf-8", errors="replace",
                       stdout=subprocess.PIPE if capture else None, stderr=subprocess.PIPE if capture else None)
    if check and r.returncode != 0:
        msg = (r.stderr or "")[-1500:] if capture else ""
        sys.exit(f"command failed ({r.returncode}): {' '.join(map(str, cmd))[:200]}\n{msg}")
    return r


def ytdlp_base():
    import importlib.util
    exe = [sys.executable, "-m", "yt_dlp"] if importlib.util.find_spec("yt_dlp") else [tool("yt-dlp")]
    base = exe + ["--no-warnings", "--no-progress"]
    if sys.platform == "win32":
        base += ["--compat-options", "no-certifi"]  # use the Windows certificate store
    return base


def ytdlp_json(url, extra=()):
    r = run(ytdlp_base() + ["-J", *extra, url], capture=True)
    return json.loads(r.stdout)


def is_url(s):
    return bool(re.match(r"https?://", s))


def job_dir(src):
    key = hashlib.sha1(src.encode()).hexdigest()[:8]
    stem = re.sub(r"[^a-z0-9]+", "-", Path(src).stem.lower() if not is_url(src) else src.split("v=")[-1].split("/")[-1].lower())[:24].strip("-")
    d = JOBS / f"{stem or 'job'}-{key}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def ffprobe(path):
    r = run([tool("ffprobe"), "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height,r_frame_rate",
             "-of", "json", str(path)], capture=True)
    return json.loads(r.stdout)


def save_json(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def permitted_text(root):
    """Lowercased text of the files that name creators the page may clip."""
    files = [root / "campaigns.md", root / "watchlist.md", *root.glob("media/raw/*/SOURCE.md")]
    return "\n".join(f.read_text(encoding="utf-8", errors="ignore") for f in files if f.exists()).lower()


def is_listed(known, *names):
    """True if any channel name or handle appears as a whole word in the permission files' text."""
    return any(re.search(rf"(?<![\w@]){re.escape(n.lower())}(?!\w)", known) for n in names if n and len(n) > 2)


def video_source(c, s0, e0, d, margin=3.0):
    """(path, offset): a file with video covering source seconds [s0, e0], and the source time its 0 s is at.
    URL jobs keep only audio, so the range (plus a margin) is downloaded once at up to 4K into jobs/<id>/sections/."""
    src = c["source"]
    if any(s.get("codec_type") == "video" for s in ffprobe(src).get("streams", [])):
        return src, 0.0
    url = (c.get("info") or {}).get("webpage_url") or ""
    if not is_url(url):
        sys.exit(f"{src} has no video, and the job has no source URL to fetch it from")
    a, b = max(0.0, s0 - margin), e0 + margin
    out = Path(d) / "sections" / f"{a:.1f}-{b:.1f}.mp4"
    if not out.exists():
        out.parent.mkdir(exist_ok=True)
        # exact cut points keep burned captions in sync with the speech
        run(ytdlp_base() + ["-f", "bv*[height<=2160]+ba/b[height<=2160]/b", "--merge-output-format", "mp4",
                            "--download-sections", f"*{a:.2f}-{b:.2f}", "--force-keyframes-at-cuts", "-o", str(out), url])
    return str(out), a
