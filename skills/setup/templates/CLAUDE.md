# [PAGE NAME] — [NICHE] clip page

- Niche: [NICHE AND SOURCE TYPE]. Platforms: [PLATFORMS]. Time zone: [TIME ZONE].
- Earn through clipping campaigns that pay per 1,000 approved views (mainly Content Rewards). Rules per campaign live in `campaigns.md`. Page rules live in `playbook.md`.
- Run Cliprig scripts with `.venv/bin/python`, not system `python`.
- Update yt-dlp weekly: `uv pip install --python .venv/bin/python -U "yt-dlp[default]"`
- Captions need ffmpeg with libass. On macOS: `export PATH=/opt/homebrew/opt/ffmpeg-full/bin:$PATH` before cutting.
- If YouTube asks downloads to "confirm you're not a bot": the human exports their YouTube cookies to `cookies.txt` here, then uncomment `--cookies cookies.txt` in `yt-dlp.conf`. It works like a password: never commit it, never print it. While the line is on, yt-dlp rewrites the file on every run, so comment it out again and delete `cookies.txt` once downloads work.
- Copyright: never offer a clip that could draw a claim or strike. Only clip sources with permission: joined campaigns, campaign-supplied footage, or creators who allow clipping in writing (link the proof in `media/raw/<source>/SOURCE.md`). No segment with audible music; check gaps between speech and run an unfiltered transcription for lyrics. Official-sound campaigns are fine. If permission can't be confirmed, say so and don't cut it.
- Credit the creator or show in every caption. No AI voiceover unless a campaign allows it.
- A person approves every clip and posts it. Never upload anything.
