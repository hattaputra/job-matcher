import os
import re
import httpx
import asyncio
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler,
    ConversationHandler, filters, ContextTypes
)
from dotenv import load_dotenv
from app.services.profile import (
    profile_exists, save_profile, append_preferences,
    generate_profile_from_cv, load_profile, delete_profile,
    append_salary_benchmarks
)
from app.services.cv_extractor import extract_text_from_pdf, generate_profile_from_cv_text, generate_salary_benchmarks

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000/api/v1/rate-job")

# Conversation states
WAITING_CV = 1
WAITING_MARKETS = 2
WAITING_WORK_ARRANGEMENT = 3
WAITING_EMPLOYMENT_TYPE = 4
WAITING_RELOCATION = 5

LINKEDIN_PATTERN = re.compile(r"https?://(?:www\.)?linkedin\.com/jobs/view/\S+")


def extract_linkedin_url(text: str) -> str | None:
    match = LINKEDIN_PATTERN.search(text)
    return match.group(0).rstrip("/") + "/" if match else None


def format_rating(data: dict) -> str:
    r = data.get("rating", {})
    score_pct = r.get("score_pct", 0)
    grade_label = r.get("grade_label", "")
    title = r.get("raw_title") or "Unknown Role"
    company = r.get("raw_company") or ""
    scorecard = r.get("scorecard", [])
    red_flags = r.get("red_flags", [])

    # Grade emoji
    if score_pct >= 80:
        grade_emoji = "🟢"
    elif score_pct >= 60:
        grade_emoji = "🟡"
    else:
        grade_emoji = "🔴"

    # Header
    lines = [
        f"{grade_emoji} *{title}*",
        f"🏢 {company}" if company else "",
        "",
        f"⭐ *Overall: {score_pct}% — {grade_label}*",
        "",
    ]

    # Scorecard
    if scorecard:
        lines.append("📊 *Scorecard:*")
        for i, row in enumerate(scorecard):
            score = row.get("score", 0)
            metric = row.get("metric", "")
            evaluation = row.get("evaluation", "")

            # Score bar
            if score >= 70:
                bar = "🟩"
            elif score >= 40:
                bar = "🟨"
            elif score < 0:
                bar = "🟥"
            else:
                bar = "🟥"

            prefix = "└─" if i == len(scorecard) - 1 else "├─"
            lines.append(f"`{prefix}` {bar} *{metric}* `{score}`")
            if evaluation:
                lines.append(f"      _{evaluation}_")

        lines.append("")

    # Red flags
    if red_flags:
        lines.append("⚠️ *Red Flags:*")
        for flag in red_flags:
            lines.append(f"• {flag}")
        lines.append("")

    return "\n".join(filter(lambda x: x is not None, lines)).strip()


# ─── Onboarding Flow ───────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender_id = update.effective_user.id

    if profile_exists(sender_id):
        await update.message.reply_text(
            "👋 Welcome back! Send me a LinkedIn job URL and I'll rate it for you."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "👋 *Welcome to Job Matcher!*\n\n"
        "I'll help you find the best job opportunities based on your profile.\n\n"
        "First, please *upload your CV in PDF format*.",
        parse_mode="Markdown"
    )
    return WAITING_CV


async def handle_cv_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender_id = update.effective_user.id

    if not update.message.document:
        await update.message.reply_text("Please upload your CV as a PDF file.")
        return WAITING_CV

    doc = update.message.document
    if not doc.file_name.lower().endswith(".pdf"):
        await update.message.reply_text("Please upload a PDF file only.")
        return WAITING_CV

    await update.message.reply_text("📄 Extracting your CV... please wait.")

    try:
        file = await context.bot.get_file(doc.file_id)
        pdf_bytes = await file.download_as_bytearray()

        cv_text = extract_text_from_pdf(bytes(pdf_bytes))
        if not cv_text or len(cv_text) < 100:
            await update.message.reply_text(
                "❌ Could not extract text from PDF. "
                "Please make sure your CV is not scanned/image-based."
            )
            return WAITING_CV

        await update.message.reply_text("🤖 Analyzing your CV with AI...")
        llm_profile = generate_profile_from_cv_text(cv_text)
        generate_profile_from_cv(sender_id, cv_text, llm_profile)

    except Exception as e:
        await update.message.reply_text(f"❌ Error processing CV: {str(e)}")
        return WAITING_CV

    await update.message.reply_text(
        "✅ CV analyzed successfully!\n\n"
        "Now let's set your job preferences.\n\n"
        "🌍 *Which countries are you open to work in?*\n"
        "Example: Singapore, Malaysia, Australia, Dubai, Japan, Indonesia",
        parse_mode="Markdown"
    )
    return WAITING_MARKETS


