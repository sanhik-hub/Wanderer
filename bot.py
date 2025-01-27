import logging
import requests
from uuid import uuid4
from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.ext import ApplicationBuilder, CommandHandler, InlineQueryHandler, ContextTypes
from googleapiclient.discovery import build
from flask import Flask
from threading import Thread
import time
from ntgcalls import PyTgCalls, GroupCallFactory, AudioSource
from pyrogram import Client
import os

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define your bot token, YouTube API key, Google Custom Search API key, and Giphy API key
BOT_TOKEN = "7564262351:AAGzU9ipJT1CN01JvNTgSQVBhzmhjbm5Bp4"
YOUTUBE_API_KEY = "AIzaSyCHcbAHrO383FWQqIXrS-H7Xid1G4CaGeg"
GOOGLE_API_KEY = "AIzaSyCHcbAHrO383FWQqIXrS-H7Xid1G4CaGeg"
GOOGLE_CX = "a54de47eb8d024e8f"
GIPHY_API_KEY = "cd2qSZ4eWr8ineY0X9rhBalcuWVrRxyx"
API_ID = "24645334"  # Replace with your API ID
API_HASH = "e260832f866fcabc0075c346aa8f4f82"  # Replace with your API Hash
SESSION_NAME = "none"  # Replace with your session name

# Initialize Pyrogram Client and NativeTgCalls
client = Client(SESSION_NAME, api_id=API_ID, api_hash=API_HASH)
group_call_factory = GroupCallFactory(client)
tgcalls = PyTgCalls(client)

# Create your bot application
application = ApplicationBuilder().token(BOT_TOKEN).build()

# Define API search functions
def search_youtube(query):
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    request = youtube.search().list(
        part="snippet",
        maxResults=5,  # Number of results to return
        q=query,
        type="video"  # Search only for videos
    )
    response = request.execute()
    videos = []
    for item in response.get("items", []):
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        url = f"https://www.youtube.com/watch?v={video_id}"
        videos.append({"title": title, "url": url})
    return videos

def search_google(query):
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={GOOGLE_API_KEY}&cx={GOOGLE_CX}"
    response = requests.get(url)
    results = []
    if response.status_code == 200:
        data = response.json()
        for item in data.get("items", []):
            title = item.get("title")
            link = item.get("link")
            results.append({"title": title, "url": link})
    return results

def search_gif(query):
    url = f"https://api.giphy.com/v1/gifs/search?api_key={GIPHY_API_KEY}&q={query}&limit=5"
    response = requests.get(url)
    gifs = []
    if response.status_code == 200:
        data = response.json()
        for item in data.get("data", []):
            title = item.get("title")
            url = item.get("url")
            gifs.append({"title": title, "url": url})
    return gifs

def search_music(query):
    return [
        {"title": f"Sample Song: {query}", "url": "https://example.com/sample_song"}
    ]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hi! I can help you search for YouTube videos, Google results, music, and GIFs. Use the inline search feature by typing my username in any chat, followed by your query."
    )

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.inline_query.query
    if not query:
        return

    results = []

    videos = search_youtube(query)
    for video in videos:
        results.append(
            InlineQueryResultArticle(
                id=str(uuid4()),
                title=f"YouTube: {video['title']}",
                input_message_content=InputTextMessageContent(video["url"]),
                description=f"Watch on YouTube: {video['url']}",
            )
        )

    google_results = search_google(query)
    for result in google_results:
        results.append(
            InlineQueryResultArticle(
                id=str(uuid4()),
                title=f"Google: {result['title']}",
                input_message_content=InputTextMessageContent(result["url"]),
                description=f"View on Google: {result['url']}",
            )
        )

    gifs = search_gif(query)
    for gif in gifs:
        results.append(
            InlineQueryResultArticle(
                id=str(uuid4()),
                title=f"GIF: {gif['title']}",
                input_message_content=InputTextMessageContent(gif["url"]),
                description=f"View GIF: {gif['url']}",
            )
        )

    music_results = search_music(query)
    for music in music_results:
        results.append(
            InlineQueryResultArticle(
                id=str(uuid4()),
                title=f"Music: {music['title']}",
                input_message_content=InputTextMessageContent(music["url"]),
                description=f"Listen: {music['url']}",
            )
        )

    await update.inline_query.answer(results)

async def play_music(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Please provide a YouTube URL to play.")
        return

    youtube_url = context.args[0]
    chat_id = update.message.chat_id

    try:
        await tgcalls.start()
        group_call = group_call_factory.get_group_call(chat_id)

        audio_source = AudioSource.from_youtube(youtube_url)
        await group_call.join()
        await group_call.set_audio_source(audio_source)

        await update.message.reply_text(f"Playing music from: {youtube_url}")
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {e}")

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def ping_app():
    while True:
        try:
            requests.get('https://wanderer-5g5v.onrender.com')
        except requests.exceptions.RequestException as e:
            print(f"Error pinging app: {e}")
        time.sleep(300)

def main():
    Thread(target=run).start()
    Thread(target=ping_app).start()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("play", play_music))
    application.add_handler(InlineQueryHandler(inline_query))

    client.start()
    application.run_polling()

if __name__ == "__main__":
    main()
