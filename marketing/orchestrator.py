#!/usr/bin/env python3
"""
Orchestrator — runs all marketing agents in sequence, with an optional scheduler
for daily/weekly automated content generation and publishing.

Usage:
    python marketing/orchestrator.py               # run all agents once
    python marketing/orchestrator.py --schedule    # start the scheduler
"""

import argparse
import asyncio
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlretrieve

from dotenv import load_dotenv

# ── Load .env from project root (regardless of current working directory) ─
ROOT = Path(__file__).resolve().parent.parent  # project root
load_dotenv(ROOT / ".env")

AGENTS_DIR = ROOT / "marketing" / "agents"
IMAGES_DIR = ROOT / "marketing" / "images"

# Ensure images directory exists
IMAGES_DIR.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════
#  Run-once: execute all agents in sequence
# ═══════════════════════════════════════════════════════════════════════

AGENTS = [
    {
        "script": "cmo_agent.py",
        "label": "CMO Agent: creating strategy...",
        "output": "MARKETING_PLAN.md",
    },
    {
        "script": "seo_agent.py",
        "label": "SEO Agent: finding keywords...",
        "output": "SEO_KEYWORDS.md",
    },
    {
        "script": "content_writer.py",
        "label": "Content Writer: generating articles + posts + images...",
        "output": "2 articles, 2 posts, 2 images",
    },
    {
        "script": "telegram_agent.py",
        "label": "Telegram Agent: creating content calendar + publishing...",
        "output": "TELEGRAM_CONTENT_CALENDAR.md",
    },
]


def run_all_agents():
    """Run every agent script in order, printing progress for each."""
    print("══════════════════════════════════════════════")
    print("  Novicado Marketing Pipeline")
    print("══════════════════════════════════════════════\n")

    for agent in AGENTS:
        script_path = AGENTS_DIR / agent["script"]
        if not script_path.exists():
            print(f"  ✗ SKIPPED: {agent['script']} not found")
            continue

        print(f"  ▶ {agent['label']}")
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"  ✗ FAILED (exit code {result.returncode})")
            print(f"  stderr: {result.stderr.strip()[:300]}")
        else:
            print(f"  ✓ Done → {agent['output']}")
        print()

    print("Done! All files created and content published.")


# ═══════════════════════════════════════════════════════════════════════
#  Scheduler: background tasks for daily/weekly content
# ═══════════════════════════════════════════════════════════════════════


def _get_deepseek_client():
    """Lazy-init the DeepSeek client for scheduled tasks."""
    from openai import OpenAI

    return OpenAI(
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url="https://api.deepseek.com",
    )


def _generate_post_text(client, post_type: str) -> str:
    """Generate a short Telegram post via DeepSeek."""
    prompts = {
        "morning": (
            "You write short Telegram posts for an AI school audience. "
            "Write an educational post (150-250 words) about AI development "
            "tools, tips, or techniques. Use Telegram-friendly formatting: "
            "emoji, short paragraphs, no markdown headings. "
            "Be practical and encouraging. End with a question to spark "
            "discussion."
        ),
        "evening": (
            "You write short Telegram posts for an AI school audience. "
            "Write a personal/reflective post (150-250 words) about building "
            "with AI — share a lesson learned, a small win, or a behind-the-"
            'scenes thought. "Building in public" style. Use Telegram-friendly '
            "formatting: emoji, short paragraphs. Be honest and relatable."
        ),
    }

    system = prompts.get(post_type, prompts["morning"])
    user = (
        f"Write a {post_type} Telegram post for Novicado Materials, an AI school "
        f"that teaches developers to build with AI tools (Zed, DeepSeek, GitHub, "
        f"fly.io, Supabase). Today is {datetime.now().strftime('%A, %B %d, %Y')}."
    )

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.8,
        max_tokens=600,
    )
    return response.choices[0].message.content


