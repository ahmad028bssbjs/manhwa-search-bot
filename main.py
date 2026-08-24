import os
import re
import sqlite3
import asyncio
from flask import Flask
from threading import Thread

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


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

# اگر فایل‌ها کنار همین فایل Python هستند،
# می‌توانی ARCHIVE_DIR را "." قرار بدهی.
#
# ساختار پیشنهادی:
#
# archives/
#   VEGASIMANHWA_archive.txt
#   manskee_archive.txt
#   Paradise_manhwa_archive.txt
#   MANGA_RISE_archive.txt
#   ...
#


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
# 🧹 تمیز کردن نام کانال
# =========================================================
def clean_channel_name(filename):
    """
    مثال:

    VEGASIMANHWA_archive.txt
        ↓
    VEGASIMANHWA
    """

    name = os.path.basename(filename)

    if name.lower().endswith("_archive.txt"):
        name = name[:-len("_archive.txt")]

    return name.strip().lstrip("@").strip()


# =========================================================
# 🔢 استخراج Message ID
# =========================================================
def extract_message_id(header):
    """
    ورودی‌های قابل قبول مثل:

    781
    781 ---
    """

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

    # -----------------------------------------------------
    # فرمت مورد انتظار:
    #
    # --- ID: 781 ---
    # متن پست
    #
    # --- ID: 782 ---
    # متن پست
    #
    # -----------------------------------------------------

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

        # ---------------------------------------------
        # جدا کردن ID از متن
        # ---------------------------------------------
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

        # ---------------------------------------------
        # ساخت لینک صحیح
        # ---------------------------------------------
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

        if (
            filename.lower().endswith("_archive.txt")
            and os.path.isfile(
                os.path.join(ARCHIVE_DIR, filename)
            )
        ):
            files.append(
                os.path.join(
                    ARCHIVE_DIR,
                    filename
                )
            )

    files.sort()

    if not files:
        print()
        print("❌ هیچ فایل آرشیوی پیدا نشد.")
        print()
        print("باید فایل‌ها را داخل این پوشه قرار بدهی:")
        print(f"📁 {ARCHIVE_DIR}/")
        print()
        return

    print()
    print("🚀 شروع ساخت دیتابیس...")
    print(f"📚 تعداد آرشیوها: {len(files)}")
    print()

    total = 0

    for file_path in files:

        total += load_archive_file(file_path)

    # -----------------------------------------------------
    # آمار نهایی
    # -----------------------------------------------------
    cursor.execute(
        "SELECT COUNT(*) FROM archive"
    )

    total_database = cursor.fetchone()[0]

    print()
    print("=" * 60)
    print("🎉 عملیات تمام شد")
    print("=" * 60)
    print(f"📥 رکوردهای جدید: {total}")
    print(f"🗄️ کل رکوردهای دیتابیس: {total_database}")
    print("=" * 60)


# =========================================================
# 🔍 نرمال‌سازی جستجو
# =========================================================
def normalize_text(text):

    text = text.strip()

    # تبدیل ی/ک عربی به فارسی
    text = text.replace("ي", "ی")
    text = text.replace("ى", "ی")
    text = text.replace("ك", "ک")

    return text


# =========================================================
# ▶️ /start
# =========================================================
@bot.on_message(filters.command("start"))
async def start_command(client, message):

    await message.reply_text(
        "👋 سلام!\n\n"
        "🔎 نام مانهوا را بفرست.\n"
        "من در آرشیو کانال‌ها جستجو می‌کنم "
        "و لینک پست مربوطه را نشان می‌دهم.\n\n"
        "مثال:\n"
        "Solo Leveling"
    )


# =========================================================
# 🔎 جستجو
# =========================================================
@bot.on_message(
    filters.text &
    ~filters.command("start")
)
async def search_manhwa(client, message):

    query = normalize_text(message.text)

    if not query:
        await message.reply_text(
            "❌ عبارت جستجو را وارد کن."
        )
        return

    # -----------------------------------------------------
    # جستجوی ساده SQLite
    # -----------------------------------------------------
    cursor.execute(
        """
        SELECT channel, message_id, link, text
        FROM archive
        WHERE text LIKE ?
        LIMIT 5
        """,
        (f"%{query}%",)
    )

    results = cursor.fetchall()

    if not results:

        await message.reply_text(
            "❌ متأسفانه نتیجه‌ای در آرشیو پیدا نشد."
        )

        return

    # -----------------------------------------------------
    # نمایش نتایج
    # -----------------------------------------------------
    for channel, message_id, link, post_text in results:

        short_text = post_text.replace(
            "\n",
            " "
        ).strip()

        if len(short_text) > 300:
            short_text = short_text[:300] + "..."

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🔗 ورود مستقیم به پست",
                        url=link
                    )
                ]
            ]
        )

        await message.reply_text(
            f"📌 کانال: @{channel}\n"
            f"🆔 شماره پست: {message_id}\n\n"
            f"📝 {short_text}",
            reply_markup=keyboard
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

    # ساخت دیتابیس از تمام فایل‌ها
    load_all_archives()

    # اجرای Flask در Thread جدا
    flask_thread = Thread(
        target=run_flask,
        daemon=True
    )

    flask_thread.start()

    print()
    print("🌐 Flask روشن شد.")
    print("
