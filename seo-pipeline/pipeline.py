#!/usr/bin/env python3
"""
BoldlyBalance Programmatic SEO Pipeline

Orchestrates the content generation workflow:
1. Keyword Research → 2. Content Outline → 3. AI Writing → 4. Human Review → 5. Publish

Done-criteria: Pipeline can generate 10+ articles per week with keyword research, content outline, AI writing, and human review stages.
"""

import json
import os
import re
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import subprocess
import sys
import time

PROJECT_ROOT = Path(__file__).parent.parent
KEYWORDS_DIR = PROJECT_ROOT / "seo-pipeline/keywords"
OUTLINES_DIR = PROJECT_ROOT / "seo-pipeline/outlines"
ARTICLES_DIR = PROJECT_ROOT / "seo-pipeline/articles"
REVIEW_DIR = PROJECT_ROOT / "review"
POSTS_DIR = PROJECT_ROOT / "posts"
TEMPLATES_DIR = PROJECT_ROOT / "templates"
CONFIG_FILE = PROJECT_ROOT / ".pipeline_config.json"

# Status constants
STATUS = {
    "pending": "pending",
    "completed": "completed",
    "review": "review",
    "approved": "approved",
    "published": "published",
    "failed": "failed"
}


class SEO_Pipeline:
    def __init__(self):
        self.keywords_file = KEYWORDS_DIR / "keyword-clusters.json"
        self.outlines_dir = OUTLINES_DIR
        self.articles_dir = ARTICLES_DIR
        self.review_dir = REVIEW_DIR
        self.posts_dir = POSTS_DIR
        self.config = self._load_config()
        
        # Ensure directories exist
        for d in [self.outlines_dir, self.articles_dir, self.review_dir]:
            d.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load pipeline config from .pipeline_config.json or use defaults."""
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {
            "llm_provider": "ollama",  # Default to local Ollama
            "llm_model": "llama3.2:3b",
            "articles_per_week": 10,
            "batch_size": 3,  # Process 3 keywords at a time
            "timeout_seconds": 600  # 10 minutes per article
        }
    
    def load_keywords(self) -> Dict[str, Any]:
        """Load keyword clusters from JSON file."""
        with open(self.keywords_file, 'r') as f:
            return json.load(f)
    
    def get_next_keywords(self, count: int = 3) -> List[Dict]:
        """Get next set of keywords to process (not yet completed articles)."""
        data = self.load_keywords()
        clusters = data.get("clusters", {})
        
        next_keywords = []
        for cluster_id, cluster in clusters.items():
            seed_keywords = cluster.get("seed_keywords", [])
            for kw in seed_keywords[:5]:  # Limit to 5 keywords per cluster
                # Check if article exists for this keyword
                slug = kw.lower().replace(' ', '-').replace("'", '').replace("-", "-")
                article_file = self.articles_dir / f"{slug}.md"
                if not article_file.exists():
                    next_keywords.append({
                        "cluster_id": cluster_id,
                        "cluster": cluster,
                        "keyword": kw
                    })
                if len(next_keywords) >= count:
                    return next_keywords
        
        return next_keywords[:count]
    
    def generate_outline(self, keyword_data: Dict) -> str:
        """Generate content outline using template with LLM."""
        seed_keyword = keyword_data["keyword"]
        category = keyword_data["cluster"].get("category", "General")
        intent = keyword_data["cluster"].get("intent", "informational")
        
        # Build prompt for outline generation
        outline_content = f"""# {seed_keyword.title()}

> **Category:** {category} | **Intent:** {intent} | **Status:** {STATUS['pending']}

---

## The Problem

Research-driven analysis of why {seed_keyword.lower()} is misunderstood or approached incorrectly.

## Why This Approach Is Making It Worse

Explain the psychological/physiological mechanisms that make {seed_keyword.lower()} counterproductive.

## Evidence-Based Solution

### The Science Behind It

Evidence from peer-reviewed studies and clinical practice.

### Key Principles

Core frameworks for understanding {seed_keyword.lower()} correctly.

## Action Steps: Your 7-Day Protocol

### Day 1: Awareness

Initial step to recognize {seed_keyword.lower()} patterns.

### Day 2-3: Foundation

Build momentum with foundational practices.

### Day 4-5: Implementation

Deepen practice with targeted interventions.