async def handle_markets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["markets"] = update.message.text

    await update.message.reply_text(
        "🏢 *What work arrangement do you prefer?*\n\n"
        "You can choose multiple — just type them separated by comma.\n\n"
        "Options: `Remote`, `Hybrid`, `Onsite`\n\n"
        "Example: `Remote, Hybrid`",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return WAITING_WORK_ARRANGEMENT


async def handle_work_arrangement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["work_arrangement"] = update.message.text

    await update.message.reply_text(
        "💼 *What employment type do you accept?*\n\n"
        "You can choose multiple — just type them separated by comma.\n\n"
        "Options: `Full-time`, `Contract`, `Freelance`\n\n"
        "Example: `Full-time, Contract`",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return WAITING_EMPLOYMENT_TYPE


async def handle_employment_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["employment_type"] = update.message.text

    await update.message.reply_text(
        "✈️ *Relocation & remote preference?*\n\n"
        "You can choose multiple — just type them separated by comma.\n\n"
        "Options: `Open to relocation`, `Remote only`, `Hybrid acceptable`, `Onsite if needed`\n\n"
        "Example: `Open to relocation, Remote only`",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return WAITING_RELOCATION


async def handle_relocation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender_id = update.effective_user.id
    context.user_data["relocation"] = update.message.text

    preferences = {
        "markets": context.user_data.get("markets", ""),
        "work_arrangement": context.user_data.get("work_arrangement", ""),
        "employment_type": context.user_data.get("employment_type", ""),
        "relocation": context.user_data.get("relocation", ""),
    }

    append_preferences(sender_id, preferences)

    await update.message.reply_text("💰 Generating salary benchmarks for your target markets...")

    try:
        profile_md = load_profile(sender_id)
        salary_md = generate_salary_benchmarks(
            profile_md=profile_md,
            markets=preferences.get("markets", "")
        )
        append_salary_benchmarks(sender_id, salary_md)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Could not generate salary benchmarks: {str(e)}")

    await update.message.reply_text(
        "🎉 *Profile complete!*\n\n"
        "Your profile includes:\n"
        "✅ CV analysis\n"
        "✅ Job preferences\n"
        "✅ Salary benchmarks per market\n\n"
        "Send me any LinkedIn job URL and I'll analyze it for you.\n\n"
        "Example:\n`https://www.linkedin.com/jobs/view/1234567890/`",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Onboarding cancelled. Type /start to begin again.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


# ─── Profile Commands ─────────────────────────────────────────────

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender_id = update.effective_user.id

    if not profile_exists(sender_id):
        await update.message.reply_text(
            "You don't have a profile yet. Type /start to create one."
        )
        return

    profile = load_profile(sender_id)
    # Telegram max message length is 4096
    if len(profile) > 4000:
        profile = profile[:4000] + "\n\n_...truncated_"

    await update.message.reply_text(
        f"📋 *Your current profile:*\n\n```\n{profile}\n```",
        parse_mode="Markdown"
    )


async def reset_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender_id = update.effective_user.id

    if not profile_exists(sender_id):
        await update.message.reply_text(
            "You don't have a profile yet. Type /start to create one."
        )
        return

    delete_profile(sender_id)
    await update.message.reply_text(
        "🗑️ *Profile deleted.*\n\n"
        "Type /start to create a new one.",
        parse_mode="Markdown"
    )


# ─── Job Matching ──────────────────────────────────────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender_id = update.effective_user.id
    text = update.message.text or ""

    # Check profile exists
    if not profile_exists(sender_id):
        await update.message.reply_text(
            "👋 Welcome! Please type /start to set up your profile first."
        )
        return

    url = extract_linkedin_url(text)
    if not url:
        await update.message.reply_text(
            "Send me a LinkedIn job URL to get started.\n"
            "Example: `https://www.linkedin.com/jobs/view/1234567890/`",
            parse_mode="Markdown"
        )
        return

    await update.message.reply_text("🔍 Analyzing job... this may take a minute.")

    try:
        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.post(
                FASTAPI_URL,
                json={"url": url, "sender_id": sender_id}
            )
            response.raise_for_status()
            data = response.json()

        result = format_rating(data)
        await update.message.reply_text(result, parse_mode="Markdown")

    except httpx.HTTPStatusError as e:
        await update.message.reply_text(f"❌ API error: {e.response.text}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


# ─── Main ──────────────────────────────────────────────────────────

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_CV: [MessageHandler(filters.Document.PDF, handle_cv_upload)],
            WAITING_MARKETS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_markets)],
            WAITING_WORK_ARRANGEMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_work_arrangement)],
            WAITING_EMPLOYMENT_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_employment_type)],
            WAITING_RELOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_relocation)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("profile", show_profile))
    app.add_handler(CommandHandler("reset", reset_profile))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot started.")
    app.run_polling()


if __name__ == "__main__":
    main()