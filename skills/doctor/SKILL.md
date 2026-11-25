---
name: doctor
description: Check and repair a clip page's setup (Python, packages, yt-dlp version, ffmpeg captions, speech model, page files, cookies, self-tests). Use when the user says "check my setup", "something's broken", "doctor", when a download or cut fails with a tool error, or about once a month.
---

# Doctor

## 1. Run

In the page folder:

`.venv/bin/python "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py"`

On Windows the interpreter is `.venv/Scripts/python.exe`. If `.venv` itself is missing or broken, re-run the install part of `setup`.

Each line is PASS, WARN or FAIL with the fix in brackets.

## 2. Fix

Do these without asking:

- **yt-dlp old (WARN):** run the update command it prints. Sites change often, and an old yt-dlp is the most common cause of failed downloads.
- **Speech model missing (WARN):** run the download command it prints.
- **Packages missing (FAIL):** reinstall `requirements.txt` into `.venv`, as in `setup`.
- **ffmpeg without captions (FAIL):** install ffmpeg with libass, as in `setup` (macOS: `brew install ffmpeg-full`).
- **cookies.txt not gitignored (FAIL):** add `cookies.txt` to `.gitignore`.

Ask the human first:

- **cookies.txt on disk, or yt-dlp.conf using cookies (WARN):** it's their login. Say so, and offer to comment out the line and delete the file once downloads work. Never print or read out its contents.
- **Python outside 3.10–3.12 (FAIL):** rebuilding `.venv` takes a few minutes. Offer it.
- **Self-test failing (FAIL):** show the failing script's output (`... <script>.py --self-test`). It's likely a bug in Cliprig: suggest reporting it on GitHub with that output.

## 3. Report

Run `doctor.py` again after fixing, and show the final list. Say in one line what was fixed and what still needs the human.
