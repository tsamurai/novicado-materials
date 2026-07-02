#!/usr/bin/env python3
"""
SEO Agent for Novicado Materials.
Generates keyword research and on-page SEO recommendations using DeepSeek API.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# ── Load .env from project root (regardless of current working directory) ─
ROOT = Path(__file__).resolve().parent.parent.parent  # project root
load_dotenv(ROOT / ".env")

# ── Paths ──────────────────────────────────────────────────────────────
STRATEGY_PATH = ROOT / "marketing" / "PRODUCT_STRATEGY.md"
PLAN_PATH = ROOT / "marketing" / "MARKETING_PLAN.md"
KEYWORDS_OUTPUT = ROOT / "marketing" / "SEO_KEYWORDS.md"
RECOMMENDATIONS_OUTPUT = ROOT / "marketing" / "SEO_RECOMMENDATIONS.md"

# ── DeepSeek client ────────────────────────────────────────────────────
client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
)

# ── System prompts ─────────────────────────────────────────────────────
KEYWORDS_SYSTEM = """\
You are an SEO strategist for an AI school platform called Novicado Materials.
You produce keyword research documents grouped by thematic clusters.

Rules:
- Use the provided product strategy and marketing plan as your only source of
  truth about the product.
- Output ONLY valid Markdown — no preamble, no signature.
- Start directly with a level-2 heading: ## Keyword Research"""

RECOMMENDATIONS_SYSTEM = """\
You are an SEO auditor for a web application. You review a live site's home page
and produce actionable on-page SEO recommendations.

Rules:
- Be specific — recommend exact title text, exact meta description text,
  and specific heading structure changes.
- Keep recommendations realistic for a small team.
- Output ONLY valid Markdown — no preamble, no signature.
- Start directly with a level-2 heading: ## On-Page SEO Recommendations"""

# ── Keyword research prompt ────────────────────────────────────────────
KEYWORDS_PROMPT = """\
Based on the product strategy and marketing plan below, generate a keyword
research document with 15-20 keywords relevant to this product.

Group them into 3-4 thematic clusters. For each keyword, indicate estimated
search volume as high / medium / low.

Format the output as follows:

## Keyword Research

### Cluster: <Cluster Name>
Brief: one sentence describing this topic cluster.

| # | Keyword | Volume |
|---|---------|--------|
| 1 | example keyword | high |
| 2 | another keyword | medium |

(Repeat for each cluster)

### Summary
- Total keywords: N
- Clusters: N
- Primary target: <best high-volume keyword>

---

Product strategy:

{strategy}

Marketing plan:

{plan}
"""

# ── SEO recommendations prompt ─────────────────────────────────────────
RECOMMENDATIONS_PROMPT = """\
Analyze the home page content below (extracted from https://novicado-materials.fly.dev)
and provide on-page SEO recommendations.

The site is a React SPA that lists 6 AI school course lessons. The content below
is the full text visible on the home page.

{site_content}

---

Provide recommendations for:

### Title Tag
- Current: "<current>"
- Recommended: "<your recommendation>"
- Reason: one sentence

### Meta Description
- Recommended: "<your recommendation>"
- Reason: one sentence

### Heading Structure
- Current issues (if any)
- Recommended h1, h2 structure

### Content Gaps
- What's missing from the page that would help SEO?
- 2-3 concrete suggestions

### Technical SEO Quick Wins
- 2-3 actionable items (e.g., sitemap, robots.txt, canonical URL,
  Open Graph tags)
"""


# ── Fetch site content ─────────────────────────────────────────────────
def fetch_site_content():
    """Fetch the live home page and extract visible text + meta tags."""
    import re
    from html import unescape
    from urllib.request import urlopen

    url = "https://novicado-materials.fly.dev"
    print(f"[SEO] Fetching live site: {url}")

    resp = urlopen(url, timeout=15)
    html = resp.read().decode("utf-8")

    # Extract title
    title_match = re.search(r"<title>(.*?)</title>", html)
    title = unescape(title_match.group(1)) if title_match else "(not found)"

    # Extract meta description
    desc_match = re.search(
        r'<meta\s+name="description"\s+content="(.*?)"', html, re.IGNORECASE
    )
    description = unescape(desc_match.group(1)) if desc_match else "(not found)"

    # Extract visible text (strip HTML tags)
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return {
        "title": title,
        "description": description,
        "text": text,
    }


def main():
    # ── Step 1: Generate keyword research ───────────────────────────────
    print("[SEO] Reading product strategy and marketing plan...")

    strategy = ""
    plan = ""

    if STRATEGY_PATH.exists():
        strategy = STRATEGY_PATH.read_text(encoding="utf-8")
        print(f"[SEO]   Strategy: {len(strategy)} chars")
    else:
        print("[SEO]   WARNING: PRODUCT_STRATEGY.md not found, continuing without it")

    if PLAN_PATH.exists():
        plan = PLAN_PATH.read_text(encoding="utf-8")
        print(f"[SEO]   Marketing plan: {len(plan)} chars")
    else:
        print("[SEO]   WARNING: MARKETING_PLAN.md not found, continuing without it")

    print("[SEO] Generating keywords via DeepSeek...")
    kw_response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": KEYWORDS_SYSTEM},
            {
                "role": "user",
                "content": KEYWORDS_PROMPT.format(strategy=strategy, plan=plan),
            },
        ],
        temperature=0.3,
        max_tokens=2500,
    )

    keywords = kw_response.choices[0].message.content
    KEYWORDS_OUTPUT.write_text(keywords, encoding="utf-8")
    print(f"[SEO] Keywords saved → {KEYWORDS_OUTPUT} ({len(keywords)} chars)")

    # ── Step 2: Analyze live site for SEO ───────────────────────────────
    print("[SEO] Analyzing live site for on-page SEO...")
    try:
        site = fetch_site_content()
        print(f"[SEO]   Title: {site['title']}")
        print(f"[SEO]   Description: {site['description']}")
        print(f"[SEO]   Visible text: {len(site['text'])} chars")
    except Exception as e:
        print(f"[SEO]   ERROR fetching site: {e}")
        print("[SEO]   Skipping site analysis — will use generic content.")
        site = {
            "title": "Novicado Materials",
            "description": "(not found)",
            "text": "Novicado Materials — AI School lesson materials. "
            "Welcome to Novicado. AI School lesson materials — access your "
            "course content in one place. Sign in with Google. "
            "Lesson 1: GitHub, Zed, DeepSeek & Context Optimization. "
            "Lesson 2: Architecture, Design & AI Agent Team. "
            "Lesson 3: Deployment & Databases. "
            "Lesson 4: Autonomous AI Agent with Memory. "
            "Lesson 5: AI Marketing Team. "
            "Lesson 6: Diploma Project — Product Presentation.",
        }

    rec_response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": RECOMMENDATIONS_SYSTEM},
            {
                "role": "user",
                "content": RECOMMENDATIONS_PROMPT.format(
                    site_content=f"Title: {site['title']}\n"
                    f"Meta description: {site['description']}\n\n"
                    f"Page text:\n{site['text']}"
                ),
            },
        ],
        temperature=0.3,
        max_tokens=2000,
    )

    recommendations = rec_response.choices[0].message.content
    RECOMMENDATIONS_OUTPUT.write_text(recommendations, encoding="utf-8")
    print(
        f"[SEO] Recommendations saved → {RECOMMENDATIONS_OUTPUT} "
        f"({len(recommendations)} chars)"
    )


if __name__ == "__main__":
    main()
