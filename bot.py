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

# Define your API keys and bot token
BOT_TOKEN = "7564262351:AAGzU9ipJT1CN01JvNTgSQVBhzmhjbm5Bp4"
YOUTUBE_API_KEY = "AIzaSyCHcbAHrO383FWQqIXrS-H7Xid1G4CaGeg"
GOOGLE_API_KEY = "AIzaSyCHcbAHrO383FWQqIXrS-H7Xid1G4CaGeg"
GOOGLE_CX = "a54de47eb8d024e8f"
GIPHY_API_KEY = "cd2qSZ4eWr8ineY0X9rhBalcuWVrRxyx"
OPENAI_API_KEY = "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"

# Set OpenAI API key
openai.api_key = OPENAI_API_KEY

# Create a Flask app
app = Flask(__name__)

# User personalities storage
user_personalities = {}

# Initialize the bot application
application = ApplicationBuilder().token(BOT_TOKEN).build()

# Function to generate ChatGPT responses
async def generate_response(prompt, personality):
    try:
        full_prompt = f"The bot's personality is: {personality}\nUser: {prompt}\nBot:"
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=full_prompt,
            max_tokens=150,
            temperature=0.7
        )
        return response.choices[0].text.strip()
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return "Sorry, I couldn't process that. Please try again later."

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

# Command to search YouTube
async def search_youtube(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.args:
        query = " ".join(context.args)
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        request = youtube.search().list(
            part="snippet",
            maxResults=5,
            q=query
        )
        response = request.execute()
        results = [f"{item['snippet']['title']}: https://www.youtube.com/watch?v={item['id']['videoId']}" for item in response['items'] if item['id']['kind'] == 'youtube#video']
        await update.message.reply_text("\n".join(results) if results else "No results found.")
    else:
        await update.message.reply_text("Please provide a search query. Example: /search_youtube Python tutorials")

# Command to search Google
async def search_google(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.args:
        query = " ".join(context.args)
        url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={GOOGLE_CX}&q={query}"
        try:
            response = requests.get(url).json()
            results = [f"{item['title']}: {item['link']}" for item in response.get('items', [])]
            await update.message.reply_text("\n".join(results) if results else "No results found.")
        except Exception as e:
            logger.error(f"Error searching Google: {e}")
            await update.message.reply_text("Error occurred while searching Google.")
    else:
        await update.message.reply_text("Please provide a search query. Example: /search_google AI news")

# Command to search GIFs
async def search_gif(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.args:
        query = " ".join(context.args)
        url = f"https://api.giphy.com/v1/gifs/search?api_key={GIPHY_API_KEY}&q={query}&limit=5"
        try:
            response = requests.get(url).json()
            results = [gif['url'] for gif in response.get('data', [])]
            await update.message.reply_text("\n".join(results) if results else "No GIFs found.")
        except Exception as e:
            logger.error(f"Error searching GIFs: {e}")
            await update.message.reply_text("Error occurred while searching GIFs.")
    else:
        await update.message.reply_text("Please provide a search query. Example: /search_gif cats")

# Handle all text messages for ChatGPT-like chatting
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    message = update.message.text

    # Get the personality for the user
    personality = user_personalities.get(user_id, "neutral and helpful")

    # Generate ChatGPT response
    response = await generate_response(message, personality)

    # Send the response back
    await update.message.reply_text(response)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hi! I can help you search for YouTube videos, Google results, GIFs, and chat with you.\n"
        "Use /set_personality to define my personality."
    )

# Flask app to keep the bot running
@app.route('/')
def home():
    return "Bot is running!"

# Threaded function to run Flask app
def run():
    app.run(host='0.0.0.0', port=8080)

# Function to ping the app periodically
def ping_app():
    while True:
        try:
            requests.get('https://wanderer-5g5v.onrender.com')  # Replace with your app URL
        except requests.exceptions.RequestException as e:
            logger.error(f"Error pinging app: {e}")
        time.sleep(300)  # Sleep for 5 minutes

# Main function to start the bot and Flask app
def main():
    # Start the Flask app in a separate thread
    Thread(target=run).start()

    # Start pinging the app every 5 minutes in a separate thread
    Thread(target=ping_app).start()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set_personality", set_personality))
    application.add_handler(CommandHandler("get_personality", get_personality))
    application.add_handler(CommandHandler("search_youtube", search_youtube))
    application.add_handler(CommandHandler("search_google", search_google))
    application.add_handler(CommandHandler("search_gif", search_gif))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
