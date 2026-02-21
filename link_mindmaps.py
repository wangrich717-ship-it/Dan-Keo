#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 "Dan Keo 思维导图" 文件夹里的 PNG 文件
模糊匹配到对应的文章 JSON，复制到 danko-web/mindmaps/ 并写入 mindmap_img 字段。
"""

import json
import shutil
import re
import difflib
from pathlib import Path

SOURCE_IMGS = Path(__file__).parent.parent / "Dan Keo 思维导图"
MINDMAPS_DIR = Path(__file__).parent / "mindmaps"
ARTICLES_DIR = Path(__file__).parent / "data" / "articles"

MINDMAPS_DIR.mkdir(exist_ok=True)


def normalize(s: str) -> str:
    """统一化：小写、去掉非字母数字、空格压缩。"""
    s = s.lower()
    s = re.sub(r'[_\-]', ' ', s)
    s = re.sub(r'[^a-z0-9 ]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def strip_suffix(name: str) -> str:
    """去掉 PNG 文件名末尾的 _ima思维导图 之类的后缀（含乱码变体）。"""
    # 去掉扩展名
    name = Path(name).stem
    # 已知后缀模式：_ima思维导图 或 _ima??ͼ 等编码变体
    name = re.sub(r'[_ ]+ima.*$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'[_ ]+\S{0,8}[\u4e00-\u9fff]\S{0,8}$', '', name)
    return name.strip()


def main():
    png_files = list(SOURCE_IMGS.glob("*.png"))
    article_files = list(ARTICLES_DIR.glob("*.json"))

    print(f"PNG 文件：{len(png_files)}")
    print(f"文章 JSON：{len(article_files)}\n")

    # 构建文章查找表：normalized_title -> article_path
    articles = {}
    for af in article_files:
        data = json.loads(af.read_text(encoding='utf-8'))
        key = normalize(data['title'])
        articles[key] = (af, data)

    matched = 0
    unmatched = []

    for png in sorted(png_files):
        raw_name = strip_suffix(png.name)
        query = normalize(raw_name)

        # 精确匹配
        if query in articles:
            af, data = articles[query]
            best_key = query
            score = 1.0
        else:
            # 模糊匹配
            keys = list(articles.keys())
            matches = difflib.get_close_matches(query, keys, n=1, cutoff=0.55)
            if matches:
                best_key = matches[0]
                af, data = articles[best_key]
                score = difflib.SequenceMatcher(None, query, best_key).ratio()
            else:
                unmatched.append(png.name)
                continue

        # 复制图片到 mindmaps/{article_id}.png
        dest = MINDMAPS_DIR / f"{data['id']}.png"
        shutil.copy2(png, dest)

        # 写入 mindmap_img 字段
        data['mindmap_img'] = f"mindmaps/{data['id']}.png"
        af.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

        safe_title = data['title'][:50].encode('gbk', errors='replace').decode('gbk')
        safe_name  = raw_name[:50].encode('gbk', errors='replace').decode('gbk')
        print(f"  [{score:.2f}] {safe_name}")
        print(f"         -> {safe_title}")
        matched += 1

    print(f"\n{'='*50}")
    print(f"匹配成功：{matched} / {len(png_files)}")
    if unmatched:
        print(f"\nUnmatched PNGs ({len(unmatched)}):")
        for u in unmatched:
            print(f"  - {u[:70].encode('gbk', errors='replace').decode('gbk')}")


if __name__ == "__main__":
    main()
