"""Audience questions into clip leads.

Collects questions from subreddits (public JSON, 1 request/s) and/or pasted comments, clusters similar ones,
then searches the transcripts already in jobs/*/transcript.json for a moment that answers each cluster.
Writes questions.md; clusters with no matching moment go to idea-bank.md as sources to find.

usage: python questions.py --subs podcasts,standupcomedy [--days 3] [--comments comments.txt] [--out questions.md]
       python questions.py --self-test
"""
import argparse, base64, difflib, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import ROOT, load_json

UA = "script:cliprig:0.3 (read-only questions)"
STARTERS = ("how", "where", "what", "can", "is", "does", "why", "when", "who")
STOP = set("""a an the to of in on at for and or is are was were be been do does did can could would should will
i you we they he she it my your our this that these those there here with about as by from if any what why how who when
where which me him her them his their its im ive dont not no yes so just really like get got have has had know think
one thing things people anyone someone something way much many more most very also still even ever""".split())
WINDOW = 40  # max seconds of transcript per searchable moment
_last = [0.0]
_token = {}


def reddit_keys():
    """(client id, secret) of the user's own Reddit script app: REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET from the
    environment or the page's reddit.env (KEY=value lines, git-ignored). None without them: public JSON is used."""
    keys = dict(os.environ)
    f = ROOT / "reddit.env"
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            k, _, v = line.partition("=")
            keys.setdefault(k.strip(), v.strip().strip('"'))
    cid, secret = keys.get("REDDIT_CLIENT_ID"), keys.get("REDDIT_CLIENT_SECRET")
    return (cid, secret) if cid and secret else None


def token():
    """App-only OAuth token (read-only, no Reddit login), fetched once and renewed when it expires."""
    if _token.get("t") and time.time() < _token["until"]:
        return _token["t"]
    cid, secret = reddit_keys()
    req = urllib.request.Request("https://www.reddit.com/api/v1/access_token", method="POST",
                                 data=urllib.parse.urlencode({"grant_type": "client_credentials"}).encode(),
                                 headers={"User-Agent": UA, "Authorization": "Basic " +
                                          base64.b64encode(f"{cid}:{secret}".encode()).decode()})
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read().decode("utf-8"))
    _token.update(t=d["access_token"], until=time.time() + int(d.get("expires_in", 3600)) - 60)
    return _token["t"]


def fetch(url):
    """GET JSON, 1 request/sec, retry on 429 with backoff."""
    for attempt in range(4):
        wait = 1.0 - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        headers = {"User-Agent": UA}
        if reddit_keys():  # the official API with the user's own app; public JSON otherwise
            url = url.replace("https://www.reddit.com/", "https://oauth.reddit.com/")
            try:
                headers["Authorization"] = "bearer " + token()
            except Exception as e:  # never print the keys, only that the token request failed
                print(f"Reddit OAuth token request failed ({type(e).__name__}): check reddit.env", file=sys.stderr)
                return None
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                delay = int(e.headers.get("Retry-After", "") or 0) or 10 * (attempt + 1)
                print(f"429 on {url}, waiting {delay}s", file=sys.stderr)
                time.sleep(delay)
                continue
            print(f"HTTP {e.code} on {url}, skipped", file=sys.stderr)
            return None
        except Exception as e:
            print(f"error on {url}: {e}, skipped", file=sys.stderr)
            return None
    print(f"gave up on {url} after repeated 429", file=sys.stderr)
    return None


def is_question(text):
    t = text.strip().lower()
    return 10 <= len(t) <= 300 and (t.endswith("?") or t.startswith(STARTERS))


def question_lines(text):
    out = []
    for line in re.split(r"[\n\r]+|(?<=[.!?])\s+", text):
        line = re.sub(r"\s+", " ", line).strip()
        if is_question(line):
            out.append(line)
    return out


def tokens(s):
    s = re.sub(r"https?://\S+", " ", s.lower())
    return {w for w in re.findall(r"[a-z0-9']+", s) if w.strip("'") not in STOP and len(w) > 2}


def similar(a, b):
    ta, tb = a["tok"], b["tok"]
    if ta and tb and len(ta & tb) / len(ta | tb) >= 0.5:
        return True
    return difflib.SequenceMatcher(None, a["norm"], b["norm"]).ratio() >= 0.75


