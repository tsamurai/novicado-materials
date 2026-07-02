#!/usr/bin/env python3
"""
Telegram Agent for Novicado Materials.
Generates a weekly content calendar, long-form posts, and AI images,
then publishes to a Telegram channel via python-telegram-bot.

Usage:
    python telegram_agent.py                 # generate calendar + images only
    python telegram_agent.py --publish-one   # send 1 test post to the channel
"""

import argparse
import asyncio
import os
import sys
import time
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlretrieve

from dotenv import load_dotenv
from openai import OpenAI

# ── Load .env from project root (regardless of current working directory) ─
ROOT = Path(__file__).resolve().parent.parent.parent  # project root
load_dotenv(ROOT / ".env")

# ── Paths ──────────────────────────────────────────────────────────────
PLAN_PATH = ROOT / "marketing" / "MARKETING_PLAN.md"
CALENDAR_OUTPUT = ROOT / "marketing" / "TELEGRAM_CONTENT_CALENDAR.md"
IMAGES_DIR = ROOT / "marketing" / "images"

# ── DeepSeek client ────────────────────────────────────────────────────
client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
)

# ── System prompts ─────────────────────────────────────────────────────
CALENDAR_SYSTEM = """\
You are a Telegram content strategist for Novicado Materials, an AI school.
You create structured weekly content calendars for a Telegram channel.

Rules:
- Output ONLY valid Markdown — no preamble, no signature.
- Start directly with a level-2 heading: ## 7-Day Content Calendar
- Each post entry must include: day, time slot (morning/afternoon/evening),
  type (educational/news/personal/product), topic, and a short draft (2-3 sentences).
- Content mix: 40% educational, 30% industry news/insights, 20% personal build
  thoughts, 10% direct product mentions.
- Total: 21 posts (3 per day × 7 days)."""

LONGFORM_SYSTEM = """\
You write engaging long-form Telegram posts for an AI school audience.
Each post is 400-600 words, uses Telegram-friendly formatting (emoji, line breaks,
no markdown headings), and ends with a soft call-to-action.

Output ONLY the post text — no preamble."""

IMAGE_SYSTEM = """\
You describe images for AI generation. Given a post topic, describe a clean,
modern illustration for a Telegram channel header image.

Rules:
- One paragraph of plain English, 20–40 words.
- Describe ONLY the visual scene — no text overlays, no words on the image.
- Focus on: subject, colors, mood, composition.
- Output the description only — no preamble, no quotes."""

# ── Prompts ────────────────────────────────────────────────────────────
CALENDAR_PROMPT = """\
Based on this marketing plan, create a 7-day Telegram content calendar with
21 posts (3 per day: morning, afternoon, evening).

Content mix:
- 40% educational (tips, how-tos, tool comparisons)
- 30% industry news/insights (AI trends, tool launches, what's happening)
- 20% personal build thoughts (behind-the-scenes, lessons learned, building in public)
- 10% direct product mentions (course highlights, materials, sign-up calls)

Format:

## 7-Day Content Calendar

### Day 1 — Monday

| Slot | Type | Topic | Draft |
|------|------|-------|-------|
| Morning | educational | ... | ... |
| Afternoon | news | ... | ... |
| Evening | personal | ... | ... |

(Repeat for all 7 days, Monday–Sunday)

---

Marketing plan:

{plan}
"""

LONGFORM_1_PROMPT = """\
Write a long-form Telegram post (400-600 words) for an AI school audience.

Topic: "The 6 tools every AI developer needs in 2026 — and how to set them up
in one afternoon."

Tone: practical, encouraging, slightly personal. Include specific tool names:
Zed, DeepSeek, GitHub, fly.io, Supabase.

Format for Telegram:
- Use emoji for section breaks
- Short paragraphs (2-3 sentences max)
- No markdown headings
- End with: "🚀 Want the full step-by-step guide with templates? Join Novicado."

Marketing context:

{plan}
"""

LONGFORM_2_PROMPT = """\
Write a long-form Telegram post (400-600 words) for an AI school audience.

Topic: "What I learned building and deploying a full-stack app with AI — in 3 hours
and for $0."

Tone: honest, personal, "building in public" style. Mention that the app itself
(Novicado Materials) was built with these tools as proof.

Format for Telegram:
- Use emoji for section breaks
- Short paragraphs (2-3 sentences max)
- No markdown headings
- End with: "🔗 See the full curriculum and start building: [link]"

Marketing context:

{plan}
"""


# ── Helpers ────────────────────────────────────────────────────────────
def read_file(path: Path, label: str) -> str:
    """Read a file if it exists, return empty string with a warning otherwise."""
    if path.exists():
        content = path.read_text(encoding="utf-8")
        print(f"   [{label}] {len(content)} chars")
        return content
    print(f"   [{label}] WARNING: not found, continuing without it")
    return ""


def call_deepseek(system: str, user: str, temperature: float, max_tokens: int) -> str:
    """Call DeepSeek and return the response text."""
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


def generate_image(prompt: str, save_path: Path) -> str:
    """
    Generate an image via Pollinations.ai.
    Falls back to a colored Pillow image if generation fails.
    Returns the local file path.
    """
    encoded = quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=800&height=400"

    print(f"   Downloading image from Pollinations.ai...")
    try:
        urlretrieve(url, save_path)
        print(f"   Image saved → {save_path}")
        return str(save_path)
    except Exception as e:
        print(f"   Pollinations.ai failed: {e}")
        print(f"   Generating fallback image via Pillow...")
        return _generate_fallback_image(prompt, save_path)


