# Contributing to Cliprig

Thanks for helping. Bug reports, niche-specific ideas and pull requests are all welcome. Security problems go through [SECURITY.md](SECURITY.md), not public issues.

## How it's built

- **Skills** live in `skills/<name>/SKILL.md`. Each one is instructions Claude follows: when to use it, which script to run, how to review the result, and what to hand to the human.
- **Scripts** live in `scripts/`. Skills call them with the page's `.venv` Python. `common.py` holds the shared helpers (yt-dlp, ffmpeg, job folders, permission matching, fetching a clip's video range).
- **Page templates** for `setup` live in `skills/setup/templates/`.

## Setting up

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

You'll also need ffmpeg with libass for anything that burns captions (macOS: `brew install ffmpeg-full`).

## Before you open a pull request

1. **Run the self-tests.** CI runs the same ones on macOS, Linux and Windows:

   ```bash
   for s in music_check moments cut check review trends translate questions doctor; do .venv/bin/python scripts/$s.py --self-test; done
   ```

2. **Add a self-test for new logic.** A new branch, loop or parser gets a small assert-based check under `--self-test` in its script.
3. **Run it for real once.** For anything that touches downloads, cutting or captions, run it on a real source with permission to clip it (CC BY works well) and say what you checked in the pull request.
4. **Add a line to `CHANGELOG.md`** under `Unreleased`.

## What we hold the line on

- **Any niche.** Skills stay niche-agnostic. Niche words come from the page's `playbook.md` or options like `--hype`, not from the code.
- **Permission first.** Nothing may cut a source without the permission check, or skip the music check.
- **Nothing is posted for the user.** No uploading, signing in, joining or accepting terms on their behalf.
- **Real numbers only.** No invented views, rates or earnings, in code, docs or examples.
- **Privacy.** A new network call must be added to the "What leaves your machine" table in the README.
- **Small diffs.** One skill or one fix per pull request. Use what's already in `common.py` before adding a helper, and don't add a dependency for a few lines of code.