### Day 6-7: Integration

Make {seed_keyword.lower()} part of daily routine.

## References

Relevant studies, books, and resources about {seed_keyword.lower()}.
"""
        
        # Save outline
        safe_name = seed_keyword.lower().replace(' ', '-').replace("'", '').replace('"', '')
        outline_file = self.outlines_dir / f"{safe_name}.md"
        with open(outline_file, 'w') as f:
            f.write(outline_content)
        
        return str(outline_file)
    
    async def generate_ai_content(self, keyword_data: Dict, outline_path: str) -> str:
        """Generate full article using LLM from outline."""
        seed_keyword = keyword_data["keyword"]
        category = keyword_data["cluster"].get("category", "General")
        
        # Load outline
        outline_file = Path(outline_path)
        if not outline_file.exists():
            raise FileNotFoundError(f"Outline not found: {outline_file}")
        
        outline_content = outline_file.read_text()
        
        # Check provider - Ollama for local LLM
        if self.config.get("llm_provider") == "ollama":
            # Generate content using Ollama with structured output
            prompt = f"""Generate a complete wellness article based on this outline. Write in a conversational, evidence-based style typical of BoldlyBalance.

OUTLINE:
{outline_content}

ARTICLE MARKDOWN (including标题 and proper formatting):

## The Problem

## Why This Approach Is Making It Worse

## Evidence-Based Solution

### The Science Behind It
[Detailed explanation]

### Key Principles
[Core frameworks]

## Action Steps: Your 7-Day Protocol

### Day 1: Awareness

[Day-specific content]

### Day 2-3: Foundation

[Day-specific content]

### Day 4-5: Implementation

[Day-specific content]

### Day 6-7: Integration

[Day-specific content]

## References
[List relevant sources]
"""
            try:
                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: subprocess.run(
                        ["curl", "-s", "http://localhost:11434/api/generate", 
                         "-H", "Content-Type: application/json",
                         "-d", json.dumps({
                             "model": self.config["llm_model"],
                             "prompt": prompt[:15000],  # Truncate if too long
                             "stream": False
                         })],
                        capture_output=True,
                        text=True,
                        timeout=self.config["timeout_seconds"]
                    )
                )
                if result.returncode == 0:
                    response = json.loads(result.stdout)
                    article_content = response.get("response", "")
                else:
                    raise Exception(f"Ollama error: {result.stderr}")
            except asyncio.TimeoutError:
                raise Exception("LLM generation timeout")
        else:
            # Fallback: Generate placeholder content
            article_content = f"""# {seed_keyword.title()}

Category: {category} | Status: Placeholder (AI generation needs config)

[AI-generated content would appear here with proper LLM integration]
"""
        
        # Save article
        safe_name = seed_keyword.lower().replace(' ', '-').replace("'", '').replace('"', '')
        article_file = self.articles_dir / f"{safe_name}.md"
        with open(article_file, 'w') as f:
            f.write(f"# {seed_keyword.title()}\n\n## Status\n\n- Outline: ✅\n- AI Draft: ✅\n- Review: ⏳\n\n---\n\n{article_content}")
        
        return str(article_file)
    
    def create_review_request(self, article_path: str, keyword_data: Dict) -> str:
        """Create review request in review folder."""
        article_file = Path(article_path)
        if not article_file.exists():
            raise FileNotFoundError(f"Article not found: {article_file}")
        
        content = article_file.read_text()
        keyword = keyword_data["keyword"]
        cluster_id = keyword_data["cluster_id"]
        
        review_request = f"""# Review Request: {keyword.title()}

**Cluster:** {cluster_id}  
**Status:** Awaiting Human Review  
**Created:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Original Content

{content[:3000]}  # Truncate for review

## Review Checklist

- [ ] Accuracy of health/wellness advice
- [ ] Alignment with BoldlyBalance voice and tone
- [ ] SEO optimization suggestions
- [ ] Reading flow and clarity
- [ ] Any necessary corrections or edits

## Approval/Rejection

- Approved by: [Name]
- Date: [Date]
- Notes: [Feedback]

## Final Status

