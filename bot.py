import os
import requests
from io import BytesIO
from flask import Flask, request
from telegram import Update, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction
from bs4 import BeautifulSoup
import random
import re

BOT_TOKEN = "8658717135:AAHCSqhyRoefkZRAETbYga9DU7WInv83GG0"
BOT_USERNAME = "@SrarchMembot"
WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://твой-сервер.onrender.com")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/121.0",
]

web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "ok"

@web_app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), app.bot)
    app.update_queue.put(update)
    return "ok"

def search_google_images(query, num_images=10):
    search_query = f'"{query}" мем'
    url = f"https://www.google.com/search?q={search_query}&tbm=isch&hl=ru&safe=off"
    
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
        "Accept-Encoding": "gzip, deflate",
        "Cache-Control": "no-cache",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15, cookies={"CONSENT": "YES+"})
        soup = BeautifulSoup(response.text, "html.parser")
        
        image_urls = []
        
        for img in soup.find_all("img"):
            src = img.get("src")
            if src and src.startswith("http") and "gstatic" not in src and "google" not in src:
                image_urls.append(src)
        
        for div in soup.find_all("div"):
            data_src = div.get("data-src")
            if data_src and data_src.startswith("http"):
                image_urls.append(data_src)
        
        pattern = r'\["(https?://[^"]+?\.(?:jpg|jpeg|png|gif|webp))",\d+,\d+\]'
        matches = re.findall(pattern, response.text)
        image_urls.extend(matches)
        
        image_urls = list(dict.fromkeys(image_urls))
        return image_urls[:num_images]
    
    except:
        return []

def search_yandex_images(query, num_images=10):
    search_query = f'"{query}" мем'
    url = f"https://yandex.ru/images/search?text={search_query}&isize=eq&iw=300&ih=300"
    
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
        "Cache-Control": "no-cache",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        
        image_urls = []
        
        patterns = [
            r'"img_url":"(https?://[^"]+?\.(?:jpg|jpeg|png|gif|webp))"',
            r'"thumb_url":"(https?://[^"]+?\.(?:jpg|jpeg|png|gif|webp))"',
            r'"origin":"(https?://[^"]+?\.(?:jpg|jpeg|png|gif|webp))"',
            r'"(https?://avatars\.mds\.yandex\.net/[^"]+?\.(?:jpg|jpeg|png|gif|webp))"',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response.text)
            image_urls.extend(matches)
        
        soup = BeautifulSoup(response.text, "html.parser")
        for img in soup.find_all("img"):
            src = img.get("src")
            if src and src.startswith("http") and "yandex" not in src.lower():
                image_urls.append(src)
        
        image_urls = list(dict.fromkeys(image_urls))
        return image_urls[:num_images]
    
    except:
        return []

def download_image(url):
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Referer": "https://www.google.com/",
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        content_type = response.headers.get("content-type", "")
        if response.status_code == 200 and len(response.content) > 3000 and "image" in content_type:
            return BytesIO(response.content)
    except:
        pass
    return None

def extract_query_from_message(text):
    if BOT_USERNAME in text:
        query = text.replace(BOT_USERNAME, "").strip()
        if not query:
            return None
        return query
    
    if "@" in text:
        words = text.split()
        query_words = [w for w in words if not w.startswith("@")]
        query = " ".join(query_words).strip()
        if not query:
            return None
        return query
    
    return text.strip()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    
    message_text = update.message.text
    chat_type = update.message.chat.type
    
    if chat_type in ["group", "supergroup"]:
        if "@SrarchMembot" not in message_text:
            return
        
        query = extract_query_from_message(message_text)
        if not query:
            return
    else:
        query = message_text.strip()
        if not query:
            return
    
    await update.message.chat.send_action(action=ChatAction.UPLOAD_PHOTO)
    
    google_images = search_google_images(query, num_images=5)
    yandex_images = search_yandex_images(query, num_images=5)
    
    google_unique = []
    for url in google_images:
        if url not in google_unique:
            google_unique.append(url)
    
    yandex_unique = []
    for url in yandex_images:
        if url not in yandex_unique:
            yandex_unique.append(url)
    
    downloaded_google = []
    for url in google_unique:
        if len(downloaded_google) >= 2:
            break
        img_data = download_image(url)
        if img_data:
            downloaded_google.append(img_data)
    
    downloaded_yandex = []
    for url in yandex_unique:
        if len(downloaded_yandex) >= 2:
            break
        if url not in google_unique:
            img_data = download_image(url)
            if img_data:
                downloaded_yandex.append(img_data)
    
    if len(downloaded_yandex) < 2:
        for url in yandex_unique:
            if len(downloaded_yandex) >= 2:
                break
            if url not in google_unique:
                img_data = download_image(url)
                if img_data:
                    downloaded_yandex.append(img_data)
    
    all_images = downloaded_google[:2] + downloaded_yandex[:2]
    
    if len(all_images) >= 4:
        try:
            media_group = []
            for img_data in all_images[:4]:
                media_group.append(InputMediaPhoto(media=img_data))
            
            await update.message.reply_media_group(media=media_group)
            return
        except:
            pass
    
    if len(all_images) >= 2:
        try:
            media_group = [InputMediaPhoto(media=img) for img in all_images]
            await update.message.reply_media_group(media=media_group)
            return
        except:
            pass
    
    for img_data in all_images:
        try:
            await update.message.reply_photo(photo=img_data)
            return
        except:
            pass
    
    await update.message.reply_text("не найдено мема")

if __name__ == "__main__":
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    web_app.run(host="0.0.0.0", port=10000)
