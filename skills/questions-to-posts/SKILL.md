---
name: questions-to-posts
description: Turn questions the audience keeps asking (subreddits for the niche, comments on the page's posts) into clip leads, by finding the moment in already-transcribed sources that answers each one. Use when the user asks what people are asking, wants clip ideas from comments, or says to turn questions into posts.
---

# Questions to posts

A clip that answers a question people keep asking has a ready-made hook and audience.

## 1. Collect

Ask the human to paste comments from the page's recent posts into `comments.txt`, one per line. Pick 1 to 3 subreddits where the niche's audience talks (a show's, a creator's or the topic's). Then:

`.venv/bin/python "${CLAUDE_PLUGIN_ROOT}/scripts/questions.py" --subs <sub1,sub2> --comments comments.txt --days 3`

Either source alone works. Reddit's public JSON often refuses scripts (HTTP 403 or 429). If it does, run with `--comments` only. Don't try to get around the block.

It clusters similar questions, ranks them by how often they're asked, then searches every transcript in `jobs/*/transcript.json` for the moment that answers each one. It writes `questions.md`, and adds questions with no matching moment to `idea-bank.md`.

## 2. Review

For each cluster with a moment:

1. Read the transcript snippet. The match is by shared words, so check it really answers the question. Drop it if not.
2. It needs a source that passed `source-check`. Then `source-check` part 2 (music) on those times.
3. Cut it: `clip-cutter` with an unused `--pick` number (for example 90) and the moment's `--start` / `--end`. Trim to the answer itself.
4. The question often makes the hook ("Why did she quit the show?"). Run it past `hook-writer` rules: true, and the clip must answer it.
5. `rule-check`, then the approval message as usual.

For questions with no moment: search for a permitted source with `trend-radar --channel` on watchlist creators, run `moment-finder` on it, then re-run this. A question nobody has answered on camera stays in the idea bank.

## Rules

- The clip answers the question with the creator's own words. Don't add claims the clip doesn't make.
- Don't quote or name Reddit users or commenters. Their questions are only a signal of what to clip.
- Skip questions about leaks, piracy, private lives of non-public people, or anything on the playbook's skip list.
