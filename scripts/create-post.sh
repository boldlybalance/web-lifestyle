#!/bin/bash
# Boldly Balance Post Creator - SEO Optimized
# Creates a new blog post from template with full SEO metadata

set -euo pipefail

POSTS_DIR="/home/frn/.openclaw/workspace/projects/web-applications/boldlybalance/posts"
TEMPLATE="/home/frn/.openclaw/workspace/projects/web-applications/boldlybalance/templates/post-template.html"
BASE_URL="https://blog.boldlybalance.life"

# Validate inputs
if [ $# -lt 8 ]; then
    echo "Usage: $0 <slug> '<title>' '<category>' '<excerpt>' <unsplash-id> '<tldr>' <reading-time> '<tags>'"
    echo ""
    echo "Example:"
    echo "  $0 healthy-sleep-habits 'Healthy Sleep Habits' 'Sleep' 'Improve your sleep quality' 'photo-123' 'TLDR here' 8 'sleep,wellness'"
    exit 1
fi

SLUG="$1"
TITLE="$2"
CATEGORY="$3"
EXCERPT="$4"
IMAGE_ID="$5"
TLDR="$6"
READING_TIME="$7"
TAGS="$8"
DATE=$(date +%Y-%m-%d)
FILENAME="$POSTS_DIR/${SLUG}.html"

# Validate category
VALID_CATEGORIES=("Fitness" "Food" "Sleep" "Travel" "Mind" "Wellness" "Lifestyle" "Technology" "Recovery" "Finance" "Home Decor" "Mindset" "Case Study" "Routine" "Reviews")
CATEGORY_VALID=false
for valid_cat in "${VALID_CATEGORIES[@]}"; do
    if [ "$CATEGORY" = "$valid_cat" ]; then
        CATEGORY_VALID=true
        break
    fi
done

if [ "$CATEGORY_VALID" = false ]; then
    echo "Warning: '$CATEGORY' may not be a standard category"
fi

# Check if file already exists
if [ -f "$FILENAME" ]; then
    echo "Error: Post already exists: $FILENAME"
    exit 1
fi

# Generate URLs and metadata
CANONICAL_URL="$BASE_URL/posts/${SLUG}.html"
CATEGORY_URL="../category/$(echo "$CATEGORY" | tr '[:upper:]' '[:lower:]' | sed 's/ /-/g').html"
HERO_IMAGE_URL="https://images.unsplash.com/${IMAGE_ID}?w=1200\&h=630\&fit=crop"
META_KEYWORDS="$TAGS,boldly balance,wellness,${CATEGORY,,}"

# Build share URLs (simplified, use actual URLs)
SHARE_TWITTER="https://twitter.com/intent/tweet?text=POST_TITLE\&url=POST_URL"
SHARE_FACEBOOK="https://www.facebook.com/sharer/sharer.php?u=POST_URL"
SHARE_LINKEDIN="https://www.linkedin.com/sharing/share-offsite/?url=POST_URL"
SHARE_BLUESKY="https://bsky.app/intent/compose?text=POST_TITLE%20POST_URL"
SHARE_EMAIL="mailto:?subject=POST_TITLE\&body=POST_URL"

echo "Creating post from template..."
cp "$TEMPLATE" "$FILENAME"

echo "Populating placeholders..."

# Use Python for complex replacements (handles special characters)
python3 << PYEOF
import re

with open('$FILENAME', 'r') as f:
    content = f.read()

# Replace all placeholders
replacements = {
    'TITLE': '''$TITLE''',
    'META_DESCRIPTION': '''$EXCERPT''',
    'META_KEYWORDS': '''$META_KEYWORDS''',
    'CANONICAL_URL': '''$CANONICAL_URL''',
    'OG_TITLE': '''$TITLE''',
    'OG_DESCRIPTION': '''$EXCERPT''',
    'OG_IMAGE_URL': '''$HERO_IMAGE_URL''',
    'OG_IMAGE_ALT': '''$TITLE''',
    'OG_TAGS': '''$TAGS''',
    'TWITTER_TITLE': '''$TITLE''',
    'TWITTER_DESCRIPTION': '''$EXCERPT''',
    'TWITTER_IMAGE_URL': '''$HERO_IMAGE_URL''',
    'TWITTER_IMAGE_ALT': '''$TITLE''',
    'PUBLISHED_DATE': '''$DATE''',
    'MODIFIED_DATE': '''$DATE''',
    'SCHEMA_HEADLINE': '''$TITLE''',
    'SCHEMA_DESCRIPTION': '''$EXCERPT''',
    'SCHEMA_IMAGE_URL': '''$HERO_IMAGE_URL''',
    'SCHEMA_DATE_PUBLISHED': '''$DATE''',
    'SCHEMA_DATE_MODIFIED': '''$DATE''',
    'SCHEMA_CATEGORY': '''$CATEGORY''',
    'SCHEMA_KEYWORDS': '''$TAGS''',
    'BREADCRUMB_CATEGORY': '''$CATEGORY''',
    'BREADCRUMB_CATEGORY_URL': '''$CATEGORY_URL''',
    'BREADCRUMB_TITLE': '''$TITLE''',
    'CATEGORY': '''$CATEGORY''',
    'EXCERPT': '''$EXCERPT''',
    'READING_TIME': '''$READING_TIME''',
    'TLDR_CONTENT': '''$TLDR''',
}

for placeholder, value in replacements.items():
    content = content.replace(placeholder, value)

with open('$FILENAME', 'w') as f:
    f.write(content)

print(f"Created: $FILENAME")
PYEOF

echo ""
echo "✅ Post created successfully!"
echo ""
echo "Next steps:"
echo "  1. Edit the file: $FILENAME"
echo "  2. Replace CONTENT_GOES_HERE with your article content"
echo "  3. Update related articles section"
echo "  4. Test the page locally"
echo "  5. Commit and push"
echo ""
echo "Live URL will be: $CANONICAL_URL"