def collect_reddit(subs, days):
    cutoff = time.time() - days * 86400
    items, posts = [], []
    for sub in subs:
        data = fetch(f"https://www.reddit.com/r/{sub}/new.json?limit=100")
        if not data:
            continue
        for ch in data.get("data", {}).get("children", []):
            d = ch["data"]
            if d.get("created_utc", 0) < cutoff:
                continue
            link = "https://www.reddit.com" + d.get("permalink", "")
            posts.append({"id": d["id"], "score": d.get("score", 0), "link": link, "n": d.get("num_comments", 0)})
            for q in ([d.get("title", "")] if is_question(d.get("title", "")) else []) + question_lines(d.get("selftext", "")):
                items.append({"text": q, "score": d.get("score", 0), "link": link})
    for p in sorted((p for p in posts if p["n"] > 0), key=lambda p: p["score"], reverse=True)[:8]:
        data = fetch(f"https://www.reddit.com/comments/{p['id']}.json?limit=200&depth=1")
        if not data or len(data) < 2:
            continue
        for ch in data[1].get("data", {}).get("children", []):
            if ch.get("kind") == "t1":
                d = ch["data"]
                items += [{"text": q, "score": d.get("score", 0), "link": "https://www.reddit.com" + d.get("permalink", p["link"])}
                          for q in question_lines(d.get("body", ""))]
    return items


def collect_file(path):
    return [{"text": q, "score": 0, "link": ""} for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
            for q in question_lines(line.strip())]


def cluster(items):
    for it in items:
        it["tok"] = tokens(it["text"])
        it["norm"] = " ".join(sorted(it["tok"])) or it["text"].lower()
    clusters = []
    for it in items:
        for c in clusters:
            if similar(it, c["items"][0]):
                c["items"].append(it)
                break
        else:
            clusters.append({"items": [it]})
    for c in clusters:
        c["count"] = len(c["items"])
        c["votes"] = sum(max(i["score"], 0) for i in c["items"])
        c["question"] = sorted(c["items"], key=lambda i: (not i["text"].endswith("?"), -i["score"], len(i["text"])))[0]["text"]
        c["tok"] = set().union(*(i["tok"] for i in c["items"]))
        c["links"] = list(dict.fromkeys(i["link"] for i in c["items"] if i["link"]))[:3]
    return sorted(clusters, key=lambda c: (c["count"], c["votes"]), reverse=True)


def moments(words, job, title):
    """Searchable windows: runs of transcript sentences up to WINDOW seconds."""
    out, cur = [], []
    for w in words:
        if cur and (w.get("b") and w["e"] - cur[0]["s"] > WINDOW):
            out.append(cur); cur = []
        cur.append(w)
    if cur:
        out.append(cur)
    return [{"job": job, "title": title, "s": m[0]["s"], "e": m[-1]["e"], "text": " ".join(w["w"] for w in m),
             "tok": {w[:4] for w in tokens(" ".join(w["w"] for w in m))}} for m in out]  # 4-letter stems: drive ~ driving


def load_moments(root):
    res = []
    for t in sorted(root.glob("jobs/*/transcript.json")):
        info = t.parent / "info.json"
        title = (load_json(info).get("title") if info.exists() else None) or t.parent.name
        res += moments(load_json(t), t.parent.name, title)
    return res


