---
name: playbook
description: Run the clip page's day, from the 7-day kickoff to the normal daily routine, using the other Cliprig skills. Use when the user says "daily routine", "what do I do today", "run the page", "start the day", or asks about the kickoff week, posting slots or the page's rules.
---

# Playbook

## 1. Where is the page

- No page folder (`CLAUDE.md`, `playbook.md`, `scoreboard.csv`)? Run `setup` first.
- Read the page's `playbook.md`: it is the page's own rules (pillars, skip list, posting mix, captions). It wins over anything here.
- Count posts in `scoreboard.csv` and days in `log.md`. Under 7 days since setup: kickoff (section 2). Otherwise: normal day (section 3).

## 2. Kickoff week

- **Day 1:** Profiles on every platform: name, handle, bio, avatar. Instagram set to Professional. `campaign-finder`, then the human joins 2 campaigns and pastes the briefs.
- **Day 2:** Build `watchlist.md`: each campaign's creators with their channel links, plus 5 small creators in the niche to ask for written permission (draft the message; the human sends it). The human follows and engages in the niche. No posts yet.
- **Day 3:** `trend-radar --channel` on the watchlist. Cut the first 3 clips (section 3, Make). First post from the phone app.
- **Day 4:** Start the daily mix. Log every post. Start the engagement routine.
- **Day 5:** First 24h reads. Start the first one-variable test.
- **Day 6:** Keep posting. Re-run `campaign-finder`: budgets run out fast.
- **Day 7:** First weekly review with `learning-loop`.

## 3. Normal day

**Start:** Read `takedowns.md` and handle anything new first. Re-run `campaign-finder` if `campaigns.md` was checked more than 2 days ago. `trend-radar` on watchlist and campaign creators.

**Make** (as many clips as the playbook's daily mix, quality over count):

1. Pick sources: campaign footage first, then `listed` creators from `trend-radar`.
2. `source-check` (permission), `moment-finder`, `source-check` (music) on each pick.
3. `hook-writer`, `clip-cutter`, `rule-check`.

**Approve:** ONE message to the human with every post: file path, platform, hook, exact caption with credit, campaign, suggested time. They reply "yes" and post or schedule it themselves. Never upload anything.

**After posting:** `learning-loop` logs it. Remind the human to submit campaign posts within 30 minutes.

**Engage** (2-3 times a day, about 15 minutes, done by the human): reply to comments in the first hour, thank credited creators, save good questions to `idea-bank.md`. Draft replies on request. Never argue, never DM for follows.

**Evening:** 12h, 24h and 72h reads, then the `learning-loop` daily review.

## 4. Report

End the day with 4 lines: what posted (with links), top post with real numbers, today's lesson, tomorrow's test.

Flag at once, not in the report: a takedown or claim (log it in `takedowns.md`, stop using that source), a post that might be wrong, a rejected campaign submission.

Hard rules: permission for every source, no audible music, credit every creator, no invented facts or numbers, no earnings promises. Anything outside the daily mix needs the human's yes first.
