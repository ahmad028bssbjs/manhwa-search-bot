import asyncio
import sqlite3
import os
from flask import Flask
from threading import Thread
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# 🔴 اطلاعات خود را اینجا دقیقاً داخل علامت نقل قول "" جایگذاری کنید:
API_ID = 37892084         # عدد api_id خود را بگذارید
API_HASH = "0ad073f34a32e295610f8672461447a1"   # متن api_hash خود را بگذارید
BOT_TOKEN = "8841689194:AAE234UrxQQa2Ghtxm4zPG_vgLYK17BDA7A" # توکن رباتی که از BotFather گرفتید را بگذارید
CHANNELS = ["@Takmanhwafiles"] 

# 🌐 بخش فریب دادن سرور رندر (ساخت سایت فرضی)
web_app = Flask('')

@web_app.route('/')
def home():
    return "Bot is Running!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

# دیتابیس ربات
conn = sqlite3.connect("manhwa.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS archive (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel TEXT,
        link TEXT UNIQUE,
        text TEXT
    )
""")
conn.commit()

# راه‌اندازی ربات تلگرام
bot = Client("manhwa_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.chat(CHANNELS) & (filters.text | filters.caption))
async def save_message(client, message):
    text = message.text or message.caption
    channel_title = message.chat.title
    if message.chat.username:
        link = f"https://t.me{message.chat.username}/{message.id}"
    else:
        link = f"https://t.mec/{str(message.chat.id).replace('-100', '')}/{message.id}"
    try:
        cursor.execute("INSERT OR IGNORE INTO archive (channel, link, text) VALUES (?, ?, ?)", (channel_title, link, text))
        conn.commit()
    except:
        pass

@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    await message.reply_text("👋 سلام! اسم مانهوا را بفرست تا در کانال تک مانهوا سرچ کنم.")

@bot.on_message(filters.text & filters.private)
async def search_cmd(client, message):
    query = message.text
    cursor.execute("SELECT channel, link, text FROM archive WHERE text LIKE ?", (f"%{query}%",))
    results = cursor.fetchall()
    if not results:
        await message.reply_text("❌ نتیجه‌ای پیدا نشد.")
        return
    buttons = []
    for row in results[-5:]:
        channel_name, link, text = row
        short_text = text.split('\n')[0][:20]
        buttons.append([InlineKeyboardButton(text=f"📢 {channel_name} | {short_text}...", url=link)])
    await message.reply_text(f"🔍 نتایج برای **{query}**:", reply_markup=InlineKeyboardMarkup(buttons))

# اجرای همزمان سایت فرضی و ربات تلگرام
if __name__ == "__main__":
    Thread(target=run_web).start() # روشن کردن سایت در پس‌زمینه
    print("⚡ ربات تلگرام روشن شد.")
    bot.run()
        link = f"https://t.mec/{str(message.chat.id).replace('-100', '')}/{message.id}"
    
    try:
        cursor.execute("INSERT OR IGNORE INTO archive (channel, link, text) VALUES (?, ?, ?)", (channel_title, link, text))
        conn.commit()
    except:
        pass

# پاسخ به دستور شروع کاربران
@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    await message.reply_text(
        "👋 سلام به ربات جستجوگر مانهوا خوش آمدید!\n\n"
        "🔍 لطفاً نام مانهوای مورد نظر خود را بفرستید تا آخرین لینک‌های منتشر شده در کانال‌ها را برایتان پیدا کنم."
    )

# جستجو وقتی کاربر اسم مانهوا را می‌فرستد
@bot.on_message(filters.text & filters.private)
async def search_cmd(client, message):
    query = message.text
    # جستجو در پایگاه داده
    cursor.execute("SELECT channel, link, text FROM archive WHERE text LIKE ?", (f"%{query}%",))
    results = cursor.fetchall()
    
    if not results:
        await message.reply_text("❌ متأسفانه نتیجه‌ای پیدا نشد. مطمئن شوید نام را درست وارد کرده‌اید.")
        return
    
    # ساخت دکمه‌های شیشه‌ای برای نتایج (حداکثر ۵ نتیجه آخر)
    buttons = []
    for row in results[-5:]:
        channel_name, link, text = row
        # پیدا کردن خط اول متن برای نشان دادن روی دکمه
        short_text = text.split('\n')[0][:20]
        buttons.append([InlineKeyboardButton(text=f"📢 {channel_name} | {short_text}...", url=link)])
    
    await message.reply_text(
        f"🔍 نتایج یافت شده برای: **{query}**\n📌 روی دکمه‌های زیر بزنید تا مستقیم به پست هدایت شوید:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

print("⚡ ربات آماده است و دکمه‌ها فعال شدند.")
bot.run()
