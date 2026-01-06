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
        "welcome": "💖 Welcome to DateMe\nChoose language",
        "lang_saved": "✅ Language saved.\nChoose an option:",
        "btn_create_profile": "Create Profile",
        "btn_match": "Match",
        "btn_help": "Help",
        "need_profile": "Please create your profile first ✅\nTap Create Profile or type /pro",
        "gender": "Select your sex:",
        "looking": "Looking for:",
        "age": "Enter your age (18+):",
        "city": "Choose your city (Cambodia):",
        "bio": "Write a short bio (max 150) or type S to skip.",
        "saved": "✅ Profile saved!\nTap Match to start browsing.",
        "help": "Help:\nstart/sta (/start /sta also ok)\nCreate Profile button or /pro\nMatch button to browse\n",
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
    },
    "kh": {
        "welcome": "💖 ស្វាគមន៍មកកាន់ DateMe\nជ្រើសរើសភាសា",
        "lang_saved": "✅ បានរក្សាទុកភាសា។\nសូមជ្រើសរើស:",
        "btn_create_profile": "បង្កើតប្រូហ្វាល់",
        "btn_match": "ស្វែងរកគូ",
        "btn_help": "ជំនួយ",
        "need_profile": "សូមបង្កើតប្រូហ្វាល់សិន ✅\nចុច 'បង្កើតប្រូហ្វាល់' ឬវាយ /pro",
        "gender": "ជ្រើសរើសភេទ:",
        "looking": "អ្នកចង់ស្វែងរក:",
        "age": "បញ្ចូលអាយុ (18+):",
        "city": "ជ្រើសរើសទីក្រុង (កម្ពុជា):",
        "bio": "សរសេរព័ត៌មានខ្លី (មិនលើស 150) ឬវាយ S ដើម្បីរំលង។",
        "saved": "✅ បានរក្សាទុកប្រូហ្វាល់!\nចុច 'ស្វែងរកគូ' ដើម្បីចាប់ផ្តើម។",
        "help": "ជំនួយ:\nstart/sta (/start /sta ក៏បាន)\nចុច 'បង្កើតប្រូហ្វាល់' ឬវាយ /pro\nចុច 'ស្វែងរកគូ' ដើម្បីមើលគូ\n",
        "no_more": "ឥឡូវនេះមិនមានប្រូហ្វាល់ទៀតទេ។ សូមសាកល្បងម្តងទៀតពេលក្រោយ។",
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

def get_step(uid: int) -> str:
    cur.execute("SELECT step FROM users WHERE user_id=?", (uid,))
    r = cur.fetchone()
    return r[0] if r else "idle"

def set_user(uid: int, **fields):
    upsert(uid)
    for k, v in fields.items():
        cur.execute(f"UPDATE users SET {k}=? WHERE user_id=?", (v, uid))
    conn.commit()

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

def menu_keyboard(lang: str):
    return ReplyKeyboardMarkup(
        [[T[lang]["btn_match"], T[lang]["btn_create_profile"]],
         [T[lang]["btn_help"]]],
        resize_keyboard=True
    )

def language_keyboard():
    return ReplyKeyboardMarkup(
        [["K 🇰🇭 ភាសាខ្មែរ", "E 🇬🇧 English"]],
        resize_keyboard=True
    )

def gender_keyboard(lang: str):
    return ReplyKeyboardMarkup([["ប្រុស", "ស្រី"]] if lang == "kh" else [["Male", "Female"]], resize_keyboard=True)

def looking_keyboard(lang: str):
    return ReplyKeyboardMarkup([["ប្រុស", "ស្រី"]] if lang == "kh" else [["Male", "Female"]], resize_keyboard=True)

def city_keyboard():
    # Cambodia only (short codes are easy)
    return ReplyKeyboardMarkup([["PP", "SR", "BT"], ["SHV", "O"]], resize_keyboard=True)

def match_keyboard(lang: str, allow_reveal: bool):
    row1 = [T[lang]["btn_like"], T[lang]["btn_skip"]]
    if allow_reveal:
        return ReplyKeyboardMarkup([row1, [T[lang]["btn_reveal"]]], resize_keyboard=True)
    return ReplyKeyboardMarkup([row1], resize_keyboard=True)

def normalize_gender(lang: str, text: str):
    t = (text or "").strip().lower()
    if lang == "kh":
        if t == "ប្រុស":
            return "M"
        if t == "ស្រី":
            return "F"
    else:
        if t in ("male", "m"):
            return "M"
        if t in ("female", "f"):
            return "F"
    return None

def find_candidate(uid: int):
    # Candidate must match looking/gender filters
    cur.execute("SELECT gender, looking FROM users WHERE user_id=?", (uid,))
    me = cur.fetchone()
    if not me or not me[0] or not me[1]:
        return None
    my_gender, my_looking = me[0], me[1]

    # show profiles whose gender == my_looking and looking == my_gender
    # exclude liked/skipped/matched and self
    cur.execute("""
    SELECT u.user_id
    FROM users u
    WHERE u.user_id != ?
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
    else:
        sex = "Male" if g == "M" else "Female"
    bio = bio if bio else ("(គ្មាន)" if viewer_lang == "kh" else "(empty)")
    return T[viewer_lang]["card"].format(sex=sex, age=age, city=city, bio=bio, stars=viewer_stars)

def set_reveal_paid(payer: int, other: int, paid: int):
    cur.execute("INSERT OR IGNORE INTO reveal_pay (payer, other, paid) VALUES (?,?,0)", (payer, other))
    cur.execute("UPDATE reveal_pay SET paid=? WHERE payer=? AND other=?", (paid, payer, other))
    conn.commit()

def is_reveal_paid(payer: int, other: int) -> bool:
    cur.execute("SELECT paid FROM reveal_pay WHERE payer=? AND other=? LIMIT 1", (payer, other))
    r = cur.fetchone()
    return bool(r and r[0] == 1)

# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    upsert(uid)
    lang = get_lang(uid)
    set_user(uid, step="lang")
    await update.message.reply_text(T[lang]["welcome"], reply_markup=language_keyboard())

async def sta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def pro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    upsert(uid)
    lang = get_lang(uid)
    set_user(uid, step="pro_gender")
    await update.message.reply_text(T[lang]["gender"], reply_markup=gender_keyboard(lang))

async def show_candidate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = get_lang(uid)

    if not has_profile(uid):
        await update.message.reply_text(T[lang]["need_profile"], reply_markup=menu_keyboard(lang))
        return

    cand = find_candidate(uid)
    if not cand:
        reset_current(context)
        await update.message.reply_text(T[lang]["no_more"], reply_markup=menu_keyboard(lang))
        return

    set_current(context, cand)
    stars = get_stars(uid)

    # reveal button only if already matched (normally it won't show here yet)
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

    # if the other also liked me -> match
    if is_liked(target, uid):
        make_match(uid, target)
        # notify both sides (still anonymous)
        await update.message.reply_text(T[lang]["matched"], reply_markup=match_keyboard(lang, True))
        try:
            other_lang = get_lang(target)
            await context.bot.send_message(chat_id=target, text=T[other_lang]["matched"], reply_markup=match_keyboard(other_lang, True))
        except Exception:
            pass
    else:
        await update.message.reply_text("✅" if lang == "en" else "✅")

    # show next
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

    # two-tap confirmation: first tap sets a flag, second tap charges
    flag_key = f"reveal_confirm_{target}"
    if not context.user_data.get(flag_key):
        context.user_data[flag_key] = True
        await update.message.reply_text(T[lang]["reveal_confirm"].format(cost=REVEAL_COST))
        return

    # clear confirm flag
    context.user_data.pop(flag_key, None)

    # charge stars
    stars = get_stars(uid)
    if stars < REVEAL_COST:
        await update.message.reply_text(T[lang]["no_stars"].format(stars=stars))
        return

    set_user(uid, stars=stars - REVEAL_COST)
    set_reveal_paid(uid, target, 1)

    # if both paid -> reveal usernames to each other
    if is_reveal_paid(uid, target) and is_reveal_paid(target, uid):
        # reveal to uid
        other_chat = await context.bot.get_chat(target)
        if other_chat.username:
            await update.message.reply_text(T[lang]["reveal_success"].format(username=other_chat.username))
        else:
            await update.message.reply_text(T[lang]["reveal_no_username"])

        # reveal to target
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

    text = (update.message.text or "").strip()
    t = text.lower()
    step = get_step(uid)
    lang = get_lang(uid)

    # start shortcuts without slash
    if t in ("start", "sta"):
        await start(update, context)
        return

    # language selection
    if step == "lang":
        if text.upper().startswith("K"):
            set_user(uid, lang="kh", step="idle")
            await update.message.reply_text(T["kh"]["lang_saved"], reply_markup=menu_keyboard("kh"))
            return
        if text.upper().startswith("E"):
            set_user(uid, lang="en", step="idle")
            await update.message.reply_text(T["en"]["lang_saved"], reply_markup=menu_keyboard("en"))
            return
        await update.message.reply_text(T[lang]["welcome"], reply_markup=language_keyboard())
        return

    # menu buttons
    if text in (T["en"]["btn_create_profile"], T["kh"]["btn_create_profile"]) or t == "pro":
        await pro(update, context)
        return

    if text in (T["en"]["btn_match"], T["kh"]["btn_match"]):
        await show_candidate(update, context)
        return

    if text in (T["en"]["btn_help"], T["kh"]["btn_help"]):
        await update.message.reply_text(T[lang]["help"], reply_markup=menu_keyboard(lang))
        return

    # profile steps
    if step == "pro_gender":
        g = normalize_gender(lang, text)
        if not g:
            await update.message.reply_text(T[lang]["gender"], reply_markup=gender_keyboard(lang))
            return
        set_user(uid, gender=g, step="pro_looking")
        await update.message.reply_text(T[lang]["looking"], reply_markup=looking_keyboard(lang))
        return

    if step == "pro_looking":
        g = normalize_gender(lang, text)
        if not g:
            await update.message.reply_text(T[lang]["looking"], reply_markup=looking_keyboard(lang))
            return
        set_user(uid, looking=g, step="pro_age")
        await update.message.reply_text(T[lang]["age"], reply_markup=ReplyKeyboardRemove())
        return

    if step == "pro_age":
        if not text.isdigit():
            await update.message.reply_text(T[lang]["age"])
            return
        age = int(text)
        if age < 18 or age > 80:
            await update.message.reply_text(T[lang]["age"])
            return
        set_user(uid, age=age, step="pro_city")
        await update.message.reply_text(T[lang]["city"], reply_markup=city_keyboard())
        return

    if step == "pro_city":
        city = text.upper()
        if city not in ("PP", "SR", "BT", "SHV", "O"):
            await update.message.reply_text(T[lang]["city"], reply_markup=city_keyboard())
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

    # matching buttons
    if text == T[lang]["btn_like"]:
        await handle_like(update, context)
        return
    if text == T[lang]["btn_skip"]:
        await handle_skip(update, context)
        return
    if text == T[lang]["btn_reveal"]:
        await handle_reveal(update, context)
        return

    # default
    await update.message.reply_text(T[lang]["help"], reply_markup=menu_keyboard(lang))

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