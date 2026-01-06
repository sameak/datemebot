from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

from config import BOT_TOKEN
from database import init_db
from keyboards import lang_keyboard, yes_no

# import profile flow
from handlers.profile import (
    ask_gender, save_gender, save_looking, save_age, save_city,
    GENDER, LOOKING, AGE, CITY
)

# ---------- BASIC START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💖 Welcome to DateMe\nChoose language\n\nK = Khmer 🇰🇭\nE = English 🇬🇧",
        reply_markup=lang_keyboard()
    )

async def sta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

# ---------- LANGUAGE CHOICE ----------
async def language_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "K":
        await update.message.reply_text("🇰🇭 ជ្រើសរើសភាសាខ្មែរ ✅", reply_markup=yes_no())
    elif text == "E":
        await update.message.reply_text("🇬🇧 English selected ✅", reply_markup=yes_no())
    else:
        await update.message.reply_text("Type /pro to create profile ✅")

def main():
    init_db()

    if not BOT_TOKEN:
        print("❌ BOT_TOKEN is missing in Railway Variables")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sta", sta))

    # profile conversation (/pro)
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

    # normal text (K/E etc.)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, language_choice))

    print("🔥 DateMeBot running")
    app.run_polling()

if __name__ == "__main__":
    main()