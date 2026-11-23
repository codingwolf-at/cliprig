"""Trend radar: recent long-form YouTube videos ranked by views per hour.

Search a niche (--query) or list the latest uploads of creators the page may clip (--channel, repeatable).
The "permission" column marks channels named in campaigns.md, watchlist.md or media/raw/*/SOURCE.md.
usage: python trends.py --query "stand-up comedy" [--hours 24] [--limit 30] [--out trends.md]
       python trends.py --channel https://www.youtube.com/@name [--channel ...] --hours 168
       python trends.py --self-test
"""
import argparse, re, sys, time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import ROOT, ytdlp_json

UPLOAD_DATE_SORT = "&sp=CAI%253D"  # YouTube search sorted by upload date


def detail(url):
    try:
        return ytdlp_json(url, ["--skip-download"])
    except SystemExit:  # one private or removed video must not stop the scan
        return None


def listing(url, limit):
    try:
        flat = ytdlp_json(url, ["--flat-playlist", "--playlist-end", str(limit)])
    except SystemExit:
        print(f"could not list {url}")
        return []
    return [e["url"] for e in flat.get("entries", []) if e.get("url") and "/shorts/" not in e["url"]]


def permitted_text(root):
    """Lowercased text of the files that name creators the page may clip."""
    files = [root / "campaigns.md", root / "watchlist.md", *root.glob("media/raw/*/SOURCE.md")]
    return "\n".join(f.read_text(encoding="utf-8", errors="ignore") for f in files if f.exists()).lower()


def rank(infos, hours, now, known):
    """(rows sorted by views per hour, {reason: count} of skipped videos)."""
    rows, skipped = [], Counter()
    for i in infos:
        t = i.get("timestamp") or i.get("release_timestamp")
        if i.get("is_live"):
            skipped["live now"] += 1; continue
        if not t:
            skipped["no upload time"] += 1; continue
        age = max(0.25, (now - t) / 3600)
        if age > hours:
            skipped[f"older than {hours:g} h"] += 1; continue
        v = i.get("view_count") or 0
        ch = i.get("channel") or i.get("uploader") or ""
        handle = (i.get("uploader_id") or "").lower()
        perm = any(re.search(rf"(?<![\w@]){re.escape(n)}(?!\w)", known) for n in (ch.lower(), handle) if len(n) > 2)
        rows.append({"vph": v / age, "views": v, "age": age, "min": (i.get("duration") or 0) / 60, "channel": ch,
                     "title": i.get("title") or "", "url": i.get("webpage_url"), "heat": bool(i.get("heatmap")), "perm": perm})
    return sorted(rows, key=lambda r: -r["vph"]), skipped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query"); ap.add_argument("--channel", action="append", default=[])
    ap.add_argument("--hours", type=float, default=24)
    ap.add_argument("--limit", type=int, default=30); ap.add_argument("--out", default="trends.md")
    a = ap.parse_args()
    if not a.query and not a.channel:
        sys.exit("give --query \"niche words\" or --channel <channel url>")
    urls = []
    if a.query:
        urls += listing(f"https://www.youtube.com/results?search_query={a.query.replace(' ', '+')}{UPLOAD_DATE_SORT}", a.limit)
    for c in a.channel:
        urls += listing(c.rstrip("/") + "/videos", a.limit)
    urls = list(dict.fromkeys(urls))
    with ThreadPoolExecutor(6) as ex:
        infos = [i for i in ex.map(detail, urls) if i]
    rows, skipped = rank(infos, a.hours, time.time(), permitted_text(ROOT))
    if len(urls) > len(infos):
        skipped["unreadable"] = len(urls) - len(infos)
    what = " + ".join(([f'"{a.query}"'] if a.query else []) + a.channel)
    md = [f"# Trend radar: {what}, last {a.hours:.0f} h ({time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())})", "",
          f"{len(urls)} found, {len(rows)} ranked" + ("; skipped: " + ", ".join(f"{n} {k}" for k, n in skipped.items()) if skipped else ""), "",
          "| # | views/h | views | age h | min | channel | title | most replayed | permission |", "|---|---|---|---|---|---|---|---|---|"]
    for k, r in enumerate(rows, 1):
        md.append(f"| {k} | {r['vph']:,.0f} | {r['views']:,} | {r['age']:.1f} | {r['min']:.0f} | {r['channel']} | "
                  f"[{r['title'][:70].replace('|', '/')}]({r['url']}) | {'yes' if r['heat'] else ''} | {'listed' if r['perm'] else ''} |")
    (ROOT / a.out).write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md[:16]))
    print(f"... {len(rows)} videos -> {ROOT / a.out}")


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        now = 1_000_000
        infos = [{"timestamp": now - 3600, "view_count": 500, "channel": "Some Pod", "uploader_id": "@somepod", "title": "a"},
                 {"timestamp": now - 7200, "view_count": 4000, "channel": "Other", "uploader_id": "@other", "title": "b"},
                 {"timestamp": now - 3600 * 48, "view_count": 9e6, "channel": "Old", "title": "c"},
                 {"timestamp": now - 60, "view_count": 10, "is_live": True, "title": "d"}]
        r, skipped = rank(infos, 24, now, "| some pod (podcast) | ...")
        assert [x["title"] for x in r] == ["b", "a"] and r[0]["vph"] == 2000, r
        assert skipped == {"older than 24 h": 1, "live now": 1}, skipped
        assert [x["perm"] for x in r] == [False, True], r
        assert not rank(infos, 24, now, "")[0][1]["perm"], "no permission files means nothing is listed"
        assert not rank(infos, 24, now, "another podcast")[0][0]["perm"], "whole words only: 'other' is not 'another'"
        assert rank(infos, 24, now, "clip @other's streams")[0][0]["perm"], "handle match"
        print("self-test ok")
    else:
        main()
