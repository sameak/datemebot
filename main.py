import os
import psycopg2
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

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing. Add Railway Postgres and connect it to this service.")

DEFAULT_STARS = 3
REVEAL_COST = 1

ADMIN_IDS = set()
_admin_raw = os.getenv("ADMIN_IDS", "").strip()
if _admin_raw:
    for x in _admin_raw.split(","):
        x = x.strip()
        if x.isdigit():
            ADMIN_IDS.add(int(x))

def is_admin(uid: int) -> bool:
    return uid in ADMIN_IDS

# ================= TEXT =================
T = {
    "en": {
        "welcome": "💖 Welcome to DateMe\nPlease choose language.",
        "lang_saved": "✅ Language saved.\nChoose an option:",
        "btn_only": "Please use the buttons below ⬇️",

        "btn_match": "Match",
        "btn_create_profile": "Create Profile",
        "btn_profile": "My Profile",
        "btn_edit": "Edit Profile",
        "btn_help": "Help",
        "btn_admin": "Admin Panel",

        "need_profile": "Please create your profile first ✅\nTap Create Profile.",
        "help": "Help:\nUse buttons.\nStart: start/sta (/start /sta ok)\n",

        "gender": "Select your sex:",
        "looking": "Looking for:",
        "age_pick": "Select your age:",
        "age_type": "Type your age (18-80):",
        "city": "Choose your city (Cambodia):",
        "bio": "Write a short bio (max 150) or tap Skip Bio.",
        "skip_bio": "Skip Bio",
        "photo": "Send 1 photo (optional) or tap Skip Photo.",
        "skip_photo": "Skip Photo",

        "saved": "✅ Profile saved!",
        "underage": "🚨 Service not available for under age user right now!",
        "banned": "🚨 Service not available for under age user right now!",

        "no_more": "No more profiles right now. Try later.",
        "card": "👤 {sex}, {age}\n📍 {city}\n📝 {bio}\n⭐ Your points: {stars}",

        "btn_like": "❤️ Like",
        "btn_skip": "⏭ Skip",
        "btn_reveal": "🔓 Reveal",
        "btn_report": "🚩 Report",

        "report_q": "🚩 Report this user. Choose a reason:",
        "report_done": "✅ Report sent. Thank you.",
        "rep_spam": "Spam/Ads",
        "rep_fake": "Fake profile",
        "rep_bad": "Harassment",
        "rep_other": "Other",

        "matched": "🎉 It's a match!\nPay ⭐ to reveal each other.",
        "reveal_need_match": "🔒 Reveal is only after you match.",
        "reveal_confirm": "🔓 Reveal costs {cost} ⭐.\nPress Reveal again to pay.",
        "reveal_paid_wait": "✅ You paid {cost} ⭐. Waiting for the other user to pay…",
        "reveal_success_user": "🔓 Identity revealed!\nUsername: @{username}",
        "reveal_no_username": "🔓 Identity revealed!\n(They have no public username.)",
        "reveal_photo_sent": "📸 Photo revealed!",
        "no_stars": "❌ Not enough ⭐. You have {stars}.",

        "edit_menu": "Choose what to edit:",
        "edit_age": "Edit Age",
        "edit_city": "Edit City",
        "edit_bio": "Edit Bio",
        "edit_photo": "Edit Photo",
        "done": "Done",

        "admin_menu": "🛠 Admin Panel (buttons only):",
        "adm_stats": "📊 Stats",
        "adm_reports": "🧾 View Reports",
        "adm_ban_reply": "🚫 Ban Replied User",
        "adm_unban_reply": "✅ Unban Replied User",
        "adm_star_reply": "⭐ +3 Stars Replied User",
        "adm_close": "❌ Close",

        "adm_need_reply": "Reply to a user's message first, then tap this button.",
        "adm_banned_ok": "✅ Banned user_id: {uid}",
        "adm_unbanned_ok": "✅ Unbanned user_id: {uid}",
        "adm_star_ok": "✅ Added +3 ⭐ to user_id: {uid}",
        "adm_reports_empty": "No reports yet.",
        "adm_reports_title": "🧾 Latest reports (last 10):",
        "my_id": "Your ID is: {uid}",
    },
    "kh": {
        "welcome": "💖 ស្វាគមន៍មកកាន់ DateMe\nសូមជ្រើសរើសភាសា។",
        "lang_saved": "អ្នកបានជ្រើសរើសភាសាខ្មែរ\nសូមជ្រើសរើសបន្ត",
        "btn_only": "សូមប្រើប៊ូតុងខាងក្រោម ⬇️",

        "btn_match": "ស្វែងរកគូ",
        "btn_create_profile": "បង្កើតប្រូហ្វាល់",
        "btn_profile": "ប្រូហ្វាល់ខ្ញុំ",
        "btn_edit": "កែប្រែប្រូហ្វាល់",
        "btn_help": "ជំនួយ",
        "btn_admin": "ផ្ទាំងអ្នកគ្រប់គ្រង",

        "need_profile": "សូមបង្កើតប្រូហ្វាល់ជាមុនសិន ✅\nសូមចុច បង្កើតប្រូហ្វាល់",
        "help": "ជំនួយ:\nសូមប្រើប៊ូតុង។\nStart: start/sta (/start /sta ក៏បាន)\n",

        "gender": "ជ្រើសរើសភេទ:",
        "looking": "អ្នកកំពុងស្វែងរកដៃគូរ:",
        "age_pick": "សូមជ្រើសរើសអាយុ:",
        "age_type": "សូមវាយអាយុ (18-80):",
        "city": "សូមជ្រើសរើសទីក្រុង (កម្ពុជា):",
        "bio": "សូមសរសេរព័ត៌មានខ្លី (មិនលើស 150) ឬចុច រំលងព័ត៌មាន",
        "skip_bio": "រំលងព័ត៌មាន",
        "photo": "ផ្ញើរូប 1 (ជាជម្រើស) ឬចុច រំលងរូប",
        "skip_photo": "រំលងរូប",

        "saved": "✅ បានរក្សាទុកប្រូហ្វាល់!",
        "underage": "🚨 Service not available for under age user right now!",
        "banned": "🚨 Service not available for under age user right now!",

        "no_more": "ឥឡូវនេះមិនមានប្រូហ្វាល់អ្នកប្រើផ្សេងទៀតនោះទេ។ សូមសាកល្បងពេលក្រោយ។",
        "card": "👤 {sex}, {age}\n📍 {city}\n📝 {bio}\n⭐ ពិន្ទុរបស់អ្នក: {stars}",

        "btn_like": "❤️ ពេញចិត្ត",
        "btn_skip": "⏭ រំលង",
        "btn_reveal": "🔓 បង្ហាញមុខ",
        "btn_report": "🚩 រាយការណ៍",

        "report_q": "🚩 រាយការណ៍អ្នកនេះ។ សូមជ្រើសរើសមូលហេតុ:",
        "report_done": "✅ បានផ្ញើរាយការណ៍។ អរគុណ។",
        "rep_spam": "សារផ្សព្វផ្សាយ",
        "rep_fake": "ប្រូហ្វាល់ក្លែងក្លាយ",
        "rep_bad": "រំខាន/បំពាន",
        "rep_other": "ផ្សេងៗ",

        "matched": "🎉 ត្រូវគ្នា!\nសូមបង់ ⭐ ដើម្បីបង្ហាញមុខគ្នា។",
        "reveal_need_match": "🔒 'បង្ហាញមុខ' អាចប្រើបានតែបន្ទាប់ពីត្រូវគ្នា។",
        "reveal_confirm": "🔓 បង្ហាញមុខ ត្រូវការ {cost} ⭐\nចុចម្តងទៀត ដើម្បីបង់។",
        "reveal_paid_wait": "✅ អ្នកបានបង់ {cost} ⭐។ កំពុងរង់ចាំភាគីម្ខាងទៀត…",
        "reveal_success_user": "🔓 បានបង្ហាញអត្តសញ្ញាណ!\nUsername: @{username}",
        "reveal_no_username": "🔓 បានបង្ហាញអត្តសញ្ញាណ!\n(ពួកគេមិនមាន username សាធារណៈទេ។)",
        "reveal_photo_sent": "📸 បានបង្ហាញរូប!",
        "no_stars": "❌ ⭐ មិនគ្រប់គ្រាន់ទេ។ អ្នកមាន {stars}។",

        "edit_menu": "សូមជ្រើសរើសចង់កែអ្វី:",
        "edit_age": "កែអាយុ",
        "edit_city": "កែទីក្រុង",
        "edit_bio": "កែព័ត៌មាន",
        "edit_photo": "កែរូប",
        "done": "រួចរាល់",

        "admin_menu": "🛠 ផ្ទាំងអ្នកគ្រប់គ្រង (ប៊ូតុងប៉ុណ្ណោះ):",
        "adm_stats": "📊 ស្ថិតិ",
        "adm_reports": "🧾 មើលរាយការណ៍",
        "adm_ban_reply": "🚫 បិទ Replied User",
        "adm_unban_reply": "✅ ដោះបិទ Replied User",
        "adm_star_reply": "⭐ +3 Stars Replied User",
        "adm_close": "❌ បិទ",

        "adm_need_reply": "សូម Reply ទៅសាររបស់អ្នកប្រើជាមុនសិន ហើយចុចប៊ូតុងនេះ។",
        "adm_banned_ok": "✅ បានបិទ user_id: {uid}",
        "adm_unbanned_ok": "✅ បានដោះបិទ user_id: {uid}",
        "adm_star_ok": "✅ បានបន្ថែម +3 ⭐ ទៅ user_id: {uid}",
        "adm_reports_empty": "មិនទាន់មានរាយការណ៍ទេ។",
        "adm_reports_title": "🧾 រាយការណ៍ថ្មីៗ (10 ចុងក្រោយ):",
        "my_id": "ID របស់អ្នកគឺ: {uid}",
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
    ("KSP", {"en": "Kampong Speu", "kh": "កំពង់ស្ពឺ"}),
    ("O", {"en": "Other", "kh": "ផ្សេងៗ"}),
]

# ================= DB =================
conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True

def db_exec(sql: str, params=None):
    with conn.cursor() as c:
        c.execute(sql, params or ())

def db_one(sql: str, params=None):
    with conn.cursor() as c:
        c.execute(sql, params or ())
        return c.fetchone()

def db_all(sql: str, params=None):
    with conn.cursor() as c:
        c.execute(sql, params or ())
        return c.fetchall()

def init_db():
    db_exec("""
    CREATE TABLE IF NOT EXISTS users (
        user_id BIGINT PRIMARY KEY,
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
    db_exec("""
    CREATE TABLE IF NOT EXISTS likes (
        from_user BIGINT,
        to_user BIGINT,
        UNIQUE(from_user, to_user)
    )
    """)
    db_exec("""
    CREATE TABLE IF NOT EXISTS skips (
        from_user BIGINT,
        to_user BIGINT,
        UNIQUE(from_user, to_user)
    )
    """)
    db_exec("""
    CREATE TABLE IF NOT EXISTS matches (
        user1 BIGINT,
        user2 BIGINT,
        UNIQUE(user1, user2)
    )
    """)
    db_exec("""
    CREATE TABLE IF NOT EXISTS reveal_pay (
        payer BIGINT,
        other BIGINT,
        paid INTEGER DEFAULT 0,
        UNIQUE(payer, other)
    )
    """)
    db_exec("""
    CREATE TABLE IF NOT EXISTS reports (
        id BIGSERIAL PRIMARY KEY,
        reporter BIGINT NOT NULL,
        reported BIGINT NOT NULL,
        reason TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT NOW()
    )
    """)

def upsert(uid: int):
    db_exec("INSERT INTO users (user_id, stars) VALUES (%s, %s) ON CONFLICT (user_id) DO NOTHING", (uid, DEFAULT_STARS))

def get_lang(uid: int) -> str:
    r = db_one("SELECT lang FROM users WHERE user_id=%s", (uid,))
    return r[0] if r else "en"

def get_flags(uid: int):
    r = db_one("SELECT step, lang, banned FROM users WHERE user_id=%s", (uid,))
    return r if r else ("idle", "en", 0)

def set_user(uid: int, **fields):
    upsert(uid)
    for k, v in fields.items():
        db_exec(f"UPDATE users SET {k}=%s WHERE user_id=%s", (v, uid))

def is_banned(uid: int) -> bool:
    r = db_one("SELECT banned FROM users WHERE user_id=%s", (uid,))
    return bool(r and r[0] == 1)

def has_profile(uid: int) -> bool:
    r = db_one("SELECT gender, looking, age, city_key FROM users WHERE user_id=%s", (uid,))
    return bool(r and all(r))

def get_stars(uid: int) -> int:
    r = db_one("SELECT stars FROM users WHERE user_id=%s", (uid,))
    return int(r[0]) if r and r[0] is not None else 0

def add_like(a: int, b: int):
    db_exec("INSERT INTO likes (from_user, to_user) VALUES (%s,%s) ON CONFLICT DO NOTHING", (a, b))

def add_skip(a: int, b: int):
    db_exec("INSERT INTO skips (from_user, to_user) VALUES (%s,%s) ON CONFLICT DO NOTHING", (a, b))

def is_liked(a: int, b: int) -> bool:
    r = db_one("SELECT 1 FROM likes WHERE from_user=%s AND to_user=%s LIMIT 1", (a, b))
    return r is not None

def is_matched(a: int, b: int) -> bool:
    u1, u2 = sorted([a, b])
    r = db_one("SELECT 1 FROM matches WHERE user1=%s AND user2=%s LIMIT 1", (u1, u2))
    return r is not None

def make_match(a: int, b: int):
    u1, u2 = sorted([a, b])
    db_exec("INSERT INTO matches (user1, user2) VALUES (%s,%s) ON CONFLICT DO NOTHING", (u1, u2))

def set_reveal_paid(payer: int, other: int, paid: int):
    db_exec("INSERT INTO reveal_pay (payer, other, paid) VALUES (%s,%s,0) ON CONFLICT DO NOTHING", (payer, other))
    db_exec("UPDATE reveal_pay SET paid=%s WHERE payer=%s AND other=%s", (paid, payer, other))

def is_reveal_paid(payer: int, other: int) -> bool:
    r = db_one("SELECT paid FROM reveal_pay WHERE payer=%s AND other=%s LIMIT 1", (payer, other))
    return bool(r and r[0] == 1)

def get_user_profile(uid: int):
    return db_one("SELECT gender, looking, age, city_key, bio, photo_id, stars FROM users WHERE user_id=%s", (uid,))

def add_report(reporter: int, reported: int, reason: str):
    db_exec("INSERT INTO reports (reporter, reported, reason) VALUES (%s,%s,%s)", (reporter, reported, reason))

# ================= KEYBOARDS =================
def kb_language():
    return ReplyKeyboardMarkup([["K 🇰🇭 ភាសាខ្មែរ", "E 🇬🇧 English"]], resize_keyboard=True)

def kb_menu(lang: str, uid: int):
    base = [
        [T[lang]["btn_match"], T[lang]["btn_create_profile"]],
        [T[lang]["btn_profile"], T[lang]["btn_edit"]],
        [T[lang]["btn_help"]],
    ]
    if is_admin(uid):
        base.append([T[lang]["btn_admin"]])
    return ReplyKeyboardMarkup(base, resize_keyboard=True)

def kb_gender(lang: str):
    return ReplyKeyboardMarkup([["👨 ប្រុស", "👩 ស្រី"]] if lang == "kh" else [["Male", "Female"]], resize_keyboard=True)

def kb_age(lang: str):
    return ReplyKeyboardMarkup(
        [
            ["18", "19", "20", "21"],
            ["22", "23", "24", "25"],
            ["26", "27", "28", "29"],
            ["30", "31", "32", "33"],
            ["34", "35", "36", "37"],
            ["38", "39", "40", "41+"],
        ],
        resize_keyboard=True,
    )

def kb_city(lang: str):
    rows, row = [], []
    for key, names in CITIES:
        row.append(f"{key} • {names[lang]}")
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

def kb_bio(lang: str):
    return ReplyKeyboardMarkup([[T[lang]["skip_bio"]]], resize_keyboard=True)

def kb_photo(lang: str):
    return ReplyKeyboardMarkup([[T[lang]["skip_photo"]]], resize_keyboard=True)

def kb_match(lang: str, allow_reveal: bool):
    row1 = [T[lang]["btn_like"], T[lang]["btn_skip"]]
    row2 = [T[lang]["btn_report"]]
    if allow_reveal:
        row1 = [T[lang]["btn_like"], T[lang]["btn_skip"], T[lang]["btn_reveal"]]
    return ReplyKeyboardMarkup([row1, row2], resize_keyboard=True)

def kb_report(lang: str):
    return ReplyKeyboardMarkup(
        [[T[lang]["rep_spam"], T[lang]["rep_fake"]],
         [T[lang]["rep_bad"], T[lang]["rep_other"]]],
        resize_keyboard=True
    )

def kb_edit(lang: str):
    return ReplyKeyboardMarkup(
        [
            [T[lang]["edit_age"], T[lang]["edit_city"]],
            [T[lang]["edit_bio"], T[lang]["edit_photo"]],
            [T[lang]["done"]],
        ],
        resize_keyboard=True,
    )

def kb_admin(lang: str):
    return ReplyKeyboardMarkup(
        [
            [T[lang]["adm_stats"], T[lang]["adm_reports"]],
            [T[lang]["adm_ban_reply"], T[lang]["adm_unban_reply"]],
            [T[lang]["adm_star_reply"]],
            [T[lang]["adm_close"]],
        ],
        resize_keyboard=True,
    )

# ================= HELPERS =================
def normalize_gender(lang: str, text: str):
    t = (text or "").strip().lower()
    if lang == "kh":
        if "ប្រុស" in t:
            return "M"
        if "ស្រី" in t:
            return "F"
        return None
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

def set_current(context: ContextTypes.DEFAULT_TYPE, target_id: int):
    context.user_data["current_target"] = target_id

def get_current(context: ContextTypes.DEFAULT_TYPE):
    return context.user_data.get("current_target")

def reset_current(context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("current_target", None)

def find_candidate(uid: int):
    me = db_one("SELECT gender, looking FROM users WHERE user_id=%s", (uid,))
    if not me or not me[0] or not me[1]:
        return None
    my_gender, my_looking = me[0], me[1]
    r = db_one(
        """
        SELECT u.user_id
        FROM users u
        WHERE u.user_id != %s
          AND u.banned = 0
          AND u.gender = %s
          AND u.looking = %s
          AND u.age IS NOT NULL
          AND u.city_key IS NOT NULL
          AND u.user_id NOT IN (SELECT to_user FROM likes WHERE from_user=%s)
          AND u.user_id NOT IN (SELECT to_user FROM skips WHERE from_user=%s)
          AND u.user_id NOT IN (
              SELECT CASE WHEN user1=%s THEN user2 ELSE user1 END
              FROM matches
              WHERE user1=%s OR user2=%s
          )
        ORDER BY RANDOM()
        LIMIT 1
        """,
        (uid, my_looking, my_gender, uid, uid, uid, uid, uid),
    )
    return r[0] if r else None

def profile_card(target_id: int, viewer_lang: str, viewer_stars: int):
    r = db_one("SELECT gender, age, city_key, bio FROM users WHERE user_id=%s", (target_id,))
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

# ================= COMMANDS =================
async def cmd_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = get_lang(uid)
    await update.message.reply_text(T[lang]["my_id"].format(uid=uid))

# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    upsert(uid)
    lang = get_lang(uid)
    if is_banned(uid):
        await update.message.reply_text(T[lang]["banned"], reply_markup=ReplyKeyboardRemove())
        return
    set_user(uid, step="lang")
    await update.message.reply_text(T[lang]["welcome"], reply_markup=kb_language())

async def sta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = get_lang(uid)
    await update.message.reply_text(T[lang]["btn_only"], reply_markup=kb_menu(lang, uid))

async def create_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = get_lang(uid)
    if is_banned(uid):
        await update.message.reply_text(T[lang]["banned"], reply_markup=ReplyKeyboardRemove())
        return
    set_user(uid, step="pro_gender")
    await update.message.reply_text(T[lang]["gender"], reply_markup=kb_gender(lang))

async def my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = get_lang(uid)
    p = get_user_profile(uid)
    if not p:
        await update.message.reply_text(T[lang]["need_profile"], reply_markup=kb_menu(lang, uid))
        return
    g, looking, age, ckey, bio, photo_id, stars = p
    if not g or not looking or not age or not ckey:
        await update.message.reply_text(T[lang]["need_profile"], reply_markup=kb_menu(lang, uid))
        return
    sex = ("ប្រុស" if g == "M" else "ស្រី") if lang == "kh" else ("Male" if g == "M" else "Female")
    lk = ("ប្រុស" if looking == "M" else "ស្រី") if lang == "kh" else ("Male" if looking == "M" else "Female")
    city = city_name(ckey, lang)
    bio_txt = bio if bio else ("(គ្មាន)" if lang == "kh" else "(empty)")
    has_photo = "✅" if photo_id else "❌"
    msg = f"👤 {sex} | {age}\n🔎 {lk}\n📍 {city}\n📝 {bio_txt}\n📸 Photo: {has_photo}\n⭐ {stars}"
    await update.message.reply_text(msg, reply_markup=kb_menu(lang, uid))

async def edit_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = get_lang(uid)
    if not has_profile(uid):
        await update.message.reply_text(T[lang]["need_profile"], reply_markup=kb_menu(lang, uid))
        return
    set_user(uid, step="edit_menu")
    await update.message.reply_text(T[lang]["edit_menu"], reply_markup=kb_edit(lang))

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = get_lang(uid)
    if not is_admin(uid):
        await update.message.reply_text(T[lang]["btn_only"], reply_markup=kb_menu(lang, uid))
        return
    set_user(uid, step="admin_menu")
    await update.message.reply_text(T[lang]["admin_menu"], reply_markup=kb_admin(lang))

async def show_candidate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = get_lang(uid)
    if is_banned(uid):
        await update.message.reply_text(T[lang]["banned"], reply_markup=ReplyKeyboardRemove())
        return
    if not has_profile(uid):
        await update.message.reply_text(T[lang]["need_profile"], reply_markup=kb_menu(lang, uid))
        return

    cand = find_candidate(uid)
    if not cand:
        reset_current(context)
        await update.message.reply_text(T[lang]["no_more"], reply_markup=kb_menu(lang, uid))
        return

    set_current(context, cand)
    stars = get_stars(uid)
    allow_reveal = is_matched(uid, cand)
    card = profile_card(cand, lang, stars)
    await update.message.reply_text(card, reply_markup=kb_match(lang, allow_reveal))

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
        await update.message.reply_text(T[lang]["matched"], reply_markup=kb_match(lang, True))
        try:
            other_lang = get_lang(target)
            await context.bot.send_message(chat_id=target, text=T[other_lang]["matched"], reply_markup=kb_match(other_lang, True))
        except Exception:
            pass

    await show_candidate(update, context)

async def handle_skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    target = get_current(context)
    if target:
        add_skip(uid, target)
    await show_candidate(update, context)

async def handle_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = get_lang(uid)
    target = get_current(context)
    if not target:
        await show_menu(update, context)
        return
    set_user(uid, step="report_reason")
    await update.message.reply_text(T[lang]["report_q"], reply_markup=kb_report(lang))

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
        other_profile = get_user_profile(target)
        other_photo_id = other_profile[5] if other_profile else None

        if other_chat.username:
            await update.message.reply_text(T[lang]["reveal_success_user"].format(username=other_chat.username))
        else:
            await update.message.reply_text(T[lang]["reveal_no_username"])

        if other_photo_id:
            try:
                await context.bot.send_photo(chat_id=uid, photo=other_photo_id, caption=T[lang]["reveal_photo_sent"])
            except Exception:
                pass

        try:
            me_chat = await context.bot.get_chat(uid)
            me_profile = get_user_profile(uid)
            me_photo_id = me_profile[5] if me_profile else None
            other_lang = get_lang(target)

            if me_chat.username:
                await context.bot.send_message(chat_id=target, text=T[other_lang]["reveal_success_user"].format(username=me_chat.username))
            else:
                await context.bot.send_message(chat_id=target, text=T[other_lang]["reveal_no_username"])

            if me_photo_id:
                try:
                    await context.bot.send_photo(chat_id=target, photo=me_photo_id, caption=T[other_lang]["reveal_photo_sent"])
                except Exception:
                    pass
        except Exception:
            pass
        return

    await update.message.reply_text(T[lang]["reveal_paid_wait"].format(cost=REVEAL_COST))

# ================= PHOTO ROUTER =================
async def photo_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    upsert(uid)
    step, lang, banned = get_flags(uid)
    if banned == 1:
        return
    if step not in ("pro_photo", "edit_photo"):
        return
    if update.message.photo:
        photo_id = update.message.photo[-1].file_id
        set_user(uid, photo_id=photo_id)
        if step == "edit_photo":
            set_user(uid, step="edit_menu")
            await update.message.reply_text(T[lang]["saved"], reply_markup=kb_edit(lang))
            return
        set_user(uid, step="idle")
        await update.message.reply_text(T[lang]["saved"], reply_markup=kb_menu(lang, uid))

# ================= ROUTER =================
async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    upsert(uid)

    step, lang, banned = get_flags(uid)
    text = (update.message.text or "").strip()
    low = text.lower()

    if banned == 1:
        await update.message.reply_text(T[lang]["banned"], reply_markup=ReplyKeyboardRemove())
        return

    if low in ("start", "sta"):
        await start(update, context)
        return

    # language
    if step == "lang":
        if text.upper().startswith("K"):
            set_user(uid, lang="kh", step="idle")
            await update.message.reply_text(T["kh"]["lang_saved"], reply_markup=kb_menu("kh", uid))
            return
        if text.upper().startswith("E"):
            set_user(uid, lang="en", step="idle")
            await update.message.reply_text(T["en"]["lang_saved"], reply_markup=kb_menu("en", uid))
            return
        await update.message.reply_text(T[lang]["btn_only"], reply_markup=kb_language())
        return

    # If profile incomplete and idle -> force Create Profile
    if (not has_profile(uid)) and (step == "idle"):
        if text == T[lang]["btn_create_profile"]:
            await create_profile(update, context)
            return
        await update.message.reply_text(T[lang]["need_profile"], reply_markup=kb_menu(lang, uid))
        return

    # menu buttons
    if text == T[lang]["btn_create_profile"]:
        await create_profile(update, context); return
    if text == T[lang]["btn_match"]:
        await show_candidate(update, context); return
    if text == T[lang]["btn_profile"]:
        await my_profile(update, context); return
    if text == T[lang]["btn_edit"]:
        await edit_profile(update, context); return
    if text == T[lang]["btn_help"]:
        await update.message.reply_text(T[lang]["help"], reply_markup=kb_menu(lang, uid)); return
    if text == T[lang]["btn_admin"]:
        await admin_panel(update, context); return

    # admin panel actions (buttons only)
    if step == "admin_menu":
        if not is_admin(uid):
            await show_menu(update, context); return

        if text == T[lang]["adm_close"]:
            set_user(uid, step="idle")
            await show_menu(update, context)
            return

        if text == T[lang]["adm_stats"]:
            total = db_one("SELECT COUNT(*) FROM users")[0]
            banned_count = db_one("SELECT COUNT(*) FROM users WHERE banned=1")[0]
            await update.message.reply_text(f"Stats:\nUsers: {total}\nBanned: {banned_count}", reply_markup=kb_admin(lang))
            return

        if text == T[lang]["adm_reports"]:
            rows = db_all("SELECT reporter, reported, reason, created_at FROM reports ORDER BY id DESC LIMIT 10")
            if not rows:
                await update.message.reply_text(T[lang]["adm_reports_empty"], reply_markup=kb_admin(lang))
                return
            lines = [T[lang]["adm_reports_title"]]
            for r, rep, reason, ts in rows:
                lines.append(f"- reporter:{r} -> reported:{rep} | {reason} | {ts:%Y-%m-%d %H:%M}")
            await update.message.reply_text("\n".join(lines), reply_markup=kb_admin(lang))
            return

        # reply-based actions (no typing)
        replied = update.message.reply_to_message
        if not replied or not replied.from_user:
            await update.message.reply_text(T[lang]["adm_need_reply"], reply_markup=kb_admin(lang))
            return
        target_uid = replied.from_user.id

        if text == T[lang]["adm_ban_reply"]:
            set_user(target_uid, banned=1, step="idle")
            await update.message.reply_text(T[lang]["adm_banned_ok"].format(uid=target_uid), reply_markup=kb_admin(lang))
            return

        if text == T[lang]["adm_unban_reply"]:
            set_user(target_uid, banned=0, step="idle")
            await update.message.reply_text(T[lang]["adm_unbanned_ok"].format(uid=target_uid), reply_markup=kb_admin(lang))
            return

        if text == T[lang]["adm_star_reply"]:
            current = get_stars(target_uid)
            set_user(target_uid, stars=current + 3)
            await update.message.reply_text(T[lang]["adm_star_ok"].format(uid=target_uid), reply_markup=kb_admin(lang))
            return

        await update.message.reply_text(T[lang]["btn_only"], reply_markup=kb_admin(lang))
        return

    # report step
    if step == "report_reason":
        target = get_current(context)
        if not target:
            set_user(uid, step="idle")
            await show_menu(update, context)
            return

        # map reasons for DB
        reason_map = {
            T[lang]["rep_spam"]: "spam",
            T[lang]["rep_fake"]: "fake",
            T[lang]["rep_bad"]: "harassment",
            T[lang]["rep_other"]: "other",
        }
        if text not in reason_map:
            await update.message.reply_text(T[lang]["btn_only"], reply_markup=kb_report(lang))
            return

        add_report(uid, target, reason_map[text])
        set_user(uid, step="idle")
        await update.message.reply_text(T[lang]["report_done"], reply_markup=kb_menu(lang, uid))
        # move on
        await show_candidate(update, context)
        return

    # edit menu
    if step == "edit_menu":
        if text == T[lang]["edit_age"]:
            set_user(uid, step="edit_age")
            await update.message.reply_text(T[lang]["age_pick"], reply_markup=kb_age(lang))
            return
        if text == T[lang]["edit_city"]:
            set_user(uid, step="edit_city")
            await update.message.reply_text(T[lang]["city"], reply_markup=kb_city(lang))
            return
        if text == T[lang]["edit_bio"]:
            set_user(uid, step="edit_bio")
            await update.message.reply_text(T[lang]["bio"], reply_markup=kb_bio(lang))
            return
        if text == T[lang]["edit_photo"]:
            set_user(uid, step="edit_photo")
            await update.message.reply_text(T[lang]["photo"], reply_markup=kb_photo(lang))
            return
        if text == T[lang]["done"]:
            set_user(uid, step="idle")
            await show_menu(update, context)
            return
        await update.message.reply_text(T[lang]["btn_only"], reply_markup=kb_edit(lang))
        return

    # profile create
    if step == "pro_gender":
        g = normalize_gender(lang, text)
        if not g:
            await update.message.reply_text(T[lang]["btn_only"], reply_markup=kb_gender(lang)); return
        set_user(uid, gender=g, step="pro_looking")
        await update.message.reply_text(T[lang]["looking"], reply_markup=kb_gender(lang))
        return

    if step == "pro_looking":
        g = normalize_gender(lang, text)
        if not g:
            await update.message.reply_text(T[lang]["btn_only"], reply_markup=kb_gender(lang)); return
        set_user(uid, looking=g, step="pro_age")
        await update.message.reply_text(T[lang]["age_pick"], reply_markup=kb_age(lang))
        return

    if step in ("pro_age", "edit_age"):
        if text == "41+":
            await update.message.reply_text(T[lang]["age_type"], reply_markup=ReplyKeyboardRemove())
            return
        if not text.isdigit():
            await update.message.reply_text(T[lang]["age_pick"], reply_markup=kb_age(lang))
            return
        age = int(text)
        if age < 18:
            set_user(uid, banned=1, step="idle")
            await update.message.reply_text(T[lang]["underage"], reply_markup=ReplyKeyboardRemove())
            return
        if age > 80:
            await update.message.reply_text(T[lang]["age_type"])
            return

        set_user(uid, age=age)
        if step == "edit_age":
            set_user(uid, step="edit_menu")
            await update.message.reply_text(T[lang]["saved"], reply_markup=kb_edit(lang))
            return

        set_user(uid, step="pro_city")
        await update.message.reply_text(T[lang]["city"], reply_markup=kb_city(lang))
        return

    if step in ("pro_city", "edit_city"):
        ckey = normalize_city_key(text)
        if not ckey:
            await update.message.reply_text(T[lang]["btn_only"], reply_markup=kb_city(lang))
            return
        set_user(uid, city_key=ckey)
        if step == "edit_city":
            set_user(uid, step="edit_menu")
            await update.message.reply_text(T[lang]["saved"], reply_markup=kb_edit(lang))
            return
        set_user(uid, step="pro_bio")
        await update.message.reply_text(T[lang]["bio"], reply_markup=kb_bio(lang))
        return

    if step in ("pro_bio", "edit_bio"):
        if text == T[lang]["skip_bio"]:
            set_user(uid, bio="")
        else:
            if len(text) > 150:
                await update.message.reply_text(T[lang]["bio"], reply_markup=kb_bio(lang))
                return
            set_user(uid, bio=text)

        if step == "edit_bio":
            set_user(uid, step="edit_menu")
            await update.message.reply_text(T[lang]["saved"], reply_markup=kb_edit(lang))
            return

        set_user(uid, step="pro_photo")
        await update.message.reply_text(T[lang]["photo"], reply_markup=kb_photo(lang))
        return

    if step in ("pro_photo", "edit_photo"):
        if text == T[lang]["skip_photo"]:
            set_user(uid, photo_id="")
            if step == "edit_photo":
                set_user(uid, step="edit_menu")
                await update.message.reply_text(T[lang]["saved"], reply_markup=kb_edit(lang))
                return
            set_user(uid, step="idle")
            await update.message.reply_text(T[lang]["saved"], reply_markup=kb_menu(lang, uid))
            return
        await update.message.reply_text(T[lang]["btn_only"], reply_markup=kb_photo(lang))
        return

    # match buttons
    if text == T[lang]["btn_like"]:
        await handle_like(update, context); return
    if text == T[lang]["btn_skip"]:
        await handle_skip(update, context); return
    if text == T[lang]["btn_reveal"]:
        await handle_reveal(update, context); return
    if text == T[lang]["btn_report"]:
        await handle_report(update, context); return

    await show_menu(update, context)

# ================= MAIN =================
def main():
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sta", sta))
    app.add_handler(CommandHandler("pro", create_profile))
    app.add_handler(CommandHandler("id", cmd_id))

    app.add_handler(MessageHandler(filters.PHOTO, photo_router))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, router))

    print("🔥 DateMeBot running (Postgres + Report + Admin Panel)")
    app.run_polling()

if __name__ == "__main__":
    main()
