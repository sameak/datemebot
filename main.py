from handlers.profile import *
from telegram.ext import ConversationHandler
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import BOT_TOKEN
from database import init_db
from languages import TEXT
from keyboards import lang_keyboard

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💖 Welcome to DateMe\nChoose language\n\n[K] Khmer\n[E] English",
        reply_markup=lang_keyboard()
    )

# ---------- SHORT COMMAND (/sta) ----------
async def sta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

# ---------- LANGUAGE BUTTON ----------
async def language_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "K":
        await update.message.reply_text("🇰🇭 ភាសាខ្មែរ បានជ្រើសរើស")
    elif update.message.text == "E":
        await update.message.reply_text("🇬🇧 English selected")

# ---------- MAIN ----------
def main():
    init_db()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sta", sta))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, language_choice))

    print("🔥 DateMeBot running")
profile_handler = ConversationHandler(
    entry_points=[CommandHandler("pro", ask_gender)],
    states={
        GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_gender)],
        LOOKING: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_looking)],
        AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_age)],
        CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_city)],
    },
    fallbacks=[]
)

app.add_handler(profile_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
