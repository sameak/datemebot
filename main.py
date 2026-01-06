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

ADMIN_IDS = set()
_admin_raw = os.getenv("ADMIN_IDS", "").strip()
if _admin_raw:
    for x in _admin_raw.split(","):
        x = x.strip()
        if x.isdigit():
            ADMIN_IDS.add(int(x))

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
        "btn_profile": "My Profile",
        "btn_edit": "Edit Profile",

        "need_profile": "Please create your profile first ✅\nTap the button below.",
        "btn_only": "Please use the buttons below ⬇️",

        "gender": "Select your sex:",
        "looking": "Looking for:",
        "age_more": "Select your age range:",
        "age": "Select your age:",
        "city": "Choose your city (Cambodia):",
        "bio": "Write a short bio (max 150) or type S to skip.",
        "photo": "Send 1 photo (optional) or tap Skip Photo.",
        "skip_photo": "Skip Photo",

        "saved": "✅ Profile saved!",
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
        "reveal_success_user": "🔓 Identity revealed!\nUsername: @{username}",
        "reveal_no_username": "🔓 Identity revealed!\n(They have no public username.)",
        "reveal_photo_sent": "📸 Photo revealed!",
        "no_stars": "❌ Not enough ⭐ points. You have {stars}.",

        "underage": "🚨 Service not available for under age user right now!",
        "banned": "🚨 Service not available for under age user right now!",

        "edit_age": "Edit Age",
        "edit_city": "Edit City",
        "edit_bio": "Edit Bio",
        "edit_photo": "Edit Photo",
        "done": "Done",
    },
    "kh": {
        "welcome": "💖 ស្វាគមន៍មកកាន់ DateMe\nសូមជ្រើសរើសភាសា។",
        "lang_saved": "អ្នកបានជ្រើសរើសភាសាខ្មែរ\nសូមជ្រើសរើសបន្ត",
        "btn_create_profile": "បង្កើតប្រូហ្វាល់",
        "btn_match": "ស្វែងរកគូ",
        "btn_help": "ជំនួយ",
        "btn_profile": "ប្រូហ្វាល់ខ្ញុំ",
        "btn_edit": "កែប្រែប្រូហ្វាល់",

        "need_profile": "សូមបង្កើតប្រូហ្វាល់ជាមុនសិន ✅\nសូមចុចប៊ូតុងខាងក្រោម។",
        "btn_only": "សូមប្រើប៊ូតុងខាងក្រោម ⬇️",

        "gender": "ជ្រើសរើសភេទ:",
        "looking": "អ្នកកំពុងស្វែងរកដៃគូរ:",
        "age_more": "សូមជ្រើសរើសជួរអាយុ:",
        "age": "សូមជ្រើសរើសអាយុ:",
        "city": "សូមជ្រើសរើសទីក្រុង (កម្ពុជា):",
        "bio": "សូមសរសេរព័ត៌មានខ្លីអំពីអ្នក (មិនលើស 150) ឬវាយ S ដើម្បីរំលង។",
        "photo": "ផ្ញើរូប 1 (ជាជម្រើស) ឬចុច រំលងរូប។",
        "skip_photo": "រំលងរូប",

        "saved": "✅ បានរក្សាទុកប្រូហ្វាល់!",
        "help": "ជំនួយ:\nសូមប្រើប៊ូតុងប៉ុណ្ណោះ។\nStart: start/sta (/start /sta ក៏បាន)\nបង្កើតប្រូហ្វាល់ → ស្វែងរកគូ\n",

        "no_more": "ឥឡូវនេះមិនមានប្រូហ្វាល់អ្នកប្រើផ្សេងទៀតនោះទេ។ សូមសាកល្បងម្តងទៀតពេលក្រោយ។",
        "card": "👤 {sex}, {age}\n📍 {city}\n📝 {bio}\n⭐ ពិន្ទុរបស់អ្នក: {stars}",

        "btn_like": "❤️ ពេញចិត្ត",
        "btn_skip": "⏭ រំលង",
        "btn_reveal": "🔓 បង្ហាញមុខ",

        "matched": "🎉 ត្រូវគ្នា!\nឥឡូវអ្នកអាចបង់ ⭐ ដើម្បីបង្ហាញមុខគ្នា។",
        "reveal_need_match": "🔒 'បង្ហាញមុខ' អាចប្រើបានតែបន្ទាប់ពីត្រូវគ្នា។",
        "reveal_confirm": "🔓 បង្ហាញមុខ ត្រូវការ {cost} ⭐\nចុច 'បង្ហាញមុខ' ម្តងទៀត ដើម្បីបង់។",
        "reveal_paid_wait": "✅ អ្នកបានបង់ {cost} ⭐។ កំពុងរង់ចាំភាគីម្ខាងទៀត…",
        "reveal_success_user": "🔓 បានបង្ហាញអត្តសញ្ញាណ!\nUsername: @{username}",
        "reveal_no_username": "🔓 បានបង្ហាញអត្តសញ្ញាណ!\n(ពួកគេមិនមាន username សាធារណៈទេ។)",
        "reveal_photo_sent": "📸 បានបង្ហាញរូប!",
        "no_stars": "❌ ⭐ មិនគ្រប់គ្រាន់ទេ។ អ្នកមាន {stars}។",

        "underage": "🚨 Service not available for under age user right now!",
        "banned": "🚨 Service not available for under age user right now!",

        "edit_age": "កែអាយុ",
        "edit_city": "កែទីក្រុង",
        "edit_bio": "កែព័ត៌មាន",
        "edit_photo": "កែរូប",
        "done": "រួចរាល់",
    }
}

