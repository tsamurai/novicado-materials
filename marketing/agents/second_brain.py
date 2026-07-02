#!/usr/bin/env python3
"""
Second Brain Agent — connects the Novicado marketing team to an LLM Wiki.
Reads past performance before agents run, writes results after.

The Brain stores what worked, what didn't, and the latest report so agents
can avoid repeating failed topics and build on successful ones.

Usage (from orchestrator or standalone):
    from marketing.agents.second_brain import read_history, write_results

    history = read_history()          # returns dict with latest report, successes, failures
    # ... run agents, get results ...
    write_results(articles, strong_posts, weak_posts, report_path)
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# ── Load .env from project root (regardless of current working directory) ─
ROOT = Path(__file__).resolve().parent.parent.parent  # project root
load_dotenv(ROOT / ".env")

BRAIN_PATH_STR = os.environ.get("BRAIN_PATH", "").strip()
if not BRAIN_PATH_STR:
    raise RuntimeError("BRAIN_PATH is not set in .env")

BRAIN_PATH = Path(BRAIN_PATH_STR).expanduser().resolve()
MARKETING_BRAIN = BRAIN_PATH / "wiki" / "marketing"
CONTENT_BRAIN = MARKETING_BRAIN / "content"

LATEST_REPORT = MARKETING_BRAIN / "latest-report.md"
SUCCESSFUL_POSTS = MARKETING_BRAIN / "successful-posts.md"
FAILED_POSTS = MARKETING_BRAIN / "failed-posts.md"


# ═══════════════════════════════════════════════════════════════════════
#  Setup — create Brain structure if missing
# ═══════════════════════════════════════════════════════════════════════


def ensure_brain_structure():
    """Create the Brain directory structure if it doesn't exist."""
    MARKETING_BRAIN.mkdir(parents=True, exist_ok=True)
    CONTENT_BRAIN.mkdir(parents=True, exist_ok=True)

    # Create default files if missing
    for path, header in [
        (LATEST_REPORT, "# Latest Marketing Report\n\n_(No report yet)_\n"),
        (
            SUCCESSFUL_POSTS,
            "# Successful Posts\n\nPosts that performed well — topics, hooks, formats.\n\n",
        ),
        (
            FAILED_POSTS,
            "# Failed Posts\n\nPosts that underperformed — what went wrong, what to avoid.\n\n",
        ),
    ]:
        if not path.exists():
            path.write_text(header, encoding="utf-8")
            print(f"[Brain] Created {path}")


ensure_brain_structure()


# ═══════════════════════════════════════════════════════════════════════
#  Read — load history before agents run
# ═══════════════════════════════════════════════════════════════════════


def read_history() -> dict:
    """
    Read the Brain's marketing history.
    Returns a dict with keys: latest_report, successful_posts, failed_posts.
    Each value is the full text of the file (or empty string if not found).
    """

    def _read(path: Path) -> str:
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""

    return {
        "latest_report": _read(LATEST_REPORT),
        "successful_posts": _read(SUCCESSFUL_POSTS),
        "failed_posts": _read(FAILED_POSTS),
    }


def get_history_context() -> str:
    """
    Return a condensed string suitable for injecting into agent prompts.
    Includes: last report summary, top successes, top failures.
    """
    history = read_history()

    # Extract first 1000 chars of the report for context
    report_preview = history["latest_report"][:1000]

    # Extract post entries (lines starting with "- " or numbered)
    success_lines = [
        line
        for line in history["successful_posts"].split("\n")
        if line.strip().startswith("- ") or line.strip().startswith("1. ")
    ][:5]

    failure_lines = [
        line
        for line in history["failed_posts"].split("\n")
        if line.strip().startswith("- ") or line.strip().startswith("1. ")
    ][:5]

    context = "### Recent Marketing History (from Brain)\n\n"

    if report_preview.strip():
        context += f"**Latest Report:**\n{report_preview}\n\n"

    if success_lines:
        context += (
            f"**Successful topics/formats:**\n" + "\n".join(success_lines) + "\n\n"
        )

    if failure_lines:
        context += f"**Topics to avoid:**\n" + "\n".join(failure_lines) + "\n\n"

    if not report_preview.strip() and not success_lines and not failure_lines:
        context += "_(No history yet — this is the first run.)_\n"

    return context


