# Changelog

All notable changes to Cliprig are listed here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-11-26

First public release: 14 skills that run a short-form clip page in any niche, from finding paid campaigns to the weekly review.

### Skills

- **Find:** `campaign-finder`, `trend-radar`, `stream-finder`, `questions-to-posts`
- **Make:** `moment-finder`, `hook-writer`, `clip-cutter`, `multilang`, `live-mode`
- **Check:** `source-check`, `rule-check`
- **Run:** `setup`, `playbook`, `learning-loop`

### Highlights

- Permission first: no source is cut without saved proof (joined campaign, supplied footage, written OK or CC BY), and every segment gets a music check.
- Moments ranked from loudness, hook phrases, YouTube's "most replayed" graph and live-chat spikes, cut on sentence edges.
- Finished 1080×1920 clips: fill, blur or facecam layout, word-by-word captions, hook box, -14 LUFS audio.
- Real numbers only: posts logged with 12/24/72-hour reads and weekly medians by pillar, platform, format, hour and test.
- No API keys and no uploads: everything runs on your machine, and you post every clip yourself.

### Known limitations

- Fully tested on macOS with Apple Silicon. CI runs the script self-tests on Linux and Windows, but the skills call `.venv/bin/python`, which is `.venv\Scripts\python.exe` on Windows.
- Reddit often refuses scripted requests. `questions-to-posts` then works from pasted comments only.
- `live-mode` spike detection is verified on Twitch. On YouTube, recording and chat capture work, but no spike has fired in testing yet.
- Caption swear masking is English only. Translated captions are masked by hand.
- Sentence edges treat abbreviations like "Mr." as the end of a sentence.

[0.1.0]: https://github.com/codingwolf-at/cliprig/releases/tag/v0.1.0
