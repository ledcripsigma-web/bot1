import os
import requests
from io import BytesIO
from flask import Flask, request
from telegram import Bot, Update, InputMediaPhoto
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
from bs4 import BeautifulSoup
import random
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8658717135:AAHCSqhyRoefkZRAETbYga9DU7WInv83GG0"
BOT_USERNAME = "@SrarchMembot"
PORT = int(os.environ.get("PORT", 10000))

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
]

bot = Bot(token=BOT_TOKEN)
web_app = Flask(__name__)

def search_google_images(query):
    try:
        url = f"https://www.google.com/search?q={query}+мем&tbm=isch&hl=ru"
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        response = requests.get(url, headers=headers, timeout=15)
        pattern = r'\["(https?://[^"]+?\.(?:jpg|jpeg|png|gif|webp))",\d+,\d+\]'
        return list(dict.fromkeys(re.findall(pattern, response.text)))
    except:
        return []

def search_yandex_images(query):
    try:
        url = f"https://yandex.ru/images/search?text={query}+мем"
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        response = requests.get(url, headers=headers, timeout=15)
        pattern = r'"img_url":"(https?://[^"]+?\.(?:jpg|jpeg|png|gif|webp))"'
        return list(dict.fromkeys(re.findall(pattern, response.text)))
    except:
        return []

def download_image(url):
    try:
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200 and len(response.content) > 2000:
            return BytesIO(response.content)
    except:
        pass
    return None

def start(update, context):
    pass

def handle_message(update, context):
    try:
        msg = update.message
        if not msg or not msg.text:
            return
        
        text = msg.text
        chat_type = msg.chat.type
        
        if chat_type in ["group", "supergroup"]:
            if BOT_USERNAME not in text:
                return
            query = text.replace(BOT_USERNAME, "").strip()
        else:
            query = text.strip()
        
        if not query:
            return
        
        msg.chat.send_action(action="upload_photo")
        
        google_urls = search_google_images(query)
        yandex_urls = search_yandex_images(query)
        
        images = []
        
        for url in (google_urls + yandex_urls):
            if len(images) >= 4:
                break
            img_data = download_image(url)
            if img_data and img_data not in images:
                images.append(img_data)
        
        if len(images) >= 2:
            try:
                media = [InputMediaPhoto(media=img) for img in images[:4]]
                msg.reply_media_group(media=media)
                return
            except:
                pass
        
        if len(images) >= 1:
            try:
                msg.reply_photo(photo=images[0])
                return
            except:
                pass
        
        msg.reply_text("не найдено мема")
    
    except Exception as e:
        logger.error(f"Error: {e}")
        try:
            msg.reply_text("не найдено мема")
        except:
            pass

dp = Dispatcher(bot, None, workers=0)
dp.add_handler(CommandHandler("start", start))
dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

@web_app.route("/")
def home():
    return "ok"

@web_app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), bot)
        dp.process_update(update)
        return "ok"
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return "ok", 200

if __name__ == "__main__":
    logger.info(f"Setting webhook to https://bot1-1-9m01.onrender.com/{BOT_TOKEN}")
    bot.set_webhook(url=f"https://bot1-1-9m01.onrender.com/{BOT_TOKEN}")
    logger.info(f"Starting server on port {PORT}")
    web_app.run(host="0.0.0.0", port=PORT)
