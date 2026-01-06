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

DEFAULT_STARS = 3
REVEAL_COST = 1

# ================= TEXT (EN + KH) =================
T = {
    "en": {
        "welcome": "💖 Welcome to DateMe\nPlease choose language.",
        "lang_saved": "✅ Language saved.\nChoose an option:",
        "btn_create_profile": "Create Profile",
        "btn_match": "Match",
        "btn_help": "Help",

        "need_profile": "Please create your profile first ✅\nTap the button below.",
        "btn_only": "Please use the buttons below ⬇️",

        "gender": "Select your sex:",
        "looking": "Looking for:",
        "age": "Enter your age (18+):",
        "city": "Choose your city (Cambodia):",
        "bio": "Write a short bio (max 150) or type S to skip.",
        "saved": "✅ Profile saved!\nTap Match to start browsing.",
        "help": "Help:\nUse buttons only.\nStart: /start or /sta\nCreate Profile → Match\n",

        "no_more": "No more profiles right now. Try later.",
        "card": "👤 {sex}, {age}\n📍 {city}\n📝 {bio}\n⭐ Your points: {stars}",

        "btn_like": "❤️ Like",
        "btn_skip": "⏭ Skip",
        "btn_reveal": "🔓 Reveal",

        "matched": "🎉 It's a match!\nNow you can pay ⭐ to reveal each other.",
        "reveal_need_match": "🔒 Reveal is only available after you match.",
        "reveal_confirm": "🔓 Reveal costs {cost} ⭐.\nPress Reveal again to pay.",
        "reveal_paid_wait": "✅ You paid {cost} ⭐. Waiting for the other user to pay…",
        "reveal_success": "🔓 Identity revealed!\nUsername: @{username}",
        "reveal_no_username": "🔓 Identity revealed!\n(They have no public username.)",
        "no_stars": "❌ Not enough ⭐ points. You have {stars}.",

        "underage": "🚨 Service not available for under age user right now!",
        "banned": "🚨 Service not available for under age user right now!",
    },
    "kh": {
        "welcome": "💖 ស្វាគមន៍មកកាន់ DateMe\nសូមជ្រើសរើសភាសា។",
        "lang_saved": "✅ អ្នកបានជ្រើសរើសភាសាខ្មែរ\nសូមជ្រើសរើសបន្ត",
        "btn_create_profile": "បង្កើតប្រូហ្វាល់",
        "btn_match": "ស្វែងរកគូ",
        "btn_help": "ជំនួយ",

        "need_profile": "សូមបង្កើតប្រូហ្វាល់ជាមុនសិន ✅\nសូមចុចប៊ូតុងខាងក្រោម។",
        "btn_only": "សូមប្រើប៊ូតុងខាងក្រោម ⬇️",

        "gender": "ជ្រើសរើសភេទ:",
        "looking": "អ្នកកំពុងស្វែងរកដៃគូរ:",
        "age": "សូមបញ្ចូលអាយុ (18+):",
        "city": "សូមជ្រើសរើសទីក្រុង (កម្ពុជា):",
        "bio": "សូមសរសេរព័ត៌មានខ្លីអំពីអ្នក (មិនលើស 150) ឬវាយ S ដើម្បីរំលង។",
        "saved": "✅ បានរក្សាទុកប្រូហ្វាល់!\nសូមចុច 'ស្វែងរកគូ' ដើម្បីចាប់ផ្តើម។",
        "help": "ជំនួយ:\nសូមប្រើប៊ូតុងប៉ុណ្ណោះ។\nStart: /start ឬ /sta\nបង្កើតប្រូហ្វាល់ → ស្វែងរកគូ\n",

        "no_more": "ឥឡូវនេះមិនមានប្រូហ្វាល់អ្នកប្រើផ្សេងទៀតនោះទេ។ សូមសាកល្បងម្តងទៀតពេលក្រោយ។",
        "card": "👤 {sex}, {age}\n📍 {city}\n📝 {bio}\n⭐ ពិន្ទុរបស់អ្នក: {stars}",

        "btn_like": "❤️ ពេញចិត្ត",
        "btn_skip": "⏭ រំលង",
        "btn_reveal": "🔓 បង្ហាញមុខ",

        "matched": "🎉 ត្រូវគ្នា!\nឥឡូវអ្នកអាចបង់ ⭐ ដើម្បីបង្ហាញមុខគ្នា។",
        "reveal_need_match": "🔒 'បង្ហាញមុខ' អាចប្រើបានតែបន្ទាប់ពីត្រូវគ្នា។",
        "reveal_confirm": "🔓 បង្ហាញមុខ ត្រូវការ {cost} ⭐\nចុច 'បង្ហាញមុខ' ម្តងទៀត ដើម្បីបង់។",
        "reveal_paid_wait": "✅ អ្នកបានបង់ {cost} ⭐។ កំពុងរង់ចាំភាគីម្ខាងទៀត…",
        "reveal_success": "🔓 បានបង្ហាញអត្តសញ្ញាណ!\nUsername: @{username}",
        "reveal_no_username": "🔓 បានបង្ហាញអត្តសញ្ញាណ!\n(ពួកគេមិនមាន username សាធារណៈទេ។)",
        "no_stars": "❌ ⭐ មិនគ្រប់គ្រាន់ទេ។ អ្នកមាន {stars}។",

        "underage": "🚨 Service not available for under age user right now!",
        "banned": "🚨 Service not available for under age user right now!",
    }
}

