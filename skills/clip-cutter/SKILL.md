---
name: clip-cutter
description: Cut a picked moment into a finished 1080x1920 vertical clip with word-by-word captions and a hook box. Use after moment-finder, or when the user says "cut it", "make the clip", "make it vertical".
---

# Clip cutter

## 1. Before cutting

- The source passed `source-check` permission, and this segment passed its music check.
- Hook: get 3 options from `hook-writer` and use the best. Without it, write 3 short ones (under 8 words, no clickbait the clip doesn't pay off) and pick one.
- Look at the source: `ffmpeg -v error -ss <peak> -i <source> -frames:v 1 jobs/<id>/frame.png`, then view the frame to choose the layout.

## 2. Pick a layout

- `fill`: crop the frame to fill 9:16. Best for one speaker or action in one spot. Set `--focus` (0 = left edge, 0.5 = centre, 1 = right edge) so the face or action stays in frame.
- `blur`: the whole frame centred over a blurred copy. Use for two people side by side, wide shots, slides or screens where cropping would cut something off.
- `facecam`: a camera box on top, the rest of the frame below. Use for streams or videos with a picture-in-picture cam. Measure the box on the frame as `--cam x:y:w:h` in fractions of the frame (for example `0.72:0.04:0.26:0.28`). `--focus` moves the lower crop.

## 3. Run

`.venv/bin/python "${CLAUDE_PLUGIN_ROOT}/scripts/cut.py" jobs/<id> --pick <n> --layout fill|blur|facecam --hook "TEXT"`

- `--start` / `--end` (seconds in the source) trim the candidate. Most clips work at 7-30 seconds and within the campaign's length rules. End on the payoff.
- Captions mask swears and always mask slurs. `--allow-profanity` only if the campaign and platform allow it. `--captions none` if the source already has burned-in captions.

It writes `media/edits/<job>_clip<n>.mp4` and a `.json` with times, layout, hook and source. Re-running with the same pick overwrites it.

## 4. Check, then hand over

1. View a frame at 1 second and one mid-clip (`ffmpeg -v error -ss 1 -i <clip> -frames:v 1 check.png`): the hook shows, captions are readable and don't cover faces or on-screen text, nothing important is cropped. Fix the layout or `--focus` and re-cut if not.
2. Run `rule-check` on it. Fix and re-cut until it passes.
3. No credit text is burned into the video. Write the post caption with the creator or show credited.
4. Show the human the file and the caption text and ask for "yes". Never upload anything.
