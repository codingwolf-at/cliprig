# Security

## Reporting a problem

Please don't open a public issue for a security problem. Report it privately on GitHub instead: the repo's **Security** tab, then **Report a vulnerability**.

Useful to include: what you ran, what happened, and the Cliprig version (`.claude-plugin/plugin.json`).

## Supported versions

Fixes go into the latest release. Update the plugin from Claude Code's `/plugin` menu.

## What counts

- A script running a command or writing a file it shouldn't, for example from a crafted video title, URL, transcript or file name.
- Anything that sends data somewhere not listed in [What leaves your machine](README.md#what-leaves-your-machine).
- Anything that exposes `cookies.txt` or other credentials.
- A skill that tells Claude to sign in, join, pay, upload or accept terms on your behalf.

Problems in yt-dlp, ffmpeg, faster-whisper or Claude Code itself belong with those projects.

## Keeping your page safe

- **`cookies.txt` works like a password.** It's only needed when YouTube asks downloads to "confirm you're not a bot". Turn it on in `yt-dlp.conf` only then, never commit it, never paste it into a chat or issue, and delete it once downloads work. The page's `.gitignore` already excludes it.
- **Keep yt-dlp updated.** Sites change often, and old versions break: `uv pip install --python .venv/bin/python -U "yt-dlp[default]"`.
- **Review before you post.** Cliprig never uploads. Read each clip, caption and credit before you approve it.