def _generate_fallback_image(prompt: str, save_path: Path) -> str:
    """Generate a simple colored rectangle with Pillow as a fallback."""
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
        print(f"   Fallback image saved → {save_path}")
        return str(save_path)
    except ImportError:
        print("   Pillow not installed — skipping image fallback.")
        return "(image unavailable)"


# ── Telegram publishing (async) ────────────────────────────────────────
def _get_bot():
    """Import and return a Telegram Bot instance. Lazy-imported."""
    try:
        from telegram import Bot
    except ImportError:
        print("ERROR: python-telegram-bot is not installed.")
        print("Run: pip install python-telegram-bot")
        sys.exit(1)

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print("ERROR: TELEGRAM_BOT_TOKEN is not set in .env")
        sys.exit(1)
    return Bot(token=token)


def _get_channel_id() -> str:
    """Get the channel ID from .env. Accepts @username or numeric IDs."""
    channel = os.environ.get("TELEGRAM_CHANNEL_ID", "").strip()
    if not channel:
        print("ERROR: TELEGRAM_CHANNEL_ID is not set in .env")
        sys.exit(1)
    return channel


async def _publish_one_test_post():
    """Publish exactly ONE test post to the channel to verify end-to-end."""
    bot = _get_bot()
    channel = _get_channel_id()
    print(f"[Telegram] Publishing test post to channel: {channel}")

    test_text = (
        "🤖 *Novicado Materials — Test Post*\n\n"
        "This is an automated test from the Telegram agent. "
        "If you see this, the bot is connected and publishing correctly.\n\n"
        "_— The Novicado AI team_"
    )

    await bot.send_message(
        chat_id=channel,
        text=test_text,
        parse_mode="Markdown",
    )
    print("[Telegram] Test post sent successfully!")


async def _publish_post(text: str, image_path: str | None = None):
    """Publish a post (text + optional image) to the channel."""
    bot = _get_bot()
    channel = _get_channel_id()

    if image_path and os.path.isfile(image_path):
        # Send photo with caption
        with open(image_path, "rb") as photo:
            await bot.send_photo(
                chat_id=channel,
                photo=photo,
                caption=text,
                parse_mode="HTML",
            )
        print(f"[Telegram] Sent photo + caption to {channel}")
    else:
        await bot.send_message(
            chat_id=channel,
            text=text,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
        print(f"[Telegram] Sent message to {channel}")


# ── Main pipeline ──────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Novicado Telegram Agent")
    parser.add_argument(
        "--publish-one",
        action="store_true",
        help="Send one test post to the Telegram channel (skip calendar generation)",
    )
    args = parser.parse_args()

    # ── Publish-one mode (quick test) ──────────────────────────────────
    if args.publish_one:
        print("[Telegram] --publish-one mode: sending test post...")
        asyncio.run(_publish_one_test_post())
        return

    # ── Full pipeline ──────────────────────────────────────────────────
    print("[Telegram] Reading marketing plan...")
    plan = read_file(PLAN_PATH, "Marketing plan")

    # Step 1: Generate content calendar
    print("[Telegram] Generating 7-day content calendar (21 posts)...")
    calendar = call_deepseek(
        CALENDAR_SYSTEM, CALENDAR_PROMPT.format(plan=plan), 0.7, 4000
    )
    CALENDAR_OUTPUT.write_text(calendar, encoding="utf-8")
    print(f"   Calendar saved → {CALENDAR_OUTPUT} ({len(calendar)} chars)")

    time.sleep(1)

    # Step 2: Generate long-form posts
    longform_prompts = [
        ("six-tools", LONGFORM_1_PROMPT),
        ("build-in-3-hours", LONGFORM_2_PROMPT),
    ]

    longform_texts: list[str] = []
    for slug, prompt_template in longform_prompts:
        print(f"[Telegram] Generating long-form post: {slug}...")
        post = call_deepseek(
            LONGFORM_SYSTEM, prompt_template.format(plan=plan), 0.7, 2000
        )
        longform_texts.append(post)
        print(f"   Post ({slug}): {len(post)} chars")
        time.sleep(1)

    # Step 3: Generate images for long-form posts
    image_paths: list[str] = []
    for idx, post_text in enumerate(longform_texts):
        print(f"[Telegram] Generating image for long-form post {idx + 1}...")
        img_prompt = call_deepseek(
            IMAGE_SYSTEM,
            f"Describe an image for this Telegram post:\n\n{post_text[:1000]}",
            0.8,
            150,
        )
        print(f"   Image prompt: {img_prompt[:80]}...")

        img_path = IMAGES_DIR / f"telegram-longform-{idx + 1}.png"
        result = generate_image(img_prompt, img_path)
        image_paths.append(result)

    # Step 4: Append long-form posts + images to the calendar doc
    longform_section = "\n\n---\n\n## Long-Form Posts\n\n"
    for idx, text in enumerate(longform_texts):
        longform_section += f"### Post {idx + 1}\n\n{text}\n\n"
        longform_section += f"![Image]({image_paths[idx]})\n\n"

    current = CALENDAR_OUTPUT.read_text(encoding="utf-8")
    CALENDAR_OUTPUT.write_text(current + longform_section, encoding="utf-8")

    # ── Done ───────────────────────────────────────────────────────────
    print()
    print("[Telegram] All done!")
    print(f"  Calendar: {CALENDAR_OUTPUT}")
    print(f"  Images: {image_paths}")
    print()
    print("To publish a test post: python telegram_agent.py --publish-one")
    print(
        "To publish a real post, call _publish_post(text, image_path) "
        "from your own script or add a --publish flag."
    )


if __name__ == "__main__":
    main()
