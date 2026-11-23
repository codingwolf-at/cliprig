---
name: stream-finder
description: Find live streams in the page's niche on YouTube and Twitch, ranked by concurrent viewers, and check whether permitted creators are live now. Use when the user asks who is streaming now, wants live moments to clip, or before live-mode.
---

# Stream finder

## 1. Run

Read `watchlist.md` and `campaigns.md` first. Then any mix of:

`.venv/bin/python "${CLAUDE_PLUGIN_ROOT}/scripts/streams.py" --channel <url> [--channel ...] --query "<niche words>" --twitch-category "<Twitch category>"`

- `--channel`: a YouTube channel or `twitch.tv/<name>` URL. Says whether that creator is live right now. Pass every watchlist and campaign creator: these are the streams the page may clip.
- `--query`: YouTube live search in the niche's own words.
- `--twitch-category`: a Twitch category, for example "Just Chatting", "Chess", "Sports" or a game name.

It writes `streams.md`. No accounts or keys are needed.

## 2. Report

1. Show the live watched channels first, then the top 10 of the rest: platform, channel, title, viewers, live for, permission, link.
2. Only `listed` streams (named in `campaigns.md`, `watchlist.md` or a `SOURCE.md`) may be clipped. For the rest, say permission is needed and suggest asking the creator in writing. Good unlisted creators can go to `watchlist.md` as "to ask".
3. Skip streams that look pirated (rebroadcast TV, sports or films) or are on the playbook's skip list. Say why in one line.
4. Next step for a listed stream: `live-mode <url>` to clip chat spikes as it runs, or `moment-finder` on the VOD once it ends.

Viewer counts are what the platform returned at that moment. Don't guess or round them up.
