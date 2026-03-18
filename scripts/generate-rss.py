#!/usr/bin/env python3
"""Generate RSS feed.xml for Boldly Balance from posts.json"""

import json
import sys
import os
from datetime import datetime

BOLDLY_HOME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_JSON = os.path.join(BOLDLY_HOME, "posts.json")
OUTPUT = os.path.join(BOLDLY_HOME, "feed.xml")
SITE_URL = "https://boldlybalance.life"
SITE_NAME = "Boldly Balance"
SITE_DESC = "Science-backed wellness, lifestyle, and personal growth. Practical strategies for living well in a connected world."
COUNT = 20

# Parse args
for i, arg in enumerate(sys.argv[1:]):
    if arg == "--count" and i + 2 < len(sys.argv):
        COUNT = int(sys.argv[i + 2])

with open(POSTS_JSON) as f:
    posts = json.load(f)

# Sort by date descending, take latest N
posts.sort(key=lambda p: p.get("date", ""), reverse=True)
posts = posts[:COUNT]

now = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

def esc(s):
    """Escape XML special characters"""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

items = []
for p in posts:
    slug = p["slug"]
    title = esc(p["title"])
    excerpt = esc(p.get("excerpt", ""))
    category = p.get("category", "Wellness")
    date_str = p.get("date", "2026-01-01")
    
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        pub_date = dt.strftime("%a, %d %b %Y 00:00:00 +0000")
    except:
        pub_date = now
    
    link = f"{SITE_URL}/posts/{slug}.html"
    image = p.get("image", "")
    if image and not image.startswith("http"):
        image_url = esc(f"https://images.unsplash.com/{image}?w=1200&h=630&fit=crop")
    else:
        image_url = esc(image)
    
    items.append(f"""    <item>
      <title>{title}</title>
      <link>{link}</link>
      <guid isPermaLink="true">{link}</guid>
      <description>{excerpt}</description>
      <category>{category}</category>
      <pubDate>{pub_date}</pubDate>
      <enclosure url="{image_url}" type="image/jpeg" length="0" />
    </item>""")

rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:media="http://search.yahoo.com/mrss/">
  <channel>
    <title>{SITE_NAME}</title>
    <link>{SITE_URL}</link>
    <description>{SITE_DESC}</description>
    <language>en-us</language>
    <lastBuildDate>{now}</lastBuildDate>
    <atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml"/>
    <image>
      <url>{SITE_URL}/favicon.ico</url>
      <title>{SITE_NAME}</title>
      <link>{SITE_URL}</link>
    </image>
{chr(10).join(items)}
  </channel>
</rss>"""

with open(OUTPUT, "w") as f:
    f.write(rss)

print(f"✅ Generated feed.xml with {len(posts)} articles")
