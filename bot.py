import logging
import os
import requests
from uuid import uuid4
from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.ext import ApplicationBuilder, CommandHandler, InlineQueryHandler, MessageHandler, ContextTypes, filters
from googleapiclient.discovery import build
from flask import Flask
from threading import Thread
import openai
import time

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# API keys
BOT_TOKEN = "7564262351:AAGzU9ipJT1CN01JvNTgSQVBhzmhjbm5Bp4"
YOUTUBE_API_KEY = "AIzaSyCHcbAHrO383FWQqIXrS-H7Xid1G4CaGeg"
GOOGLE_API_KEY = "AIzaSyCHcbAHrO383FWQqIXrS-H7Xid1G4CaGeg"
GOOGLE_CX = "a54de47eb8d024e8f"
GIPHY_API_KEY = "cd2qSZ4eWr8ineY0X9rhBalcuWVrRxyx"
OPENAI_API_KEY = "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"
openai.api_key = OPENAI_API_KEY

# Create the bot application
application = ApplicationBuilder().token(BOT_TOKEN).build()

# Store user-specific personalities
user_personalities = {}

# Helper functions for external APIs
def search_youtube(query):
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    request = youtube.search().list(
        part="snippet",
        maxResults=5,
        q=query,
        type="video"
    )
    response = request.execute()
    return [
        {"title": item["snippet"]["title"], "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}"}
        for item in response.get("items", [])
    ]

def search_google(query):
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={GOOGLE_API_KEY}&cx={GOOGLE_CX}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return [
            {"title": item.get("title"), "url": item.get("link")}
            for item in data.get("items", [])
        ]
    return []

def search_gif(query):
    url = f"https://api.giphy.com/v1/gifs/search?api_key={GIPHY_API_KEY}&q={query}&limit=5"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return [
            {"title": item.get("title"), "url": item.get("url")}
            for item in data.get("data", [])
        ]
    return []

def search_music(query):
    # Placeholder function for music search
    return [{"title": f"Sample Song: {query}", "url": "https://example.com/sample_song"}]

# Function to generate ChatGPT responses
async def generate_response(prompt, personality):
    full_prompt = f"The bot's personality is: {personality}\nUser: {prompt}\nBot:"
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=full_prompt,
            max_tokens=150
        )
        return response.choices[0].text.strip()
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return "Sorry, I couldn't process your request."

# Command to set personality
async def set_personality(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.args:
        personality = " ".join(context.args)
        user_id = update.effective_user.id
        user_personalities[user_id] = personality
        await update.message.reply_text(f"Personality set to: {personality}")
    else:
        await update.message.reply_text("Please provide a personality. Example: /set_personality friendly and humorous")

# Command to get current personality
async def get_personality(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    personality = user_personalities.get(user_id, "default (neutral)")
    await update.message.reply_text(f"Current personality: {personality}")

# Handle direct chat with the bot
async def chat_with_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    user_id = update.effective_user.id
    personality = user_personalities.get(user_id, "neutral and helpful")
    response = await generate_response(user_message, personality)
    await update.message.reply_text(response)

# Inline query handler
async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.inline_query.query
    if not query:
        return

    results = []

    if query.lower().startswith("chatgpt:"):
        gpt_query = query[len("chatgpt:"):].strip()
        personality = user_personalities.get(update.inline_query.from_user.id, "neutral and helpful")
        response = await generate_response(gpt_query, personality)
        results.append(
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="ChatGPT Response",
                input_message_content=InputTextMessageContent(response),
                description=f"Response from ChatGPT: {response}",
            )
        )
    else:
        videos = search_youtube(query)
        results.extend(
            InlineQueryResultArticle(
                id=str(uuid4()),
                title=f"YouTube: {video['title']}",
                input_message_content=InputTextMessageContent(video["url"]),
                description=f"Watch on YouTube: {video['url']}"
            )
            for video in videos
        )

        google_results = search_google(query)
        results.extend(
            InlineQueryResultArticle(
                id=str(uuid4()),
                title=f"Google: {result['title']}",
                input_message_content=InputTextMessageContent(result["url"]),
                description=f"View on Google: {result['url']}"
            )
            for result in google_results
        )

        gifs = search_gif(query)
        results.extend(
            InlineQueryResultArticle(
                id=str(uuid4()),
                title=f"GIF: {gif['title']}",
                input_message_content=InputTextMessageContent(gif["url"]),
                description=f"View GIF: {gif['url']}"
            )
            for gif in gifs
        )

        music_results = search_music(query)
        results.extend(
            InlineQueryResultArticle(
                id=str(uuid4()),
                title=f"Music: {music['title']}",
                input_message_content=InputTextMessageContent(music["url"]),
                description=f"Listen: {music['url']}"
            )
            for music in music_results
        )

    await update.inline_query.answer(results)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hi! I can help you search for YouTube videos, Google results, music, and GIFs. I can also chat and adjust my personality. "
        "Use /set_personality to define my personality."
    )

# Flask app for keeping the bot alive
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
            logger.error(f"Error pinging app: {e}")
        time.sleep(300)

# Main function to start the bot and Flask app
def main():
    Thread(target=run).start()
    Thread(target=ping_app).start()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set_personality", set_personality))
    application.add_handler(CommandHandler("get_personality", get_personality))
    application.add_handler(InlineQueryHandler(inline_query))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_with_bot))

    application.run_polling()

if __name__ == "__main__":
    main()