# ================= CITIES =================
CITIES = [
    ("PP", {"en": "Phnom Penh", "kh": "ភ្នំពេញ"}),
    ("SR", {"en": "Siem Reap", "kh": "សៀមរាប"}),
    ("SHV", {"en": "Sihanoukville", "kh": "ព្រះសីហនុ"}),
    ("BT", {"en": "Battambang", "kh": "បាត់ដំបង"}),
    ("KPC", {"en": "Kampot", "kh": "កំពត"}),
    ("KCM", {"en": "Kampong Cham", "kh": "កំពង់ចាម"}),
    ("KCH", {"en": "Kampong Chhnang", "kh": "កំពង់ឆ្នាំង"}),
    ("KSP", {"en": "Kampong Speu", "kh": "កំពង់ស្ពឺ"}),
    ("O", {"en": "Other", "kh": "ផ្សេងៗ"}),
]

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
        city_key TEXT,
        bio TEXT,
        photo_id TEXT,
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

def get_flags(uid: int):
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
    cur.execute("SELECT gender, looking, age, city_key FROM users WHERE user_id=?", (uid,))
    r = cur.fetchone()
    return bool(r and all(r))

def get_stars(uid: int) -> int:
    cur.execute("SELECT stars FROM users WHERE user_id=?", (uid,))
    r = cur.fetchone()
    return int(r[0]) if r and r[0] is not None else 0

def get_profile(uid: int):
    cur.execute("SELECT gender, looking, age, city_key, bio, photo_id, stars FROM users WHERE user_id=?", (uid,))
    return cur.fetchone()

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
    return ReplyKeyboardMarkup([["K 🇰🇭 ភាសាខ្មែរ", "E 🇬🇧 English"]], resize_keyboard=True)

def menu_keyboard(lang: str):
    return ReplyKeyboardMarkup(
        [[T[lang]["btn_match"], T[lang]["btn_create_profile"]],
         [T[lang]["btn_profile"], T[lang]["btn_edit"]],
         [T[lang]["btn_help"]]],
        resize_keyboard=True
    )

def edit_keyboard(lang: str):
    return ReplyKeyboardMarkup(
        [[T[lang]["edit_age"], T[lang]["edit_city"]],
         [T[lang]["edit_bio"], T[lang]["edit_photo"]],
         [T[lang]["done"]]],
        resize_keyboard=True
    )

def gender_keyboard(lang: str):
    return ReplyKeyboardMarkup([["👨 ប្រុស", "👩 ស្រី"]] if lang == "kh" else [["Male", "Female"]], resize_keyboard=True)

def looking_keyboard(lang: str):
    return gender_keyboard(lang)

def age_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["18", "19", "20", "21"],
            ["22", "23", "24", "25"],
            ["26", "27", "28", "29"],
            ["30", "31-40", "41+"],
        ],
        resize_keyboard=True
    )

def age_31_40_keyboard():
    return ReplyKeyboardMarkup(
        [["31", "32", "33", "34"],
         ["35", "36", "37", "38"],
         ["39", "40"]],
        resize_keyboard=True
    )

def city_keyboard(lang: str):
    rows, row = [], []
    for key, names in CITIES:
        row.append(f"{key} • {names[lang]}")
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

