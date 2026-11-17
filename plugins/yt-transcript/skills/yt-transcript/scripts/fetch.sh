#!/bin/sh
# Print a YouTube video's transcript as plain text.
#
#   fetch.sh URL [LANGUAGE]     LANGUAGE defaults to en; yt-dlp accepts regexes like en.*
#
# Tries manual subtitles before auto-generated ones, json3 before SRT (json3 sometimes fails
# with yt-dlp's _UnsafeExtensionError). Everything runs in this one shell, in a private temp
# dir that is removed on exit. yt-dlp's output goes to stderr, the transcript to stdout.
set -eu

if [ $# -lt 1 ]; then
  echo "usage: fetch.sh URL [LANGUAGE]" >&2
  exit 2
fi
url=$1
sub_lang=${2:-en}
here=$(cd "$(dirname "$0")" && pwd)
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

has() { ls "$work"/*."$1" >/dev/null 2>&1; }

# $1 = json3 or srt
fetch() {
  for which in --write-subs --write-auto-subs; do
    if [ "$1" = json3 ]; then fmt="--sub-format json3"; else fmt="--convert-subs srt"; fi
    # shellcheck disable=SC2086 # $fmt is two words on purpose
    uvx yt-dlp --skip-download "$which" --sub-lang "$sub_lang" $fmt \
      -o "$work/%(id)s.%(ext)s" "$url" >&2 || true
    has "$1" && return 0
  done
  return 1
}

if ! fetch json3 && ! fetch srt; then
  echo "no '$sub_lang' subtitles found; list them with: uvx yt-dlp --list-subs '$url'" >&2
  exit 1
fi

python3 "$here/yt_transcript.py" "$work"/*.json3 "$work"/*.srt
