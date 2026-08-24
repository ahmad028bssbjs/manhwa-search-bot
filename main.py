import os
import re
import sqlite3
from flask import Flask
from threading import Thread
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.handlers import CallbackQueryHandler


# =========================================================
# 🔐 تنظیمات
# =========================================================

API_ID = int(os.environ.get("37892084", "0"))
API_HASH = os.environ.get("0ad073f34a32e295610f8672461447a1", "")
BOT_TOKEN = os.environ.get("8841689194:AAE234UrxQQa2Ghtxm4zPG_vgLYK17BDA7A", "")

if not API_ID or not API_HASH or not BOT_TOKEN:
    raise RuntimeError(
        "❌ API_ID / API_HASH / BOT_TOKEN در Environment Variables تنظیم نشده‌اند."
    )


# =========================================================
# 📁 مسیر آرشیوها
# =========================================================

ARCHIVE_DIR = "archives"


# =========================================================
# 🗄️ دیتابیس
# =========================================================

DB_NAME = "manhwa_final.db"

conn = sqlite3.connect(
    DB_NAME,
    check_same_thread=False
)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS archive (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel TEXT NOT NULL,
    message_id INTEGER NOT NULL,
    link TEXT NOT NULL UNIQUE,
    text TEXT
)
""")

conn.commit()


# =========================================================
# 🤖 ربات
# =========================================================

bot = Client(
    "manhwa_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)


# =========================================================
# 📌 ذخیره جستجوهای فعال
#
# کل متن آرشیو اینجا ذخیره نمی‌شود.
# فقط عبارت جستجو نگهداری می‌شود.
#
# کلید:
# (chat_id, bot_message_id)
#
# مقدار:
# query
# =========================================================

search_sessions = {}


# =========================================================
# 🧹 تمیز کردن نام کانال
# =========================================================

def clean_channel_name(filename):

    name = os.path.basename(filename)

    if name.lower().endswith("_archive.txt"):
        name = name[:-len("_archive.txt")]

    return name.strip().lstrip("@").strip()


# =========================================================
# 🔢 استخراج Message ID
# =========================================================

def extract_message_id(header):

    header = header.strip()

    match = re.search(r"(\d+)", header)

    if not match:
        return None

    try:
        return int(match.group(1))
    except ValueError:
        return None


# =========================================================
# 📥 خواندن یک فایل آرشیو
# =========================================================

def load_archive_file(file_path):

    channel = clean_channel_name(file_path)

    print()
    print("=" * 60)
    print(f"📂 فایل: {os.path.basename(file_path)}")
    print(f"📢 کانال: @{channel}")
    print("=" * 60)

    try:

        with open(
            file_path,
            "r",
            encoding="utf-8",
            errors="ignore"
        ) as f:

            content = f.read()

    except Exception as e:

        print(f"❌ خطا در خواندن فایل: {e}")

        return 0

    if not content.strip():

        print("⚠️ فایل خالی است.")

        return 0

    posts = re.split(
        r"---\s*ID:\s*",
        content,
        flags=re.IGNORECASE
    )

    added = 0
    skipped = 0

    for raw_post in posts:

        raw_post = raw_post.strip()

        if not raw_post:
            continue

        parts = re.split(
            r"\s*---\s*\n?",
            raw_post,
            maxsplit=1
        )

        if len(parts) < 2:

            skipped += 1

            continue

        id_part = parts[0].strip()
        post_text = parts[1].strip()

        message_id = extract_message_id(id_part)

        if not message_id:

            skipped += 1

            continue

        if not post_text:

            skipped += 1

            continue

        # لینک صحیح
        link = f"https://t.me/{channel}/{message_id}"

        try:

            cursor.execute(
                """
                INSERT OR IGNORE INTO archive
                (channel, message_id, link, text)
                VALUES (?, ?, ?, ?)
                """,
                (
                    channel,
                    message_id,
                    link,
                    post_text
                )
            )

            if cursor.rowcount > 0:

                added += 1

        except Exception as e:

            print(
                f"⚠️ خطا در ذخیره پیام "
                f"{message_id}: {e}"
            )

    conn.commit()

    print(f"✅ اضافه شد: {added}")
    print(f"⏭️ رد شد: {skipped}")

    return added


# =========================================================
# 📚 خواندن تمام آرشیوها
# =========================================================

def load_all_archives():

    if not os.path.exists(ARCHIVE_DIR):

        os.makedirs(ARCHIVE_DIR)

    files = []

    for filename in os.listdir(ARCHIVE_DIR):

        full_path = os.path.join(
            ARCHIVE_DIR,
            filename
        )

        if (
            filename.lower().endswith("_archive.txt")
            and os.path.isfile(full_path)
        ):

            files.append(full_path)

    files.sort()

    if not files:

        print()
        print("❌ هیچ فایل آرشیوی پیدا نشد.")
        print()
        print(
            f"📁 فایل‌ها را داخل پوشه "
            f"{ARCHIVE_DIR}/ قرار بده."
        )
        print()

        return

    print()
    print("=" * 60)
    print("🚀 شروع ساخت دیتابیس")
    print("=" * 60)
    print(f"📚 تعداد فایل‌ها: {len(files)}")
    print()

    total = 0

    for file_path in files:

        total += load_archive_file(file_path)

    cursor.execute(
        "SELECT COUNT(*) FROM archive"
    )

    total_database = cursor.fetchone()[0]

    print()
    print("=" * 60)
    print("🎉 ساخت دیتابیس تمام شد")
    print("=" * 60)
    print(f"📥 رکوردهای جدید: {total}")
    print(f"🗄️ کل رکوردها: {total_database}")
    print("=" * 60)


# =========================================================
# 🔍 نرمال‌سازی متن
# =========================================================

def normalize_text(text):

    text = text.strip()

    text = text.replace("ي", "ی")
    text = text.replace("ى", "ی")
    text = text.replace("ك", "ک")

    return text


# =========================================================
# 📝 کوتاه کردن متن نتیجه
# =========================================================

def make_short_text(text, max_length=220):

    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    text = text.strip()

    if len(text) > max_length:

        return text[:max_length] + "..."

    return text


# =========================================================
# 🔎 گرفتن نتایج یک صفحه
# =========================================================

def get_results(query, page):

    PAGE_SIZE = 5

    offset = page * PAGE_SIZE

    cursor.execute(
        """
        SELECT channel, message_id, link, text
        FROM archive
        WHERE text LIKE ?
        ORDER BY id DESC
        LIMIT ? OFFSET ?
        """,
        (
            f"%{query}%",
            PAGE_SIZE,
            offset
        )
    )

    results = cursor.fetchall()

    return results


# =========================================================
# 🔢 بررسی اینکه صفحه بعدی وجود دارد
# =========================================================

def has_next_page(query, page):

    PAGE_SIZE = 5

    next_offset = (page + 1) * PAGE_SIZE

    cursor.execute(
        """
        SELECT 1
        FROM archive
        WHERE text LIKE ?
        LIMIT 1 OFFSET ?
        """,
        (
            f"%{query}%",
            next_offset
        )
    )

    return cursor.fetchone() is not None


# =========================================================
# 🧱 ساخت پیام نتایج
# =========================================================

def build_results_text(
    results,
    page
):

    text = (
        f"🔎 **نتایج جستجو**\n"
        f"📄 صفحه {page + 1}\n\n"
    )

    for index, (
        channel,
        message_id,
        link,
        post_text
    ) in enumerate(results, start=1):

        short_text = make_short_text(
            post_text
        )

        text += (
            f"**{index}. @{channel}**\n"
            f"🆔 پست: `{message_id}`\n"
            f"📝 {short_text}\n\n"
        )

    return text


# =========================================================
# 🔘 ساخت دکمه‌های نتایج
# =========================================================

def build_keyboard(
    results,
    page,
    query
):

    buttons = []

    # -----------------------------------------------------
    # دکمه ورود به هر نتیجه
    # -----------------------------------------------------

    for index, (
        channel,
        message_id,
        link,
        post_text
    ) in enumerate(results, start=1):

        buttons.append(
            [
                InlineKeyboardButton(
                    f"🔗 نتیجه {index} | @{channel}",
                    url=link
                )
            ]
        )

    # -----------------------------------------------------
    # دکمه‌های قبلی / بعدی
    # -----------------------------------------------------

    navigation = []

    if page > 0:

        navigation.append(
            InlineKeyboardButton(
                "⬅️ قبلی",
                callback_data=f"page:{page - 1}"
            )
        )

    if has_next_page(query, page):

        navigation.append(
            InlineKeyboardButton(
                "➡️ بعدی",
                callback_data=f"page:{page + 1}"
            )
        )

    if navigation:

        buttons.append(navigation)

    return InlineKeyboardMarkup(buttons)


# =========================================================
# ▶️ /start
# =========================================================

@bot.on_message(
    filters.command("start")
)
async def start_command(
    client,
    message
):

    await message.reply_text(
        "👋 سلام!\n\n"
        "🔎 نام مانهوا را بفرست.\n"
        "من در آرشیو کانال‌ها جستجو می‌کنم "
        "و پست‌های مربوطه را پیدا می‌کنم.\n\n"
        "مثال:\n"
        "Solo Leveling"
    )


# =========================================================
# 🔎 جستجوی اصلی
# =========================================================

@bot.on_message(
    filters.text &
    ~filters.command("start")
)
async def search_manhwa(
    client,
    message
):

    query = normalize_text(
        message.text
    )

    if not query:

        await message.reply_text(
            "❌ عبارت جستجو را وارد کن."
        )

        return

    # صفحه اول
    page = 0

    results = get_results(
        query,
        page
    )

    if not results:

        await message.reply_text(
            "❌ متأسفانه نتیجه‌ای در آرشیو پیدا نشد."
        )

        return

    text = build_results_text(
        results,
        page
    )

    keyboard = build_keyboard(
        results,
        page,
        query
    )

    sent_message = await message.reply_text(
        text,
        reply_markup=keyboard
    )

    # ذخیره فقط عبارت جستجو
    search_sessions[
        (
            message.chat.id,
            sent_message.id
        )
    ] = query


# =========================================================
# ⬅️➡️ صفحه‌بندی
# =========================================================

@bot.on_callback_query(
    filters.regex(r"^page:\d+$")
)
async def pagination_callback(
    client,
    callback_query
):

    try:

        page = int(
            callback_query.data.split(":")[1]
        )

    except Exception:

        await callback_query.answer(
            "❌ صفحه نامعتبر است.",
            show_alert=True
        )

        return

    key = (
        callback_query.message.chat.id,
        callback_query.message.id
    )

    query = search_sessions.get(key)

    if not query:

        await callback_query.answer(
            "⚠️ این جستجو منقضی شده است. دوباره جستجو کن.",
            show_alert=True
        )

        return

    results = get_results(
        query,
        page
    )

    if not results:

        await callback_query.answer(
            "❌ نتیجه دیگری وجود ندارد.",
            show_alert=True
        )

        return

    text = build_results_text(
        results,
        page
    )

    keyboard = build_keyboard(
        results,
        page,
        query
    )

    try:

        await callback_query.message.edit_text(
            text,
            reply_markup=keyboard
        )

        await callback_query.answer()

    except Exception as e:

        print(
            f"⚠️ خطا در صفحه‌بندی: {e}"
        )

        await callback_query.answer(
            "❌ خطایی رخ داد.",
            show_alert=True
        )


# =========================================================
# 🌐 Flask
# =========================================================

app = Flask(__name__)


@app.route("/")
def home():

    return "🤖 Manhwa Search Bot is alive!"


def run_flask():

    port = int(
        os.environ.get(
            "PORT",
            "8080"
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )


# =========================================================
# 🚀 اجرای برنامه
# =========================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("🤖 MANHWA SEARCH BOT")
    print("=" * 60)

    # ساخت / تکمیل دیتابیس
    load_all_archives()

    # اجرای Flask
    flask_thread = Thread(
        target=run_flask,
        daemon=True
    )

    flask_thread.start()

    print()
    print("🌐 Flask روشن شد.")
    print("🚀 ربات در حال اجراست...")
    print()

    bot.run()
