#!/usr/bin/env python3
"""
Safe Image Updater - Updates image for a specific post
Usage: python3 scripts/update-post-image.py <slug> <new-image-id>
Example: python3 scripts/update-post-image.py restart-fitness-after-years photo-1595078475328-1ab05d0a6a0e
"""
import sys
import json

if len(sys.argv) != 3:
    print("Usage: python3 scripts/update-post-image.py <slug> <new-image-id>")
    print("Example: python3 scripts/update-post-image.py restart-fitness-after-years photo-1595078475328-1ab05d0a6a0e")
    sys.exit(1)

slug = sys.argv[1]
new_image = sys.argv[2]

# Update posts.json
with open('posts.json', 'r') as f:
    posts = json.load(f)

found = False
for post in posts:
    if post['slug'] == slug:
        old_image = post.get('image', 'N/A')
        post['image'] = new_image
        found = True
        print(f"✓ Updated {slug}: {old_image} -> {new_image}")
        break

if not found:
    print(f"✗ Post '{slug}' not found in posts.json")
    sys.exit(1)

with open('posts.json', 'w') as f:
    json.dump(posts, f, indent=2)

# Update the HTML file directly
html_file = f"posts/{slug}.html"
try:
    with open(html_file, 'r') as f:
        content = f.read()
    
    # Replace image URLs in the HTML (both og:image and main img src)
    content = content.replace(old_image, new_image)
    
    with open(html_file, 'w') as f:
        f.write(content)
    print(f"✓ Updated {html_file}")
except FileNotFoundError:
    print(f"⚠ {html_file} not found (skipping HTML update)")

print("\n✅ Done! Run preflight-validate.py before pushing.")
