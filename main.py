import os
import sqlite3
import asyncio
from flask import Flask
from threading import Thread
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# 🔴 اطلاعات خود را در این بخش وارد کنید:
API_ID = 37892084  
API_HASH = "0ad073f34a32e295610f8672461447a1"  
BOT_TOKEN = "8841689194:AAE234UrxQQa2Ghtxm4zPG_vgLYK17BDA7A"

# ساخت و اتصال به دیتابیس لوکال برای سرعت بیشتر
conn = sqlite3.connect("manhwa.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS archive (id INTEGER PRIMARY KEY AUTOINCREMENT, channel TEXT, link TEXT, text TEXT)")
conn.commit()

# ایجاد ایندکس برای بالا بردن سرعت جستجو در متن‌ها
cursor.execute("CREATE INDEX IF NOT EXISTS idx_text ON archive(text)")
conn.commit()

# راه‌اندازی ربات تلگرام
bot = Client("manhwa_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# تابع انتقال اطلاعات از فایل متنی به دیتابیس ساختاریافته
def load_txt_to_db():
    cursor.execute("SELECT COUNT(*) FROM archive")
    if cursor.fetchone()[0] > 0:
        print("✅ دیتابیس از قبل آماده است و نیازی به پردازش مجدد ندارد.")
        return
        
    file_path = "all_manhwa_archive.txt"
    if not os.path.exists(file_path):
        print(f"❌ خطا: فایل {file_path} در کنار سورس کد پیدا نشد!")
        return

    print("⏳ در حال پردازش فایل متنی و ساخت دیتابیس پرسرعت...")
    
    channels_list = [
        "VEGASIMANHWA", "manskee", "Paradise_manhwa", "manhwa_P_R_O",
        "MANGA_RISE", "Manhwapersian_ir", "DelbarManhwa", "archive_chaneel",
        "NightManhwa", "KumaPlus", "aboutanimeirr", "ArmyManhwa", 
        "mangasekai_ir", "ManhwaDimension", "city_manga"
    ]
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    raw_posts = content.split("--- ID: ")
    current_channel = "VEGASIMANHWA"
    insert_data = []

    for raw_post in raw_posts:
        if not raw_post.strip():
            continue
        try:
            parts = raw_post.split(" ---\n", 1)
            post_id = parts[0].strip()
            post_text = parts[1].strip()

            for ch in channels_list:
                if f"Downloading: {ch}" in post_text or f"Saved: {ch}" in post_text:
                    current_channel = ch
                    break

            clean_text = post_text
            for ch in channels_list:
                clean_text = clean_text.replace(f"Downloading: {ch}", "").replace(f"Saved: {ch}", "")
            clean_text = clean_text.strip()

            if clean_text:
                link = f"https://t.me{current_channel}/{post_id}"
                insert_data.append((current_channel, link, clean_text))
        except Exception:
            continue
            
    if insert_data:
        cursor.executemany("INSERT INTO archive (channel, link, text) VALUES (?, ?, ?)", insert_data)
        conn.commit()
    print("✅ دیتابیس با موفقیت ساخته و بهینه‌سازی شد!")

# دستور /start ربات
@bot.on_message(filters.command("start"))
async def start_command(client, message):
    await message.reply_text(
        "👋 سلام احمد عزیز!\n"
        "به ربات جستجوگر مانهوا خوش آمدی.\n\n"
        "🔍 کافیست اسم مانهوای مورد نظرت را بفرستی تا لینک مستقیم پست آن را برایت پیدا کنم."
    )

# بخش جستجوی بهینه‌شده و پرسرعت
@bot.on_message(filters.text & ~filters.command("start"))
async def search_manhwa(client, message):
    query = message.text.strip()
    
    # جستجوی بهینه با محدود کردن لود کاراکترها برای جلوگیری از کرش سرور
    cursor.execute("SELECT link, SUBSTR(text, 1, 150), channel FROM archive WHERE text LIKE ? LIMIT 3", (f"%{query}%",))
    results = cursor.fetchall()

    if not results:
        await message.reply_text("❌ متأسفانه مانهوایی با این نام در آرشیو پیدا نشد.")
        return

    # ارسال نتایج به همراه دکمه شیشه‌ای هدایت به پست اصلی
    for link, short_text, channel in results:
        display_text = short_text.replace('\n', ' ').strip() + "..."
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 ورود به پست مانهوا", url=link)]
        ])
        
        await message.reply_text(
            f"📌 **کانال:** @{channel}\n"
            f"📝 **خلاصه کپشن:**\n{display_text}", 
            reply_markup=keyboard
        )

# 🌐 سایت فِکست (Flask) برای زنده نگه داشتن ربات در رندر
app = Flask('')

@app.route('/')
def home():
    return "Bot is running perfectly!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    # استخراج اطلاعات قبل از استارت ربات
    load_txt_to_db()
    
    # اجرای وب‌سرور در ترد پس‌زمینه
    Thread(target=run_flask).start()
    
    print("🚀 ربات جستجوگر مانهوا روشن شد و آماده کار است!")
    bot.run()
