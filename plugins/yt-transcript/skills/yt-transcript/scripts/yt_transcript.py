#!/usr/bin/env python3
"""Convert YouTube subtitle files (json3 or SRT) to clean plain text.

Supports two formats:
- json3: YouTube's native JSON subtitle format
- SRT: SubRip text format (used as fallback)

Strips all formatting, timestamps, and sequence numbers. Deduplicates
consecutive identical lines common in auto-generated subtitles.

Usage: python3 yt_transcript.py INPUT_FILE [INPUT_FILE ...]

The first valid file found is processed. Format is detected from extension.
Output goes to stdout.
"""

import json
import re
import sys


def clean_json3(filepath: str) -> str:
    """Extract clean text from a YouTube json3 subtitle file."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        data = json.load(f)

    lines = []
    for event in data.get("events", []):
        segments = event.get("segs", [])
        text = "".join(seg.get("utf8", "") for seg in segments).strip()
        if text and text != "\n":
            lines.append(text)

    # Deduplicate consecutive identical lines
    deduped = []
    for line in lines:
        if not deduped or line != deduped[-1]:
            deduped.append(line)

    return "\n".join(deduped)


def clean_srt(filepath: str) -> str:
    """Extract clean text from an SRT subtitle file."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    # Remove SRT sequence numbers (lines that are just digits)
    content = re.sub(r"^\d+\s*$", "", content, flags=re.MULTILINE)

    # Remove timestamp lines: 00:00:00,000 --> 00:00:02,500
    content = re.sub(
        r"\d{2}:\d{2}:\d{2}[,.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,.]\d{3}.*",
        "",
        content,
    )

    # Remove HTML-like tags (<font>, </font>, <i>, etc.)
    content = re.sub(r"<[^>]+>", "", content)

    # Remove inline VTT timestamps that may survive conversion
    content = re.sub(r"<\d{2}:\d{2}:\d{2}[,.]\d{3}>", "", content)

    # Split into lines, strip whitespace, remove empty lines
    lines = [line.strip() for line in content.splitlines() if line.strip()]

    # Deduplicate consecutive identical lines
    deduped = []
    for line in lines:
        if not deduped or line != deduped[-1]:
            deduped.append(line)

    return "\n".join(deduped)


def process_file(filepath: str) -> str:
    """Process a subtitle file, auto-detecting format from extension."""
    if filepath.endswith(".json3"):
        return clean_json3(filepath)
    elif filepath.endswith(".srt"):
        return clean_srt(filepath)
    else:
        raise ValueError(f"Unsupported format: {filepath}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 yt_transcript.py INPUT_FILE [INPUT_FILE ...]", file=sys.stderr)
        sys.exit(1)

    # Try each file argument; use the first one that exists and works.
    # This allows glob patterns like *.json3 *.srt where only one matches.
    for filepath in sys.argv[1:]:
        try:
            text = process_file(filepath)
            if text:
                print(text)
                return
        except FileNotFoundError:
            continue
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in {filepath}: {e}", file=sys.stderr)
            continue
        except ValueError:
            continue

    print("Error: No valid subtitle file found.", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
