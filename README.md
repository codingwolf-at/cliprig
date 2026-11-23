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

More skills are on the way.

## Requirements

macOS, Linux or Windows. Python 3.10-3.12. ffmpeg with libass (on macOS: `brew install ffmpeg-full`).

MIT license. No income is promised.
