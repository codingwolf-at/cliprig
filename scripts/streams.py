"""Find live streams, ranked by concurrent viewers. No accounts or API keys.

--query searches YouTube live streams. --twitch-category lists a Twitch category ("Just Chatting", "Chess").
--channel (repeatable, YouTube or twitch.tv URL) checks whether one creator is live right now.
The "permission" column marks channels named in campaigns.md, watchlist.md or media/raw/*/SOURCE.md.
Viewer counts are exactly what the platform returned at run time.
usage: python streams.py [--query "..."] [--twitch-category "..."] [--channel URL ...] [--limit 20] [--out streams.md]
"""
import argparse, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote_plus
sys.path.insert(0, str(Path(__file__).parent))
from common import ROOT, is_listed, permitted_text, ytdlp_json
import twitch as tw

LIVE_FILTER = "&sp=EgJAAQ%253D%253D"  # YouTube search: live now


def fmt_dur(sec):
    if not sec or sec < 0:
        return ""
    sec = int(sec)
    return f"{sec // 3600}h{sec % 3600 // 60:02d}m"


def quiet_json(url, extra=()):
    try:
        return ytdlp_json(url, list(extra))
    except SystemExit:  # run() exits on failure; one bad video must not stop the scan
        return None


def yt_row(i, now):
    if not i or not i.get("is_live"):
        return None
    start = i.get("release_timestamp") or i.get("timestamp")
    return {"platform": "YouTube", "channel": i.get("channel") or i.get("uploader") or "", "handle": i.get("uploader_id") or "",
            "title": i.get("title") or "", "url": i.get("webpage_url") or "", "viewers": i.get("concurrent_view_count"),
            "live_for": fmt_dur(now - start) if start else ""}


def tw_row(r, now):
    st = tw.started_ts(r["created_at"])
    return {"platform": "Twitch", "channel": r["name"], "handle": r["login"], "title": r["title"], "url": r["url"],
            "viewers": r["viewers"], "live_for": fmt_dur(now - st) if st else ""}


def youtube_search(query, limit):
    flat = quiet_json(f"https://www.youtube.com/results?search_query={quote_plus(query)}{LIVE_FILTER}",
                      ["--flat-playlist", "--playlist-end", str(limit)])
    if not flat:
        print("youtube search failed", file=sys.stderr)
        return []
    urls = [e.get("url") or f"https://www.youtube.com/watch?v={e['id']}" for e in flat.get("entries") or [] if e and e.get("id")]
    with ThreadPoolExecutor(6) as ex:
        infos = list(ex.map(quiet_json, urls))
    now = time.time()
    return [r for r in (yt_row(i, now) for i in infos) if r]


def channel_live(url):
    """Row if this YouTube or Twitch channel is live now, else None."""
    now = time.time()
    if "twitch.tv/" in url:
        try:
            r = tw.live_user(url.rstrip("/").split("/")[-1])
        except Exception as e:
            print(f"twitch check failed for {url}: {e}", file=sys.stderr)
            return None
        return tw_row(r, now) if r else None
    return yt_row(quiet_json(url.rstrip("/") + "/live"), now)  # /live resolves to the current stream, if any


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query"); ap.add_argument("--twitch-category"); ap.add_argument("--channel", action="append", default=[])
    ap.add_argument("--limit", type=int, default=20); ap.add_argument("--out", default="streams.md")
    a = ap.parse_args()
    if not (a.query or a.twitch_category or a.channel):
        sys.exit('give --query "niche words", --twitch-category "Category" or --channel <url>')
    now = time.time(); sections = []
    if a.channel:
        with ThreadPoolExecutor(6) as ex:
            live = [r for r in ex.map(channel_live, a.channel) if r]
        sections.append((f"Watched channels ({len(live)} of {len(a.channel)} live)", live))
    if a.query:
        sections.append((f'YouTube: "{a.query}"', youtube_search(a.query, a.limit)))
    if a.twitch_category:
        sections.append((f"Twitch: {a.twitch_category}", [tw_row(r, now) for r in tw.top_streams(a.twitch_category, a.limit)]))
    known = permitted_text(ROOT)
    md = ["# Live streams", f"Checked {time.strftime('%Y-%m-%d %H:%M')}. Viewer counts are as returned at that moment.", ""]
    for name, rows in sections:
        rows = sorted(rows, key=lambda r: r["viewers"] or -1, reverse=True)
        md += [f"## {name}", ""]
        if not rows:
            md += ["No live streams found.", ""]
            continue
        md += ["| # | Platform | Channel | Title | Viewers | Live for | Permission | URL |", "|---|---|---|---|---|---|---|---|"]
        for n, r in enumerate(rows, 1):
            v = "" if r["viewers"] is None else f"{r['viewers']:,}"
            perm = "listed" if is_listed(known, r["channel"], r["handle"]) else ""
            md.append(f"| {n} | {r['platform']} | {r['channel']} | {r['title'][:80].replace('|', '/')} | {v} | {r['live_for']} | {perm} | {r['url']} |")
        md.append("")
    (ROOT / a.out).write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))
    print(f"wrote {ROOT / a.out}")


if __name__ == "__main__":
    main()
