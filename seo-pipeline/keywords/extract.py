#!/usr/bin/env python3
"""
BoldlyBalance Programmatic SEO - Seed Keyword Extractor

Extracts seed keywords from existing posts, clusters by intent,
and generates keyword clusters for content generation.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent.parent
POSTS_JSON = PROJECT_ROOT / "posts.json"
OUTPUT_DIR = Path(__file__).parent


def load_posts() -> List[Dict[str, Any]]:
    """Load posts.json data."""
    with open(POSTS_JSON, 'r') as f:
        return json.load(f)


def extract_keywords_from_title(title: str) -> List[str]:
    """Extract potential keywords from article titles using pattern matching."""
    # Pattern: "Why X", "How Y", "The Z", "X for Y" etc.
    patterns = [
        r'Why\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # "Why Wellness Clubs"
        r'How\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',   # "How Pushing"
        r'The\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',   # "The Anti-Intimidation"
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+for\s+([A-Z][a-z]+)',  # "Yoga for people"
    ]
    
    keywords = []
    for pattern in patterns:
        matches = re.findall(pattern, title)
        for match in matches:
            if isinstance(match, tuple):
                keywords.extend(list(match))
            else:
                keywords.append(match)
    
    return list(set(keywords))


def extract_keywords_from_excerpt(excerpt: str) -> List[str]:
    """Extract keywords from excerpt text."""
    # Common keywords from wellness content
    wellness_keywords = [
        'recovery', 'energy', 'progress', 'plateau', 'nervous system',
        'sleep', 'wellness', 'productivity', 'fitness', ' Mindset',
        'mental', 'emotional', 'physical', 'yoga', 'exercise', 'workout',
        'habits', 'routines', 'protocol', 'evidence-based', 'clincal',
        'evidence', 'data', 'science', 'science-backed', 'backed'
    ]
    
    found = []
    excerpt_lower = excerpt.lower()
    for kw in wellness_keywords:
        if kw.lower() in excerpt_lower:
            found.append(kw)
    
    return list(set(found))


def cluster_keywords(posts: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Cluster posts into keyword groups based on category and content themes.
    Returns structured clusters for content generation.
    """
    clusters = defaultdict(lambda: {
        'cluster_id': '',
        'category': '',
        'intent': 'informational',  # default intent
        'seed_keywords': [],
        'related_posts': [],
        'content_pillars': []
    })
    
    # Extract all posts with their keywords
    for post in posts:
        if post.get('status') != 'published':
            continue
            
        category = post.get('category', 'General')
        slug = post.get('slug', '')
        title = post.get('title', '')
        excerpt = post.get('excerpt', '')
        
        # Extract keywords
        title_keywords = extract_keywords_from_title(title)
        excerpt_keywords = extract_keywords_from_excerpt(excerpt)
        all_keywords = list(set(title_keywords + excerpt_keywords))
        
        # Determine intent from title patterns
        title_lower = title.lower()
        if title_lower.startswith('why'):
            intent = 'informational'
        elif title_lower.startswith('how'):
            intent = 'instructional'
        elif 'best' in title_lower or 'guide' in title_lower:
            intent = 'commercial'
        else:
            intent = 'informational'
        
        # Create cluster key from category + main theme
        cluster_key = f"{category}_cluster"
        
        clusters[cluster_key]['cluster_id'] = cluster_key
        clusters[cluster_key]['category'] = category
        clusters[cluster_key]['intent'] = intent
        clusters[cluster_key]['seed_keywords'].extend(all_keywords)
        clusters[cluster_key]['related_posts'].append(slug)
        clusters[cluster_key]['content_pillars'].append(title)
    
    # Deduplicate keywords and content pillars
    for cluster_key in clusters:
        clusters[cluster_key]['seed_keywords'] = list(set(clusters[cluster_key]['seed_keywords']))
        clusters[cluster_key]['content_pillars'] = list(set(clusters[cluster_key]['content_pillars']))
    
    return dict(clusters)


def save_clusters(clusters: Dict[str, Dict[str, Any]], output_file: Path) -> None:
    """Save clusters to JSON file."""
    with open(output_file, 'w') as f:
        json.dump({
            'generated_at': '2026-04-10T17:30:00Z',
            'generator': 'seed-keyword-extractor.py',
            'total_clusters': len(clusters),
            'clusters': clusters
        }, f, indent=2)


def main():
    """Main extraction workflow."""
    print("BoldlyBalance SEO - Seed Keyword Extractor")
    print("=" * 50)
    
    # Load posts
    posts = load_posts()
    print(f"Loaded {len(posts)} posts from {POSTS_JSON}")
    
    # Extract and cluster keywords
    clusters = cluster_keywords(posts)
    print(f"Created {len(clusters)} keyword clusters")
    
    # Save results
    output_file = OUTPUT_DIR / 'keyword-clusters.json'
    save_clusters(clusters, output_file)
    print(f"Saved clusters to {output_file}")
    
    # Print summary
    print("\n=== Keyword Clusters Summary ===")
    for cluster_id, cluster in list(clusters.items())[:5]:  # First 5
        print(f"\n{cluster_id}")
        print(f"  Category: {cluster['category']}")
        print(f"  Intent: {cluster['intent']}")
        print(f"  Seed Keywords: {', '.join(cluster['seed_keywords'][:5])}")
        print(f"  Content Pillars: {len(cluster['content_pillars'])}")


if __name__ == '__main__':
    main()
