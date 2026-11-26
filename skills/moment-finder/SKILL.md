---
name: moment-finder
description: Find the best clip moments in a long video, podcast, stream VOD or local file. Use when the user gives a video link or file and wants highlights, "find the moments", "what should I clip from this", or candidates to cut.
---

# Moment finder

## 1. Permission first

Run `source-check` part 1 (permission) on the source. Don't download or transcribe a source that hasn't passed.

## 2. Run

Read the page's `playbook.md` (pillars, skip list) and the campaign's rules in `campaigns.md` (clip length, banned content). Then:

`.venv/bin/python "${CLAUDE_PLUGIN_ROOT}/scripts/moments.py" <url-or-file> --top 8`

For a link it downloads the audio only, which is all the ranking needs: a few hundred MB instead of gigabytes for a 4-hour VOD (transcribing it still takes a while). `clip-cutter` later fetches video for just the picked range. It writes `jobs/<id>/candidates.md`. Signals: loudness spikes (laughter, applause, shouting), hook phrases in the transcript (faster-whisper, word timestamps), the YouTube "most replayed" heatmap, and live-chat spikes, when available. A missing signal is skipped, not faked. Windows start and end on sentence edges where the transcript allows.

Options:

- `--min` / `--max`: clip length in seconds (default 15-40). Match the campaign's length rules.
- `--hype "phrase|phrase"`: extra phrases for the niche, added to the built-in reaction and hook phrases. For example sports `"buzzer beater|walk-off|hat trick"`, a founder podcast `"I almost quit|first million"`. Stand-up needs none: laughs show up as loudness.
- `--max-minutes`: only the first 90 minutes are used by default. Raise it for long podcasts.
- `--chat chat.json`: a Twitch VOD chat exported with TwitchDownloader. YouTube chat replay is fetched on its own.
- `--fast`: for multi-hour streams with chat replay or "most replayed" data. It ranks by those first and transcribes only the top 30%, about 3x faster. It can miss moments that are funny or sharp but not loud, so don't use it for podcasts: on an 86-minute podcast it kept only 4 of the 8 picks a full run found. `clip-cutter` transcribes any part it skipped when a clip needs it.

Transcription uses an NVIDIA GPU, or the Apple GPU on a Mac (an experimental backend, with the CPU as fallback). Non-English audio is translated to English as it's transcribed: the hook and sponsor phrases are English, and it's much faster. On an M3, 10 minutes of Hindi took about half a minute; transcribing Hindi as Hindi on the CPU ran at about real time. So `candidates.md` is in English for a non-English source, and `clip-cutter` captions the clip in the spoken language. For anything over 15 minutes, run it in the background. It prints a progress line every 5 minutes of audio with the time taken and the time left, so don't pipe it through `tail`. Give the user the time left from that line, not a guess. Sponsor reads ("use code", "sponsored by") never become candidates. Results are cached in `jobs/<id>/`, so a re-run with new options is fast.

## 3. Review

Read `jobs/<id>/candidates.md` and show each candidate: number, start-end, length, why it scored, transcript line.

Drop any that:

- hit the playbook's skip list or the campaign's banned content,
- need earlier context to make sense, or start or end mid-thought (adjust the times instead if a few seconds fix it),
- are mostly silence, an ad read, or an intro or outro.

Recommend the best 3 and say what hook angle each suggests.

## 4. Next

For each pick, run `source-check` part 2 (music) on its exact times. Then cut it with `clip-cutter`. Credit the creator or show in the post caption.
