# Changelog

All notable changes to Cliprig are listed here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- `clip-cutter --mask "word|word"`: masks more caption words in any language. For a non-English clip, it prints the captions so Claude can find swears and slurs the English lists miss and re-cut with `--mask`.

### Changed

- `clip-cutter`'s `fill` crop follows whoever is talking in a wide shot where two people don't both fit, instead of the larger face. It scores how well each mouth's movement follows the audio's loudness, so a listener who laughs or nods isn't mistaken for the talker. It picks one person per shot.

### Fixed

- Sentence edges and caption groups no longer treat "Mr.", "Dr.", "e.g." or an initial like "R." as the end of a sentence, so clips don't start or stop mid-name. "No." and "I." still end sentences.

## [0.3.0] - 2026-11-26

Clips that look and check better: a crop that follows faces, three caption styles, a check for footage the creator doesn't own, faster non-English transcription, and `--fast` for long streams.

### Added

- `moment-finder --fast`: for multi-hour streams with chat replay or "most replayed" data. It ranks by those first and transcribes only the top 30%, about 3x faster. It stays opt-in because it misses moments that aren't loud: on an 86-minute podcast it kept 4 of the 8 picks a full run found. `clip-cutter` transcribes any skipped range a clip needs.
- `clip-cutter`'s `fill` crop follows faces shot by shot (`--focus auto`, the new default): it finds the camera cuts, then centres each shot on the speaker, or between two people when both fit. It uses OpenCV's YuNet face model (230 KB, downloaded once). `--focus 0.5` still sets a fixed crop. Existing pages need `opencv-python-headless`: the `doctor` skill flags it.
- Caption styles: `clip-cutter --style bold|clean|box`. `bold` is the old look and stays the default; `clean` is white sentence case with the spoken word brightest; `box` is black caps on a white box. New pages name their style in `playbook.md`, which `clip-cutter` uses unless `--style` is given, and `multilang` reuses the clip's style.
- `rule-check` looks for footage the creator doesn't own. `check.py` saves one frame per shot as `<clip>_shots.png` and prints when each shot starts, and Claude checks it for film, TV, music video or other creators' footage before a clip is offered. In the first end-to-end run, a podcast's cut-in film scene had passed every other check.

### Changed

- `moment-finder` translates non-English audio to English while transcribing: about 30x faster for Hindi on an Apple GPU and 5x on the CPU, and the English hook and sponsor phrases now match. Transcription uses the Apple GPU on Macs, falling back to the CPU.
- `clip-cutter` captions non-English clips in the spoken language, transcribing just the clip's range with Whisper `medium`.

### Fixed

- `moment-finder` transcription progress now shows the time taken and the time left, measured as it runs. The skill no longer promises a quarter of the audio's length, which was far off for some sources.

## [0.2.0] - 2026-11-26

A new `doctor` skill, much smaller downloads, and fixes from the first end-to-end run driven by Claude.

### Added

- `doctor` skill: checks and repairs a page's setup (Python, packages, yt-dlp age, ffmpeg captions, speech model, page files, cookies, self-tests). `setup` now finishes by running it.
- Skill trigger evals in `evals/`: one case per skill, plus prompts that must not start any Cliprig skill. Run them with `claude plugin eval .`, or from the manual "skill evals" workflow.

### Changed

- `rule-check` now checks that a campaign clip is labelled as an ad (`#ad` in the caption or the platform's paid-promotion label), and the README lists it under "Rules it won't break".
- `moment-finder` downloads only the audio of a link, which is all the ranking needs: a few hundred MB instead of gigabytes for a long VOD. `clip-cutter` and `multilang` then download video for just the clip's range, at up to 4K. `clip-cutter --frame` saves a frame for choosing the layout. Jobs made with the old full-video download still work.

### Fixed

- `moment-finder` no longer offers sponsor reads as candidates. YouTube's "most replayed" often peaks right where viewers skip past an ad, which pushed ad reads to the top.
- `moment-finder` prints a progress line every 5 minutes of audio while it transcribes, instead of staying silent for half an hour on a long source.
- New pages' `CLAUDE.md` says yt-dlp is at `.venv/bin/yt-dlp`, so Claude stops calling a `yt-dlp` that isn't on `PATH`.
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

[Unreleased]: https://github.com/codingwolf-at/cliprig/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/codingwolf-at/cliprig/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/codingwolf-at/cliprig/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/codingwolf-at/cliprig/releases/tag/v0.1.0
