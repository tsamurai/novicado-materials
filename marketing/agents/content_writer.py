#!/usr/bin/env python3
"""
Content Writer Agent for Novicado Materials.
Generates blog articles and Telegram posts using DeepSeek API,
with AI-generated images via Pollinations.ai (Pillow fallback).
"""

import os
import time
from pathlib import Path
from urllib.request import urlretrieve

from dotenv import load_dotenv
from openai import OpenAI

# ── Load .env from project root (regardless of current working directory) ─
ROOT = Path(__file__).resolve().parent.parent.parent  # project root
load_dotenv(ROOT / ".env")

# ── Paths ──────────────────────────────────────────────────────────────
PLAN_PATH = ROOT / "marketing" / "MARKETING_PLAN.md"
KEYWORDS_PATH = ROOT / "marketing" / "SEO_KEYWORDS.md"
BLOG_DIR = ROOT / "marketing" / "blog"
TELEGRAM_DIR = ROOT / "marketing" / "telegram"
IMAGES_DIR = ROOT / "marketing" / "images"

ARTICLE_PATHS = [BLOG_DIR / "article-1.md", BLOG_DIR / "article-2.md"]
POST_PATHS = [TELEGRAM_DIR / "post-1.md", TELEGRAM_DIR / "post-2.md"]
IMAGE_PATHS = [IMAGES_DIR / "article-1.png", IMAGES_DIR / "article-2.png"]

# ── DeepSeek client ────────────────────────────────────────────────────
client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
)

# ── System prompts ─────────────────────────────────────────────────────
ARTICLE_SYSTEM = """\
You are a senior content writer for an AI school called Novicado Materials.
You write clear, engaging, practical blog articles targeted at AI-curious
developers and technical beginners.

Rules:
- Write in clear English, conversational but professional.
- Naturally include relevant keywords from the provided keyword research.
- Output ONLY valid Markdown — no preamble, no "Here is the article".
- Each article must be 1500–2000 words.
- Include a compelling title as a level-1 heading (# Title).
- Use subheadings (##), bullet points, and one call-to-action at the end."""

TELEGRAM_SYSTEM = """\
You are a Telegram content writer. You adapt long-form articles into short,
engaging Telegram channel posts.

Rules:
- 200–300 words maximum.
- Use a hook in the first sentence.
- Use line breaks for readability on mobile.
- End with a link placeholder: [Read the full article →]
- Output ONLY the post text — no preamble, no markdown headings."""

IMAGE_SYSTEM = """\
You describe images for AI generation. Given an article's topic, describe a
clean, modern illustration that works as a blog header or Telegram post image.

Rules:
- One paragraph of plain English, 20–40 words.
- Describe ONLY the visual scene — no text overlays, no words on the image.
- Focus on: subject, colors, mood, composition.
- Output the description only — no preamble, no quotes."""

# ── Article generation prompts ─────────────────────────────────────────
ARTICLE_1_PROMPT = """\
Write a blog article (1500–2000 words) about the problem Novicado Materials
solves. Frame it as: "Learning AI development is chaotic — scattered resources,
no structured path, too many tools. Here's how a structured curriculum changes
everything."

The article should:
- Describe the pain points of learning AI-assisted development today
- Explain why structured, downloadable materials matter
- Reference the 6 lessons as a coherent learning journey
- Naturally include keywords from the keyword research provided below

Marketing plan:

{plan}

Keyword research:

{keywords}
"""

