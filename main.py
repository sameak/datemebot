import os
import sqlite3
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
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
    raise RuntimeError("BOT_TOKEN is missing. Set Railway Variables: BOT_TOKEN")

# ================= TEXT (EN + KH) =================
T = {
    "en": {
        "welcome": "💖 Welcome to DateMe\nChoose language",
        "lang_saved": "✅ Language saved.\nType /pro (or pro) to create profile",
        "type_pro": "Type /pro (or pro) to create profile ✅",
        "gender": "Select your gender:",
        "created": "✅ Profile created!\nGender: {g}",
        "pick_mf": "Please choose M or F",
    },
    "kh": {
        "welcome": "💖 ស្វាគមន៍មកកាន់ DateMe\nជ្រើសរើសភាសា",
        "lang_saved": "✅ បានរក្សាទុកភាសា។\nវាយ /pro (ឬ pro) ដើម្បីបង្កើតប្រូហ្វាល់",
        "type_pro": "វាយ /pro (ឬ pro) ដើម្បីបង្កើតប្រូហ្វាល់ ✅",
        "gender": "ជ្រើសរើសភេទ:",
        "created": "✅ បង្កើតប្រូហ្វាល់រួចរាល់!\nភេទ: {g}",
        "pick_mf": "សូមជ្រើស M ឬ F",
    }
}

# ================= DATABASE =================
conn = sqlite3.connect("dateme.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    lang TEXT DEFAULT 'en',
    step TEXT DEFAULT 'idle',
    gender TEXT
)
""")
conn.commit()

def upsert(uid: int):
    cur.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (uid,))
    conn.commit()

def get_user(uid: int):
    cur.execute("SELECT step, lang FROM users WHERE user_id=?", (uid,))
    row = cur.fetchone()
    return row if row else ("idle", "en")

def set_user(uid: int, step=None, lang=None, gender=None):
    upsert(uid)
    if step is not None:
        cur.execute("UPDATE users SET step=? WHERE user_id=?", (step, uid))
    if lang is not None:
        cur.execute("UPDATE users SET lang=? WHERE user_id=?", (lang, uid))
    if gender is not None:
        cur.execute("UPDATE users SET gender=? WHERE user_id=?", (gender, uid))
    conn.commit()

def get_lang(uid: int) -> str:
    cur.execute("SELECT lang FROM users WHERE user_id=?", (uid,))
    r = cur.fetchone()
    return r[0] if r else "en"

def language_keyboard():
    # Buttons show Khmer/English text, but still map to K/E
    return ReplyKeyboardMarkup([["K 🇰🇭 Khmer", "E 🇬🇧 English"]], resize_keyboard=True)

def gender_keyboard():
    return ReplyKeyboardMarkup([["M", "F"]], resize_keyboard=True)

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = get_lang(uid)  # show welcome in stored lang if already set
    set_user(uid, step="lang")
    await update.message.reply_text(
        T[lang]["welcome"],
        reply_markup=language_keyboard()
    )

# alias for /sta
async def sta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

# ================= PROFILE =================
async def pro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = get_lang(uid)
    set_user(uid, step="gender")
    await update.message.reply_text(
        T[lang]["gender"],
        reply_markup=gender_keyboard()
    )

# ================= TEXT ROUTER =================
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    upsert(uid)

    text = (update.message.text or "").strip()
    t = text.lower()

    step, lang = get_user(uid)

    # ---------- START shortcuts: start / sta (no slash) ----------
    if t in ("start", "sta"):
        await start(update, context)
        return

    # ---------- language buttons: accept K/E or full button text ----------
    if step == "lang":
        # User may send "K" or "K 🇰🇭 Khmer"
        if text.upper().startswith("K"):
            set_user(uid, step="idle", lang="kh")
            await update.message.reply_text(
                T["kh"]["lang_saved"],
                reply_markup=ReplyKeyboardRemove()
            )
            return
        if text.upper().startswith("E"):
            set_user(uid, step="idle", lang="en")
            await update.message.reply_text(
                T["en"]["lang_saved"],
                reply_markup=ReplyKeyboardRemove()
            )
            return

        # If they typed something else while in lang step, re-show keyboard
        await update.message.reply_text(
            T[lang]["welcome"],
            reply_markup=language_keyboard()
        )
        return

    # ---------- profile shortcuts: pro (no slash) ----------
    if t == "pro":
        await pro(update, context)
        return

    # ---------- gender step ----------
    if step == "gender":
        g = text.upper()
        if g in ("M", "F"):
            set_user(uid, step="idle", gender=g)
            await update.message.reply_text(
                T[lang]["created"].format(g=g),
                reply_markup=ReplyKeyboardRemove()
            )
            return
        await update.message.reply_text(T[lang]["pick_mf"], reply_markup=gender_keyboard())
        return

    # default
    await update.message.reply_text(T[lang]["type_pro"])

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Slash commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sta", sta))
    app.add_handler(CommandHandler("pro", pro))

    # Plain text
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("🔥 DateMeBot running")
    app.run_polling()

if __name__ == "__main__":
    main()