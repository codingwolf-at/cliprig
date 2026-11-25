## What and why

<!-- What this changes, and the problem it solves. Link the issue if there is one. -->

## How you tested it

<!-- Self-tests, plus a real run if it touches downloads, cutting or captions: what source (with permission to clip it) and what you checked. -->

## Checklist

- [ ] Self-tests pass: `for s in music_check moments cut check review trends translate questions doctor; do .venv/bin/python scripts/$s.py --self-test; done`
- [ ] New logic has a self-test
- [ ] `CHANGELOG.md` has a line under `Unreleased`
- [ ] New network calls are added to "What leaves your machine" in the README (or there are none)
- [ ] Skills stay niche-agnostic, and nothing posts, signs in or joins anything for the user
