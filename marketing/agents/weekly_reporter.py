#!/usr/bin/env python3
"""
Weekly Reporter Agent for Novicado Materials.
Collects the week's content, analyzes quality via DeepSeek, produces a report,
and sends a summary to the Product Owner via Telegram.

Usage:
    python marketing/agents/weekly_reporter.py
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# ── Load .env from project root (regardless of current working directory) ─
ROOT = Path(__file__).resolve().parent.parent.parent  # project root
load_dotenv(ROOT / ".env")

# ── Paths ──────────────────────────────────────────────────────────────
MARKETING_DIR = ROOT / "marketing"
BLOG_DIR = MARKETING_DIR / "blog"
TELEGRAM_DIR = MARKETING_DIR / "telegram"
IMAGES_DIR = MARKETING_DIR / "images"
REPORTS_DIR = MARKETING_DIR / "reports"
LOG_PATH = REPORTS_DIR / "scheduler.log"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ── DeepSeek client ────────────────────────────────────────────────────
client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
)

# ── Time window: last 7 days ───────────────────────────────────────────
NOW = datetime.now()
WEEK_AGO = NOW - timedelta(days=7)


# ═══════════════════════════════════════════════════════════════════════
#  Collectors
# ═══════════════════════════════════════════════════════════════════════


def _collect_files(dir_path: Path, extensions: tuple[str, ...]) -> list[Path]:
    """Return files in dir_path matching extensions, modified within the last week."""
    if not dir_path.exists():
        return []
    files = []
    for f in dir_path.iterdir():
        if f.is_file() and f.name != ".gitkeep" and f.suffix in extensions:
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            if mtime >= WEEK_AGO:
                files.append(f)
    return sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)


def _read_content(file_path: Path) -> str:
    """Read the first 3000 characters of a file for analysis."""
    try:
        text = file_path.read_text(encoding="utf-8")
        return text[:3000]
    except Exception:
        return "(could not read)"


def _collect_week_data() -> dict:
    """Gather all content produced this week."""
    articles = _collect_files(BLOG_DIR, (".md",))
    posts = _collect_files(TELEGRAM_DIR, (".md",))
    images = _collect_files(IMAGES_DIR, (".png", ".jpg", ".jpeg", ".webp", ".gif"))

    # Read article content for analysis (first 3000 chars each)
    article_texts = [(a.name, _read_content(a)) for a in articles]

    # Read post content for analysis
    post_texts = [(p.name, _read_content(p)) for p in posts]

    # Recent log lines
    log_lines = ""
    if LOG_PATH.exists():
        all_log_lines = LOG_PATH.read_text(encoding="utf-8").strip().split("\n")
        log_lines = "\n".join(all_log_lines[-20:])

    return {
        "articles": articles,
        "posts": posts,
        "images": images,
        "article_texts": article_texts,
        "post_texts": post_texts,
        "log_lines": log_lines,
        "article_count": len(articles),
        "post_count": len(posts),
        "image_count": len(images),
    }


# ═══════════════════════════════════════════════════════════════════════
#  DeepSeek analysis
# ═══════════════════════════════════════════════════════════════════════

ANALYSIS_SYSTEM = """\
You are a content strategist reviewing a week's worth of marketing content for
an AI school called Novicado Materials. You provide honest, constructive analysis.

Rules:
- Be specific: name actual topics, not generic praise.
- If content is missing or sparse, say so directly.
- Output ONLY valid Markdown — no preamble, no signature.
- Use the exact heading structure requested."""

ANALYSIS_PROMPT = """\
Review this week's content for Novicado Materials (AI school marketing).

Stats:
- Articles published: {article_count}
- Telegram posts published: {post_count}
- Images generated: {image_count}

Article content:

{article_content}

---

Telegram post content:

{post_content}

---

Recent activity log:

{log}

---

Provide your analysis using EXACTLY this structure:

### Best Topics
- Which topics performed strongest? Why?
- What resonated? Be specific with titles/themes.

### Weak Topics
- Which topics underperformed or were missing? Why?
- What gaps exist in the content mix?

