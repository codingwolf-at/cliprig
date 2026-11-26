---
name: setup
description: First-run setup for a Cliprig clip page in any niche (podcasts, stand-up, streams, sports, education, gaming). Use when the user installs the plugin, says "set up", "start", "new page", "new channel", or when ffmpeg, yt-dlp or faster-whisper are missing or the page folder does not exist yet.
---

# Setup

Do the work yourself. Ask the human only what is listed here.

## 1. Ask at most 4 questions, in ONE numbered message

1. Page name and handle (@).
2. Niche and source type, in one lane (for example: stand-up punchlines, podcast founder stories, Twitch gaming funny moments, football highlights, science explainers).
3. Platforms (YouTube Shorts, Instagram Reels, X, TikTok, Facebook). Note: TikTok is banned in some countries, such as India.
4. Time zone.

If the human already gave an answer, don't ask it again. Skip the message if all four are known.

## 2. Show the plan, ask ONE "yes"

List the folder and files below, then wait for a single "yes". Create the folder in the current directory, named after the page.

If another page folder already exists (a second channel), create the new one beside it. Keep pages separate: own accounts, campaigns and logs. Tell the human in one line: Content Rewards allows one account per person, so link the new page's social accounts to the existing Content Rewards account. Never open a second one.

## 3. Install tools (no questions)

Inside the page folder:

- Python venv: `uv venv --python 3.12 .venv` if `uv` exists, else `python3 -m venv .venv` (Windows: `py -3.12 -m venv .venv`, since `python3` there often opens the Microsoft Store) (Python 3.10 to 3.12; faster-whisper has no wheels for newer versions yet). Then install: `uv pip install --python .venv/bin/python -r "${CLAUDE_PLUGIN_ROOT}/requirements.txt"` (or `.venv/bin/python -m pip install -r ...`). On Windows the interpreter is `.venv\Scripts\python.exe`: use it wherever this skill says `.venv/bin/python`.
- ffmpeg with subtitle support (captions need libass). Check with `ffmpeg -hide_banner -filters | grep -w subtitles`.
  - macOS: Homebrew's plain `ffmpeg` has no libass. `brew install ffmpeg-full`. No `PATH` change needed: the scripts find ffmpeg-full on their own.
  - Windows: `winget install --id Gyan.FFmpeg -e --source winget`. Linux: `sudo apt install -y ffmpeg`.
- If an install needs a new terminal for `PATH`, say so in one line and re-check. Never spend money or add a card.
- Speech model: download it now so the first `moment-finder` run doesn't stall on it. About 500 MB, cached once for every page on this machine:
  `.venv/bin/python -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8')"`

## 4. Create the page folder

Copy from `${CLAUDE_PLUGIN_ROOT}/skills/setup/templates/` and fill every `[BRACKETED]` field with the answers:

- `CLAUDE.md` from `CLAUDE.md`
- `playbook.md` from `playbook.md`. Write 2 or 3 pillars that fit the niche, and a skip list for that niche.
- `campaigns.md` from `campaigns.md`
- `.gitignore` from `gitignore`
- `yt-dlp.conf` from `yt-dlp.conf`

Create these as well:

- `log.md`, `idea-bank.md`, `watchlist.md`, `takedowns.md`: a title line each.
- `learning.md` with headings Wins, Losses, Current Rules.
- `scoreboard.csv` with this header line only:
  `post_id,date,time,platform,pillar,format,hook,length_sec,credit,views_12h,views_24h,views_72h,likes,reposts_or_shares,replies_or_comments,saves_or_bookmarks,followers_at_read,test_name,notes`
- `payouts.csv` with header `date,campaign,platform,post_url,views,rate_per_1k,est_payout,status`
- folders `media/raw`, `media/edits`.

Then run `git init` in the folder. Don't commit: the human owns history.

Check everything with the `doctor` skill: `.venv/bin/python "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py"`. Every line must be PASS. Fix any WARN or FAIL as `doctor` says before finishing.

## 5. Finish

Tell the human, in 4 lines:

1. What was installed (`doctor` all PASS), and where the folder is.
2. Next step: `campaign-finder`.
3. New accounts: days 1-2 set up the profile and engage, no posts. First posts from the phone app.
4. They approve every clip and post it themselves. Nothing is uploaded automatically.
