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

# Define your bot token, API keys
BOT_TOKEN = "7564262351:AAGzU9ipJT1CN01JvNTgSQVBhzmhjbm5Bp4"
YOUTUBE_API_KEY = "AIzaSyCHcbAHrO383FWQqIXrS-H7Xid1G4CaGeg"
GOOGLE_API_KEY = "AIzaSyCHcbAHrO383FWQqIXrS-H7Xid1G4CaGeg"
GOOGLE_CX = "a54de47eb8d024e8f"
GIPHY_API_KEY = "cd2qSZ4eWr8ineY0X9rhBalcuWVrRxyx"
OPENAI_API_KEY = "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"
'openai.api_key = os.getenv("OPENAI_API_KEY")'
# Create your bot application
application = ApplicationBuilder().token(BOT_TOKEN).build()

# Store user-specific personalities
user_personalities = {}

# Define API search functions
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
    return [{"title": f"Sample Song: {query}", "url": "https://example.com/sample_song"}]

# Function to generate ChatGPT responses
async def generate_response(prompt, personality):
    full_prompt = f"The bot's personality is: {personality}\nUser: {prompt}\nBot:"
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=full_prompt,
        max_tokens=150
    )
    return response.choices[0].text.strip()

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
        "Hi! I can help you search for YouTube videos, Google results, music, and GIFs. I can also chat and adjust my personality. "
        "Use /set_personality to define my personality."
    )

# Inline query handler
async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.inline_query.query
    if not query:
        return

    results = []

    if query.lower().startswith("chatgpt:"):
        # If query starts with 'chatgpt:', use ChatGPT to answer the query
        gpt_query = query[len("chatgpt:"):].strip()  # Remove 'chatgpt:' prefix
        response = await chatgpt_response(gpt_query)
        results.append(
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="ChatGPT Response",
                input_message_content=InputTextMessageContent(response),
                description=f"Response from ChatGPT: {response}",
            )
        )
    else:
        # Your other API search logic (YouTube, Google, etc.)
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
# Flask app to run alongside the bot
app = Flask(__name__)

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
            requests.get('https://wanderer-5g5v.onrender.com')  # Ping your app URL
        except requests.exceptions.RequestException as e:
            print(f"Error pinging app: {e}")
        time.sleep(300)  # Sleep for 5 minutes

# Main function to start the bot and Flask app

# Handle direct chat with the bot
async def chat_with_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    if user_message:
        try:
            response = get_openai_response(user_message)
            await update.message.reply_text(response)
        except Exception as e:
            await update.message.reply_text("Sorry, I couldn't process that. Please try again later.")
            logger.error(f"Error in chat_with_bot: {e}")

# Add the message handler for non-command messages
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_with_bot))
async def chatgpt_response(query: str) -> str:
    try:
        response = openai.Completion.create(
            model="text-davinci-003",  # Use appropriate model
            prompt=query,
            temperature=0.7,  # You can adjust this to make responses more creative
            max_tokens=150  # You can adjust this for response length
        )
        return response.choices[0].text.strip()
    except Exception as e:
        return f"Error: {str(e)}"  
def main():
    # Start the Flask app in a separate thread
    Thread(target=run).start()

    # Start pinging the app every 5 minutes in a separate thread
    Thread(target=ping_app).start()

    # Add command and inline query handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set_personality", set_personality))
    application.add_handler(CommandHandler("get_personality", get_personality))
    application.add_handler(InlineQueryHandler(inline_query))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chat))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()

