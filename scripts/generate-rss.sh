#!/usr/bin/env bash
# Generate RSS feed.xml for Boldly Balance
# Reads posts.json (sorted by date), outputs RSS 2.0 feed with latest 20 articles

set -euo pipefail

BOLDLY_HOME="$(cd "$(dirname "$0")/.." && pwd)"
python3 "$BOLDLY_HOME/scripts/generate-rss.py" "${@}"
