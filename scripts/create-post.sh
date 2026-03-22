#!/bin/bash
# Boldly Balance Post Creator - SEO Optimized
# Creates a new blog post from template with full SEO metadata

set -euo pipefail

POSTS_DIR="/home/frn/.openclaw/workspace/projects/web-applications/boldlybalance/posts"
TEMPLATE="/home/frn/.openclaw/workspace/projects/web-applications/boldlybalance/templates/post-template.html"
POSTS_JSON="/home/frn/.openclaw/workspace/projects/web-applications/boldlybalance/posts.json"
SEARCH_INDEX="/home/frn/.openclaw/workspace/projects/web-applications/boldlybalance/search-index.json"
SITEMAP="/home/frn/.openclaw/workspace/projects/web-applications/boldlybalance/sitemap.xml"
API_DIR="/home/frn/.openclaw/workspace/projects/web-applications/boldlybalance/api/posts"
FEED_XML="/home/frn/.openclaw/workspace/projects/web-applications/boldlybalance/feed.xml"
BASE_URL="https://blog.boldlybalance.life"

# Validate inputs
if [ $# -lt 8 ]; then
    echo "Usage: $0 <slug> '<title>' '<category>' '<excerpt>' <unsplash-id> '<tldr>' <reading-time> '<tags>'"
    echo ""
    echo "Example:"
    echo "  $0 healthy-sleep-habits 'Healthy Sleep Habits' Sleep 'Improve your sleep quality with these evidence-based strategies' photo-1531353826977-0941b4779a1c 'Get 7-9 hours of quality sleep by maintaining consistent schedule, optimizing bedroom environment, and limiting blue light exposure before bed.' 8 'sleep,wellness,health'"
    echo ""
    echo "Required:"
    echo "  slug         - URL-friendly article slug (e.g., 'healthy-sleep-habits')"
    echo "  title        - Full article title"
    echo "  category     - Valid category (Fitness, Food, Sleep, Travel, Mind, Wellness, etc.)"
    echo "  excerpt      - 2-3 sentence summary for SEO"
    echo "  unsplash-id  - Unsplash photo ID (e.g., 'photo-1234567890')"
    echo "  tldr         - ≤100 word TL;DR summary for GEO"
    echo "  reading-time - Estimated reading time in minutes"
    echo "  tags         - Comma-separated tags for SEO"
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
DATE_DISPLAY=$(date +"%B %d, %Y")
FILENAME="$POSTS_DIR/${SLUG}.html"
API_FILE="$API_DIR/${SLUG}.json"

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
    echo "Valid categories: ${VALID_CATEGORIES[*]}"
fi

# Check if file already exists
if [ -f "$FILENAME" ]; then
    echo "Error: Post already exists: $FILENAME"
    exit 1
fi

# Generate URLs and metadata
CANONICAL_URL="$BASE_URL/posts/${SLUG}.html"
CATEGORY_URL="../category/$(echo "$CATEGORY" | tr '[:upper:]' '[:lower:]' | sed 's/ /-/g').html"
HERO_IMAGE_URL="https://images.unsplash.com/${IMAGE_ID}?w=1200&h=630&fit=crop"
META_KEYWORDS="$TAGS,boldly balance,wellness,${CATEGORY,,}"
OG_TITLE="$TITLE"
OG_DESCRIPTION="$EXCERPT"
TWITTER_TITLE="$TITLE"
TWITTER_DESCRIPTION="$EXCERPT"

# Build share URLs (URL encoded)
SHARE_TWITTER="https://twitter.com/intent/tweet?text=$(echo "$TITLE" | sed 's/ /%20/g')&url=$(echo "$CANONICAL_URL" | sed 's/:/%3A/g' | sed 's/\//%2F/g')"
SHARE_FACEBOOK="https://www.facebook.com/sharer/sharer.php?u=$(echo "$CANONICAL_URL" | sed 's/:/%3A/g' | sed 's/\//%2F/g')"
SHARE_LINKEDIN="https://www.linkedin.com/sharing/share-offsite/?url=$(echo "$CANONICAL_URL" | sed 's/:/%3A/g' | sed 's/\//%2F/g')"
SHARE_BLUESKY="https://bsky.app/intent/compose?text=$(echo "$TITLE" | sed 's/ /%20/g')%20$(echo "$CANONICAL_URL" | sed 's/:/%3A/g' | sed 's/\//%2F/g')"
SHARE_EMAIL="mailto:?subject=$(echo "$TITLE" | sed 's/ /%20/g')&body=$(echo "$CANONICAL_URL" | sed 's/:/%3A/g' | sed 's/\//%2F/g')"

# Generate tags HTML
TAGS_HTML=""
IFS=',' read -ra TAG_ARRAY <<< "$TAGS"
for tag in "${TAG_ARRAY[@]}"; do
    tag_clean=$(echo "$tag" | sed 's/^ *//;s/ *$//')
    TAGS_HTML="${TAGS_HTML}
                    <span class=\"tag-item\">${tag_clean}</span>"
done

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
    'OG_TITLE': '''$OG_TITLE''',
    'OG_DESCRIPTION': '''$OG_DESCRIPTION''',
    'OG_IMAGE_URL': '''$HERO_IMAGE_URL''',
    'OG_IMAGE_ALT': '''$TITLE''',
    'OG_TAGS': '''$TAGS''',
    'TWITTER_TITLE': '''$TWITTER_TITLE''',
    'TWITTER_DESCRIPTION': '''$TWITTER_DESCRIPTION''',
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
    'CATEGORY_URL': '''$CATEGORY_URL''',
    'CATEGORY': '''$CATEGORY''',
    'PUBLISHED_DATE_DISPLAY': '''$DATE_DISPLAY''',
    'EXCERPT': '''$EXCERPT''',
    'READING_TIME': '''$READING_TIME''',
    'WORD_COUNT': str(int($READING_TIME) * 200),
    'HERO_IMAGE_URL': '''$HERO_IMAGE_URL''',
    'HERO_IMAGE_ALT': '''$TITLE''',
    'IMAGE_CAPTION': '''Photo from Unsplash''',
    'TLDR_CONTENT': '''$TLDR''',
    'TAGS_LIST': '''$TAGS_HTML''',
    'SHARE_TWITTER': '''$SHARE_TWITTER''',
    'SHARE_FACEBOOK': '''$SHARE_FACEBOOK''',
    'SHARE_LINKEDIN': '''$SHARE_LINKEDIN''',
    'SHARE_BLUESKY': '''$SHARE_BLUESKY''',
    'SHARE_EMAIL': '''$SHARE_EMAIL''',
    'RELATED_ARTICLES_PLACEHOLDER': '''<!-- Related articles will be auto-populated -->'''
}

for placeholder, value in replacements.items():
    content = content.replace(placeholder, value)

with open('$FILENAME', 'w') as f:
    f.write(content)

print(f"✅ Created: $FILENAME")
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
