#!/usr/bin/env python3
"""
CMO Agent — Chief Marketing Officer for Novicado Materials.
Generates a one-month marketing strategy using DeepSeek API.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# ── Load .env from project root (regardless of current working directory) ─
ROOT = Path(__file__).resolve().parent.parent.parent  # project root
load_dotenv(ROOT / ".env")
STRATEGY_PATH = ROOT / "marketing" / "PRODUCT_STRATEGY.md"
OUTPUT_PATH = ROOT / "marketing" / "MARKETING_PLAN.md"

# ── DeepSeek client ────────────────────────────────────────────────────
client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
)

# ── System prompt ──────────────────────────────────────────────────────
SYSTEM_PROMPT = """\
You are the Chief Marketing Officer (CMO) for Novicado Materials, an AI school
platform. You produce structured, actionable marketing strategy documents.

Rules:
- Write in clear, concise English.
- All numbers must be realistic for a bootstrapped AI school (small audience,
  early stage).
- Use the provided product strategy as your only source of truth about the product.
- Output ONLY valid Markdown — no preamble, no signature, no "here is the plan".
- Start directly with a level-2 heading: ## One-Month Marketing Strategy"""

# ── User prompt template ───────────────────────────────────────────────
USER_PROMPT_TEMPLATE = """\
Read the product strategy below and create a one-month marketing strategy.

The strategy MUST include these sections, in this order:

## Monthly Goals
- 3-5 specific, measurable goals with numeric targets
  (e.g., "400 unique visitors", "50 new sign-ups", "4 blog articles published")

## Content Themes
- 5-7 themes relevant to the product's audience and lessons
- Each theme: headline + one sentence why it works for this audience

## Publishing Calendar
- Weekly breakdown (Week 1 through Week 4)
- Per week: how many articles, how many Telegram/Reddit/social posts, what topics
- Keep it realistic — this is a small team, likely 1 person handling everything

## Channel KPIs
- One row per marketing channel mentioned in the strategy
- Columns: Channel | Weekly Target | Metric | Tool/Method
- Examples: organic search (visitors), Twitter (impressions), Telegram
  (subscribers), GitHub (stars), Reddit (upvotes)

---

Here is the product strategy:

{strategy}
"""


def main():
    # 1. Read the product strategy
    if not STRATEGY_PATH.exists():
        raise FileNotFoundError(f"Product strategy not found: {STRATEGY_PATH}")

    strategy_text = STRATEGY_PATH.read_text(encoding="utf-8")
    print(f"[CMO] Read product strategy ({len(strategy_text)} chars)")

    # 2. Call DeepSeek
    print("[CMO] Generating marketing plan via DeepSeek...")
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": USER_PROMPT_TEMPLATE.format(strategy=strategy_text),
            },
        ],
        temperature=0.7,
        max_tokens=3000,
    )

    plan = response.choices[0].message.content
    print(f"[CMO] Received plan ({len(plan)} chars)")

    # 3. Save to disk
    OUTPUT_PATH.write_text(plan, encoding="utf-8")
    print(f"[CMO] Marketing plan saved → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
