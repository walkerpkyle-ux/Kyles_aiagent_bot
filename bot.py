import os
import logging
from anthropic import Anthropic
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
ALLOWED_USER_ID = int(os.environ.get("ALLOWED_USER_ID", "0"))

client = Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are Kyle Walker's personal AI assistant. Kyle is a professional concert pianist, educator, and entrepreneur based in northern New Jersey.

His roles:
- Artist Faculty in Piano Studies at NYU Steinhardt
- Faculty at Kaufman Music Center (Lucy Moses School)
- Private piano studio owner (tiered monthly pricing)
- YouTube channel creator: Piano Lab with Kyle (for serious adult pianists)

His active projects:
- Piano Lab with Kyle YouTube channel
- Practice Lab PWA (practice tracker for adult pianists)
- 30-day practice system PDF lead magnet
- NYU Steinhardt graduate entrepreneurship course

His income goal: $10,000/month, majority from digital products and online services.

Communication style:
- Be direct, concise, and warm
- No em dashes, no markdown bold in messages
- Plain text only
- No filler phrases or generic advice
- Give strong recommendations, not just options
- Think ahead and flag risks or opportunities

You are his strategic assistant helping with decisions, writing, content, scheduling, and business growth."""

conversation_histories = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if ALLOWED_USER_ID and user_id != ALLOWED_USER_ID:
        await update.message.reply_text("Unauthorized.")
        return
    await update.message.reply_text("Hey Kyle, ready to work.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if ALLOWED_USER_ID and user_id != ALLOWED_USER_ID:
        await update.message.reply_text("Unauthorized.")
        return

    user_text = update.message.text

    if user_id not in conversation_histories:
        conversation_histories[user_id] = []

    conversation_histories[user_id].append({
        "role": "user",
        "content": user_text
    })

    # Keep last 20 messages to manage token usage
    if len(conversation_histories[user_id]) > 20:
        conversation_histories[user_id] = conversation_histories[user_id][-20:]

    try:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=conversation_histories[user_id]
        )

        reply = response.content[0].text

        conversation_histories[user_id].append({
            "role": "assistant",
            "content": reply
        })

        await update.message.reply_text(reply)

    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("Something went wrong. Try again.")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conversation_histories[user_id] = []
    await update.message.reply_text("Conversation cleared.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot running...")
    app.run_polling()