ARTICLE_2_PROMPT = """\
Write a blog article (1500–2000 words) that is a practical guide: "How to build
your first AI project with the Novicado stack (Zed, DeepSeek, GitHub, fly.io,
Supabase)."

The article should:
- Walk through a realistic project setup step-by-step
- Show the reader what each tool does and why it was chosen
- Reference the 6-lesson curriculum as the full learning path
- Naturally include keywords from the keyword research provided below
- End with a call-to-action to sign in and access the full materials

Marketing plan:

{plan}

Keyword research:

{keywords}
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
    Returns the path or URL of the image.
    """
    # URL-encode the prompt for Pollinations.ai
    from urllib.parse import quote

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
        from PIL import Image, ImageDraw

        # Pick a color based on the prompt hash for variety
        hue = hash(prompt) % 360
        import colorsys

        r, g, b = colorsys.hsv_to_rgb(hue / 360, 0.3, 0.9)
        rgb = (int(r * 255), int(g * 255), int(b * 255))

        img = Image.new("RGB", (800, 400), rgb)
        draw = ImageDraw.Draw(img)
        draw.text(
            (20, 180),
            "Novicado Materials",
            fill=(255, 255, 255),
        )
        img.save(save_path, "PNG")
        print(f"   Fallback image saved → {save_path}")
        return str(save_path)
    except ImportError:
        print("   Pillow not installed — skipping image fallback.")
        return "(image unavailable)"


# ── Main ───────────────────────────────────────────────────────────────
def main():
    print("[ContentWriter] Reading inputs...")
    plan = read_file(PLAN_PATH, "Marketing plan")
    keywords = read_file(KEYWORDS_PATH, "SEO keywords")

    # ── Step 1: Generate blog articles ──────────────────────────────────
    article_prompts = [
        ("Article 1 — Problem/Solution", ARTICLE_1_PROMPT),
        ("Article 2 — Practical Guide", ARTICLE_2_PROMPT),
    ]

    for idx, (label, prompt_template) in enumerate(article_prompts):
        print(f"[ContentWriter] Generating {label}...")
        user_prompt = prompt_template.format(plan=plan, keywords=keywords)
        article = call_deepseek(ARTICLE_SYSTEM, user_prompt, 0.7, 4000)

        ARTICLE_PATHS[idx].write_text(article, encoding="utf-8")
        print(f"   Saved → {ARTICLE_PATHS[idx]} ({len(article)} chars)")

        # Small delay to avoid rate limits
        if idx < len(article_prompts) - 1:
            time.sleep(1)

    # ── Step 2: Generate Telegram posts ─────────────────────────────────
    for idx, article_path in enumerate(ARTICLE_PATHS):
        print(f"[ContentWriter] Adapting article {idx + 1} for Telegram...")
        article_text = article_path.read_text(encoding="utf-8")

        user_prompt = (
            "Convert this blog article into a short Telegram channel post "
            f"(200–300 words):\n\n{article_text}"
        )
        post = call_deepseek(TELEGRAM_SYSTEM, user_prompt, 0.7, 800)

        POST_PATHS[idx].write_text(post, encoding="utf-8")
        print(f"   Telegram post saved → {POST_PATHS[idx]} ({len(post)} chars)")

    # ── Step 3: Generate images ─────────────────────────────────────────
    for idx, article_path in enumerate(ARTICLE_PATHS):
        print(f"[ContentWriter] Generating image for article {idx + 1}...")
        article_text = article_path.read_text(encoding="utf-8")

        # Get an image description from DeepSeek
        img_prompt = call_deepseek(
            IMAGE_SYSTEM,
            f"Describe an image for this article:\n\n{article_text[:1500]}",
            0.8,
            150,
        )
        print(f"   Image prompt: {img_prompt[:80]}...")

        # Generate the image
        img_result = generate_image(img_prompt, IMAGE_PATHS[idx])

        # Append image info to the Telegram post
        current_post = POST_PATHS[idx].read_text(encoding="utf-8")
        updated_post = f"{current_post}\n\n![Image]({img_result})"
        POST_PATHS[idx].write_text(updated_post, encoding="utf-8")

    # ── Done ────────────────────────────────────────────────────────────
    print()
    print("[ContentWriter] All done!")
    print(f"  Blog articles: {ARTICLE_PATHS[0]}, {ARTICLE_PATHS[1]}")
    print(f"  Telegram posts: {POST_PATHS[0]}, {POST_PATHS[1]}")
    print(f"  Images: {IMAGE_PATHS[0]}, {IMAGE_PATHS[1]}")


if __name__ == "__main__":
    main()
