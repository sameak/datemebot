import os
import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")

# ================= DATABASE =================
conn = sqlite3.connect("dateme.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    lang TEXT,
    step TEXT,
    gender TEXT
)
""")
conn.commit()

# ================= HELPERS =================
def kb(buttons):
    return ReplyKeyboardMarkup([[b] for b in buttons], resize_keyboard=True)

def get_user(uid):
    cur.execute("SELECT step, lang FROM users WHERE user_id=?", (uid,))
    return cur.fetchone()

def set_user(uid, step=None, lang=None, gender=None):
    cur.execute(
        "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
        (uid,)
    )
    if step:
        cur.execute("UPDATE users SET step=? WHERE user_id=?", (step, uid))
    if lang:
        cur.execute("UPDATE users SET lang=? WHERE user_id=?", (lang, uid))
    if gender:
        cur.execute("UPDATE users SET gender=? WHERE user_id=?", (gender, uid))
    conn.commit()

# ================= COMMANDS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    set_user(uid, step="lang")

    await update.message.reply_text(
        "💖 Welcome to DateMe\nChoose language",
        reply_markup=kb(["K", "E"])
    )

async def pro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    set_user(uid, step="gender")

    await update.message.reply_text(
        "Select your gender:",
        reply_markup=kb(["M", "F"])
    )

# ================= TEXT HANDLER =================
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip().upper()

    user = get_user(uid)
    if not user:
        await start(update, context)
        return

    step, lang = user

    # allow typing pro without slash
    if text == "PRO":
        await pro(update, context)
        return

    if step == "lang":
        if text in ("K", "E"):
            set_user(uid, step="idle", lang=text)
            await update.message.reply_text(
                "Language saved ✅\nType /pro to create profile"
            )
        else:
            await update.message.reply_text("Choose K or E")
        return

    if step == "gender":
        if text in ("M", "F"):
            set_user(uid, step="done", gender=text)
            await update.message.reply_text(
                f"✅ Profile created!\nGender: {text}"
            )
        else:
            await update.message.reply_text("Please choose M or F")
        return

    await update.message.reply_text("Type /pro to create profile")

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("pro", pro))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("🔥 DateMeBot running")
    app.run_polling()

if __name__ == "__main__":
    main()