import sys
import os
import logging
from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.ext import ApplicationBuilder, CommandHandler, InlineQueryHandler, ContextTypes
from googleapiclient.discovery import build
import requests
from uuid import uuid4
from flask import Flask

# Initialize Flask app
app = Flask(__name__)

# Suppress logging output
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING  # Change to WARNING or ERROR to suppress info/debug logs
)
logger = logging.getLogger(__name__)

# Redirect stdout to /dev/null
sys.stdout = open(os.devnull, 'w')

# Define your bot token, YouTube API key, Google Custom Search API key, and Giphy API key
BOT_TOKEN = "7564262351:AAGzU9ipJT1CN01JvNTgSQVBhzmhjbm5Bp4"
YOUTUBE_API_KEY = "AIzaSyCHcbAHrO383FWQqIXrS-H7Xid1G4CaGeg"
GOOGLE_API_KEY = "AIzaSyCHcbAHrO383FWQqIXrS-H7Xid1G4CaGeg"
GOOGLE_CX = "a54de47eb8d024e8f"
GIPHY_API_KEY = "cd2qSZ4eWr8ineY0X9rhBalcuWVrRxyx"
def search_youtube(query):
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    request = youtube.search().list(
        part="snippet",
        maxResults=5,
        q=query,
        type="video"
    )
    response = request.execute()
    videos = []
    for item in response.get("items", []):
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        url = f"https://www.youtube.com/watch?v={video_id}"
        videos.append({"title": title, "url": url})
    return videos

# Define other search functions (Google, Giphy, etc.)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hi! I can help you search for YouTube videos, Google results, music, and GIFs."
    )

# Inline query handler
async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.inline_query.query
    if not query:
        return

    results = []

    # Fetch YouTube videos
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

    await update.inline_query.answer(results)

# Flask route for webhook
@app.route("/")
def index():
    return "Bot is running!"

# Webhook setup for Telegram bot
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(InlineQueryHandler(inline_query))

    # Run the bot in polling mode (while Flask server is also running)
    application.run_polling()

if __name__ == "__main__":
    # Set up Flask to listen on the correct port for Replit
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

