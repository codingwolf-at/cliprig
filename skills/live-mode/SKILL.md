---
name: live-mode
description: Record a live YouTube or Twitch stream with its chat and cut raw clips around chat spikes as it runs. Use when the user gives a live URL, says "go live mode", or wants clips from a stream while it is happening.
---

# Live mode

## 1. Before starting

- The stream must be `listed` in `stream-finder` (a joined campaign's creator, or written permission in `watchlist.md` or a `SOURCE.md`). Otherwise stop and say so.
- Skip rebroadcasts of TV, sports or films, and anything on the playbook's skip list.
- Note the streamer's name and handle for the credit.

## 2. Run

`.venv/bin/python "${CLAUDE_PLUGIN_ROOT}/scripts/live.py" <live-url> --minutes 60`

Works with YouTube live URLs and `twitch.tv/<name>`. No accounts or keys. Run it in the background. It records the stream in 60-second segments to `jobs/<id>/live/`, reads chat as it arrives, and on a chat spike cuts a raw clip, `spike_<n>.mp4` (15 seconds before, 20 after), and adds a row to `spikes.md` (time, messages, top chat words).

Tuning, only if needed:

- Too many spikes: raise `--ratio` (default 3) or `--min-msgs` (default 8). Too few in a small chat: lower them.
- Clips start too early or late: change `--lag` (default 8 seconds of stream delay plus reaction time).
- Busy chat but no spikes: raise `--chat-delay`, the seconds to wait for chat to arrive before judging a moment (default 15 on YouTube, whose chat arrives in late batches, and 3 on Twitch).
- `--before` / `--after` set the clip window. `--cooldown` (45) is the minimum gap between spikes.

## 3. While it runs

Every few minutes, read `spikes.md`. Top chat words hint at what happened. For each promising spike:

1. `source-check` part 2 (music) on `spike_<n>.mp4`: streams often play music.
2. `moment-finder jobs/<id>/live/spike_<n>.mp4 --top 1 --min 10 --max 35` to transcribe it and snap it to sentence edges.
3. `hook-writer`, `clip-cutter` on that job, `rule-check`.

Speed matters: send the human ONE message with the best 1 to 3 clips (file path, caption with credit, campaign). They say "yes" and post. Never upload anything.

## 4. When done

List what was recorded, how many spikes, what was clipped and posted. Log posts with `learning-loop`. Delete `seg_*.ts` files once the clips are done: they are large.
