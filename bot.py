from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.ext import ApplicationBuilder, CommandHandler, InlineQueryHandler, ContextTypes
from googleapiclient.discovery import build
import requests
import logging
from uuid import uuid4

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
    # Placeholder function for music search
    # Integration with a music API like Spotify or Apple Music can be implemented here
    return [
        {"title": f"Sample Song: {query}", "url": "https://example.com/sample_song"}
    ]

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hi! I can help you search for YouTube videos, Google results, music, and GIFs. Use the inline search feature by typing my username in any chat, followed by your query."
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

    # Fetch Google search results
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

    # Fetch GIFs
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

    # Fetch music
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

# Main function to start the bot
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add command and inline query handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(InlineQueryHandler(inline_query))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run).start()
