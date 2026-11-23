---
name: trend-radar
description: Rank recent long-form YouTube videos in the page's niche, or from creators the page may clip, by views per hour. Use when the user asks what is hot, what to clip today, or wants fresh source videos.
---

# Trend radar

## 1. Run

Read `playbook.md` (niche, pillars), `campaigns.md` and `watchlist.md` first. Then either:

- Creators the page may clip (best first step): `.venv/bin/python "${CLAUDE_PLUGIN_ROOT}/scripts/trends.py" --channel <channel url> [--channel ...] --hours 168`
- The niche at large: `.venv/bin/python "${CLAUDE_PLUGIN_ROOT}/scripts/trends.py" --query "<niche words>" --hours 24 --limit 30`

Use the niche's own words for `--query` (a show name, a creator, "stand-up special", "champions league highlights"). Widen `--hours` for slow niches. Shorts are skipped: they are too short to clip from. It writes `trends.md` and takes a few minutes, since it reads every video's page.

## 2. Report

1. Show the top 10 as a short table: title, channel, views, views per hour, age, length, permission, link.
2. Pick 3 that fit a pillar. Only videos marked `listed` (the channel is named in `campaigns.md`, `watchlist.md` or a `SOURCE.md`) can go straight to `source-check`. For anything else, say it needs permission first and stop there for that video.
3. Drop anything that looks pirated, leaked, reuploaded from another creator, or on the playbook's skip list, and say why in one line.
4. Next step for each pick: `source-check`, then `moment-finder <url>`. A "most replayed: yes" video gives moment-finder an extra signal.

Numbers are what YouTube showed at that moment. If the script errors, show the last error line and fix the cause (yt-dlp outdated, bot check needs `cookies.txt`, network). Don't invent a list.

Creators who said yes to clipping go in `watchlist.md` with their channel link, so the next run marks them `listed`.
