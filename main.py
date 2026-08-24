import os
import sqlite3
import asyncio
from flask import Flask
from threading import Thread
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# 🔴 اطلاعات خود را دقیقاً وارد کنید:
API_ID = 37892084  # آیدی شما
API_HASH = "0ad073f34a32e295610f8672461447a1"  # هش شما
BOT_TOKEN = "8841689194:AAE234UrxQQa2Ghtxm4zPG_vgLYK17BDA7A"

# ساخت و اتصال به دیتابیس
conn = sqlite3.connect("manhwa.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute(
    "CREATE TABLE IF NOT EXISTS archive (id INTEGER PRIMARY KEY AUTOINCREMENT, channel TEXT, link TEXT, text TEXT)"
)
conn.commit()

# راه‌اندازی ربات
bot = Client("manhwa_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


# تابع وارد کردن اطلاعات از فایل متنی گیت‌هاب به دیتابیس ربات
def load_txt_to_db():
    cursor.execute("SELECT COUNT(*) FROM archive")
    if cursor.fetchone()[0] > 0:
        print("✅ دیتابیس قبلاً پر شده است.")
        return

    file_path = "all_manhwa_archive.txt"
    if not os.path.exists(file_path):
        print(
            f"❌ فایل {file_path} پیدا نشد! لطفاً آن را در گیت‌هاب کنار این کد آپلود کنید."
        )
        return

    print("⏳ در حال انتقال اطلاعات فایل متنی به دیتابیس... لطفا صبر کنید.")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # تکه‌تکه کردن فایل بر اساس کانال‌ها و آیدی پست‌ها
    # فرض بر این است که نام کانال‌ها در ابتدای بخش‌ها یا در ساختار فایل موجود است
    # برای ساده‌سازی، متن‌ها بر اساس شناسه پست جدا می‌شوند
    raw_posts = content.split("--- ID: ")
    current_channel = "Manhwa_Channel"

    for raw_post in raw_posts:
        if not raw_post.strip():
            continue
        try:
            # استخراج آیدی و متن
            parts = raw_post.split(" ---\n", 1)
            post_id = parts[0].strip()
            post_text = parts[1].strip()

            # ساخت لینک مستقیم
            link = f"https://t.me{current_channel}/{post_id}"

            cursor.execute(
                "INSERT INTO archive (channel, link, text) VALUES (?, ?, ?)",
                (current_channel, link, post_text),
            )
        except Exception:
            continue

    conn.commit()
    print("✅ تمام اطلاعات با موفقیت وارد دیتابیس ربات شد!")


# دستور استارت ربات
@bot.on_message(filters.command("start"))
async def start_command(client, message):
    await message.reply_text(
        "👋 سلام احمد عزیز!\n"
        "به ربات جستجوگر مانهوا خوش آمدی.\n\n"
        "🔍 کافیست اسم مانهوای مورد نظرت را (فارسی یا انگلیسی) بفرستی تا لینک پستش را پیدا کنم."
    )


# بخش جستجوی پیشرفته در دیتابیس
@bot.on_message(filters.text & ~filters.command("start"))
async def search_manhwa(client, message):
    query = message.text.strip()
    await message.reply_text("⏳ در حال جستجو در دیتابیس مانهواها...")

    # جستجوی کلمه در متن پست‌ها داخل دیتابیس
    cursor.execute(
        "SELECT link, text FROM archive WHERE text LIKE ? LIMIT 5",
        (f"%{query}%",),
    )
    results = cursor.fetchall()

    if not results:
        await message.reply_text(
            "❌ متأسفانه مانهوایی با این نام در آرشیو پیدا نشد."
        )
        return

    # ارسال نتایج به صورت دکمه‌های شیشه‌ای جذاب
    for link, text in results:
        # قطع کردن متن طولانی برای زیبایی پیام (نمایش ۵۰ کاراکتر اول)
        short_text = (
            text[:100].replace("\n", " ") + "..."
            if len(text) > 100
            else text
        )

        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔗 ورود به پست مانهوا", url=link)]]
        )

        await message.reply_text(
            f"📌 **نتیجه یافت شده:**\n\n{short_text}", reply_markup=keyboard
        )


# 🌐 بخش وب‌سایت Flask برای زنده نگه داشتن ربات در هاست Render
app = Flask("")


@app.route("/")
def home():
    return "Bot is alive!"


def run_flask():
    app.run(host="0.0.0.0", port=8080)


# اجرای همزمان ربات و سایت
if __name__ == "__main__":
    # پر کردن دیتابیس از روی فایل متنی قبل از روشن شدن ربات
    load_txt_to_db()

    # روشن کردن سرور وب در یک ثرد (Thread) جداگانه
    Thread(target=run_flask).start()

    print("🚀 ربات جستجوگر مانهوا روشن شد و آماده کار است!")
    bot.run()
