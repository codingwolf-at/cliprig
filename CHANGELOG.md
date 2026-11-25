# Changelog

All notable changes to Cliprig are listed here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- `doctor` skill: checks and repairs a page's setup (Python, packages, yt-dlp age, ffmpeg captions, speech model, page files, cookies, self-tests). `setup` now finishes by running it.
- Skill trigger evals in `evals/`: one case per skill, plus prompts that must not start any Cliprig skill. Run them with `claude plugin eval .`, or from the manual "skill evals" workflow.

### Changed

- `rule-check` now checks that a campaign clip is labelled as an ad (`#ad` in the caption or the platform's paid-promotion label), and the README lists it under "Rules it won't break".
- `moment-finder` downloads only the audio of a link, which is all the ranking needs: a few hundred MB instead of gigabytes for a long VOD. `clip-cutter` and `multilang` then download video for just the clip's range, at up to 4K. `clip-cutter --frame` saves a frame for choosing the layout. Jobs made with the old full-video download still work.

### Fixed

- `moment-finder` no longer offers sponsor reads as candidates. YouTube's "most replayed" often peaks right where viewers skip past an ad, which pushed ad reads to the top.
- `moment-finder` prints a progress line every 5 minutes of audio while it transcribes, instead of staying silent for half an hour on a long source.
- `live-mode` never fired a spike on YouTube: its chat arrives in batches about 10 seconds late, and seconds were judged after 3. It now waits 15 seconds on YouTube (`--chat-delay` to change it). In a 4-minute test on a busy stream, 0 spikes became 5.
- Windows: a page's `CLAUDE.md` now says to use `.venv/Scripts/python.exe` wherever a skill says `.venv/bin/python`, and `doctor` prints fix commands with the interpreter actually running it (and `uv` when the venv has no `pip`).
- The README now says Reddit often refuses `questions-to-posts`' requests, and that pasted comments always work.

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

[Unreleased]: https://github.com/codingwolf-at/cliprig/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/codingwolf-at/cliprig/releases/tag/v0.1.0
