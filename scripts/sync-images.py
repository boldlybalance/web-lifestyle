#!/usr/bin/env python3
"""
Sync images from posts.json to all HTML post files.
"""
import json
import os
import re

def main():
    with open('posts.json', 'r') as f:
        posts = json.load(f)
    
    # Create slug -> image mapping
    slug_to_image = {post['slug']: post.get('image', '') for post in posts}
    
    updated = 0
    for filename in os.listdir('posts'):
        if not filename.endswith('.html'):
            continue
        
        filepath = os.path.join('posts', filename)
        with open(filepath, 'r') as f:
            content = f.read()
        
        original = content
        slug = filename.replace('.html', '')
        
        if slug in slug_to_image:
            img_url = f"https://images.unsplash.com/{slug_to_image[slug]}?w=1200&q=80"
            # Update article image src
            content = re.sub(
                r'<img src="https://images\.unsplash\.com/[^"]+\?w=1200[^"]*"',
                f'<img src="{img_url}"',
                content
            )
            # Update og:image
            content = re.sub(
                r'<meta property="og:image" content="https://images\.unsplash\.com/[^"]+"',
                f'<meta property="og:image" content="{img_url}">',
                content
            )
        
        if content != original:
            with open(filepath, 'w') as f:
                f.write(content)
            updated += 1
    
    print(f"📊 Total files updated: {updated}")

if __name__ == '__main__':
    main()
