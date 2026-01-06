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
        # Requested change: "Please choose language."
        "welcome": "💖 Welcome to DateMe\nPlease choose language.",
        "lang_saved": "✅ Language saved.\nChoose an option:",
        "btn_create_profile": "Create Profile",
        "btn_match": "Match",
        "btn_help": "Help",

        # Requested: force button click; ignore typing
        "need_profile": "Please create your profile first ✅\nTap the button below.",
        "btn_only": "Please use the buttons below ⬇️",

        "gender": "Select your sex:",
        "looking": "Looking for:",
        "age": "Enter your age (18+):",
        "city": "Choose your city (Cambodia):",
        "bio": "Write a short bio (max 150) or type S to skip.",
        "saved": "✅ Profile saved!\nTap Match to start browsing.",
        "help": "Help:\nUse buttons only.\nStart: start/sta (/start /sta ok)\nCreate Profile → Match\n",

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

        # Underage ban message
        "underage": "🚨 Service not available for under age user right now!",
        "banned": "🚨 Service not available for under age user right now!",
    },
    "kh": {
        # Requested: Khmer welcome text can remain Khmer + same idea
        "welcome": "💖 ស្វាគមន៍មកកាន់ DateMe\nសូមជ្រើសរើសភាសា។",

        # Requested change:
        # ✅ Language saved.\nChoose an option:
        # -> អ្នកបានជ្រើសរើសភាសាខ្មែរ\nសូមជ្រើសរើសបន្ត
        "lang_saved": "អ្នកបានជ្រើសរើសភាសាខ្មែរ\nសូមជ្រើសរើសបន្ត",

        "btn_create_profile": "បង្កើតប្រូហ្វាល់",
        "btn_match": "ស្វែងរកគូ",
        "btn_help": "ជំនួយ",

        # Requested: force button click; ignore typing
        "need_profile": "សូមបង្កើតប្រូហ្វាល់ជាមុនសិន ✅\nសូមចុចប៊ូតុងខាងក្រោម។",
        "btn_only": "សូមប្រើប៊ូតុងខាងក្រោម ⬇️",

        "gender": "ជ្រើសរើសភេទ:",
        "looking": "អ្នកកំពុងស្វែងរកដៃគូរ:",
        "age": "សូមបញ្ចូលអាយុ (18+):",
        "city": "សូមជ្រើសរើសទីក្រុង (កម្ពុជា):",
        "bio": "សូមសរសេរព័ត៌មានខ្លីអំពីអ្នក (មិនលើស 150) ឬវាយ S ដើម្បីរំលង។",
        "saved": "✅ បានរក្សាទុកប្រូហ្វាល់!\nសូមចុច 'ស្វែងរកគូ' ដើម្បីចាប់ផ្តើម។",
        "help": "ជំនួយ:\nសូមប្រើប៊ូតុងប៉ុណ្ណោះ។\nStart: start/sta (/start /sta ក៏បាន)\nបង្កើតប្រូហ្វាល់ → ស្វែងរកគូ\n",

        "no_more": "ឥឡូវនេះមិនមានប្រូហ្វាល់អ្នកប្រើផ្សេងទៀតនោះទេ។ សូមសាកល្បងម្តងស្វែងរកម្តងទៀតពេលនៅក្រោយ។",
        "card": "👤 {sex}, {age}\n📍 {city}\n📝 {bio}\n⭐ ពិន្ទុរបស់អ្នក: {stars}",

        # Requested buttons
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

        # Underage ban message (requested in English, but Khmer UI can show same)
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

def upsert(uid: int):
    cur.execute("INSERT OR IGNORE INTO users (user_id, stars) VALUES (?, ?)", (uid, DEFAULT_STARS))
    conn.commit()

def get_lang(uid: int) -> str:
    cur.execute("SELECT lang FROM users WHERE user_id=?", (uid,))
    r = cur.fetchone()
    return r[0] if r else "en"

def get_user_flags(uid: int):
    cur.execute("SELECT step, lang, banned FROM users WHERE user_id=?", (uid,))
    r = cur.fetchone()
    return r if r else ("idle", "en", 0)

def set_user(uid: int, **fields):
    upsert(uid)
    for k, v in fields.items():
        cur.execute(f"UPDATE users SET {k}=? WHERE user_id=?", (v, uid))
    conn.commit()

def is_banned(uid: int) -> bool:
    cur.execute("SELECT banned FROM users WHERE user_id=?", (uid,))
    r = cur.fetchone()
    return bool(r and r[0] == 1)

def has_profile(uid: int) -> bool:
    cur.execute("SELECT gender, looking, age, city FROM users WHERE user_id=?", (uid,))
    r = cur.fetchone()
    return bool(r and all(r))

def get_stars(uid: int) -> int:
    cur.execute("SELECT stars FROM users WHERE user_id=?", (uid,))
    r = cur.fetchone()
    return int(r[0]) if r and r[0] is not None else 0

def add_like(a: int, b: int):
    cur.execute("INSERT OR IGNORE INTO likes (from_user, to_user) VALUES (?,?)", (a, b))
    conn.commit()

def add_skip(a: int, b: int):
    cur.execute("INSERT OR IGNORE INTO skips (from_user, to_user) VALUES (?,?)", (a, b))
    conn.commit()

def is_liked(a: int, b: int) -> bool:
    cur.execute("SELECT 1 FROM likes WHERE from_user=? AND to_user=? LIMIT 1", (a, b))
    return cur.fetchone() is not None

def is_matched(a: int, b: int) -> bool:
    u1, u2 = sorted([a, b])
    cur.execute("SELECT 1 FROM matches WHERE user1=? AND user2=? LIMIT 1", (u1, u2))
    return cur.fetchone() is not None

def make_match(a: int, b: int):
    u1, u2 = sorted([a, b])
    cur.execute("INSERT OR IGNORE INTO matches (user1, user2) VALUES (?,?)", (u1, u2))
    conn.commit()

def set_current(context: ContextTypes.DEFAULT_TYPE, target_id: int):
    context.user_data["current_target"] = target_id

def get_current(context: ContextTypes.DEFAULT_TYPE):
    return context.user_data.get("current_target")

def reset_current(context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("current_target", None)

def set_reveal_paid(payer: int, other: int, paid: int):
    cur.execute("INSERT OR IGNORE INTO reveal_pay (payer, other, paid) VALUES (?,?,0)", (payer, other))
    cur.execute("UPDATE reveal_pay SET paid=? WHERE payer=? AND other=?", (paid, payer, other))
    conn.commit()

def is_reveal_paid(payer: int, other: int) -> bool:
    cur.execute("SELECT paid FROM reveal_pay WHERE payer=? AND other=? LIMIT 1", (payer, other))
    r = cur.fetchone()
    return bool(r and r[0] == 1)

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
    return ReplyKeyboardMarkup([["👨 ប្រុស", "👩 ស្រី"]] if lang == "kh" else [["Male", "Female"]], resize_keyboard=True)

def looking_keyboard(lang: str):
    return ReplyKeyboardMarkup([["👨 ប្រុស", "👩 ស្រី"]] if lang == "kh" else [["Male", "Female"]], resize_keyboard=True)

def city_keyboard():
    return ReplyKeyboardMarkup([["PP", "SR", "BT"], ["SHV", "O"]], resize_keyboard=True)

def match_keyboard(lang: str, allow_reveal: bool):
    row1 = [T[lang]["btn_like"], T[lang]["btn_skip"]]
    if allow_reveal:
        return ReplyKeyboardMarkup([row1, [T[lang]["btn_reveal"]]], resize_keyboard=True)
    return ReplyKeyboardMarkup([row1], resize_keyboard=True)

def normalize_gender(lang: str, text: str):
    t = (text or "").strip().lower()
    if lang == "kh":
        if "ប្រុស" in t:
    return "M"
if "ស្រី" in t:
    return "F"
    else:
        if t in ("male", "m"):
            return "M"
        if t in ("female", "f"):
            return "F"
    return None

def find_candidate(uid: int):
    cur.execute("SELECT gender, looking FROM users WHERE user_id=?", (uid,))
    me = cur.fetchone()
    if not me or not me[0] or not me[1]:
        return None
    my_gender, my_looking = me[0], me[1]

    cur.execute("""
    SELECT u.user_id
    FROM users u
    WHERE u.user_id != ?
      AND u.banned = 0
      AND u.gender = ?
      AND u.looking = ?
      AND u.age IS NOT NULL
      AND u.city IS NOT NULL
      AND u.user_id NOT IN (SELECT to_user FROM likes WHERE from_user=?)
      AND u.user_id NOT IN (SELECT to_user FROM skips WHERE from_user=?)
      AND u.user_id NOT IN (
        SELECT CASE WHEN user1=? THEN user2 ELSE user1 END
        FROM matches
        WHERE user1=? OR user2=?
      )
    ORDER BY RANDOM()
    LIMIT 1
    """, (uid, my_looking, my_gender, uid, uid, uid, uid, uid))
    r = cur.fetchone()
    return r[0] if r else None

def get_card(uid: int, viewer_lang: str, viewer_stars: int):
    cur.execute("SELECT gender, age, city, bio FROM users WHERE user_id=?", (uid,))
    r = cur.fetchone()
    if not r:
        return None
    g, age, city, bio = r
    if viewer_lang == "kh":
        sex = "ប្រុស" if g == "M" else "ស្រី"
        empty = "(គ្មាន)"
    else:
        sex = "Male" if g == "M" else "Female"
        empty = "(empty)"
    bio = bio if bio else empty
    return T[viewer_lang]["card"].format(sex=sex, age=age, city=city, bio=bio, stars=viewer_stars)

# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    upsert(uid)

    # If banned, always show ban message and stop
    lang = get_lang(uid)
    if is_banned(uid):
        await update.message.reply_text(T[lang]["banned"], reply_markup=ReplyKeyboardRemove())
        return

    set_user(uid, step="lang")
    await update.message.reply_text(T[lang]["welcome"], reply_markup=language_keyboard())

async def sta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def pro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    upsert(uid)
    lang = get_lang(uid)

    if is_banned(uid):
        await update.message.reply_text(T[lang]["banned"], reply_markup=ReplyKeyboardRemove())
        return

    set_user(uid, step="pro_gender")
    await update.message.reply_text(T[lang]["gender"], reply_markup=gender_keyboard(lang))

async def show_candidate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = get_lang(uid)

    if is_banned(uid):
        await update.message.reply_text(T[lang]["banned"], reply_markup=ReplyKeyboardRemove())
        return

    if not has_profile(uid):
        # Requested: don't allow typing -> show only buttons, ignore text later
        await update.message.reply_text(T[lang]["need_profile"], reply_markup=menu_keyboard(lang))
        return

    cand = find_candidate(uid)
    if not cand:
        reset_current(context)
        await update.message.reply_text(T[lang]["no_more"], reply_markup=menu_keyboard(lang))
        return

    set_current(context, cand)
    stars = get_stars(uid)
    allow_reveal = is_matched(uid, cand)
    card = get_card(cand, lang, stars)
    await update.message.reply_text(card, reply_markup=match_keyboard(lang, allow_reveal))

async def handle_like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = get_lang(uid)
    target = get_current(context)
    if not target:
        await show_candidate(update, context)
        return

    add_like(uid, target)

    if is_liked(target, uid):
        make_match(uid, target)
        await update.message.reply_text(T[lang]["matched"], reply_markup=match_keyboard(lang, True))
        try:
            other_lang = get_lang(target)
            await context.bot.send_message(chat_id=target, text=T[other_lang]["matched"], reply_markup=match_keyboard(other_lang, True))
        except Exception:
            pass

    await show_candidate(update, context)

async def handle_skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    target = get_current(context)
    if target:
        add_skip(uid, target)
    await show_candidate(update, context)

async def handle_reveal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = get_lang(uid)
    target = get_current(context)

    if not target or not is_matched(uid, target):
        await update.message.reply_text(T[lang]["reveal_need_match"])
        return

    flag_key = f"reveal_confirm_{target}"
    if not context.user_data.get(flag_key):
        context.user_data[flag_key] = True
        await update.message.reply_text(T[lang]["reveal_confirm"].format(cost=REVEAL_COST))
        return

    context.user_data.pop(flag_key, None)

    stars = get_stars(uid)
    if stars < REVEAL_COST:
        await update.message.reply_text(T[lang]["no_stars"].format(stars=stars))
        return

    set_user(uid, stars=stars - REVEAL_COST)
    set_reveal_paid(uid, target, 1)

    if is_reveal_paid(uid, target) and is_reveal_paid(target, uid):
        other_chat = await context.bot.get_chat(target)
        if other_chat.username:
            await update.message.reply_text(T[lang]["reveal_success"].format(username=other_chat.username))
        else:
            await update.message.reply_text(T[lang]["reveal_no_username"])

        try:
            me_chat = await context.bot.get_chat(uid)
            other_lang = get_lang(target)
            if me_chat.username:
                await context.bot.send_message(chat_id=target, text=T[other_lang]["reveal_success"].format(username=me_chat.username))
            else:
                await context.bot.send_message(chat_id=target, text=T[other_lang]["reveal_no_username"])
        except Exception:
            pass
        return

    await update.message.reply_text(T[lang]["reveal_paid_wait"].format(cost=REVEAL_COST))

async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    upsert(uid)

    step, lang, banned = get_user_flags(uid)

    # If banned: always block
    if banned == 1:
        await update.message.reply_text(T[lang]["banned"], reply_markup=ReplyKeyboardRemove())
        return

    text = (update.message.text or "").strip()
    t = text.lower()

    # Start shortcuts
    if t in ("start", "sta"):
        await start(update, context)
        return

    # Language selection
    if step == "lang":
        if text.upper().startswith("K"):
            set_user(uid, lang="kh", step="idle")
            await update.message.reply_text(T["kh"]["lang_saved"], reply_markup=menu_keyboard("kh"))
            return
        if text.upper().startswith("E"):
            set_user(uid, lang="en", step="idle")
            await update.message.reply_text(T["en"]["lang_saved"], reply_markup=menu_keyboard("en"))
            return
        await update.message.reply_text(T[lang]["btn_only"], reply_markup=language_keyboard())
        return

    # Force "no typing" when no profile: ignore typed text and show menu
    if (not has_profile(uid)) and (step not in ("pro_gender", "pro_looking", "pro_age", "pro_city", "pro_bio")):
    if text in (T[lang]["btn_create_profile"], T[lang]["btn_match"], T[lang]["btn_help"]):
        pass
    else:
        await update.message.reply_text(T[lang]["btn_only"], reply_markup=menu_keyboard(lang))
        return

    # Menu buttons
    if text == T[lang]["btn_create_profile"]:
        await pro(update, context)
        return

    if text == T[lang]["btn_match"]:
        await show_candidate(update, context)
        return

    if text == T[lang]["btn_help"]:
        await update.message.reply_text(T[lang]["help"], reply_markup=menu_keyboard(lang))
        return

    # Profile steps
    if step == "pro_gender":
        g = normalize_gender(lang, text)
        if not g:
            await update.message.reply_text(T[lang]["btn_only"], reply_markup=gender_keyboard(lang))
            return
        set_user(uid, gender=g, step="pro_looking")
        await update.message.reply_text(T[lang]["looking"], reply_markup=looking_keyboard(lang))
        return

    if step == "pro_looking":
        g = normalize_gender(lang, text)
        if not g:
            await update.message.reply_text(T[lang]["btn_only"], reply_markup=looking_keyboard(lang))
            return
        set_user(uid, looking=g, step="pro_age")
        await update.message.reply_text(T[lang]["age"], reply_markup=ReplyKeyboardRemove())
        return

    if step == "pro_age":
        # Requested: strict numeric validation
        if not text.isdigit():
            await update.message.reply_text(T[lang]["age"])
            return

        age = int(text)

        # Requested: auto-ban under 18 + alert
        if age < 18:
            set_user(uid, banned=1, step="idle")
            await update.message.reply_text(T[lang]["underage"], reply_markup=ReplyKeyboardRemove())
            return

        if age > 80:
            await update.message.reply_text(T[lang]["age"])
            return

        set_user(uid, age=age, step="pro_city")
        await update.message.reply_text(T[lang]["city"], reply_markup=city_keyboard())
        return

    if step == "pro_city":
        city = text.upper()
        if city not in ("PP", "SR", "BT", "SHV", "O"):
            await update.message.reply_text(T[lang]["btn_only"], reply_markup=city_keyboard())
            return
        set_user(uid, city=city, step="pro_bio")
        await update.message.reply_text(T[lang]["bio"], reply_markup=ReplyKeyboardRemove())
        return

    if step == "pro_bio":
        if text.upper() == "S":
            set_user(uid, bio="", step="idle")
        else:
            if len(text) > 150:
                await update.message.reply_text(T[lang]["bio"])
                return
            set_user(uid, bio=text, step="idle")
        await update.message.reply_text(T[lang]["saved"], reply_markup=menu_keyboard(lang))
        return

    # Matching buttons
    if text == T[lang]["btn_like"]:
        await handle_like(update, context)
        return
    if text == T[lang]["btn_skip"]:
        await handle_skip(update, context)
        return
    if text == T[lang]["btn_reveal"]:
        await handle_reveal(update, context)
        return

    # Default: show menu (buttons only)
    await update.message.reply_text(T[lang]["btn_only"], reply_markup=menu_keyboard(lang))

# ================= MAIN =================
def main():
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sta", sta))
    app.add_handler(CommandHandler("pro", pro))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))

    print("🔥 DateMeBot running")
    app.run_polling()

if __name__ == "__main__":
    main()