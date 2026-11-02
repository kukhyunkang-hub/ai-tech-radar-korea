#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Tech Radar Korea — Static Directory Builder (build_site.py)
--------------------------------------------------------------
Loads the latest tool dataset from `outputs/directory/*.json` and
partner links from `web/affiliate-config.json`, then injects
`AFFILIATE_CONFIG`, `BUILD_META`, and `TOOLS_DB` into `web/index.html`.
"""

import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DIRECTORY_DATA_DIR = BASE_DIR / "outputs" / "directory"
AFFILIATE_CONFIG_PATH = BASE_DIR / "web" / "affiliate-config.json"
INDEX_HTML_PATH = BASE_DIR / "web" / "index.html"


def load_latest_tools_db() -> list[dict]:
    """Load and merge the latest tools-db-*.json files in outputs/directory/."""
    if not DIRECTORY_DATA_DIR.exists():
        raise FileNotFoundError(f"Directory data folder not found: {DIRECTORY_DATA_DIR}")

    json_files = sorted(DIRECTORY_DATA_DIR.glob("*.json"))
    if not json_files:
        raise FileNotFoundError(f"No JSON files found in {DIRECTORY_DATA_DIR}")

    merged_by_id: dict[str, dict] = {}
    for jf in json_files:
        with jf.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "id" in item:
                        merged_by_id[item["id"]] = item
            elif isinstance(item := data, dict) and "id" in item:
                merged_by_id[item["id"]] = item

    return list(merged_by_id.values())


def load_affiliate_links() -> dict[str, str]:
    """Load partner URL map from web/affiliate-config.json."""
    if not AFFILIATE_CONFIG_PATH.exists():
        raise FileNotFoundError(f"Affiliate config file not found: {AFFILIATE_CONFIG_PATH}")

    with AFFILIATE_CONFIG_PATH.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    links = raw.get("links", raw) if isinstance(raw, dict) else {}
    return {k: v for k, v in links.items() if not k.startswith("_") and isinstance(v, str)}


def sync_index_html(tools_data: list[dict], affiliate_links: dict[str, str]) -> None:
    """Replace AFFILIATE_CONFIG, BUILD_META, and TOOLS_DB blocks inside web/index.html."""
    if not INDEX_HTML_PATH.exists():
        raise FileNotFoundError(f"Target HTML file not found: {INDEX_HTML_PATH}")

    html_content = INDEX_HTML_PATH.read_text(encoding="utf-8")

    kst = timezone(timedelta(hours=9))
    now_iso = datetime.now(kst).isoformat(timespec="seconds")

    build_meta_obj = {
        "edition": "2026년 11월 최신 공식 가격표 기준",
        "verified_by": "AI Tech Radar Korea 리서치랩 공식 과금 검증",
        "last_built_at": now_iso,
        "tool_count": len(tools_data),
        "category_count": 3,
    }

    affiliate_block = (
        "/* __AFFILIATE_CONFIG_START__ */\n"
        f"    const AFFILIATE_CONFIG = {json.dumps(affiliate_links, ensure_ascii=False, separators=(',', ':'))};\n"
        "    /* __AFFILIATE_CONFIG_END__ */"
    )

    build_meta_block = (
        "/* __BUILD_META_START__ */\n"
        f"    const BUILD_META = {json.dumps(build_meta_obj, ensure_ascii=False, separators=(',', ':'))};\n"
        "    /* __BUILD_META_END__ */"
    )

    tools_db_block = (
        "/* __TOOLS_DB_START__ */\n"
        f"    const TOOLS_DB = {json.dumps(tools_data, ensure_ascii=False, separators=(',', ':'))};\n"
        "    /* __TOOLS_DB_END__ */"
    )

    updated_html, aff_subs = re.subn(
        r"/\*\s*__AFFILIATE_CONFIG_START__\s*\*/.*?/\*\s*__AFFILIATE_CONFIG_END__\s*\*/",
        lambda _: affiliate_block,
        html_content,
        flags=re.DOTALL,
    )

    updated_html, meta_subs = re.subn(
        r"/\*\s*__BUILD_META_START__\s*\*/.*?/\*\s*__BUILD_META_END__\s*\*/",
        lambda _: build_meta_block,
        updated_html,
        flags=re.DOTALL,
    )

    updated_html, db_subs = re.subn(
        r"/\*\s*__TOOLS_DB_START__\s*\*/.*?/\*\s*__TOOLS_DB_END__\s*\*/",
        lambda _: tools_db_block,
        updated_html,
        flags=re.DOTALL,
    )

    if db_subs == 0:
        raise RuntimeError("Could not find /* __TOOLS_DB_START__ */ marker in index.html")
    if aff_subs == 0:
        raise RuntimeError("Could not find /* __AFFILIATE_CONFIG_START__ */ marker in index.html")

    INDEX_HTML_PATH.write_text(updated_html, encoding="utf-8")
    print(f"[build_site.py] Synced {len(tools_data)} tools and {len(affiliate_links)} partner links into '{INDEX_HTML_PATH.name}'.")
    print(f"[build_site.py] Build timestamp: {now_iso}")


def main() -> None:
    tools_data = load_latest_tools_db()
    affiliate_links = load_affiliate_links()
    sync_index_html(tools_data, affiliate_links)


if __name__ == "__main__":
    main()