# ================= DATABASE =================
conn = sqlite3.connect("dateme.db", check_same_thread=False)
cur = conn.cursor()

def init_db():
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        lang TEXT DEFAULT 'en',
        step TEXT DEFAULT 'idle',
        banned INTEGER DEFAULT 0,
        gender TEXT,
        looking TEXT,
        age INTEGER,
        city TEXT,
        bio TEXT,
        stars INTEGER DEFAULT 3
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS likes (
        from_user INTEGER,
        to_user INTEGER,
        UNIQUE(from_user, to_user)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS skips (
        from_user INTEGER,
        to_user INTEGER,
        UNIQUE(from_user, to_user)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS matches (
        user1 INTEGER,
        user2 INTEGER,
        UNIQUE(user1, user2)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS reveal_pay (
        payer INTEGER,
        other INTEGER,
        paid INTEGER DEFAULT 0,
        UNIQUE(payer, other)
    )
    """)
    conn.commit()

# ... (all database functions remain the same as in your code – upsert, get_lang, set_user, etc.)

# ================= KEYBOARDS =================
def language_keyboard():
    return ReplyKeyboardMarkup(
        [["K 🇰🇭 ភាសាខ្មែរ", "E 🇬🇧 English"]],
        resize_keyboard=True
    )

def menu_keyboard(lang: str):
    return ReplyKeyboardMarkup(
        [[T[lang]["btn_match"], T[lang]["btn_create_profile"]],
         [T[lang]["btn_help"]]],
        resize_keyboard=True
    )

def gender_keyboard(lang: str):
    if lang == "kh":
        return ReplyKeyboardMarkup([["👨 ប្រុស", "👩 ស្រី"]], resize_keyboard=True)
    return ReplyKeyboardMarkup([["👨 Male", "👩 Female"]], resize_keyboard=True)

def looking_keyboard(lang: str):
    return gender_keyboard(lang)  # same options

def city_keyboard():
    return ReplyKeyboardMarkup([["PP", "SR", "BT"], ["SHV", "O"]], resize_keyboard=True)

def match_keyboard(lang: str, allow_reveal: bool):
    row1 = [T[lang]["btn_like"], T[lang]["btn_skip"]]
    if allow_reveal:
        row1.append(T[lang]["btn_reveal"])
    return ReplyKeyboardMarkup([row1], resize_keyboard=True)

def normalize_gender(lang: str, text: str):
    t = (text or "").strip().lower()
    if lang == "kh":
        if "ប្រុស" in t:
            return "M"
        if "ស្រី" in t:
            return "F"
    else:
        if t in ("male", "m", "👨"):
            return "M"
        if t in ("female", "f", "👩"):
            return "F"
    return None

# ... (find_candidate, get_card functions same as yours, with Khmer sex labels)

# ================= HANDLERS =================
# (All handlers from your code: start, sta, pro, show_candidate, handle_like, handle_skip, handle_reveal, text_router)

# ================= MAIN =================
def main():
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sta", sta))
    app.add_handler(CommandHandler("pro", pro))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))

    print("🔥 DateMeBot running...")
    app.run_polling()

if __name__ == "__main__":
    main()