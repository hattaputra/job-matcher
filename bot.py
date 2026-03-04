import os
import re
import httpx
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000/api/v1/rate-job")
ALLOWED_USER_ID = int(os.getenv("TELEGRAM_USER_ID", "0"))

LINKEDIN_PATTERN = re.compile(r"https?://(?:www\.)?linkedin\.com/jobs/view/\S+")


def extract_linkedin_url(text: str) -> str | None:
    match = LINKEDIN_PATTERN.search(text)
    return match.group(0).rstrip("/") + "/" if match else None


def format_rating(data: dict) -> str:
    r = data.get("rating", {})
    score = r.get("score", 0)

    # Score emoji
    if score >= 8:
        grade = "🟢"
    elif score >= 6:
        grade = "🟡"
    else:
        grade = "🔴"

    stack_match = ", ".join(r.get("stack_match", [])) or "None"
    stack_missing = ", ".join(r.get("stack_missing", [])) or "None"
    highlights = "\n".join(f"  • {h}" for h in r.get("highlights", []))
    red_flags = "\n".join(f"  • {f}" for f in r.get("red_flags", []))

    return (
        f"{grade} *{r.get('raw_title', 'Unknown Role')}* — {r.get('raw_company', '')}\n\n"
        f"⭐ *Score:* {score}/10\n"
        f"✅ *Stack Match:* {stack_match}\n"
        f"⚠️ *Stack Missing:* {stack_missing}\n"
        f"🎯 *Seniority Match:* {'Yes' if r.get('seniority_match') else 'No'}\n"
        f"🌐 *Remote Friendly:* {'Yes' if r.get('remote_friendly') else 'No'}\n\n"
        f"✨ *Highlights:*\n{highlights}\n\n"
        f"🚩 *Red Flags:*\n{red_flags}\n\n"
        f"📝 *Summary:*\n{r.get('summary', '')}"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if ALLOWED_USER_ID and user_id != ALLOWED_USER_ID:
        return

    text = update.message.text or ""
    url = extract_linkedin_url(text)

    if not url:
        return  # ignore non-LinkedIn messages

    await update.message.reply_text("🔍 Analyzing job... please wait.")

    try:
        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.post(FASTAPI_URL, json={"url": url})
            response.raise_for_status()
            data = response.json()

        result = format_rating(data)
        await update.message.reply_text(result, parse_mode="Markdown")

    except httpx.HTTPStatusError as e:
        await update.message.reply_text(f"❌ API error: {e.response.text}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot started. Listening for LinkedIn URLs...")
    app.run_polling()


if __name__ == "__main__":
    main()