def match_keyboard(lang: str, allow_reveal: bool):
    row1 = [T[lang]["btn_like"], T[lang]["btn_skip"]]
    if allow_reveal:
        return ReplyKeyboardMarkup([row1, [T[lang]["btn_reveal"]]], resize_keyboard=True)
    return ReplyKeyboardMarkup([row1], resize_keyboard=True)

def photo_keyboard(lang: str):
    return ReplyKeyboardMarkup([[T[lang]["skip_photo"]]], resize_keyboard=True)

# ================= NORMALIZERS =================
def normalize_gender(lang: str, text: str):
    t = (text or "").strip().lower()
    if lang == "kh":
        if "ប្រុស" in t:
            return "M"
        if "ស្រី" in t:
            return "F"
        return None
    else:
        if t in ("male", "m"):
            return "M"
        if t in ("female", "f"):
            return "F"
        return None

def normalize_city_key(text: str):
    if not text:
        return None
    s = text.strip().split()[0].upper()
    for key, _ in CITIES:
        if s == key:
            return key
    return None

def city_name(city_key: str, lang: str):
    for key, names in CITIES:
        if key == city_key:
            return names[lang]
    return city_key or "-"

# ================= MATCHING =================
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
      AND u.city_key IS NOT NULL
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

def profile_card(target_id: int, viewer_lang: str, viewer_stars: int):
    cur.execute("SELECT gender, age, city_key, bio FROM users WHERE user_id=?", (target_id,))
    r = cur.fetchone()
    if not r:
        return None
    g, age, ckey, bio = r
    if viewer_lang == "kh":
        sex = "ប្រុស" if g == "M" else "ស្រី"
        empty = "(គ្មាន)"
    else:
        sex = "Male" if g == "M" else "Female"
        empty = "(empty)"
    bio = bio if bio else empty
    city = city_name(ckey, viewer_lang)
    return T[viewer_lang]["card"].format(sex=sex, age=age, city=city, bio=bio, stars=viewer_stars)

# ================= ADMIN =================
def is_admin(uid: int) -> bool:
    return uid in ADMIN_IDS

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        return
    cur.execute("SELECT COUNT(*) FROM users")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE banned=1")
    banned = cur.fetchone()[0]
    await update.message.reply_text(f"Stats:\nUsers: {total}\nBanned: {banned}")

async def cmd_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /ban <user_id>")
        return
    target = int(context.args[0])
    set_user(target, banned=1, step="idle")
    await update.message.reply_text(f"✅ banned {target}")

async def cmd_unb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /unb <user_id>")
        return
    target = int(context.args[0])
    set_user(target, banned=0, step="idle")
    await update.message.reply_text(f"✅ unbanned {target}")

async def cmd_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        return
    if len(context.args) < 2 or (not context.args[0].isdigit()) or (not context.args[1].lstrip("-").isdigit()):
        await update.message.reply_text("Usage: /add <user_id> <stars>")
        return
    target = int(context.args[0])
    delta = int(context.args[1])
    current = get_stars(target)
    set_user(target, stars=max(0, current + delta))
    await update.message.reply_text(f"✅ {target} stars: {current} -> {max(0, current + delta)}")

# ================= CORE =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    upsert(uid)
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

async def show_my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = get_lang(uid)
    p = get_profile(uid)
    if not p:
        await update.message.reply_text(T[lang]["need_profile"], reply_markup=menu_keyboard(lang))
        return
    g, looking, age, ckey, bio, photo_id, stars = p
    if not g or not looking or not age or not ckey:
        await update.message.reply_text(T[lang]["need_profile"], reply_markup=menu_keyboard(lang))
        return

    sex = ("ប្រុស" if g == "M" else "ស្រី") if lang == "kh" else ("Male" if g == "M" else "Female")
    lk = ("ប្រុស" if looking == "M" else "ស្រី") if lang == "kh" else ("Male" if looking == "M" else "Female")
    city = city_name(ckey, lang)
    bio = bio if bio else ("(គ្មាន)" if lang == "kh" else "(empty)")
    has_photo = "✅" if photo_id else "❌"
    msg = (
        f"👤 {sex} | {age}\n"
        f"🔎 {lk}\n"
        f"📍 {city}\n"
        f"📝 {bio}\n"
        f"📸 Photo: {has_photo}\n"
        f"⭐ {stars}"
    )
    await update.message.reply_text(msg, reply_markup=menu_keyboard(lang))

