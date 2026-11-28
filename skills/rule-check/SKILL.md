---
name: rule-check
description: Check a finished clip and its caption against specs, campaign rules and banned content before posting. Use before every post, after clip-cutter, or when the user asks "is this ok to post".
---

# Rule check

## 1. Gather the rules

Read the campaign's row in `campaigns.md` and its brief under `## Rules to paste`. Note: clip length, required hashtags and mentions, banned words or brands, and anything the script can't check (logo or overlay, CTA, official sound, audience rule, footage source). If the brief is `unknown` or missing, ask the human to paste it. Don't guess.

Write the post caption first, following the playbook's caption rules for the platform, with the credit line "Clip from <show or channel> with <creator>."

## 2. Run

`.venv/bin/python "${CLAUDE_PLUGIN_ROOT}/scripts/check.py" media/edits/<clip>/<clip>.mp4 --min <s> --max <s> --caption "<caption>" --require "#tag @handle" --ban "word|phrase"`

It checks: 1080x1920, about 30 fps, audio present, length, banned terms in hook and caption (piracy and leak words plus `--ban`), required tags and mentions, and a credit in the caption. Without `--min`/`--max` it uses 7-60 seconds. It also saves `<clip>_shots.png`, one frame per shot, and prints when each shot starts.

## 3. Check by hand

The script can't judge these. Check each and list it:

- Permission: `media/raw/<source>/SOURCE.md` exists for this source, and this campaign covers this creator or footage.
- Music: the segment passed `source-check` part 2.
- Inserted footage: view `<clip>_shots.png`. Podcasts and streams often cut in a film or TV scene, a music video, a sports broadcast, news or another creator's clip, and Content ID matches those. Permission for the source covers only the creator's own footage. If a shot isn't theirs, re-cut to leave it out (`--start`/`--end` from the printed shot times) or drop the clip. If the insert is a still image, treat it the same way.
- Campaign items not in the script: logo or overlay, CTA, official sound and its timing, the person the campaign is about is the main focus.
- Ad disclosure: a campaign clip earns money, so it's an ad. The caption has `#ad`, or the human will turn on the platform's paid-promotion label when posting. Say which in the report.
- Caption and hook: true, nothing invented, no "official" wording for fan content, nothing on the playbook's skip list.
- Not a repeat: the same clip isn't already posted to this account (`log.md`, `scoreboard.csv`).

## 4. Report

PASS or FAIL per check in a short list. On a FAIL, fix the cause (re-cut with `clip-cutter`, fix the caption, trim) and re-run. Don't argue with a failed check.

Only after everything passes, show the human the clip, the caption, the credit and the ad disclosure, and wait for "yes". The human posts it. Never upload anything.
