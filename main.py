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

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing. Set Railway Variables: BOT_TOKEN")

# ================= TEXT (EN + KH) =================
T = {
    "en": {
        "welcome": "💖 Welcome to DateMe\nChoose language",
        "lang_saved": "✅ Language saved.\nChoose an option:",
        "btn_create_profile": "Create Profile",
        "btn_help": "Help",
        "type_pro": "Type /pro (or pro) to create profile ✅",
        "gender": "Select your sex:",
        "created": "✅ Profile created!\nSex: {g}",
        "pick_mf": "Please choose Male or Female",
    },
    "kh": {
        "welcome": "💖 ស្វាគមន៍មកកាន់ DateMe\nជ្រើសរើសភាសា",
        "lang_saved": "✅ បានរក្សាទុកភាសា។\nសូមជ្រើសរើស:",
        "btn_create_profile": "បង្កើតប្រូហ្វាល់",
        "btn_help": "ជំនួយ",
        "type_pro": "វាយ /pro (ឬ pro) ដើម្បីបង្កើតប្រូហ្វាល់ ✅",
        "gender": "ជ្រើសរើសភេទ:",
        "created": "✅ បង្កើតប្រូហ្វាល់រួចរាល់!\nភេទ: {g}",
        "pick_mf": "សូមជ្រើស ប្រុស ឬ ស្រី",
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

# ================= KEYBOARDS =================
def language_keyboard():
    # Your request: use ភាសាខ្មែរ (not Khmer)
    return ReplyKeyboardMarkup(
        [["K 🇰🇭 ភាសាខ្មែរ", "E 🇬🇧 English"]],
        resize_keyboard=True
    )

def menu_keyboard(lang: str):
    if lang == "kh":
        return ReplyKeyboardMarkup(
            [[T["kh"]["btn_create_profile"], T["kh"]["btn_help"]]],
            resize_keyboard=True
        )
    return ReplyKeyboardMarkup(
        [[T["en"]["btn_create_profile"], T["en"]["btn_help"]]],
        resize_keyboard=True
    )

def gender_keyboard(lang: str):
    # Your request: Khmer labels for M/F
    if lang == "kh":
        return ReplyKeyboardMarkup([["ប្រុស", "ស្រី"]], resize_keyboard=True)
    return ReplyKeyboardMarkup([["Male", "Female"]], resize_keyboard=True)

# Map display labels -> internal (M/F)
def normalize_gender(lang: str, text: str):
    t = (text or "").strip().lower()
    if lang == "kh":
        if t in ("ប្រុស",):
            return "M"
        if t in ("ស្រី",):
            return "F"
    else:
        if t in ("male", "m"):
            return "M"
        if t in ("female", "f"):
            return "F"
    return None

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = get_lang(uid)
    set_user(uid, step="lang")
    await update.message.reply_text(
        T[lang]["welcome"],
        reply_markup=language_keyboard()
    )

async def sta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

# ================= PROFILE =================
async def pro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = get_lang(uid)
    set_user(uid, step="gender")
    await update.message.reply_text(
        T[lang]["gender"],
        reply_markup=gender_keyboard(lang)
    )

# ================= TEXT ROUTER =================
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    upsert(uid)

    text = (update.message.text or "").strip()
    t_lower = text.lower()

    step, lang = get_user(uid)

    # Start shortcuts without slash
    if t_lower in ("start", "sta"):
        await start(update, context)
        return

    # Language selection step
    if step == "lang":
        # Accept "K ..." or "E ..." or just "K"/"E"
        if text.upper().startswith("K"):
            set_user(uid, step="idle", lang="kh")
            await update.message.reply_text(
                T["kh"]["lang_saved"],
                reply_markup=menu_keyboard("kh")
            )
            return
        if text.upper().startswith("E"):
            set_user(uid, step="idle", lang="en")
            await update.message.reply_text(
                T["en"]["lang_saved"],
                reply_markup=menu_keyboard("en")
            )
            return

        await update.message.reply_text(T[lang]["welcome"], reply_markup=language_keyboard())
        return

    # Menu buttons (Create Profile)
    if text == T["en"]["btn_create_profile"] or text == T["kh"]["btn_create_profile"]:
        await pro(update, context)
        return

    # Still allow typing pro without slash
    if t_lower == "pro":
        await pro(update, context)
        return

    # Gender step
    if step == "gender":
        g = normalize_gender(lang, text)
        if g:
            set_user(uid, step="idle", gender=g)
            shown = "ប្រុស" if (lang == "kh" and g == "M") else "ស្រី" if (lang == "kh" and g == "F") else "Male" if g == "M" else "Female"
            await update.message.reply_text(
                T[lang]["created"].format(g=shown),
                reply_markup=menu_keyboard(lang)
            )
            return

        await update.message.reply_text(T[lang]["pick_mf"], reply_markup=gender_keyboard(lang))
        return

    # Help button (simple)
    if text == T["en"]["btn_help"]:
        await update.message.reply_text("Help:\n/start, /sta, start, sta\nCreate Profile button or /pro")
        return
    if text == T["kh"]["btn_help"]:
        await update.message.reply_text("ជំនួយ:\n/start, /sta, start, sta\nចុច 'បង្កើតប្រូហ្វាល់' ឬវាយ /pro")
        return

    # Default hint
    await update.message.reply_text(T[lang]["type_pro"], reply_markup=menu_keyboard(lang))

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sta", sta))
    app.add_handler(CommandHandler("pro", pro))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("🔥 DateMeBot running")
    app.run_polling()

if __name__ == "__main__":
    main()