async def edit_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = get_lang(uid)
    if not has_profile(uid):
        await update.message.reply_text(T[lang]["need_profile"], reply_markup=menu_keyboard(lang))
        return
    set_user(uid, step="edit_menu")
    await update.message.reply_text(T[lang]["btn_only"], reply_markup=edit_keyboard(lang))

async def show_candidate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = get_lang(uid)

    if is_banned(uid):
        await update.message.reply_text(T[lang]["banned"], reply_markup=ReplyKeyboardRemove())
        return

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
    allow_reveal = is_matched(uid, cand)
    card = profile_card(cand, lang, stars)
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
            await update.message.reply_text(T[lang]["reveal_success_user"].format(username=other_chat.username))
        else:
            await update.message.reply_text(T[lang]["reveal_no_username"])
        return

    await update.message.reply_text(T[lang]["reveal_paid_wait"].format(cost=REVEAL_COST))

# ================= ROUTER =================
PROFILE_STEPS = {
    "pro_gender", "pro_looking", "pro_age", "pro_age_31_40", "pro_age_41plus",
    "pro_city", "pro_bio", "pro_photo",
    "edit_menu", "edit_age", "edit_city", "edit_bio", "edit_photo",
}

async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    upsert(uid)
    step, lang, banned = get_flags(uid)

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

    # ✅ FIXED: only block when IDLE (never interrupt profile steps)
    if (not has_profile(uid)) and (step == "idle"):
        if text == T[lang]["btn_create_profile"]:
            await pro(update, context)
            return
        if text == T[lang]["btn_help"]:
            await update.message.reply_text(T[lang]["help"], reply_markup=menu_keyboard(lang))
            return
        await update.message.reply_text(T[lang]["need_profile"], reply_markup=menu_keyboard(lang))
        return

    # Menu
    if text == T[lang]["btn_create_profile"]:
        await pro(update, context)
        return
    if text == T[lang]["btn_match"]:
        await show_candidate(update, context)
        return
    if text == T[lang]["btn_help"]:
        await update.message.reply_text(T[lang]["help"], reply_markup=menu_keyboard(lang))
        return
    if text == T[lang]["btn_profile"]:
        await show_my_profile(update, context)
        return
    if text == T[lang]["btn_edit"]:
        await edit_profile(update, context)
        return

    # Edit menu
    if step == "edit_menu":
        if text == T[lang]["edit_age"]:
            set_user(uid, step="edit_age")
            await update.message.reply_text(T[lang]["age_more"], reply_markup=age_keyboard())
            return
        if text == T[lang]["edit_city"]:
            set_user(uid, step="edit_city")
            await update.message.reply_text(T[lang]["city"], reply_markup=city_keyboard(lang))
            return
        if text == T[lang]["edit_bio"]:
            set_user(uid, step="edit_bio")
            await update.message.reply_text(T[lang]["bio"], reply_markup=ReplyKeyboardRemove())
            return
        if text == T[lang]["edit_photo"]:
            set_user(uid, step="edit_photo")
            await update.message.reply_text(T[lang]["photo"], reply_markup=photo_keyboard(lang))
            return
        if text == T[lang]["done"]:
            set_user(uid, step="idle")
            await update.message.reply_text(T[lang]["btn_only"], reply_markup=menu_keyboard(lang))
            return
        await update.message.reply_text(T[lang]["btn_only"], reply_markup=edit_keyboard(lang))
        return

    # Profile creation
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
        await update.message.reply_text(T[lang]["age_more"], reply_markup=age_keyboard())
        return

    if step in ("pro_age", "edit_age"):
        if text == "31-40":
            set_user(uid, step="pro_age_31_40")
            await update.message.reply_text(T[lang]["age"], reply_markup=age_31_40_keyboard())
            return
        if text == "41+":
            set_user(uid, step="pro_age_41plus")
            await update.message.reply_text("Type your age number:", reply_markup=ReplyKeyboardRemove())
            return

        if not text.isdigit():
            await update.message.reply_text(T[lang]["age_more"], reply_markup=age_keyboard())
            return

        age = int(text)
        if age < 18:
            set_user(uid, banned=1, step="idle")
            await update.message.reply_text(T[lang]["underage"], reply_markup=ReplyKeyboardRemove())
            return
        if age > 80:
            await update.message.reply_text(T[lang]["age_more"], reply_markup=age_keyboard())
            return

        set_user(uid, age=age)
        if step == "edit_age":
            set_user(uid, step="edit_menu")
            await update.message.reply_text(T[lang]["saved"], reply_markup=edit_keyboard(lang))
            return

        set_user(uid, step="pro_city")
        await update.message.reply_text(T[lang]["city"], reply_markup=city_keyboard(lang))
        return

    if step == "pro_age_31_40":
        if not text.isdigit():
            await update.message.reply_text(T[lang]["age"], reply_markup=age_31_40_keyboard())
            return
        age = int(text)
        if age < 18:
            set_user(uid, banned=1, step="idle")
            await update.message.reply_text(T[lang]["underage"], reply_markup=ReplyKeyboardRemove())
            return
        if age > 80:
            await update.message.reply_text(T[lang]["age"], reply_markup=age_31_40_keyboard())
            return
        set_user(uid, age=age, step="pro_city")
        await update.message.reply_text(T[lang]["city"], reply_markup=city_keyboard(lang))
        return

    if step == "pro_age_41plus":
        if not text.isdigit():
            await update.message.reply_text("Type your age number:")
            return
        age = int(text)
        if age < 18:
            set_user(uid, banned=1, step="idle")
            await update.message.reply_text(T[lang]["underage"], reply_markup=ReplyKeyboardRemove())
            return
        if age > 80:
            await update.message.reply_text("Type your age number:")
            return
        set_user(uid, age=age, step="pro_city")
        await update.message.reply_text(T[lang]["city"], reply_markup=city_keyboard(lang))
        return

    if step in ("pro_city", "edit_city"):
        ckey = normalize_city_key(text)
        if not ckey:
            await update.message.reply_text(T[lang]["btn_only"], reply_markup=city_keyboard(lang))
            return
        set_user(uid, city_key=ckey)
        if step == "edit_city":
            set_user(uid, step="edit_menu")
            await update.message.reply_text(T[lang]["saved"], reply_markup=edit_keyboard(lang))
            return
        set_user(uid, step="pro_bio")
        await update.message.reply_text(T[lang]["bio"], reply_markup=ReplyKeyboardRemove())
        return

    if step in ("pro_bio", "edit_bio"):
        if text.upper() == "S":
            set_user(uid, bio="")
        else:
            if len(text) > 150:
                await update.message.reply_text(T[lang]["bio"])
                return
            set_user(uid, bio=text)
        if step == "edit_bio":
            set_user(uid, step="edit_menu")
            await update.message.reply_text(T[lang]["saved"], reply_markup=edit_keyboard(lang))
            return
        set_user(uid, step="pro_photo")
        await update.message.reply_text(T[lang]["photo"], reply_markup=photo_keyboard(lang))
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

    await update.message.reply_text(T[lang]["btn_only"], reply_markup=menu_keyboard(lang))

