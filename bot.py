import logging
import requests
from uuid import uuid4
from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.ext import ApplicationBuilder, CommandHandler, InlineQueryHandler, ContextTypes
from googleapiclient.discovery import build
from flask import Flask
from threading import Thread
from pytgcalls import PyTgCalls
from pyrogram import Client, filters
from pyrogram.types import Message
import youtube_dl
import time

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
API_ID = "24645334"
API_HASH = "e260832f866fcabc0075c346aa8f4f82"

# Initialize bot clients
application = ApplicationBuilder().token(BOT_TOKEN).build()
pyro_client = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
pytgcalls = PyTgCalls(pyro_client)

# YouTube download options
ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'outtmpl': '%(id)s.%(ext)s',
}

# Define API search functions
def search_youtube(query):
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    request = youtube.search().list(
        part="snippet",
        maxResults=1,
        q=query,
        type="video"
    )
    response = request.execute()
    if "items" in response:
        video = response["items"][0]
        video_id = video["id"]["videoId"]
        title = video["snippet"]["title"]
        url = f"https://www.youtube.com/watch?v={video_id}"
        return {"title": title, "url": url}
    return None

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

async def play_audio(chat_id, query):
    video = search_youtube(query)
    if video:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video["url"], download=False)
            pytgcalls.join_group_call(
                chat_id,
                input_stream=info['url'],
                stream_type="local",
            )
        return f"Now playing: {video['title']}"
    return "Couldn't find the song."

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hi! I can play songs in voice chat, chat with users, and help with searches. "
        "Use /play <song name> to play a song in voice chat."
    )

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("Please provide a song name or YouTube URL.")
        return
    chat_id = update.message.chat_id
    response = await play_audio(chat_id, query)
    await update.message.reply_text(response)

# Inline query handler
async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.inline_query.query
    if not query:
        return

    results = []

    # Fetch YouTube videos
    video = search_youtube(query)
    if video:
        results.append(
            InlineQueryResultArticle(
                id=str(uuid4()),
                title=f"YouTube: {video['title']}",
                input_message_content=InputTextMessageContent(video["url"]),
                description=f"Watch on YouTube: {video['url']}",
            )
        )

    await update.inline_query.answer(results)

# Group and PM chat interaction
@pyro_client.on_message(filters.text)
async def chat_response(client, message: Message):
    if "hello" in message.text.lower():
        await message.reply("Hi there! How can I assist you?")

# Flask app to run alongside the bot
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

# Threaded function to run Flask app
def run():
    app.run(host='0.0.0.0', port=8080)

# Function to ping the app periodically (every 5 minutes)
def ping_app():
    while True:
        try:
            requests.get('https://wanderer-5g5v.onrender.com')
        except requests.exceptions.RequestException as e:
            print(f"Error pinging app: {e}")
        time.sleep(300)

# Main function to start the bot and Flask app
def main():
    Thread(target=run).start()
    Thread(target=ping_app).start()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("play", play))
    application.add_handler(InlineQueryHandler(inline_query))
    pytgcalls.start()
    pyro_client.start()
    application.run_polling()

if __name__ == "__main__":
    main()

