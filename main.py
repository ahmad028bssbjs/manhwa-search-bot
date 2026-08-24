import os, sqlite3, asyncio
from flask import Flask
from threading import Thread
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# 🔴 اطلاعات شما کاملاً جایگذاری شد:
API_ID = 37892084  
API_HASH = "0ad073f34a32e295610f8672461447a1"  
BOT_TOKEN = "8841689194:AAE234UrxQQa2Ghtxm4zPG_vgLYK17BDA7A"  

# نام دیتابیس جدید برای اصلاح لینک‌های خراب قبلی
conn = sqlite3.connect("manhwa_final.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS archive (id INTEGER PRIMARY KEY AUTOINCREMENT, channel TEXT, link TEXT UNIQUE, text TEXT)")
conn.commit()

# راه‌اندازی ربات اصلی
bot = Client("manhwa_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# تابع وارد کردن اطلاعات از فایل متنی یکپارچه به دیتابیس ربات
def load_txt_to_db():
    cursor.execute("SELECT COUNT(*) FROM archive")
    if cursor.fetchone()[0] > 0:
        print("✅ دیتابیس قبلاً پر شده است.")
        return
        
    file_path = "all_manhwa_archive.txt"
    if not os.path.exists(file_path):
        print(f"❌ فایل {file_path} پیدا نشد!")
        return

    print("⏳ در حال استخراج و ساخت دیتابیس هوشمند... لطفا کمی صبر کنید.")
    
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
                # 🛑 لینک با اسلش (/) کاملاً درست شد
                link = f"https://t.me{current_channel}/{post_id}"
                cursor.execute("INSERT OR IGNORE INTO archive (channel, link, text) VALUES (?, ?, ?)", (current_channel, link, clean_text))
        except Exception:
            continue
            
    conn.commit()
    print("✅ دیتابیس با موفقیت ساخته شد!")

# دستور استارت ربات
@bot.on_message(filters.command("start"))
async def start_command(client, message):
    await message.reply_text(
        "👋 سلام احمد عزیز!\n"
        "به ربات جستجوگر مانهوا خوش آمدی.\n\n"
        "🔍 کافیست اسم مانهوای مورد نظرت را (فارسی یا انگلیسی) بفرستی تا لینک پستش را پیدا کنم."
    )

# بخش جستجوی سریع در دیتابیس
@bot.on_message(filters.text & ~filters.command("start"))
async def search_manhwa(client, message):
    query = message.text.strip()
    
    cursor.execute("SELECT link, SUBSTR(text, 1, 150), channel FROM archive WHERE text LIKE ? LIMIT 3", (f"%{query}%",))
    results = cursor.fetchall()

    if not results:
        await message.reply_text("❌ متأسفانه مانهوایی با این نام در آرشیو پیدا نشد.")
        return

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

# 🌐 بخش وب‌سایت Flask برای زنده نگه داشتن ربات در هاست Render
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    load_txt_to_db()
    Thread(target=run_flask).start()
    print("🚀 ربات جستجوگر مانهوا روشن شد!")
    bot.run()
