---
name: yt-transcript
description: >-
  Downloads and extracts clean text transcripts from YouTube videos using yt-dlp
  via uvx. Use when the user wants a YouTube video transcript, captions, or
  subtitles as plain text. Handles both manual and auto-generated subtitles with
  language selection.
compatibility: Requires uvx (or uv) and python3 installed. Requires network access.
allowed-tools: Bash(uvx:*) Bash(python3:*) Bash(mktemp:*) Bash(rm:*) Bash(ls:*) Bash(cat:*)
metadata:
  author: tinnet
  version: "1.0"
---

# YouTube Transcript Extraction

Download clean plain-text transcripts from YouTube videos using `uvx yt-dlp`.
No installation needed beyond `uvx` and `python3`.

## Usage

The user provides a YouTube URL as `$ARGUMENTS`. An optional language code can
follow the URL (default: `en`).

Example: `/yt-transcript https://www.youtube.com/watch?v=dQw4w9WgXcQ`
Example: `/yt-transcript https://www.youtube.com/watch?v=dQw4w9WgXcQ de`

### Step 1: Set up

```bash
TMPDIR=$(mktemp -d)
URL="<youtube-url-from-arguments>"
LANG="<language-code-or-en>"
SKILL_DIR="<absolute-path-to-this-skill-directory>"
```

### Step 2: Try json3 format first (best for machine parsing)

Try manual subtitles:

```bash
uvx yt-dlp --skip-download --write-subs --sub-lang "$LANG" --sub-format json3 -o "$TMPDIR/%(id)s.%(ext)s" "$URL" 2>&1
```

Check if a `.json3` file was created:

```bash
ls "$TMPDIR"/*.json3 2>/dev/null
```

If no json3 file, try auto-generated subtitles:

```bash
uvx yt-dlp --skip-download --write-auto-subs --sub-lang "$LANG" --sub-format json3 -o "$TMPDIR/%(id)s.%(ext)s" "$URL" 2>&1
```

### Step 3: If json3 failed, fall back to SRT

If no `.json3` file exists in `$TMPDIR` (e.g. due to yt-dlp's `_UnsafeExtensionError`
bug), fall back to SRT format.

Try manual subtitles:

```bash
uvx yt-dlp --skip-download --write-subs --sub-lang "$LANG" --convert-subs srt -o "$TMPDIR/%(id)s.%(ext)s" "$URL" 2>&1
```

Check for `.srt` file:

```bash
ls "$TMPDIR"/*.srt 2>/dev/null
```

If no SRT file, try auto-generated subtitles:

```bash
uvx yt-dlp --skip-download --write-auto-subs --sub-lang "$LANG" --convert-subs srt -o "$TMPDIR/%(id)s.%(ext)s" "$URL" 2>&1
```

### Step 4: Extract clean text

Find the downloaded subtitle file and run the cleanup script:

```bash
SUBFILE=$(ls "$TMPDIR"/*.json3 "$TMPDIR"/*.srt 2>/dev/null | head -1)
python3 "$SKILL_DIR/scripts/yt_transcript.py" "$SUBFILE"
```

The script auto-detects the format from the file extension and outputs clean
plain text to stdout.

If the user wants the transcript saved to a file, or if the transcript is very
long (e.g. multi-hour video), redirect the output:

```bash
python3 "$SKILL_DIR/scripts/yt_transcript.py" "$SUBFILE" > transcript.txt
```

### Step 5: Clean up

```bash
rm -rf "$TMPDIR"
```

## Listing available languages

If the user is unsure which subtitle languages are available:

```bash
uvx yt-dlp --list-subs "$URL"
```

This shows all available subtitle tracks (both manual and auto-generated).

## Error handling

- **No subtitles found**: The video has no subtitles in the requested language.
  Run `--list-subs` to show what's available, or suggest trying a different
  language code. Note: `--sub-lang` accepts regex patterns like `en.*` to match
  `en`, `en-US`, `en-GB`, etc.
- **`_UnsafeExtensionError`**: Known yt-dlp bug with json3 format. The SRT
  fallback in Step 3 handles this automatically.
- **Video unavailable**: The URL is invalid, the video is private, or
  region-restricted. Inform the user.
- **Network errors**: Check internet connectivity.
- **uvx not found**: The user needs to install uv. Direct them to:
  https://docs.astral.sh/uv/getting-started/installation/

## Notes

- Manual subtitles are higher quality than auto-generated. Always try manual first.
- Auto-generated subtitles often have duplicate overlapping lines. The cleanup
  script handles deduplication.
- For very long videos, the transcript may be large. Consider saving to a file
  and/or summarizing if the user doesn't need the full text.