def best_moment(c, ms):
    """The window sharing the most question words (by stem) with the cluster's main question.
    Needs 2 shared words, or 1 long specific one (7+ letters) like a name or term."""
    q = tokens(c["question"]) or c["tok"]
    best, top = None, 0
    for m in ms:
        shared = [w for w in q if w[:4] in m["tok"]]
        if len(shared) > top and (len(shared) >= 2 or any(len(w) >= 7 for w in shared)):
            best, top = m, len(shared)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subs", default="", help="comma-separated subreddits for the niche")
    ap.add_argument("--days", type=float, default=3)
    ap.add_argument("--comments", help="text file of comments pasted from our own posts, one per line")
    ap.add_argument("--ideas", default="idea-bank.md"); ap.add_argument("--out", default="questions.md")
    ap.add_argument("--min-count", type=int, default=1); ap.add_argument("--top", type=int, default=25)
    a = ap.parse_args()
    subs = [s.strip() for s in a.subs.split(",") if s.strip()]
    if not subs and not a.comments:
        sys.exit("give --subs and/or --comments")
    items = collect_reddit(subs, a.days) if subs else []
    if a.comments:
        if not Path(a.comments).exists():
            sys.exit(f"comments file not found: {a.comments}")
        items += collect_file(a.comments)
    if not items:
        sys.exit("No questions found (Reddit empty, blocked or rate limited). Try later or pass --comments.")
    clusters = [c for c in cluster(items) if c["count"] >= a.min_count][: a.top]
    ms = load_moments(ROOT)
    fmt = lambda t: f"{int(t // 60)}:{int(t % 60):02d}"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out = [f"# Questions {today}", "",
           f"{len(items)} questions from {', '.join('r/' + s for s in subs) or 'comments'}"
           f"{' + ' + a.comments if subs and a.comments else ''}, {len(clusters)} clusters, searched {len(ms)} moments "
           f"in {len({m['job'] for m in ms})} transcripts. Ranked by count, then upvotes.", ""]
    found, missing = 0, []
    for n, c in enumerate(clusters, 1):
        out += [f"## {n}. {c['question']}", f"- count: {c['count']}, upvotes: {c['votes']}"]
        out += [f"- example: {l}" for l in c["links"]]
        m = best_moment(c, ms)
        if m:
            found += 1
            out += [f"- moment: {m['title']} ({m['job']}) {fmt(m['s'])}-{fmt(m['e'])}, --start {m['s']:.1f} --end {m['e']:.1f}",
                    f"  > {m['text'][:300]}"]
        else:
            out.append("- no moment in any transcript yet")
            missing.append(c)
        out.append("")
    (ROOT / a.out).write_text("\n".join(out), encoding="utf-8")
    if missing:
        ib = ROOT / a.ideas
        old = ib.read_text(encoding="utf-8") if ib.exists() else "# Idea bank\n"
        add = [f"\n## Questions with no clip yet ({today})"] + [
            f"- [ ] Find a permitted source that answers: \"{c['question']}\" ({c['count']} asks)" for c in missing]
        ib.write_text(old.rstrip("\n") + "\n" + "\n".join(add) + "\n", encoding="utf-8")
    print(f"{len(clusters)} clusters: {found} with a moment, {len(missing)} without -> {ROOT / a.out}"
          + (f", added to {ROOT / a.ideas}" if missing else ""))


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        assert is_question("Why did he quit the show?") and not is_question("great episode")
        cs = cluster([{"text": "Why did Ann quit the show?", "score": 5, "link": "u1"},
                      {"text": "why did ann quit the show??", "score": 1, "link": "u2"},
                      {"text": "Where is the studio located?", "score": 2, "link": "u3"}])
        assert [c["count"] for c in cs] == [2, 1] and cs[0]["votes"] == 6, cs
        W = lambda w, s, b=False: {"w": w, "s": s, "e": s + 0.4, **({"b": True} if b else {})}
        words = [W("Hello", 0, True), W("folks.", 1), W("Ann", 50, True), W("quit", 51), W("because", 52), W("the", 53), W("show", 54)]
        ms = moments(words, "j", "Ep 1")
        assert [(m["s"], m["e"]) for m in ms] == [(0, 1.4), (50, 54.4)], ms
        assert best_moment(cs[0], ms)["s"] == 50
        assert best_moment(cs[1], ms) is None
        ms2 = moments([W("Who", 0, True), W("drives", 1), W("this", 2), W("car?", 3), W("She", 9, True), W("has", 10),
                       W("cataracts.", 11), W("Weird", 60, True), W("show.", 61)], "j", "Ep 2")
        q = lambda t: {"question": t, "tok": tokens(t)}
        assert best_moment(q("who was driving the car??"), ms2)["s"] == 0, "stems: driving ~ drives"
        assert best_moment(q("why does she have cataracts"), ms2)["s"] == 0, "one long specific word is enough"
        assert best_moment(q("is the show weird"), ms2) is not None and best_moment(q("best show"), ms2) is None
        import tempfile
        seen = []

        class Resp:
            def __init__(self, body): self.body = body
            def __enter__(self): return self
            def __exit__(self, *a): pass
            def read(self): return json.dumps(self.body).encode()

        def fake(req, timeout=30):
            seen.append((req.full_url, req.get_header("Authorization")))
            return Resp({"access_token": "tok", "expires_in": 3600} if "access_token" in req.full_url else {"ok": 1})
        urllib.request.urlopen, ROOT = fake, Path(tempfile.mkdtemp())
        for k in ("REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET"):
            os.environ.pop(k, None)
        _last[0] = 0
        assert fetch("https://www.reddit.com/r/x/new.json") == {"ok": 1} and seen[-1] == ("https://www.reddit.com/r/x/new.json", None)
        (ROOT / "reddit.env").write_text('REDDIT_CLIENT_ID=abc\nREDDIT_CLIENT_SECRET="s3"\n')
        _last[0] = 0
        assert fetch("https://www.reddit.com/r/x/new.json") == {"ok": 1}
        assert seen[-2] == ("https://www.reddit.com/api/v1/access_token", "Basic " + base64.b64encode(b"abc:s3").decode())
        assert seen[-1] == ("https://oauth.reddit.com/r/x/new.json", "bearer tok"), seen
        print("self-test ok")
    else:
        main()
