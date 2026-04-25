import os
import requests
from io import BytesIO
from flask import Flask, request
from telegram import Bot, Update, InputMediaPhoto
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
from telegram.constants import ChatAction
from bs4 import BeautifulSoup
import random
import re

BOT_TOKEN = "8658717135:AAHCSqhyRoefkZRAETbYga9DU7WInv83GG0"
BOT_USERNAME = "@SrarchMembot"
WEBHOOK_URL = "https://bot1-1-9m01.onrender.com"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
]

bot = Bot(token=BOT_TOKEN)
dispatcher = Dispatcher(bot, None, workers=0)
web_app = Flask(__name__)

def search_google_images(query):
    search_query = f'"{query}" мем'
    url = f"https://www.google.com/search?q={search_query}&tbm=isch&hl=ru"
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        pattern = r'\["(https?://[^"]+?\.(?:jpg|jpeg|png|gif|webp))",\d+,\d+\]'
        matches = re.findall(pattern, response.text)
        return list(dict.fromkeys(matches))[:5]
    except:
        return []

def search_yandex_images(query):
    search_query = f'"{query}" мем'
    url = f"https://yandex.ru/images/search?text={search_query}"
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        pattern = r'"img_url":"(https?://[^"]+?\.(?:jpg|jpeg|png|gif|webp))"'
        matches = re.findall(pattern, response.text)
        return list(dict.fromkeys(matches))[:5]
    except:
        return []

def download_image(url):
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200 and len(response.content) > 3000:
            return BytesIO(response.content)
    except:
        pass
    return None

def extract_query(text):
    if BOT_USERNAME in text:
        query = text.replace(BOT_USERNAME, "").strip()
        return query if query else None
    words = text.split()
    query_words = [w for w in words if not w.startswith("@")]
    query = " ".join(query_words).strip()
    return query if query else None

def start(update, context):
    pass

def handle_message(update, context):
    if not update.message or not update.message.text:
        return
    
    message_text = update.message.text
    chat_type = update.message.chat.type
    
    if chat_type in ["group", "supergroup"]:
        if "@SrarchMembot" not in message_text:
            return
        query = extract_query(message_text)
        if not query:
            return
    else:
        query = message_text.strip()
        if not query:
            return
    
    update.message.chat.send_action(action=ChatAction.UPLOAD_PHOTO)
    
    google_images = search_google_images(query)
    yandex_images = search_yandex_images(query)
    
    downloaded = []
    
    for url in google_images[:3]:
        img = download_image(url)
        if img:
            downloaded.append(img)
            if len(downloaded) >= 2:
                break
    
    for url in yandex_images[:3]:
        img = download_image(url)
        if img:
            downloaded.append(img)
            if len(downloaded) >= 4:
                break
    
    if len(downloaded) >= 4:
        try:
            media = [InputMediaPhoto(media=img) for img in downloaded[:4]]
            update.message.reply_media_group(media=media)
            return
        except:
            pass
    
    if len(downloaded) >= 2:
        try:
            media = [InputMediaPhoto(media=img) for img in downloaded[:2]]
            update.message.reply_media_group(media=media)
            return
        except:
            pass
    
    if len(downloaded) >= 1:
        try:
            update.message.reply_photo(photo=downloaded[0])
            return
        except:
            pass
    
    update.message.reply_text("не найдено мема")

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

@web_app.route("/")
def home():
    return "ok"

@web_app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

if __name__ == "__main__":
    bot.set_webhook(url=f"{WEBHOOK_URL}/{BOT_TOKEN}")
    web_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
