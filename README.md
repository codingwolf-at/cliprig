# Cliprig

A Claude Code plugin that runs a short-form clip page in any niche: podcasts, stand-up, streams, sports, education, gaming. It finds paid clipping campaigns, finds the best moments in long videos, cuts captioned 1080x1920 clips, checks permission and campaign rules, and learns from real numbers.

You approve every clip and post it yourself. Nothing is uploaded automatically.

## Install

```
/plugin marketplace add <owner>/cliprig
/plugin install cliprig@cliprig
```

Then say "set up my clip page". Setup asks 4 questions (page name, niche, platforms, time zone), installs the tools and creates the page folder.

## Rules built in

- **Permission first.** Clip only joined campaigns, campaign-supplied footage, or creators who allow clipping in writing, with the proof saved. No audible music.
- **One Content Rewards account per person.** Run several pages from one account by linking each page's social accounts.
- **Real numbers only.** No invented rates, budgets, views or earnings.

## Skills

| skill | what it does |
|---|---|
| `setup` | Installs ffmpeg, yt-dlp and faster-whisper, asks 4 questions, builds the page folder |
| `campaign-finder` | Live campaigns for the page's niche: rate per 1K, views to first payout, budget left, rules, link. Ranked for a new or established page |
| `source-check` | Before any cut: is there permission to clip this source (with proof saved), and is the segment free of music (loud gaps, hidden lyrics) |
| `moment-finder` | Ranks clip candidates in a long video, podcast or VOD from laughs and loudness, hook phrases, "most replayed" and chat spikes, cut on sentence edges |
| `clip-cutter` | Cuts a pick into a 1080x1920 clip: fill, blur or facecam layout, word-by-word captions with swears masked, hook box, -14 LUFS audio |
| `hook-writer` | 3 on-screen hook options per clip in different patterns, checked against the clip, past hooks and what won on the page |
| `rule-check` | Before posting: specs, length, required tags, banned terms and credit, plus a hand check of permission, music and campaign-only rules |
| `learning-loop` | Logs each post, fills 12/24/72h reads, daily and weekly reviews with medians by pillar, platform, format, hour and test. Real numbers only |
| `trend-radar` | Recent long-form videos in the niche, or from permitted creators, ranked by views per hour, with a permission column |
| `stream-finder` | Live streams on YouTube and Twitch ranked by viewers, plus whether permitted creators are live now. No keys needed |
| `playbook` | Runs the day: 7-day kickoff, then find, check, cut and gate clips, one approval message, logging, engagement and the evening report |

More skills are on the way.

## Requirements

macOS, Linux or Windows. Python 3.10-3.12. ffmpeg with libass (on macOS: `brew install ffmpeg-full`).

MIT license. No income is promised.
