#!/usr/bin/env bash
# Add <link rel="alternate"> RSS tag to all Boldly Balance HTML posts
# Inserts after the canonical link tag in <head>

set -euo pipefail

BOLDLY_HOME="$(cd "$(dirname "$0")/.." && pwd)"
POSTS_DIR="$BOLDLY_HOME/posts"
RSS_TAG='    <link rel="alternate" type="application/rss+xml" title="Boldly Balance RSS Feed" href="/feed.xml">'
COUNT=0
SKIPPED=0

for html in "$POSTS_DIR"/*.html; do
  # Skip if already has RSS link
  if grep -q 'rel="alternate"' "$html" 2>/dev/null; then
    SKIPPED=$((SKIPPED + 1))
    continue
  fi
  
  # Insert RSS link after the canonical link tag
  if grep -q 'rel="canonical"' "$html"; then
    sed -i "/rel=\"canonical\"/a\\$RSS_TAG" "$html"
    COUNT=$((COUNT + 1))
  else
    # Fallback: insert before </head>
    sed -i "s|</head>|$RSS_TAG\n</head>|" "$html"
    COUNT=$((COUNT + 1))
  fi
done

echo "✅ Updated $COUNT posts with RSS link"
echo "⏭️  Skipped $SKIPPED (already had RSS link)"
