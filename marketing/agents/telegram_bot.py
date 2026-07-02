#!/usr/bin/env python3
"""
Marketing Team Bot — connects the Product Owner to the Novicado marketing team
via Telegram. Gatekept to a single user; provides status, content, and control
commands for the marketing pipeline.

Usage:
    python marketing/agents/telegram_bot.py
"""

import asyncio
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# ── Load .env from project root (regardless of current working directory) ─
ROOT = Path(__file__).resolve().parent.parent.parent  # project root
load_dotenv(ROOT / ".env")

# Add agents dir to path so we can import second_brain
sys.path.insert(0, str(ROOT / "marketing" / "agents"))

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
OWNER_ID = os.environ.get("MY_TELEGRAM_USER_ID", "").strip()

if not TOKEN:
    print("ERROR: TELEGRAM_BOT_TOKEN is not set in .env")
    sys.exit(1)
if not OWNER_ID:
    print("ERROR: MY_TELEGRAM_USER_ID is not set in .env")
    sys.exit(1)

try:
    OWNER_ID_INT = int(OWNER_ID)
except ValueError:
    print("ERROR: MY_TELEGRAM_USER_ID must be a numeric user ID")
    sys.exit(1)

# ── Paths ──────────────────────────────────────────────────────────────
MARKETING_DIR = ROOT / "marketing"
BLOG_DIR = MARKETING_DIR / "blog"
TELEGRAM_DIR = MARKETING_DIR / "telegram"
REPORTS_DIR = MARKETING_DIR / "reports"

STRATEGY_PATH = MARKETING_DIR / "PRODUCT_STRATEGY.md"
PLAN_PATH = MARKETING_DIR / "MARKETING_PLAN.md"
KEYWORDS_PATH = MARKETING_DIR / "SEO_KEYWORDS.md"
RECOMMENDATIONS_PATH = MARKETING_DIR / "SEO_RECOMMENDATIONS.md"
CALENDAR_PATH = MARKETING_DIR / "TELEGRAM_CONTENT_CALENDAR.md"
ORCHESTRATOR_PATH = MARKETING_DIR / "orchestrator.py"


# ═══════════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════════


def _check_access(user_id: int) -> bool:
    """Only the Product Owner can use this bot."""
    return user_id == OWNER_ID_INT


def _file_status(path: Path) -> str:
    """Return a status string for a file: ✅ exists with size, or ❌ not found."""
    if path.exists():
        size_kb = path.stat().st_size / 1024
        mtime = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        return f"✅ {path.name}  ({size_kb:.1f} KB, {mtime})"
    return f"❌ {path.name}  (not found)"


def _list_dir(dir_path: Path, label: str) -> str:
    """List files in a directory, or show 'empty' message."""
    if not dir_path.exists():
        return f"📁 {label}/  — directory does not exist"
    files = sorted(
        f for f in dir_path.iterdir() if f.is_file() and f.name != ".gitkeep"
    )
    if not files:
        return f"📁 {label}/  — empty"
    lines = [f"📁 {label}/"]
    for f in files:
        size_kb = f.stat().st_size / 1024
        lines.append(f"  • {f.name}  ({size_kb:.1f} KB)")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════
#  Command handlers
# ═══════════════════════════════════════════════════════════════════════


