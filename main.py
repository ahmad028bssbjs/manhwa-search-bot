import os, sqlite3, asyncio
from flask import Flask
from threading import Thread
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

API_ID = 37892084         # عدد خود را بدون علامت بگذارید
API_HASH = "0ad073f34a32e295610f8672461447a1"   # متن خود را داخل علامت نقل قول بگذارید
BOT_TOKEN = "8841689194:AAE234UrxQQa2Ghtxm4zPG_vgLYK17BDA7A" # توکن ربات را داخل علامت نقل قول بگذارید

CHANNELS = [
    "@Takmanhwafiles", "@Takmanhwa", "@city_manga", "@ManhwaDimension",
    "@ArmyManhwa", "@aboutanimeirr", "@KumaPlus", "@NightManhwa",
    "@DelbarManhwa", "@Manhwapersian_ir", "@MANGA_RISE", "@manhwa_P_R_O",
    "@paradise_manhwa", "@manskee", "@VEGASIMANHWA", "@archive_chaneel"
]

conn = sqlite3.connect("manhwa.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS archive (id INTEGER PRIMARY KEY AUTOINCREMENT, channel TEXT, link TEXT UNIQUE, text TEXT)")
conn.commit()

bot = Client("manhwa_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
def save_to_db(channel_title, link, text):
 try:
  cursor.execute("INSERT OR IGNORE INTO archive (channel, link, text) VALUES (?, ?, ?)", (channel_title, link, text))
  conn.commit()
 except: pass

async def download_old_posts():
 await asyncio.sleep(10)
 print("⏳ Start downloading...")
 for channel in CHANNELS:
  try:
   print(f"📥 Downloading: {channel}")
   async for message in bot.get_chat_history(channel, limit=500):
    if message.text or message.caption:
     text = message.text or message.caption
     channel_title = message.chat.title
     if message.chat.username: link = f"https://t.me{message.chat.username}/{message.id}"
     else: link = f"https://t.mec/{str(message.chat.id).replace('-100', '')}/{message.id}"
     save_to_db(channel_title, link, text)
   await asyncio.sleep(3)
  except Exception as e: print(f"❌ Error {channel}: {e}")
 print("✅ Done old posts!")
@bot.on_message(filters.chat(CHANNELS) & (filters.text | filters.caption))
async def save_message(client, message):
 text = message.text or message.caption
 channel_title = message.chat.title
 if message.chat.username: link = f"https://t.me{message.chat.username}/{message.id}"
 else: link = f"https://t.mec/{str(message.chat.id).replace('-100', '')}/{message.id}"
 save_to_db(channel_title, link, text)

@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
 await message.reply_text("👋 سلام! اسم مانهوا را بفرست تا در آرشیو کانال‌ها سرچ کنم.")

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

web_app = Flask('')
@web_app.route('/')
def home(): return "Live"

if __name__ == "__main__":
 Thread(target=lambda: web_app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))).start()
 bot.loop.create_task(download_old_posts())
 print("⚡ Done")
 bot.run()
