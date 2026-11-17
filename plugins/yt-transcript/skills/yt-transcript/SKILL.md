---
name: yt-transcript
description: >-
  Downloads and extracts clean text transcripts from YouTube videos using yt-dlp
  via uvx. Use when the user wants a YouTube video transcript, captions, or
  subtitles as plain text. Handles both manual and auto-generated subtitles with
  language selection.
compatibility: Requires uvx (or uv) and python3 installed. Requires network access.
allowed-tools: Bash(uvx:*)
metadata:
  author: tinnet
---

# YouTube Transcript Extraction

Download clean plain-text transcripts from YouTube videos with `uvx yt-dlp`.
No installation needed beyond `uv` and `python3`.

## Usage

The user provides a YouTube URL as `$ARGUMENTS`. An optional language code can
follow the URL (default: `en`).

Example: `/yt-transcript https://www.youtube.com/watch?v=dQw4w9WgXcQ`
Example: `/yt-transcript https://www.youtube.com/watch?v=dQw4w9WgXcQ de`

Run the bundled script **in a single Bash call**, with the absolute path of this
skill's base directory (shown when the skill loads) in place of `<skill-dir>`:

```bash
sh "<skill-dir>/scripts/fetch.sh" "<youtube-url>" "<language-code>"
```

It tries manual subtitles before auto-generated ones and json3 before SRT, works
in its own temp directory that it removes when done, and prints the clean
transcript to stdout (yt-dlp's progress goes to stderr). Don't reimplement these
steps as separate Bash calls: shell variables don't survive between calls.

If the user wants the transcript in a file, or the video is very long (e.g. a
multi-hour talk), redirect stdout:

```bash
sh "<skill-dir>/scripts/fetch.sh" "<youtube-url>" en > transcript.txt
```

## Listing available languages

If the user is unsure which subtitle languages are available:

```bash
uvx yt-dlp --list-subs "<youtube-url>"
```

This shows all available subtitle tracks (both manual and auto-generated).

## Error handling

- **No subtitles found** (the script exits 1 and says so): list the available
  languages, or suggest another language code. The language accepts regexes,
  e.g. `en.*` matches `en`, `en-US` and `en-GB`.
- **Video unavailable**: the URL is invalid, or the video is private or
  region-restricted. Tell the user.
- **Network errors**: check connectivity.
- **uvx not found**: the user needs to install uv:
  https://docs.astral.sh/uv/getting-started/installation/

## Notes

- Manual subtitles are better than auto-generated ones; the script tries them first.
- Auto-generated subtitles repeat overlapping lines; the cleanup drops repeats.
- For very long videos, save to a file and/or summarize if the user doesn't
  need the full text.