async def cmd_status(update, _context):
    """Show team status — which agents ran, what files exist."""
    lines = ["📊 *Marketing Team Status*", ""]

    # Core strategy docs
    lines.append("*Strategy & Planning:*")
    lines.append(_file_status(STRATEGY_PATH))
    lines.append(_file_status(PLAN_PATH))
    lines.append("")

    # SEO outputs
    lines.append("*SEO:*")
    lines.append(_file_status(KEYWORDS_PATH))
    lines.append(_file_status(RECOMMENDATIONS_PATH))
    lines.append("")

    # Content
    lines.append("*Content:*")
    lines.append(_list_dir(BLOG_DIR, "blog"))
    lines.append(_list_dir(TELEGRAM_DIR, "telegram"))
    lines.append(_file_status(CALENDAR_PATH))
    lines.append("")

    # Reports
    lines.append("*Reports:*")
    lines.append(_list_dir(REPORTS_DIR, "reports"))
    lines.append("")

    # Agent count
    agents_dir = MARKETING_DIR / "agents"
    agents = sorted(
        f.name
        for f in agents_dir.iterdir()
        if f.suffix == ".py" and f.name not in ("__init__.py",)
    )
    lines.append(f"*Agents:* {len(agents)} scripts ready")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines.append(f"\n_Last update: {now}_")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_content(update, _context):
    """Show latest articles and posts."""
    lines = ["📝 *Latest Content*", ""]

    # Blog articles
    if BLOG_DIR.exists():
        articles = sorted(
            [
                f
                for f in BLOG_DIR.iterdir()
                if f.suffix == ".md" and f.name != ".gitkeep"
            ],
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )
        if articles:
            lines.append("*Blog Articles:*")
            for a in articles[:5]:
                size_kb = a.stat().st_size / 1024
                # Show first line as preview
                first_line = a.read_text(encoding="utf-8").strip().split("\n")[0]
                preview = first_line[:80] + ("..." if len(first_line) > 80 else "")
                lines.append(f"  • {preview}  ({size_kb:.1f} KB)")
        else:
            lines.append("*Blog Articles:* — none yet")
    lines.append("")

    # Telegram posts
    if TELEGRAM_DIR.exists():
        posts = sorted(
            [
                f
                for f in TELEGRAM_DIR.iterdir()
                if f.suffix == ".md" and f.name != ".gitkeep"
            ],
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )
        if posts:
            lines.append("*Telegram Posts:*")
            for p in posts[:5]:
                size_kb = p.stat().st_size / 1024
                first_line = p.read_text(encoding="utf-8").strip().split("\n")[0]
                preview = first_line[:80] + ("..." if len(first_line) > 80 else "")
                lines.append(f"  • {preview}  ({size_kb:.1f} KB)")
        else:
            lines.append("*Telegram Posts:* — none yet")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_run(update, _context):
    """Run the orchestrator once."""
    if not ORCHESTRATOR_PATH.exists():
        await update.message.reply_text("❌ orchestrator.py not found")
        return

    await update.message.reply_text("🚀 Running the full marketing pipeline...")

    result = subprocess.run(
        [sys.executable, str(ORCHESTRATOR_PATH)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=300,
    )

    if result.returncode == 0:
        # Show last few lines of output
        output_lines = result.stdout.strip().split("\n")
        summary = "\n".join(output_lines[-8:])
        await update.message.reply_text(
            f"✅ Pipeline complete!\n\n```\n{summary}\n```",
            parse_mode="Markdown",
        )
    else:
        err = result.stderr.strip()[:500]
        await update.message.reply_text(
            f"❌ Pipeline failed (exit {result.returncode})\n\n```\n{err}\n```",
            parse_mode="Markdown",
        )


async def cmd_post(update, _context):
    """Publish a custom post to the Telegram channel."""
    text = " ".join(_context.args) if _context.args else ""
    if not text:
        await update.message.reply_text(
            "Usage: `/post Your post text here...`\n"
            "The post will be published to the marketing channel.",
            parse_mode="Markdown",
        )
        return

    await _publish_to_channel(text)
    await update.message.reply_text(
        f"✅ Post published to channel!\n\n_Preview:_ {text[:200]}...",
        parse_mode="Markdown",
    )


async def cmd_post_now(update, _context):
    """Emergency publish — same as /post but with higher visibility prefix."""
    text = " ".join(_context.args) if _context.args else ""
    if not text:
        await update.message.reply_text(
            "Usage: `/post_now Your urgent post text...`\n"
            "Published immediately with an URGENT prefix.",
            parse_mode="Markdown",
        )
        return

    urgent_text = f"🚨 *URGENT* 🚨\n\n{text}"
    await _publish_to_channel(urgent_text)
    await update.message.reply_text(
        f"⚠️ Emergency post published!\n\n_Preview:_ {text[:200]}...",
        parse_mode="Markdown",
    )


async def cmd_report(update, _context):
    """Request a weekly report to be generated asynchronously."""
    await update.message.reply_text(
        "📋 Weekly report requested.\n\n"
        "I'll generate the report now. Use /report_now to skip the queue.",
        parse_mode="Markdown",
    )
    await _generate_and_send_report(update)


async def cmd_report_now(update, _context):
    """Generate and deliver the report immediately."""
    await update.message.reply_text("⏳ Generating report...", parse_mode="Markdown")
    await _generate_and_send_report(update)


async def cmd_brain(update, _context):
    """Show the Second Brain summary — report, top successes, top failures."""
    try:
        from second_brain import get_brain_summary

        summary = get_brain_summary()
    except Exception as e:
        summary = f"❌ Could not read Brain: {e}"
    await update.message.reply_text(summary, parse_mode="Markdown")


# ═══════════════════════════════════════════════════════════════════════
#  Shared logic
# ═══════════════════════════════════════════════════════════════════════


async def _publish_to_channel(text: str):
    """Publish a text post to the configured Telegram channel."""
    from telegram import Bot

    channel = os.environ.get("TELEGRAM_CHANNEL_ID", "").strip()
    if not channel:
        return

    bot = Bot(token=TOKEN)
    await bot.send_message(
        chat_id=channel,
        text=text,
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


async def _generate_and_send_report(update):
    """Generate a weekly report and send it as a message."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Gather file status
    files_status = []
    for p in [
        STRATEGY_PATH,
        PLAN_PATH,
        KEYWORDS_PATH,
        RECOMMENDATIONS_PATH,
        CALENDAR_PATH,
    ]:
        files_status.append(_file_status(p))

    # Count content
    blog_count = 0
    if BLOG_DIR.exists():
        blog_count = len(
            [
                f
                for f in BLOG_DIR.iterdir()
                if f.suffix == ".md" and f.name != ".gitkeep"
            ]
        )

    post_count = 0
    if TELEGRAM_DIR.exists():
        post_count = len(
            [
                f
                for f in TELEGRAM_DIR.iterdir()
                if f.suffix == ".md" and f.name != ".gitkeep"
            ]
        )

    img_count = 0
    images_dir = MARKETING_DIR / "images"
    if images_dir.exists():
        img_count = len([f for f in images_dir.iterdir() if f.name != ".gitkeep"])

    # Read last scheduler log lines
    log_path = REPORTS_DIR / "scheduler.log"
    log_tail = ""
    if log_path.exists():
        log_lines = log_path.read_text(encoding="utf-8").strip().split("\n")
        log_tail = "\n".join(log_lines[-5:])

    report = (
        f"📊 *Weekly Report*  ({now})\n\n"
        f"*Files:*\n" + "\n".join(files_status) + f"\n\n*Content produced:*\n"
        f"  • {blog_count} blog articles\n"
        f"  • {post_count} Telegram posts\n"
        f"  • {img_count} generated images\n"
        f"\n*Recent activity:*\n"
        f"```\n{log_tail or '(no log yet)'}\n```"
    )

    await update.message.reply_text(report, parse_mode="Markdown")


# ═══════════════════════════════════════════════════════════════════════
#  Bot setup
# ═══════════════════════════════════════════════════════════════════════


async def _access_denied(update):
    """Reply to unauthorized users."""
    await update.message.reply_text("🚫 Access denied. This bot is private.")


def _build_app():
    """Build the Telegram Application instance."""
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters

    app = Application.builder().token(TOKEN).build()

    # Command handlers (gated by user ID check)
    async def gate(handler, update: Update, context):
        if not _check_access(update.effective_user.id):
            await _access_denied(update)
            return
        await handler(update, context)

    app.add_handler(CommandHandler("status", lambda u, c: gate(cmd_status, u, c)))
    app.add_handler(CommandHandler("content", lambda u, c: gate(cmd_content, u, c)))
    app.add_handler(CommandHandler("run", lambda u, c: gate(cmd_run, u, c)))
    app.add_handler(CommandHandler("post", lambda u, c: gate(cmd_post, u, c)))
    app.add_handler(CommandHandler("post_now", lambda u, c: gate(cmd_post_now, u, c)))
    app.add_handler(CommandHandler("report", lambda u, c: gate(cmd_report, u, c)))
    app.add_handler(
        CommandHandler("report_now", lambda u, c: gate(cmd_report_now, u, c))
    )
    app.add_handler(CommandHandler("brain", lambda u, c: gate(cmd_brain, u, c)))

    # Any non-command message → access denied for non-owner, or help for owner
    async def handle_message(update: Update, _context):
        if _check_access(update.effective_user.id):
            await update.message.reply_text(
                "👋 Available commands:\n\n"
                "/status — team status\n"
                "/content — latest articles & posts\n"
                "/run — run full pipeline\n"
                "/post [text] — publish to channel\n"
                "/post_now [text] — emergency publish\n"
                "/brain — second brain history\n"
                "/report — weekly report\n"
                "/report_now — report immediately",
                parse_mode="Markdown",
            )
        else:
            await _access_denied(update)

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    return app


def main():
    print("══════════════════════════════════════════════")
    print("  🤖  Novicado Marketing Team Bot")
    print(f"  Owner ID: {OWNER_ID_INT}")
    print(
        f"  Commands: /status /content /run /post /post_now /brain /report /report_now"
    )
    print("══════════════════════════════════════════════\n")

    app = _build_app()

    # Python 3.14 compatible: create/get event loop explicitly
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    print("[Bot] Polling for messages... (Ctrl+C to stop)")
    app.run_polling()


if __name__ == "__main__":
    main()
