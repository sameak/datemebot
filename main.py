import os
import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# ----------------- CONFIG -----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")  # set in Railway Variables

# Tier A internal points (not Telegram Stars)
DEFAULT_STARS = 3

# Conversation states
LANG, AGE_CHECK, GENDER, LOOKING, AGE, CITY, BIO, PHOTO, MENU = range(10)

CITIES = ["PP", "SR", "BT", "SHV", "O"]  # Cambodia only

TEXT = {
    "en": {
        "welcome": "💖 Welcome to DateMe\nChoose language\n\nK = Khmer 🇰🇭\nE = English 🇬🇧",
        "age_check": "🔞 Are you 18 or older? (Y/N)",
        "blocked": "Sorry, DateMe is for 18+ only.",
        "gender": "Select your gender (M/F):",
        "looking": "Looking for (M/F):",
        "age": "Enter your age (number):",
        "city": "Choose your city in Cambodia: (PP/SR/BT/SHV/O)",
        "bio": "Write a short bio (max 150). Or type S to skip.",
        "photo": "Send 1 photo (optional) or type S to skip.",
        "saved": "✅ Profile saved!\n\nMenu:\nM = Match (coming next)\nP = Profile\nH = Help",
        "need_profile": "Type /pro (or just pro) to create profile ✅",
        "your_profile": "👤 Your Profile",
        "help": "Help:\n/start or /sta\n/pro or pro = create profile\nP = view profile\nM = match (next)\n",
        "choose_lang": "Choose language: K/E",
        "unknown": "I didn’t understand. Type H for help.",
    },
    "kh": {
        "welcome": "💖 ស្វាគមន៍មកកាន់ DateMe\nជ្រើសរើសភាសា\n\nK = ខ្មែរ 🇰🇭\nE = English 🇬🇧",
        "age_check": "🔞 តើអ្នកមានអាយុ 18+ ទេ? (Y/N)",
        "blocked": "សូមអភ័យទោស។ DateMe សម្រាប់អាយុ 18+ ប៉ុណ្ណោះ។",
        "gender": "ជ្រើសរើសភេទ (M/F):",
        "looking": "អ្នកចង់ស្វែងរក (M/F):",
        "age": "បញ្ចូលអាយុ (លេខ):",
        "city": "ជ្រើសរើសទីក្រុងក្នុងកម្ពុជា: (PP/SR/BT/SHV/O)",
        "bio": "សរសេរព័ត៌មានខ្លី (មិនលើស 150) ឬវាយ S ដើម្បីរំលង។",
        "photo": "ផ្ញើរូប 1 (ជាជម្រើស) ឬវាយ S ដើម្បីរំលង។",
        "saved": "✅ បានរក្សាទុកប្រូហ្វាល់!\n\nMenu:\nM = Match (បន្ត)\nP = Profile\nH = Help",
        "need_profile": "វាយ /pro (ឬ pro) ដើម្បីបង្កើតប្រូហ្វាល់ ✅",
        "your_profile": "👤 ប្រូហ្វាល់របស់អ្នក",
        "help": "ជំនួយ:\n/start ឬ /sta\n/pro ឬ pro = បង្កើតប្រូហ្វាល់\nP = មើលប្រូហ្វាល់\nM = match (បន្ត)\n",
        "choose_lang": "ជ្រើសរើសភាសា: K/E",
        "unknown": "ខ្ញុំមិនយល់ទេ។ វាយ H សម្រាប់ជំនួយ។",
    }
}

def kb(options):
    # 2 buttons per row when possible
    rows = []
    row = []
    for opt in options:
        row.append(opt)
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

# ----------------- DATABASE -----------------
conn = sqlite3.connect("dateme.db", check_same_thread=False)
cur = conn.cursor()