# Photo handler
async def photo_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    upsert(uid)
    step, lang, banned = get_flags(uid)
    if banned == 1:
        await update.message.reply_text(T[lang]["banned"], reply_markup=ReplyKeyboardRemove())
        return
    if step not in ("pro_photo", "edit_photo"):
        return
    if update.message.photo:
        photo_id = update.message.photo[-1].file_id
        set_user(uid, photo_id=photo_id, step="idle")
        await update.message.reply_text(T[lang]["saved"], reply_markup=menu_keyboard(lang))
        await show_my_profile(update, context)

async def skip_photo_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    upsert(uid)
    step, lang, banned = get_flags(uid)
    if banned == 1:
        await update.message.reply_text(T[lang]["banned"], reply_markup=ReplyKeyboardRemove())
        return
    text = (update.message.text or "").strip()
    if step == "pro_photo" and text == T[lang]["skip_photo"]:
        set_user(uid, photo_id="", step="idle")
        await update.message.reply_text(T[lang]["saved"], reply_markup=menu_keyboard(lang))
        await show_my_profile(update, context)
        return
    await router(update, context)

# ================= MAIN =================
def main():
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # user commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sta", sta))
    app.add_handler(CommandHandler("pro", pro))

    # admin commands
    app.add_handler(CommandHandler("sta", cmd_stats))  # only works for admins
    app.add_handler(CommandHandler("ban", cmd_ban))
    app.add_handler(CommandHandler("unb", cmd_unb))
    app.add_handler(CommandHandler("add", cmd_add))

    # photos first
    app.add_handler(MessageHandler(filters.PHOTO, photo_router))

    # text router (also handles Skip Photo)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, skip_photo_router))

    print("🔥 DateMeBot running")
    app.run_polling()

if __name__ == "__main__":
    main()