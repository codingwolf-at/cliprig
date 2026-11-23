---
name: source-check
description: Check that a source video may be clipped and that a segment has no music, before downloading or cutting. Use before every cut, when the user shares a video to clip, asks "can I clip this", "is this safe", or worries about copyright claims or strikes.
---

# Source check

A clip that draws a claim or strike costs more than it earns. Run this before `moment-finder` on a new source, and again on each picked segment before `clip-cutter`.

## 1. Permission (per source)

The source passes only with one of these, in this order:

1. **Joined campaign**: the campaign is in `campaigns.md` and its brief allows this creator, show or footage. A brief covers only the content it names.
2. **Campaign-supplied footage**: from the campaign's own Drive or download link.
3. **Written permission**: the creator allows clipping in writing (a bio, video description, post, DM or email reply). Get the link or a screenshot.
4. **Creative Commons "CC BY"**: shown on the video page itself. CC BY-ND, BY-NC and "Standard license" don't count.

Also check `takedowns.md`: never reuse a source or creator that sent a claim or takedown.

"Fair use", "transformative edit", "everyone clips them" and "it's on YouTube" are not permission. If permission can't be confirmed, say so plainly and stop. Suggest asking the creator in writing.

On a pass, write `media/raw/<source>/SOURCE.md`:

```
link:
creator / show:
on camera:
permission: <campaign name | supplied footage | written | CC BY>
proof: <link to brief, message or license>
checked on: <date>
```

## 2. Music (per segment)

Run on the picked segment, with a few seconds of margin:

`.venv/bin/python "${CLAUDE_PLUGIN_ROOT}/scripts/music_check.py" <video-or-audio> --start <sec> --end <sec>`

- `LOUD GAP`: sound between speech, often background music, a song, game radio or stream music.
- `HIDDEN WORDS`: words only an unfiltered transcription heard, often sung lyrics.
- Exit 0 = nothing flagged.

On a flag, listen to that span (cut a short audio preview with ffmpeg and send it to the human). Then trim the segment around it, pick another, or drop it. Laughter, applause and room noise are fine; music is not, even quietly under speech. For a noisy room, raise `--floor` (for example `-45`) and re-run, but still listen to anything flagged.

Exception: a campaign that supplies or names an official sound may use it. Note that in `SOURCE.md`.

## 3. Report

Two lines, PASS or STOP each, with the reason: Permission, Music. Only after both pass, go on to `clip-cutter`.
