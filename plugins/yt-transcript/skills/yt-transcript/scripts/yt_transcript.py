#!/usr/bin/env python3
"""Convert YouTube subtitle files (json3 or SRT) to clean plain text.

Supports two formats:
- json3: YouTube's native JSON subtitle format
- SRT: SubRip text format (used as fallback)

Strips formatting, timestamps and sequence numbers, and drops consecutive identical lines,
which are common in auto-generated subtitles.

Usage: python3 yt_transcript.py INPUT_FILE [INPUT_FILE ...]

The first file that exists and yields text is printed to stdout; the format is taken from the
extension. Missing files are skipped, so unmatched shell globs are harmless.
"""

import json
import re
import sys

TIMESTAMP = re.compile(r"\d{2}:\d{2}:\d{2}[,.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,.]\d{3}")
TAG = re.compile(r"<[^>]+>")  # <font>, <i>, and inline <00:00:01.000> timestamps


def dedupe(lines: list[str]) -> str:
    """Join lines, dropping each one that repeats the line before it."""
    out: list[str] = []
    for line in lines:
        if not out or line != out[-1]:
            out.append(line)
    return "\n".join(out)


def clean_json3(filepath: str) -> str:
    """Extract clean text from a YouTube json3 subtitle file."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        data = json.load(f)

    lines = []
    for event in data.get("events", []):
        text = "".join(seg.get("utf8", "") for seg in event.get("segs", [])).strip()
        if text:
            lines.append(text)
    return dedupe(lines)


def clean_srt(filepath: str) -> str:
    """Extract clean text from an SRT subtitle file.

    Works block by block: a block's sequence number is the line right before its timestamp,
    so a caption that is only a number (say "1984") is kept.
    """
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        blocks = re.split(r"\n\s*\n", f.read().replace("\r\n", "\n"))

    lines = []
    for block in blocks:
        rows = block.strip().splitlines()
        for i, row in enumerate(rows):
            if TIMESTAMP.search(row):
                continue
            if row.strip().isdigit() and i + 1 < len(rows) and TIMESTAMP.search(rows[i + 1]):
                continue
            text = TAG.sub("", row).strip()
            if text:
                lines.append(text)
    return dedupe(lines)


def process_file(filepath: str) -> str:
    """Process a subtitle file, auto-detecting format from extension."""
    if filepath.endswith(".json3"):
        return clean_json3(filepath)
    if filepath.endswith(".srt"):
        return clean_srt(filepath)
    raise ValueError(f"Unsupported format: {filepath}")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python3 yt_transcript.py INPUT_FILE [INPUT_FILE ...]", file=sys.stderr)
        sys.exit(1)

    for filepath in sys.argv[1:]:
        try:
            text = process_file(filepath)
        except FileNotFoundError:
            continue
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in {filepath}: {e}", file=sys.stderr)
            continue
        except ValueError:
            continue
        if text:
            print(text)
            return

    print("Error: No valid subtitle file found.", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
