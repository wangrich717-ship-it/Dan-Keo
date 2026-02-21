#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dan Koe Knowledge Base - Data Builder
Reads all .txt article files and generates JSON data for the web frontend.
"""

import os
import json
import re
import hashlib
from datetime import datetime
from pathlib import Path

SOURCE_DIR = Path(__file__).parent.parent / "Dan Keo"
OUTPUT_DIR = Path(__file__).parent / "data"
ARTICLES_DIR = OUTPUT_DIR / "articles"

ARTICLES_DIR.mkdir(parents=True, exist_ok=True)

CATEGORY_RULES = [
    ("Business & Money", [
        "business", "money", "rich", "wealth", "income", "product", "startup",
        "earn", "profitable", "million", "billionaire", "$", "monetize", "productize"
    ]),
    ("Content & Writing", [
        "write", "writing", "content", "brand", "audience", "creator", "persuasion",
        "newsletter", "follow", "framework", "social media", "personal brand"
    ]),
    ("Future & AI", [
        "ai", "artificial intelligence", "future", "digital", "technology", "skill stack",
        "irreplaceable", "generalist", "leverage", "future-proof"
    ]),
    ("Productivity & Focus", [
        "productivity", "focus", "deep work", "routine", "habit", "work less",
        "time", "monk mode", "disappear", "distraction", "minimalist", "schedule"
    ]),
    ("Mindset & Growth", [
        "mindset", "life", "change", "discipline", "self", "think", "mental",
        "reset", "comeback", "stuck", "lost", "intelligent", "reinvent", "dopamine"
    ]),
]

def detect_category(title: str, content: str) -> str:
    text = (title + " " + content[:500]).lower()
    scores = {}
    for cat_name, keywords in CATEGORY_RULES:
        score = sum(text.count(kw) for kw in keywords)
        scores[cat_name] = score
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Mindset & Growth"

def is_body_line(line: str) -> bool:
    """Return True if this line is real content (not header metadata)."""
    s = line.strip()
    if not s:
        return False
    if s.startswith("http://") or s.startswith("https://"):
        return False
    # Filter any line that is purely metadata (无作者, author labels, etc.)
    # Use 'in' so encoding variants like '无作者 ' or partial matches are caught
    META_FRAGMENTS = ["无作者", "作者：", "作者:", "no author", "transcript:"]
    sl = s.lower()
    for frag in META_FRAGMENTS:
        if sl == frag.lower() or sl.startswith(frag.lower()):
            return False
    return True


def parse_article(filepath: Path) -> dict | None:
    try:
        raw = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"  [ERROR] Cannot read: {e}")
        return None

    lines = raw.split("\n")

    # ── Title: always use the filename stem (user confirmed filenames = titles)
    title = filepath.stem
    for suffix in [" - YouTube", "- YouTube", " | YouTube", " - Dan Koe"]:
        if title.endswith(suffix):
            title = title[:-len(suffix)].strip()

    # ── URL: scan first 8 lines
    url = ""
    for line in lines[:8]:
        s = line.strip()
        if s.startswith("http://") or s.startswith("https://"):
            url = s
            break

    # ── Sections: scan all lines, skip header metadata
    # Normalised title for deduplication (skip if a body line IS the title)
    title_norm = title.lower().strip()

    sections = []
    current_section = {"title": "Introduction", "content": []}

    for line in lines:
        line_stripped = line.strip()
        if line_stripped.startswith("[章节]"):
            if current_section["content"]:
                text = " ".join(current_section["content"]).strip()
                if text:
                    sections.append({
                        "title": current_section["title"],
                        "content": text
                    })
            section_title = line_stripped.replace("[章节]", "").strip()
            current_section = {"title": section_title, "content": []}
        elif is_body_line(line):
            # Skip lines that are just the article title repeated
            if line_stripped.lower().strip() != title_norm:
                current_section["content"].append(line_stripped)

    if current_section["content"]:
        text = " ".join(current_section["content"]).strip()
        if text:
            sections.append({
                "title": current_section["title"],
                "content": text
            })

    # If no sections found at all, nothing useful in the file
    if not sections:
        return None

    all_content = " ".join(s["content"] for s in sections)
    word_count = len(all_content.split())
    if word_count < 20:
        return None  # Too short to be a real article

    excerpt = all_content[:300].rsplit(" ", 1)[0] + "..." if len(all_content) > 300 else all_content

    article_id = hashlib.md5(title.encode()).hexdigest()[:8]
    category = detect_category(title, all_content)
    read_time = max(1, word_count // 200)

    mtime = filepath.stat().st_mtime
    mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")

    return {
        "id": article_id,
        "title": title,
        "url": url,
        "author": "Dan Koe",
        "category": category,
        "sections": sections,
        "excerpt": excerpt,
        "word_count": word_count,
        "read_time": read_time,
        "filename": filepath.name,
        "mtime": mtime,        # Unix timestamp for sorting
        "date": mtime_str,     # Human-readable date
    }

def build():
    print(f"Source directory: {SOURCE_DIR}")
    print(f"Output directory: {OUTPUT_DIR}\n")

    if not SOURCE_DIR.exists():
        print(f"[ERROR] Source directory not found: {SOURCE_DIR}")
        return

    txt_files = [f for f in SOURCE_DIR.glob("*.txt") if f.stat().st_size > 100]
    # Sort alphabetically by filename (A-Z)
    txt_files.sort(key=lambda f: f.stem.lower())
    print(f"Found {len(txt_files)} article files (sorted A-Z)\n")

    index = []
    category_counts = {}

    for filepath in sorted(txt_files):
        safe_name = filepath.name[:60].encode('gbk', errors='replace').decode('gbk')
        print(f"Processing: {safe_name}...")
        article = parse_article(filepath)
        if not article:
            print(f"  [SKIP] Empty or invalid file")
            continue

        article_file = ARTICLES_DIR / f"{article['id']}.json"
        article_file.write_text(
            json.dumps(article, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        category_counts[article["category"]] = category_counts.get(article["category"], 0) + 1

        index.append({
            "id": article["id"],
            "title": article["title"],
            "category": article["category"],
            "excerpt": article["excerpt"],
            "word_count": article["word_count"],
            "read_time": article["read_time"],
            "section_count": len(article["sections"]),
            "mtime": article["mtime"],
            "date": article["date"],
        })

    index_file = OUTPUT_DIR / "index.json"
    index_file.write_text(
        json.dumps({
            "total": len(index),
            "categories": sorted(category_counts.keys()),
            "category_counts": category_counts,
            "articles": index
        }, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"\n{'='*50}")
    print(f"Build complete! {len(index)} articles processed.")
    print(f"\nCategories:")
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count} articles")
    print(f"\nOutput: {index_file}")

if __name__ == "__main__":
    build()