def init_db():
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        lang TEXT DEFAULT 'en',
        age_check INTEGER DEFAULT 0,
        gender TEXT,
        looking TEXT,
        age INTEGER,
        city TEXT,
        bio TEXT,
        photo_id TEXT,
        stars INTEGER DEFAULT 3
    )
    """)
    conn.commit()

def get_lang(uid: int) -> str:
    cur.execute("SELECT lang FROM users WHERE user_id=?", (uid,))
    row = cur.fetchone()
    return row[0] if row else "en"

def upsert_user(uid: int):
    cur.execute("INSERT OR IGNORE INTO users (user_id, stars) VALUES (?, ?)", (uid, DEFAULT_STARS))
    conn.commit()

def set_field(uid: int, field: str, value):
    cur.execute(f"UPDATE users SET {field}=? WHERE user_id=?", (value, uid))
    conn.commit()

def get_profile(uid: int):
    cur.execute("SELECT lang, gender, looking, age, city, bio, stars FROM users WHERE user_id=?", (uid,))
    return cur.fetchone()

# ----------------- BOT FLOWS -----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    upsert_user(update.effective_user.id)
    await update.message.reply_text(TEXT["en"]["welcome"], reply_markup=kb(["K", "E"]))
    return LANG

async def sta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # alias for /sta
    return await start(update, context)

async def lang_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    upsert_user(uid)

    t = update.message.text.strip().upper()
    lang = "kh" if t == "K" else "en"
    set_field(uid, "lang", lang)

    await update.message.reply_text(TEXT[lang]["age_check"], reply_markup=kb(["Y", "N"]))
    return AGE_CHECK

async def age_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = get_lang(uid)

    t = update.message.text.strip().upper()
    if t != "Y":
        await update.message.reply_text(TEXT[lang]["blocked"])
        return ConversationHandler.END

    set_field(uid, "age_check", 1)
    await update.message.reply_text(TEXT[lang]["need_profile"], reply_markup=kb(["pro", "/pro"]))
    return ConversationHandler.END

# ---------- PROFILE ----------
async def pro_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    upsert_user(uid)
    lang = get_lang(uid)

    await update.message.reply_text(TEXT[lang]["gender"], reply_markup=kb(["M", "F"]))
    return GENDER

async def pro_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = get_lang(uid)
    t = update.message.text.strip().upper()
    if t not in ("M", "F"):
        await update.message.reply_text(TEXT[lang]["gender"], reply_markup=kb(["M", "F"]))
        return GENDER

    set_field(uid, "gender", t)
    await update.message.reply_text(TEXT[lang]["looking"], reply_markup=kb(["M", "F"]))
    return LOOKING

async def pro_looking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = get_lang(uid)
    t = update.message.text.strip().upper()
    if t not in ("M", "F"):
        await update.message.reply_text(TEXT[lang]["looking"], reply_markup=kb(["M", "F"]))
        return LOOKING

    set_field(uid, "looking", t)
    await update.message.reply_text(TEXT[lang]["age"])
    return AGE

async def pro_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = get_lang(uid)
    t = update.message.text.strip()

    if not t.isdigit():
        await update.message.reply_text(TEXT[lang]["age"])
        return AGE

    age = int(t)
    if age < 18 or age > 80:
        await update.message.reply_text(TEXT[lang]["age"])
        return AGE

    set_field(uid, "age", age)
    await update.message.reply_text(TEXT[lang]["city"], reply_markup=kb(CITIES))
    return CITY

async def pro_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = get_lang(uid)
    t = update.message.text.strip().upper()

    if t not in CITIES:
        await update.message.reply_text(TEXT[lang]["city"], reply_markup=kb(CITIES))
        return CITY

    set_field(uid, "city", t)
    await update.message.reply_text(TEXT[lang]["bio"])
    return BIO

async def pro_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = get_lang(uid)
    t = update.message.text.strip()

    if t.upper() == "S":
        set_field(uid, "bio", "")
    else:
        if len(t) > 150:
            await update.message.reply_text(TEXT[lang]["bio"])
            return BIO
        set_field(uid, "bio", t)

    await update.message.reply_text(TEXT[lang]["photo"])
    return PHOTO

async def pro_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = get_lang(uid)

    # user skips
    if update.message.text and update.message.text.strip().upper() == "S":
        set_field(uid, "photo_id", "")
        await update.message.reply_text(TEXT[lang]["saved"], reply_markup=kb(["M", "P", "H"]))
        return ConversationHandler.END

    # user sends photo
    if update.message.photo:
        photo_id = update.message.photo[-1].file_id
        set_field(uid, "photo_id", photo_id)
        await update.message.reply_text(TEXT[lang]["saved"], reply_markup=kb(["M", "P", "H"]))
        return ConversationHandler.END

    await update.message.reply_text(TEXT[lang]["photo"])
    return PHOTO

# ---------- MENU / TEXT ----------
async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    upsert_user(uid)
    lang = get_lang(uid)
    t = update.message.text.strip()

    # allow typing "pro" without slash
    if t.lower() == "pro":
        return await pro_entry(update, context)

    if t.upper() == "H":
        await update.message.reply_text(TEXT[lang]["help"])
        return

    if t.upper() == "P":
        prof = get_profile(uid)
        if not prof:
            await update.message.reply_text(TEXT[lang]["need_profile"])
            return

        _, gender, looking, age, city, bio, stars = prof
        bio = bio or "(no bio)"
        msg = (
            f"{TEXT[lang]['your_profile']}\n"
            f"Gender: {gender}\n"
            f"Looking: {looking}\n"
            f"Age: {age}\n"
            f"City: {city}\n"
            f"Bio: {bio}\n"
            f"⭐ Points: {stars}"
        )
        await update.message.reply_text(msg)
        return

    if t.upper() == "M":
        await update.message.reply_text("🔜 Matching is coming next. (Next step)")
        return

    await update.message.reply_text(TEXT[lang]["unknown"])

def build_app():
    init_db()

    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN missing. Set Railway Variables: BOT_TOKEN")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # /start and /sta
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sta", sta))

    # start flow: language + age check
    start_conv = ConversationHandler(
        entry_points=[CommandHandler("start", start), CommandHandler("sta", sta)],
        states={
            LANG: [MessageHandler(filters.Regex("^(K|E|k|e)$"), lang_choice)],
            AGE_CHECK: [MessageHandler(filters.Regex("^(Y|N|y|n)$"), age_check)],
        },
        fallbacks=[],
        allow_reentry=True,
    )
    app.add_handler(start_conv)

    # profile flow: /pro or pro (text)
    profile_conv = ConversationHandler(
        entry_points=[
            CommandHandler("pro", pro_entry),
            MessageHandler(filters.Regex(r"^pro$"), pro_entry),
        ],
        states={
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, pro_gender)],
            LOOKING: [MessageHandler(filters.TEXT & ~filters.COMMAND, pro_looking)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, pro_age)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, pro_city)],
            BIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, pro_bio)],
            PHOTO: [MessageHandler((filters.PHOTO) | (filters.TEXT & ~filters.COMMAND), pro_photo)],
        },
        fallbacks=[],
        allow_reentry=True,
    )
    app.add_handler(profile_conv)

    # normal text router
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))

    return app

if __name__ == "__main__":
    app = build_app()
    print("🔥 DateMeBot running")
    app.run_polling()