# ═══════════════════════════════════════════════════════════════════════
#  Write — save results after agents run
# ═══════════════════════════════════════════════════════════════════════


def write_results(
    articles: list[Path] | None = None,
    strong_posts: list[str] | None = None,
    weak_posts: list[str] | None = None,
    report_path: Path | None = None,
):
    """
    Write agent outputs back to the Brain.

    Args:
        articles: list of Paths to article files to copy into the Brain.
        strong_posts: list of strings — post topics/texts that performed well.
        weak_posts: list of strings — post topics/texts that underperformed.
        report_path: Path to the weekly report file to copy as latest-report.md.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    written = []

    # Copy articles
    if articles:
        for article_path in articles:
            if article_path.exists():
                dest = CONTENT_BRAIN / article_path.name
                shutil.copy2(article_path, dest)
                written.append(f"article: {article_path.name}")

    # Update latest report
    if report_path and report_path.exists():
        shutil.copy2(report_path, LATEST_REPORT)
        written.append("latest-report.md")

    # Append successful posts
    if strong_posts:
        entry = f"\n## {timestamp}\n\n"
        for post in strong_posts:
            entry += f"- {post}\n"
        with open(SUCCESSFUL_POSTS, "a") as f:
            f.write(entry)
        written.append(f"successful-posts: +{len(strong_posts)} entries")

    # Append failed posts
    if weak_posts:
        entry = f"\n## {timestamp}\n\n"
        for post in weak_posts:
            entry += f"- {post}\n"
        with open(FAILED_POSTS, "a") as f:
            f.write(entry)
        written.append(f"failed-posts: +{len(weak_posts)} entries")

    if written:
        print(f"[Brain] Written: {', '.join(written)}")
    else:
        print("[Brain] Nothing new to write")


# ═══════════════════════════════════════════════════════════════════════
#  Brain summary — for the Telegram bot /brain command
# ═══════════════════════════════════════════════════════════════════════


def get_brain_summary() -> str:
    """
    Return a Markdown summary of the Brain for the /brain Telegram command.
    Includes: latest report preview, top 3 successes, top 3 failures.
    """
    history = read_history()

    lines = ["🧠 *Second Brain — Marketing History*\n"]

    # Latest report
    if history["latest_report"].strip():
        # Show first 3 non-empty, non-heading lines
        report_lines = [
            l
            for l in history["latest_report"].split("\n")
            if l.strip() and not l.strip().startswith("#")
        ][:3]
        if report_lines:
            lines.append("*Latest Report:*")
            for rl in report_lines:
                lines.append(f"  {rl[:100]}")
            lines.append("")

    # Top 3 successful
    success_entries = [
        line.strip("- ").strip()
        for line in history["successful_posts"].split("\n")
        if line.strip().startswith("- ")
    ]
    if success_entries:
        lines.append("*Top 3 successful posts:*")
        for entry in success_entries[-3:]:
            lines.append(f"  ✅ {entry[:120]}")
        lines.append("")

    # Top 3 failed
    failure_entries = [
        line.strip("- ").strip()
        for line in history["failed_posts"].split("\n")
        if line.strip().startswith("- ")
    ]
    if failure_entries:
        lines.append("*Top 3 failed posts:*")
        for entry in failure_entries[-3:]:
            lines.append(f"  ❌ {entry[:120]}")
        lines.append("")

    if (
        not success_entries
        and not failure_entries
        and not history["latest_report"].strip()
    ):
        lines.append("_(No history yet — the Brain is empty.)_")

    lines.append(f"\n📁 `{str(MARKETING_BRAIN)}`")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════
#  Standalone
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("🧠 Second Brain Agent")
    print(f"   Brain path: {BRAIN_PATH}")
    print(f"   Marketing wiki: {MARKETING_BRAIN}")
    print()

    history = read_history()
    print(
        f"   Latest report:  {'present' if history['latest_report'].strip() else 'empty'}"
    )
    print(
        f"   Successes:      {history['successful_posts'].count(chr(10) + '- ')} entries"
    )
    print(f"   Failures:       {history['failed_posts'].count(chr(10) + '- ')} entries")
    print()

    print(get_brain_summary())
