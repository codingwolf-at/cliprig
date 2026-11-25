---
name: multilang
description: Turn one finished clip into other languages with translated word-by-word captions and hook, same layout as the original. Use when the user says "translate the clip", "make it in Spanish", "other languages", "localize".
---

# Multilang

One clip can reach audiences in other languages. The spoken audio stays original; captions and hook are translated.

## 1. Export the lines

The clip must already exist in `media/edits/` from `clip-cutter`.

`.venv/bin/python "${CLAUDE_PLUGIN_ROOT}/scripts/translate.py" media/edits/<clip>.mp4 --export`

It writes `<clip>_lines.json`: the hook and each spoken sentence.

## 2. Translate

For each language, write `<clip>_<lang>.json` next to the clip, same shape: `{"hook": "...", "lines": [...]}`, one translated line per original line, same count and order.

- Translate meaning, in natural spoken words for that language. Keep names, numbers and facts exactly. Add nothing that isn't in the original.
- Keep each line about as long as the original: it has to fit the same seconds.
- The hook follows `hook-writer` rules in the new language: short, sentence case, true.
- Swear masking in captions only works for English. Leave slurs out, and mask swears yourself (first letter plus asterisks) unless the campaign allows them.
- For a language you can't check well, say so and ask the human to have a native speaker read it.

## 3. Render

`.venv/bin/python "${CLAUDE_PLUGIN_ROOT}/scripts/translate.py" media/edits/<clip>.mp4 --lang es [--lang pt ...]`

It writes `<clip>_<lang>.mp4` and `.json` with the original's layout, crop, hook box and loudness. View a frame at 1 second and one mid-clip: hook and captions show, accents and special characters render.

## 4. Before posting

- Run `rule-check` on each language version, with a caption in that language (credit line included).
- Check the campaign allows non-English posts and counts their views. Many pay only for certain audiences.
- Post each language to a page or account for that language, or as a translated upload where the platform supports it. Don't post 5 versions of one clip to the same page.
- No AI voiceover unless the campaign allows it.
- Show the files and captions to the human and wait for "yes". Never upload anything.
