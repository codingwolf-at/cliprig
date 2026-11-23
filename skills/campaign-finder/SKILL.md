---
name: campaign-finder
description: Find live clipping campaigns that pay per 1,000 views for the page's niche (Content Rewards and similar) and record them in campaigns.md. Use when the user asks where to earn, which campaigns are open or fit a new channel, what the pay per 1K views is, or to refresh campaigns.md.
---

# Campaign finder

Read pages live. Rates and budgets change daily; never rely on memory.

## 1. Know the page

Read the page's `CLAUDE.md`, `playbook.md` (niche, pillars, skip list, platforms) and `campaigns.md` (filter line, earlier rows, Skipped). Check `scoreboard.csv` for how many posts the page has: a page with fewer than 10-15 posts counts as new.

## 2. Search

- Content Rewards: the Discover feed on `https://contentrewards.com/` (campaign pages look like `contentrewards.com/c/campaigns/<id>`). Search the niche, its source type and its well-known creators.
- Whop: `https://whop.com/discover/` with the same search terms.
- Clip: `https://www.clip.tech/clippers` lists rate per 1K and budget share without login. Briefs live in their Discord, so ask the human to paste them. Their terms say payouts are Net 30 after a campaign ends and depend on the client paying; say so in one line.

Use the browser tools if a page needs JavaScript. Don't sign in, join, or accept terms for the human.

## 3. Filter

Keep a campaign only if it passes the filter line in `campaigns.md`. Default:

- Pays per view, at least $1 per 1K on a platform the page posts to.
- At least $1,000 budget left.
- No application, or one the human can pass.
- In the page's language, fits a pillar, not UGC (filming yourself or products).
- Not finance or trading advice, crypto, gambling, or anything on the playbook's skip list.
- No public "tier-1 audience only" rule (US/UK/CA/AU) while the page is new.
- Footage the page is allowed to clip. The campaign brief counts as permission for that creator's content only.

Write every dropped campaign under `## Skipped` with the reason in a few words.

## 4. Record

One row per kept campaign in `campaigns.md`: name (org), platform, rate per 1K (min and max per clip), budget left / total, rules, link, checked on. In rules, note: what footage is allowed or supplied, creator count, any "established accounts only" line, audience rule.

A value not visible on the page is `unknown`. Never estimate or invent a number. Audience rules usually sit behind "Join": write `unknown` until the human joins and pastes the brief under `## Rules to paste`.

## 5. Rank and report

Work out views to first payout: min payout ÷ rate × 1,000. Rank for the page's stage:

- New page: fit with a pillar, low views to first payout, supplied or pre-cut footage, few creators, no "established accounts only" rule.
- Established page: rate, budget left and cap per clip.

Report a short ranked list: campaign, rate, views to first payout, budget left, creators, why it fits. Then a "skip for now" list with one reason each. Recommend joining 2 at once to cover more than one platform.

## Content Rewards rules to repeat when relevant

- One Content Rewards account per person (Creator Terms 13.3). Link every page's social accounts to that one account. Never suggest a second account.
- Unapproved clips are capped across campaigns, not per campaign. Pending, rejected and deleted clips all count, so deleting doesn't free a slot. Old clips stop counting after a recent period (about 30 days). The cap depends on approval and earnings history. A page that hits it should submit fewer, stronger clips.
- Only videos posted after joining count. Submit each link within 30 minutes of posting.

These come from the Creator Terms at `https://contentrewards.com/terms`. If the human asks for details or the terms look changed, read the page again.

No earnings promises: pay depends on approved views and each campaign's own rules.
