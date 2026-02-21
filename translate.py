#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dan Koe Knowledge Base - Translation Script
Adds Chinese translations to article JSON files (incrementally).

Usage:
  python translate.py              # translate all untranslated articles
  python translate.py --reset      # clear all translations and re-translate

Requires: pip install deep-translator
"""

import json
import sys
import time
import argparse
from pathlib import Path

ARTICLES_DIR = Path(__file__).parent / "data" / "articles"
DELAY_SECTION = 0.8   # seconds between sections
DELAY_ARTICLE = 1.5   # seconds between articles
CHUNK_SIZE    = 4500  # chars per translate call (Google limit ~5000)

# ── TRANSLATOR SETUP ────────────────────────────────────────────────────────

def get_translator():
    try:
        from deep_translator import GoogleTranslator
        return GoogleTranslator(source='en', target='zh-CN')
    except ImportError:
        print("Installing deep-translator…")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "deep-translator"], check=True)
        from deep_translator import GoogleTranslator
        return GoogleTranslator(source='en', target='zh-CN')

# ── TRANSLATE HELPERS ────────────────────────────────────────────────────────

def split_into_chunks(text: str, max_len: int = CHUNK_SIZE) -> list[str]:
    """Split text into chunks <= max_len at sentence boundaries."""
    if len(text) <= max_len:
        return [text]
    sentences = []
    buf = ""
    for char in text:
        buf += char
        if char in '.!?' and len(buf) > 50:
            sentences.append(buf)
            buf = ""
    if buf.strip():
        sentences.append(buf)

    chunks, cur = [], ""
    for s in sentences:
        if len(cur) + len(s) > max_len:
            if cur:
                chunks.append(cur.strip())
            cur = s
        else:
            cur += s
    if cur.strip():
        chunks.append(cur.strip())
    return chunks or [text[:max_len]]


def translate_text(translator, text: str) -> str:
    """Translate text, handling long content by chunking."""
    if not text or len(text.strip()) < 5:
        return text
    chunks = split_into_chunks(text)
    results = []
    for chunk in chunks:
        for attempt in range(3):
            try:
                result = translator.translate(chunk)
                if result:
                    results.append(result)
                break
            except Exception as e:
                if attempt == 2:
                    print(f"      [WARN] Translation failed after 3 tries: {e}")
                    results.append("")  # empty placeholder
                else:
                    time.sleep(2 ** attempt)  # exponential backoff
        time.sleep(0.3)
    return " ".join(r for r in results if r)


# ── MAIN ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Translate Dan Koe articles to Chinese")
    parser.add_argument("--reset", action="store_true", help="Clear existing translations and redo all")
    args = parser.parse_args()

    if not ARTICLES_DIR.exists():
        print("[ERROR] Articles directory not found. Run build_data.py first.")
        sys.exit(1)

    article_files = sorted(ARTICLES_DIR.glob("*.json"))
    if not article_files:
        print("[ERROR] No article JSON files found.")
        sys.exit(1)

    translator = get_translator()

    total = len(article_files)
    already_done = sum(
        1 for f in article_files
        if json.loads(f.read_text(encoding="utf-8")).get("translated")
    )

    print(f"\n  Dan Koe Knowledge Base – Translation")
    print(f"  {'─' * 42}")
    print(f"  Total articles : {total}")
    print(f"  Already done   : {already_done}")
    print(f"  To translate   : {total - already_done if not args.reset else total}")
    print(f"\n  Progress is saved after each article.")
    print(f"  You can safely interrupt (Ctrl+C) and resume later.\n")

    translated_count = 0

    for idx, article_path in enumerate(article_files, 1):
        article = json.loads(article_path.read_text(encoding="utf-8"))
        title = article.get("title", article_path.stem)

        if article.get("translated") and not args.reset:
            print(f"  [{idx:3}/{total}] SKIP  {title[:55]}")
            continue

        if args.reset:
            for s in article.get("sections", []):
                s.pop("content_zh", None)
            article.pop("translated", None)

        print(f"  [{idx:3}/{total}] ···   {title[:55]}")
        sections = article.get("sections", [])
        any_change = False

        for si, section in enumerate(sections, 1):
            content = section.get("content", "")
            if not content or (section.get("content_zh") and not args.reset):
                continue

            print(f"           ↳ Section {si}/{len(sections)}: {section['title'][:40]}…")
            zh = translate_text(translator, content)
            section["content_zh"] = zh
            any_change = True
            time.sleep(DELAY_SECTION)

        if any_change:
            article["translated"] = True
            article_path.write_text(
                json.dumps(article, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            translated_count += 1
            print(f"           ✓ Saved.")
        else:
            print(f"           – Nothing to translate.")

        time.sleep(DELAY_ARTICLE)

    print(f"\n  {'─' * 42}")
    print(f"  Done. {translated_count} articles translated this run.")
    print(f"  Refresh the knowledge base in your browser to see Chinese content.\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Interrupted. Progress has been saved. Run again to continue.\n")
