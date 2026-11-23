---
name: learning-loop
description: Log posts and learn from real numbers using scoreboard.csv, learning.md and payouts.csv. Use after a post goes out, at 12/24/72 hour reads, for the daily or weekly review, or when the user asks what is working or what they earned.
---

# Learning loop

Files in the page folder: `scoreboard.csv` (one row per post), `learning.md` (Wins, Losses, Current Rules), `payouts.csv` (amounts the campaign shows), `log.md`.

## Rules

1. Real numbers only. Ask the human to paste metrics or a screenshot. A number that isn't available stays blank. Never guess or round up.
2. One test at a time. Change one variable (hook style, length, posting time, caption length, layout) and name it in `test_name`.
3. No verdict before the 24h read. Prefer 72h if the post is still growing.
4. Never project earnings. `est_payout` is only approved views × rate ÷ 1,000, within the campaign's min and max per clip, from numbers the campaign dashboard shows.

## When a post goes out

- Append a row to `scoreboard.csv`: post_id (the post link), date, time (page time zone), platform, pillar, format (layout), hook, length_sec, credit, test_name. Quote fields that contain commas.
- Append to `log.md`: date, platform, link, hook, campaign.
- If it's in a campaign, remind the human to submit the link within 30 minutes, and add a `payouts.csv` row with status `submitted` and blank views.

## Reads at 12h, 24h, 72h

Fill views_12h, views_24h or views_72h, then likes, reposts_or_shares, replies_or_comments, saves_or_bookmarks, followers_at_read. Update `payouts.csv` views and status (`pending`, `approved`, `rejected`, `paid`) from the campaign dashboard.

## Daily review (evening)

`.venv/bin/python "${CLAUDE_PLUGIN_ROOT}/scripts/review.py" --days 1 --read 12h`

Best and worst post, one lesson written as a rule. Append it to `learning.md` under Wins or Losses. Pick tomorrow's one test. If reads are missing, say which instead of filling them in.

## Weekly review

`.venv/bin/python "${CLAUDE_PLUGIN_ROOT}/scripts/review.py" --days 7 --read 24h`

It prints top 3 and bottom 3, and medians by pillar, platform, format, posting hour and test, plus payout totals by status. Compare groups only when each has 3 or more posts; say so when a group is too small to judge.

- Double down on what is above the median. Rework or drop what stayed below it all week.
- Move lessons that held for 2 weeks into `learning.md` Current Rules, and change `playbook.md` to match.
- Pick next week's tests.
- Send the human a short summary: posts, median views, best post with numbers, what changes next week, payouts by status.