def _generate_image_for_post(client, post_text: str) -> Path:
    """Generate an image for a post via DeepSeek description → Pollinations.ai."""
    # Get image description from DeepSeek
    img_response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": (
                    "Describe an image for a Telegram post. One paragraph, "
                    "20-40 words, plain English. Describe only the visual scene — "
                    "no text overlays. Focus on subject, colors, mood, composition."
                ),
            },
            {
                "role": "user",
                "content": f"Describe an image for this post:\n\n{post_text[:500]}",
            },
        ],
        temperature=0.8,
        max_tokens=100,
    )
    img_prompt = img_response.choices[0].message.content
    print(f"     Image prompt: {img_prompt[:80]}...")

    # Generate via Pollinations.ai
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    img_path = IMAGES_DIR / f"auto-{timestamp}.png"

    encoded = quote(img_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=800&height=400"

    try:
        urlretrieve(url, img_path)
        print(f"     Image saved → {img_path}")
        return img_path
    except Exception as e:
        print(f"     Pollinations.ai failed: {e} — using fallback")
        return _fallback_image(img_prompt, img_path)


def _fallback_image(prompt: str, save_path: Path) -> Path:
    """Generate a simple colored Pillow image."""
    try:
        import colorsys

        from PIL import Image, ImageDraw

        hue = hash(prompt) % 360
        r, g, b = colorsys.hsv_to_rgb(hue / 360, 0.3, 0.9)
        rgb = (int(r * 255), int(g * 255), int(b * 255))

        img = Image.new("RGB", (800, 400), rgb)
        draw = ImageDraw.Draw(img)
        draw.text((20, 180), "Novicado Materials", fill=(255, 255, 255))
        img.save(save_path, "PNG")
        print(f"     Fallback image saved → {save_path}")
        return save_path
    except ImportError:
        print("     Pillow not installed — skipping image.")
        return save_path  # won't exist, but path is returned


async def _publish_to_telegram(text: str, image_path: Path | None = None):
    """Publish a post to the Telegram channel."""
    try:
        from telegram import Bot
    except ImportError:
        print("     ERROR: python-telegram-bot not installed")
        return

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    channel = os.environ.get("TELEGRAM_CHANNEL_ID", "").strip()

    if not token or not channel:
        print(
            f"     WARNING: TELEGRAM_BOT_TOKEN or TELEGRAM_CHANNEL_ID not set — skipping publish"
        )
        return

    bot = Bot(token=token)

    if image_path and image_path.is_file():
        with open(image_path, "rb") as photo:
            await bot.send_photo(
                chat_id=channel,
                photo=photo,
                caption=text,
                parse_mode="HTML",
            )
        print(f"     Published photo + caption → {channel}")
    else:
        await bot.send_message(
            chat_id=channel,
            text=text,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
        print(f"     Published message → {channel}")


def _log_to_file(message: str):
    """Append a timestamped log entry."""
    log_path = ROOT / "marketing" / "reports" / "scheduler.log"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a") as f:
        f.write(f"[{timestamp}] {message}\n")


# ── Scheduled tasks ────────────────────────────────────────────────────


def scheduled_morning_post():
    """Generate and publish a morning Telegram post (educational)."""
    print(f"\n{'=' * 50}")
    print(f"  ☀️  Morning post — {datetime.now().strftime('%H:%M')}")
    print(f"{'=' * 50}")
    try:
        client = _get_deepseek_client()
        text = _generate_post_text(client, "morning")
        print(f"     Generated: {text[:100]}...")
        img = _generate_image_for_post(client, text)
        asyncio.run(_publish_to_telegram(text, img))
        _log_to_file("Morning post published")
    except Exception as e:
        print(f"     ERROR: {e}")
        _log_to_file(f"Morning post FAILED: {e}")


def scheduled_evening_post():
    """Generate and publish an evening Telegram post (personal/reflective)."""
    print(f"\n{'=' * 50}")
    print(f"  🌙  Evening post — {datetime.now().strftime('%H:%M')}")
    print(f"{'=' * 50}")
    try:
        client = _get_deepseek_client()
        text = _generate_post_text(client, "evening")
        print(f"     Generated: {text[:100]}...")
        img = _generate_image_for_post(client, text)
        asyncio.run(_publish_to_telegram(text, img))
        _log_to_file("Evening post published")
    except Exception as e:
        print(f"     ERROR: {e}")
        _log_to_file(f"Evening post FAILED: {e}")


def scheduled_weekly_article():
    """Run the content writer agent to generate a new article."""
    print(f"\n{'=' * 50}")
    print(f"  📝  Weekly article — {datetime.now().strftime('%A %H:%M')}")
    print(f"{'=' * 50}")
    try:
        script = AGENTS_DIR / "content_writer.py"
        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("     Article generated successfully")
            _log_to_file("Weekly article generated")
        else:
            print(f"     FAILED: {result.stderr.strip()[:200]}")
            _log_to_file(f"Weekly article FAILED: {result.stderr.strip()[:200]}")
    except Exception as e:
        print(f"     ERROR: {e}")
        _log_to_file(f"Weekly article FAILED: {e}")


def start_scheduler():
    """Start the schedule loop — runs until interrupted."""
    try:
        import schedule as schedule_lib
    except ImportError:
        print("ERROR: 'schedule' library is not installed.")
        print("Run: pip install schedule")
        sys.exit(1)

    schedule_lib.every().day.at("09:00").do(scheduled_morning_post)
    schedule_lib.every().day.at("19:00").do(scheduled_evening_post)
    schedule_lib.every().monday.at("09:00").do(scheduled_weekly_article)

    print("══════════════════════════════════════════════")
    print("  ⏰  Scheduler started")
    print("  ☀️  09:00 daily  — morning Telegram post")
    print("  🌙  19:00 daily  — evening Telegram post")
    print("  📝  Mon 09:00    — weekly article")
    print("  Press Ctrl+C to stop")
    print("══════════════════════════════════════════════\n")

    _log_to_file("Scheduler started")

    while True:
        schedule_lib.run_pending()
        time.sleep(30)


# ═══════════════════════════════════════════════════════════════════════
#  Entry point
# ═══════════════════════════════════════════════════════════════════════


def main():
    parser = argparse.ArgumentParser(description="Novicado Marketing Orchestrator")
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Start the scheduler for daily/weekly automated publishing",
    )
    args = parser.parse_args()

    if args.schedule:
        start_scheduler()
    else:
        run_all_agents()


if __name__ == "__main__":
    main()