- [ ] Ready to publish
- [ ] Requires revision
- [ ] Rejected (reason: _)
"""
        
        safe_name = keyword.lower().replace(' ', '-').replace("'", '').replace('"', '')
        review_file = self.review_dir / f"{safe_name}-review.md"
        with open(review_file, 'w') as f:
            f.write(review_request)
        
        # Mark article as in review
        article_file.write_text(content.replace(STATUS['pending'], STATUS['review']))
        
        # Notify Ferdy via Slack DM
        self._slack_draft_notification(keyword, keyword_data["cluster"].get("category", "General"), content, str(review_file))
        
        return str(review_file)
    
    def publish_to_posts(self, article_path: str, keyword_data: Dict) -> str:
        """Convert markdown article to HTML and publish to posts directory."""
        article_file = Path(article_path)
        if not article_file.exists():
            raise FileNotFoundError(f"Article not found: {article_path}")
        
        content = article_file.read_text()
        keyword = keyword_data["keyword"]
        category = keyword_data["cluster"].get("category", "General")
        
        # Generate HTML from markdown (basic conversion)
        html_content = self._convert_markdown_to_html(content, keyword, category)
        
        # Save as HTML in posts directory
        safe_slug = keyword.lower().replace(' ', '-').replace("'", '').replace('"', '')
        output_file = self.posts_dir / f"{safe_slug}.html"
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        # Update article status
        article_file.write_text(content.replace(STATUS['review'], STATUS['published']))
        
        return str(output_file)
    
    def _convert_markdown_to_html(self, markdown: str, keyword: str, category: str) -> str:
        """Convert markdown content to BoldlyBalance post HTML using post-template.html."""
        from html import escape
        import re as _re

        template_file = TEMPLATES_DIR / "post-template.html"
        template = template_file.read_text()

        lines = markdown.strip().split('\n')
        # Flat sections dict: heading_text -> content (for meta/TL;DR lookups and simple sections)
        sections = {}
        current_heading = None
        current_content = []
        for line in lines:
            m = re.match(r'^#{2,4} (.+)$', line.strip())
            if m:
                if current_heading:
                    sections[current_heading] = '\n'.join(current_content).strip()
                current_heading = m.group(1).strip()
                current_content = []
            else:
                current_content.append(line)
        if current_heading:
            sections[current_heading] = '\n'.join(current_content).strip()

        def md(text):
            text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
            text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
            text = re.sub(r'^#{2,4} (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
            text = re.sub(r'^- (.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)
            text = re.sub(r'(<li>.*?</li>\n?)+', lambda m: '<ul>' + m.group(0) + '</ul>', text)
            paragraphs = []
            for para in text.split('\n\n'):
                para = para.strip()
                if not para:
                    continue
                if para.startswith(('<h', '<ul', '<ol', '<li')):
                    paragraphs.append(para)
                else:
                    paragraphs.append(f'<p>{para}</p>')
            return '\n'.join(paragraphs)

        # Helper: extract subsections under a heading keyword
        # Heading hierarchy in generated articles:
        # # = doc title (skip), ## = article intro (skip), ### = section (h2), #### = subsection (h3)
        # We traverse looking for h3 (level==3) as parent sections, h4 (level==4) as their children.

        def get_subsections(parent_keyword):
            """Return dict of h4 sub-section -> content for all h4s that appear after the matching h3."""
            parent_lower = parent_keyword.lower()
            found_parent = False
            subs = {}
            current_sub = None
            current_content = []

            def save_sub():
                if current_sub:
                    subs[current_sub] = '\n'.join(current_content).strip()

            for idx, line in enumerate(lines):
                m = re.match(r'^(#{1,4}) (.+)$', line.strip())
                if m:
                    hashes, heading = m.groups()
                    level = len(hashes)
                    if level == 1:
                        found_parent = False
                        save_sub()
                        current_sub = None
                        current_content = []
                    elif level == 2:
                        found_parent = False
                        save_sub()
                        current_sub = None
                        current_content = []
                    elif level == 3:
                        save_sub()
                        found_parent = heading.strip().lower() == parent_lower
                        current_sub = None
                        current_content = []
                    elif level == 4:
                        save_sub()
                        if found_parent:
                            current_sub = heading.strip()
                            current_content = []
                elif current_sub is not None:
                    current_content.append(line)
                else:
                    pass  # content when not in a sub-section

            save_sub()
            return subs

        def get_h3_section(keyword):
            """Get all content under a h3 heading (direct text, no h4 children)."""
            keyword_lower = keyword.lower()
            content_lines = []
            found = False
            for line in lines:
                m = re.match(r'^(#{1,4}) (.+)$', line.strip())
                if m:
                    _, heading = m.groups()
                    level = len(m.group(1))
                    if level == 1 or level == 2:
                        found = False
                        content_lines = []
                    elif level == 3:
                        found = heading.strip().lower() == keyword_lower
                        if not found:
                            content_lines = []
                    elif level == 4:
                        if found:
                            break
                elif found:
                    content_lines.append(line)
            return '\n'.join(content_lines) if content_lines else ''
        why_subs = get_subsections('Why This Approach Is Making It Worse')
        why_targets = [
            ('The Anxiety Loop', 'anxiety loop'),
            ('The Sleep Effort Paradox', 'sleep effort paradox'),
            ('The Light-Dark Blind Spot', 'light-dark blind spot'),
            ('The Meal Timing Blind Spot', 'meal timing blind spot'),
        ]
        why_parts = []
        for label, kw in why_targets:
            for k, v in why_subs.items():
                if kw in k.lower() and v.strip():
                    why_parts.append(f'<h3>{label}</h3>\n{md(v)}')
                    break
        why_worse_html = '<h2>Why This Approach Is Making It Worse</h2>\n' + '\n'.join(why_parts) if why_parts else ''

        # Evidence-Based Solution — h3 section content + h4 children (Science, Principles)
        ebs_intro = get_h3_section('Evidence-Based Solution')  # text before first h4
        ebs_subs = get_subsections('Evidence-Based Solution')    # h4 children
        science_content = ebs_subs.get('The Science Behind It', '') or \
                         sections.get('The Science Behind It', '')
        principles_content = ebs_subs.get('Key Principles', '') or \
                             sections.get('Key Principles', '')

        # Day subsections — h4 children under h3 "Action Steps"
        day_subs = get_subsections('Action Steps: Your 7-Day Protocol')
        # Normalize keys for matching: replace en-dashes/em-dashes with hyphens, remove markdown bold
        def normalize_key(s):
            return s.replace('–', '-').replace('—', '-').replace('**', '').lower()
        # Map normalized key -> original key
        day_norm_to_orig = {normalize_key(k): k for k in day_subs}
        day_order = [
            ('Day 1: Awareness', ['day 1']),
            ('Days 2–3: Foundation', ['day 2', 'day 3']),
            ('Days 4–5: Implementation', ['day 4', 'day 5']),
            ('Days 6–7: Integration', ['day 6', 'day 7']),
        ]
        def key_contains(keywords, norm_k):
            """Check if any keyword is contained in norm_k, handling dash-separated day ranges."""
            for kw in keywords:
                if kw in norm_k:
                    return True
                # Also check after splitting on dashes (day 2 vs days 2-3)
                for part in norm_k.replace('-', ' ').replace('/', ' ').split():
                    if kw in part:
                        return True
            return False
        day_parts = []
        for label, keywords in day_order:
            for norm_k, orig_k in day_norm_to_orig.items():
                if key_contains(keywords, norm_k) and day_subs[orig_k].strip():
                    day_parts.append(f'<h3>{label}</h3>\n{md(day_subs[orig_k])}')
                    break
        days_html = '<h2>Action Steps: Your 7-Day Protocol</h2>\n' + '\n'.join(day_parts)

        # Problem section — use the flat sections dict (h3 heading)
        problem_html = f'<h2>The Problem</h2>\n{md(sections.get("The Problem", ""))}' if sections.get("The Problem") else ''

        # References
        refs_html = f'<h2>References</h2>\n{md(sections.get("References", ""))}' if sections.get("References") else ''

        # Build final content HTML
        content_parts = [problem_html, why_worse_html]
        if science_content or principles_content or ebs_intro:
            content_parts.append('<h2>Evidence-Based Solution</h2>')
            if ebs_intro.strip():
                content_parts.append(md(ebs_intro))
            if science_content.strip():
                content_parts.append(f'<h3>The Science Behind It</h3>\n{md(science_content)}')
            if principles_content.strip():
                content_parts.append(f'<h3>Key Principles</h3>\n{md(principles_content)}')
        content_parts.append(days_html)
        if refs_html:
            content_parts.append(refs_html)

        content_html = '\n'.join(content_parts).strip()

        # Generate slug and metadata
        slug = keyword.lower().replace(' ', '-').replace("'", '').replace('"', '')
        today = datetime.now().strftime('%Y-%m-%d')
        word_count = len(markdown.split())
        reading_time = max(1, word_count // 200)

        # Meta description from first paragraph
        meta_desc = sections.get('The Problem', keyword)[ : 160].strip()

        # TL;DR from science section
        tldr = sections.get('The Science Behind It', meta_desc)[ : 200].strip()

        # Photo pool — cycle through Unsplash fitness/wellness photos
        photo_ids = [
            'photo-1544367567-0f2fcb009e0b',  # yoga
            'photo-1571019613454-1cb2f99b2d8b',  # fitness
            'photo-1518611012118-696072aa579a',  # wellness
            'photo-1493836512294-502baa1986e2',  # lifestyle
            'photo-1545205597-3d9d02c29597',  # recovery
        ]
        photo_id = photo_ids[hash(keyword) % len(photo_ids)]

        # Related posts (static — pull from existing posts.json)
        related = self._get_related_posts(category, slug)
        rel1, rel2, rel3 = related

        # Share URLs
        share_x = f"https://twitter.com/intent/tweet?text={escape(keyword)}&url=https://lifestyle.boldlybalance.life/posts/{slug}.html"
        share_fb = f"https://www.facebook.com/sharer/sharer.php?u=https://lifestyle.boldlybalance.life/posts/{slug}.html"
        share_bs = f"https://bsky.app/profile/boldlybalance.bsky.social"
        share_li = f"https://www.linkedin.com/shareArticle?mini=true&url=https://lifestyle.boldlybalance.life/posts/{slug}.html"

        # Fill template
        html = (template
            .replace('TITLE', escape(keyword.title()))
            .replace('SLUG', slug)
            .replace('META_DESCRIPTION', escape(meta_desc))
            .replace('CATEGORY', category)
            .replace('CATEGORY_SLUG', category.lower().replace(' ', '-'))
            .replace('DATE_PUBLISHED', today)
            .replace('DATE_MODIFIED', today)
            .replace('WORD_COUNT', str(word_count))
            .replace('READING_TIME', str(reading_time))
            .replace('ARTICLE_TAGS', escape(keyword))
            .replace('ARTICLE_IMAGE_ALT', escape(f'{keyword} — Boldly Balance'))
            .replace('PHOTO_ID', photo_id)
            .replace('CONTENT_GOES_HERE', content_html)
            .replace('TLDR_CONTENT', escape(tldr))
            .replace('RELATED_LINK_1', rel1['url'])
            .replace('RELATED_IMG_1', rel1['img'])
            .replace('RELATED_TITLE_1', escape(rel1['title']))
            .replace('RELATED_DESC_1', escape(rel1['desc']))
            .replace('RELATED_CAT_1', rel1['cat'])
            .replace('RELATED_LINK_2', rel2['url'])
            .replace('RELATED_IMG_2', rel2['img'])
            .replace('RELATED_TITLE_2', escape(rel2['title']))
            .replace('RELATED_DESC_2', escape(rel2['desc']))
            .replace('RELATED_CAT_2', rel2['cat'])
            .replace('RELATED_LINK_3', rel3['url'])
            .replace('RELATED_IMG_3', rel3['img'])
            .replace('RELATED_TITLE_3', escape(rel3['title']))
            .replace('RELATED_DESC_3', escape(rel3['desc']))
            .replace('RELATED_CAT_3', rel3['cat'])
            .replace('SHARE_X', share_x)
            .replace('SHARE_FB', share_fb)
            .replace('SHARE_BS', share_bs)
            .replace('SHARE_LI', share_li)
        )

        return html

    def _get_related_posts(self, category: str, exclude_slug: str) -> list:
        """Get 3 related posts from posts.json, falling back to popular defaults."""
        try:
            posts_file = PROJECT_ROOT / "posts.json"
            if posts_file.exists():
                with open(posts_file) as f:
                    all_posts = json.load(f)
                # Same category first, then any
                same_cat = [p for p in all_posts if p.get('category') == category and p.get('slug') != exclude_slug]
                others = [p for p in all_posts if p.get('slug') != exclude_slug]
                pool = same_cat + others
                chosen = pool[:3]
                # If less than 3, pad with defaults
                defaults = [
                    {'title': 'Why Rest Days Are Not Optional', 'slug': 'why-rest-days-are-not-optional', 'category': 'Fitness'},
                    {'title': 'The Morning Routine Myth', 'slug': 'the-morning-routine-myth-why-perfect-am-rituals-backfire', 'category': 'Mind'},
                    {'title': 'Why Sleep Tracking Is Making You Sleep Worse', 'slug': 'why-sleep-tracking-is-making-you-sleep-worse', 'category': 'Sleep'},
                ]
                while len(chosen) < 3:
                    for d in defaults:
                        if d['slug'] != exclude_slug and d not in chosen:
                            chosen.append(d)
                            break
                    else:
                        break
                result = []
                for p in chosen[:3]:
                    img_pool = [
                        'photo-1544367567-0f2fcb009e0b',
                        'photo-1571019613454-1cb2f99b2d8b',
                        'photo-1518611012118-696072aa579a',
                    ]
                    result.append({
                        'url': f'https://lifestyle.boldlybalance.life/posts/{p["slug"]}.html',
                        'img': f'https://images.unsplash.com/{img_pool[len(result)]}?w=400&h=250&fit=crop',
                        'title': p.get('title', ''),
                        'desc': p.get('meta_description', '')[:100] or 'Practical wisdom for a balanced life.',
                        'cat': p.get('category', 'Wellness'),
                    })
                return result
        except Exception:
            pass
        # Fallback
        return [
            {'url': '/posts/why-rest-days-are-not-optional.html', 'img': 'https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=400&h=250&fit=crop', 'title': 'Why Rest Days Are Not Optional', 'desc': 'Recovery is your superpower.', 'cat': 'Fitness'},
            {'url': '/posts/the-morning-routine-myth-why-perfect-am-rituals-backfire.html', 'img': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400&h=250&fit=crop', 'title': 'The Morning Routine Myth', 'desc': 'Perfect AM rituals might be holding you back.', 'cat': 'Mind'},
            {'url': '/posts/why-sleep-tracking-is-making-you-sleep-worse.html', 'img': 'https://images.unsplash.com/photo-1518611012118-696072aa579a?w=400&h=250&fit=crop', 'title': 'Why Sleep Tracking Is Making You Sleep Worse', 'desc': 'The data is not helping you.', 'cat': 'Sleep'},
        ]

    def _slack_draft_notification(self, keyword: str, category: str, excerpt: str, draft_path: str):
        """Post draft notification to Slack DM with Ferdy."""
        import urllib.request
        slug = keyword.lower().replace(' ', '-').replace("'", '')
        msg = {
            "channel": "D0AQAM0DECA",
            "text": f"📝 *New article draft ready for review*\n\n*Keyword:* {keyword}\n*Category:* {category}\n*Draft:* `seo-pipeline/review/{slug}-review.md`\n\n---\n{excerpt[:300]}...\n\n—\nReply `publish` to move live, `rewrite [note]` to send back to Aria."
        }
        try:
            req = urllib.request.Request(
                "https://slack.com/api/chat.postMessage",
                data=json.dumps(msg).encode(),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=10):
                pass
        except Exception as e:
            print(f"[Slack notification] {e}")
    
    def run_workflow(self, keywords_count: int = 10) -> List[Dict[str, Any]]:
        """Run the full pipeline for specified number of keywords."""
        results = []
        
        keywords_to_process = self.get_next_keywords(count=keywords_count)
        
        if not keywords_to_process:
            print("No keywords to process.")
            return results
        
        print(f"Processing {len(keywords_to_process)} keywords...")
        
        # Process in batches for throughput
        batch_size = self.config.get("batch_size", 3)
        
        for i in range(0, len(keywords_to_process), batch_size):
            batch = keywords_to_process[i:i+batch_size]
            print(f"  Batch {(i // batch_size) + 1}: Processing {len(batch)} keywords...")
            
            for kw_data in batch:
                try:
                    # Step 1: Generate Outline
                    print(f"    Step 1/3: Generating outline for '{kw_data['keyword']}'...")
                    outline_path = self.generate_outline(kw_data)

                    # Step 2: AI Content Generation
                    print(f"    Step 2/3: AI content generation for '{kw_data['keyword']}'...")
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        article_path = loop.run_until_complete(self.generate_ai_content(kw_data, outline_path))
                    finally:
                        loop.close()

                    # Step 3: Send to review — STOP here, Ferdy approves before publishing
                    print(f"    Step 3/3: Sending '{kw_data['keyword']}' to review for your approval...")
                    review_path = self.create_review_request(article_path, kw_data)

                    results.append({
                        "keyword": kw_data["keyword"],
                        "status": STATUS['review'],
                        "outline": outline_path,
                        "article": article_path,
                        "review": review_path,
                        "published": None  # Ferdy publishes via Slack DM reply
                    })
                    
                except Exception as e:
                    print(f"    Error processing '{kw_data['keyword']}': {e}")
                    results.append({
                        "keyword": kw_data["keyword"],
                        "status": STATUS['failed'],
                        "error": str(e)
                    })
                    continue
            
            # Rate limiting - wait between batches
            if i + batch_size < len(keywords_to_process):
                print(f"    Waiting 1 second before next batch...")
                time.sleep(1)
        
        return results
    
    def get_progress(self) -> Dict[str, int]:
        """Get pipeline progress statistics."""
        outlines = len(list(self.outlines_dir.glob("*.md")))
        articles = len(list(self.articles_dir.glob("*.md")))
        reviews = len(list(self.review_dir.glob("*.md")))
        published = len(list(self.posts_dir.glob("*.html")))
        
        return {
            "outlines_completed": outlines,
            "articles_placed": articles,
            "reviews_pending": reviews,
            "published": published,
            "total_available": len(self.load_keywords().get("clusters", {})) * 5
        }


def main():
    """Main entry point for the pipeline. Supports: run, publish_pending, publish <keyword>."""
    pipeline = SEO_Pipeline()
    import sys

    print("=" * 60)
    print("BoldlyBalance SEO Content Pipeline")
    print("=" * 60)
    print()

    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"

    if cmd == "publish_pending":
        # Show all articles awaiting review
        reviews = sorted(pipeline.review_dir.glob("*-review.md"))
        if not reviews:
            print("No pending reviews.")
        for r in reviews:
            print(f"  📝 {r.stem.replace('-review', '')}")
        return

    elif cmd == "publish" and len(sys.argv) > 2:
        # Publish a specific article by keyword
        keyword = " ".join(sys.argv[2:])
        slug = keyword.lower().replace(' ', '-').replace("'", '')
        article_file = pipeline.articles_dir / f"{slug}.md"
        if not article_file.exists():
            print(f"Article not found: {article_file}")
            return
        # Find matching keyword data from clusters
        kw_data = {"keyword": keyword, "cluster": {"category": "General"}}
        clusters_data = pipeline.load_keywords()
        for cluster in clusters_data.get("clusters", {}).values():
            for seed_kw in cluster.get("seed_keywords", []):
                if seed_kw.lower() == keyword.lower():
                    kw_data = {"keyword": seed_kw, "cluster": {"category": cluster.get("category", "General")}}
                    break
        output = pipeline.publish_to_posts(str(article_file), kw_data)
        # Remove review file
        review_file = pipeline.review_dir / f"{slug}-review.md"
        if review_file.exists():
            review_file.unlink()
        print(f"✅ Published: {output}")
        return

    elif cmd == "run":
        keywords_count = pipeline.config.get("articles_per_week", 10)
        results = pipeline.run_workflow(keywords_count=keywords_count)
        print()
        print("Pipeline Results:")
        for r in results:
            if r.get("status") == STATUS['review']:
                print(f"  📝 {r['keyword']}: in review — reply `publish {r['keyword']}` to go live")
            elif r.get("status") == STATUS['completed']:
                print(f"  ✅ {r['keyword']}: published")
            else:
                print(f"  ❌ {r['keyword']}: {r.get('error', 'Unknown error')}")
        print()
        print("Pipeline Progress:", pipeline.get_progress())
        return results

    else:
        print("Usage:")
        print("  python pipeline.py run              # Generate articles (stops at review)")
        print("  python pipeline.py publish_pending  # List articles awaiting review")
        print("  python pipeline.py publish <kw>    # Publish a specific article")


if __name__ == "__main__":
    main()
