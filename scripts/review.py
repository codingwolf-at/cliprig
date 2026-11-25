"""Daily or weekly numbers from scoreboard.csv and payouts.csv. Reads only what the human logged.

Compares posts on one read (default views_24h) so 12h and 72h numbers are never mixed.
usage: python review.py [--days 7] [--read 24h|12h|72h] [--dir .]
       python review.py --self-test
"""
import argparse, csv, sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from statistics import median


def rows(path):
    if not Path(path).exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num(s):
    try:
        return float(str(s).replace(",", "").strip())
    except ValueError:
        return None


def summarize(posts, read, days, today):
    """Lines of the report for posts in the last `days` days, compared on `views_<read>`."""
    since = today - timedelta(days=days - 1)
    recent = [p for p in posts if (p.get("date") or "") >= since.isoformat()]
    col = f"views_{read}"
    have = [(num(p.get(col)), p) for p in recent]
    scored = sorted([(v, p) for v, p in have if v is not None], key=lambda x: -x[0])
    missing = [p for v, p in have if v is None]
    out = [f"{len(recent)} posts since {since}; {len(scored)} with {col}, {len(missing)} still missing it"]
    if not scored:
        return out
    out.append(f"median {col}: {median(v for v, _ in scored):g}")
    line = lambda v, p: f"  {v:g}  {p.get('platform', '')}  {p.get('date', '')} {p.get('time', '')}  \"{p.get('hook', '')}\""
    out += ["top 3:"] + [line(v, p) for v, p in scored[:3]]
    bottom = scored[max(3, len(scored) - 3):][::-1]  # never repeat a top-3 post
    out += ["bottom 3:"] + [line(v, p) for v, p in bottom] if bottom else []
    keys = [("pillar", lambda p: p.get("pillar")), ("platform", lambda p: p.get("platform")),
            ("format", lambda p: p.get("format")), ("hour", lambda p: (p.get("time") or "")[:2] + ":00"),
            ("test", lambda p: p.get("test_name"))]
    for name, key in keys:
        g = defaultdict(list)
        for v, p in scored:
            if key(p) and key(p) != ":00":
                g[key(p)].append(v)
        if len(g) > 1 or (name == "test" and g):
            out.append(f"median by {name}: " + ", ".join(f"{k} {median(vs):g} (n={len(vs)})"
                                                         for k, vs in sorted(g.items(), key=lambda x: -median(x[1]))))
    return out


def payouts(rows_):
    tot = defaultdict(float)
    for r in rows_:
        v = num(r.get("est_payout"))
        if v is not None:
            tot[r.get("status") or "unknown"] += v
    return ["payouts: " + ", ".join(f"{k} ${v:,.2f}" for k, v in sorted(tot.items()))] if tot else ["payouts: none logged"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--read", choices=["12h", "24h", "72h"], default="24h")
    ap.add_argument("--dir", default=".")
    a = ap.parse_args()
    d = Path(a.dir)
    if not (d / "scoreboard.csv").exists():
        sys.exit(f"no scoreboard.csv in {d.resolve()}: run this in the page folder")
    print("\n".join(summarize(rows(d / "scoreboard.csv"), a.read, a.days, date.today()) + payouts(rows(d / "payouts.csv"))))


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        P = lambda d, plat, v, pil="a", t="18:05": {"date": d, "time": t, "platform": plat, "pillar": pil, "hook": "h",
                                                     "views_24h": v, "format": "clip", "test_name": ""}
        ps = [P("2026-11-20", "x", "100"), P("2026-11-21", "yt", "1,000", "b", "09:10"), P("2026-11-22", "x", "300"),
              P("2026-11-22", "yt", ""), P("2026-10-01", "x", "99999")]
        out = summarize(ps, "24h", 7, date(2026, 11, 23))
        assert out[0] == "4 posts since 2026-11-17; 3 with views_24h, 1 still missing it", out
        assert out[1] == "median views_24h: 300" and out[3].startswith("  1000  yt"), out
        assert "median by platform: yt 1000 (n=1), x 200 (n=2)" in out, out
        assert "bottom 3:" not in out, "3 posts: no bottom list that repeats the top"
        more = summarize(ps[:3] + [P("2026-11-22", "x", str(v)) for v in (5, 50)], "24h", 7, date(2026, 11, 23))
        b = more.index("bottom 3:")
        assert [l.split()[0] for l in more[b + 1:b + 3]] == ["5", "50"], more
        assert "median by hour: 09:00 1000 (n=1), 18:00 200 (n=2)" in out, out
        assert payouts([{"est_payout": "1.5", "status": "paid"}, {"est_payout": "2", "status": "paid"},
                        {"est_payout": "", "status": "pending"}]) == ["payouts: paid $3.50"]
        print("self-test ok")
    else:
        main()