### Recommendations for Next Week
- 3-5 specific, actionable recommendations
- Include: what to write about, what to stop, what to try
"""


def _analyze_content(data: dict) -> str:
    """Send collected content to DeepSeek for quality analysis."""
    # Build article content summary
    article_sections = []
    for name, text in data["article_texts"]:
        article_sections.append(f"### {name}\n{text}\n")
    article_content = (
        "\n".join(article_sections) if article_sections else "(no articles this week)"
    )

    # Build post content summary
    post_sections = []
    for name, text in data["post_texts"]:
        post_sections.append(f"### {name}\n{text}\n")
    post_content = "\n".join(post_sections) if post_sections else "(no posts this week)"

    print("[Reporter] Sending content to DeepSeek for analysis...")
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": ANALYSIS_SYSTEM},
            {
                "role": "user",
                "content": ANALYSIS_PROMPT.format(
                    article_count=data["article_count"],
                    post_count=data["post_count"],
                    image_count=data["image_count"],
                    article_content=article_content,
                    post_content=post_content,
                    log=data["log_lines"],
                ),
            },
        ],
        temperature=0.5,
        max_tokens=1500,
    )
    return response.choices[0].message.content


# ═══════════════════════════════════════════════════════════════════════
#  Report generation
# ═══════════════════════════════════════════════════════════════════════


def _build_report(data: dict, analysis: str) -> str:
    """Assemble the full weekly report."""
    start = WEEK_AGO.strftime("%B %d")
    end = NOW.strftime("%B %d, %Y")

    # File list
    article_list = ""
    for a in data["articles"]:
        mtime = datetime.fromtimestamp(a.stat().st_mtime).strftime("%Y-%m-%d")
        size_kb = a.stat().st_size / 1024
        article_list += f"- {a.name} ({size_kb:.1f} KB, {mtime})\n"

    post_list = ""
    for p in data["posts"]:
        mtime = datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d")
        size_kb = p.stat().st_size / 1024
        post_list += f"- {p.name} ({size_kb:.1f} KB, {mtime})\n"

    image_list = ""
    for img in data["images"]:
        mtime = datetime.fromtimestamp(img.stat().st_mtime).strftime("%Y-%m-%d")
        image_list += f"- {img.name} ({mtime})\n"

    report = f"""# Weekly Report ({start} — {end})

## Created

### Articles: {data["article_count"]}
{article_list or "(none this week)"}

### Telegram Posts: {data["post_count"]}
{post_list or "(none this week)"}

### Images: {data["image_count"]}
{image_list or "(none this week)"}

---

## Analysis

{analysis}

---

_Report generated {NOW.strftime("%Y-%m-%d %H:%M")} by weekly_reporter.py_
"""
    return report


# ═══════════════════════════════════════════════════════════════════════
#  Telegram delivery
# ═══════════════════════════════════════════════════════════════════════


async def _send_telegram_summary(data: dict, analysis: str):
    """Send a brief summary to the Product Owner via Telegram."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    owner_id = os.environ.get("MY_TELEGRAM_USER_ID", "").strip()

    if not token or not owner_id:
        print(
            "[Reporter] WARNING: TELEGRAM_BOT_TOKEN or MY_TELEGRAM_USER_ID not set — skipping Telegram send"
        )
        return

    try:
        from telegram import Bot
    except ImportError:
        print(
            "[Reporter] WARNING: python-telegram-bot not installed — skipping Telegram send"
        )
        return

    # Extract first recommendation line as a teaser
    rec_lines = []
    in_rec = False
    for line in analysis.split("\n"):
        if "Recommendations" in line:
            in_rec = True
            continue
        if in_rec and line.startswith("###"):
            break
        if in_rec and line.strip().startswith("-"):
            rec_lines.append(line.strip())

    rec_text = "\n".join(rec_lines[:3]) if rec_lines else "(see full report)"

    start = WEEK_AGO.strftime("%b %d")
    end = NOW.strftime("%b %d")

    summary = (
        f"📊 *Weekly Report*  ({start} — {end})\n\n"
        f"📝 Articles: {data['article_count']}\n"
        f"💬 Telegram posts: {data['post_count']}\n"
        f"🖼️ Images: {data['image_count']}\n\n"
        f"*Top recommendations:*\n{rec_text}\n\n"
        f"_Full report saved to marketing/reports/_"
    )

    bot = Bot(token=token)
    await bot.send_message(
        chat_id=int(owner_id),
        text=summary,
        parse_mode="Markdown",
    )
    print("[Reporter] Telegram summary sent to Product Owner")


# ═══════════════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════════════


def main():
    print("══════════════════════════════════════════════")
    print("  📊  Weekly Reporter")
    print(f"  Window: {WEEK_AGO.strftime('%Y-%m-%d')} → {NOW.strftime('%Y-%m-%d')}")
    print("══════════════════════════════════════════════\n")

    # 1. Collect
    print("[Reporter] Collecting this week's content...")
    data = _collect_week_data()
    print(f"  Articles: {data['article_count']}")
    print(f"  Posts:    {data['post_count']}")
    print(f"  Images:   {data['image_count']}")

    # 2. Analyze
    analysis = _analyze_content(data)
    print(f"  Analysis: {len(analysis)} chars")

    # 3. Build and save report
    report = _build_report(data, analysis)
    report_path = REPORTS_DIR / f"weekly-{NOW.strftime('%Y-%m-%d')}.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"\n[Reporter] Full report saved → {report_path}")

    # 4. Send Telegram summary
    print("[Reporter] Sending Telegram summary...")
    asyncio.run(_send_telegram_summary(data, analysis))

    print("\n[Reporter] Done!")


if __name__ == "__main__":
    main()
