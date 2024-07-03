from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
import time
from pymongo import MongoClient

# Replace these with your actual credentials
api_id = 'YOUR_API_ID'
api_hash = 'YOUR_API_HASH'
bot_token = 'YOUR_BOT_TOKEN'

# MongoDB setup
mongo_url = "YOUR_MONGODB_CONNECTION_STRING"
client = MongoClient(mongo_url)
db = client['telegram_bot']
collection = db['user_settings']

# Initialize the bot
app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Delay in seconds
delay = 5

# Inline keyboard for managing words and channels
words_button = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("✚ Add More Words", callback_data="add_words"),
    ],
    [
        InlineKeyboardButton("❌ Remove Words", callback_data="rm_words"),
        InlineKeyboardButton("📖 View Words", callback_data="view_words")
    ],
    [
        InlineKeyboardButton("📑 Delete All Words", callback_data="delall_words"),
        InlineKeyboardButton("Back", callback_data="c_back"),
    ],
    [
        InlineKeyboardButton("➕ Set Source Channel", callback_data="set_source_channel"),
        InlineKeyboardButton("➕ Set Main Channel", callback_data="set_main_channel")
    ],
    [
        InlineKeyboardButton("❌ Remove Source Channel", callback_data="rm_source_channel"),
        InlineKeyboardButton("❌ Remove Main Channel", callback_data="rm_main_channel")
    ],
    [
        InlineKeyboardButton("📖 View Channels", callback_data="view_channels")
    ]
])

async def add_clearwords(query: CallbackQuery):
    sos = await app.ask(query.message.chat.id, text="📝 Send me the words you want to remove from the caption. For example: hello,how are you,test,use, etc.")
    words = sos.text
    data = words.split(",")
    add_words = list(map(str.strip, data))  # Remove any leading/trailing spaces
    collection.update_one({"user_id": query.from_user.id}, {"$set": {"clean_words": add_words}}, upsert=True)
    await query.message.reply_text("✅ Your deleted words have been successfully set.")

async def view_clearwords(query: CallbackQuery):
    data = collection.find_one({"user_id": query.from_user.id})
    if data and data.get("clean_words"):
        words = data.get("clean_words")
        lol = "\n".join([f"•> {woe}" for woe in words])
        await query.message.reply_text(f"**Here are your deleted words**\n\n`{lol}`")
    else:
        await query.answer("👀 You haven't set any deleted words !!", show_alert=True)

async def remove_clearwords(query: CallbackQuery):
    data = collection.find_one({"user_id": query.from_user.id})
    if data and data.get("clean_words"):
        sos = await app.ask(query.message.chat.id, text="📝 Send me the words you want to remove from the deleted words db. For example: hello,how are you,test,use, etc.")
        words = sos.text
        data = words.split(",")
        rm_words = list(map(str.strip, data))  # Remove any leading/trailing spaces
        updated_words = [word for word in data.get("clean_words") if word not in rm_words]
        collection.update_one({"user_id": query.from_user.id}, {"$set": {"clean_words": updated_words}})
        await query.message.reply_text("☘️ Your deleted words have been successfully deleted.")
    else:
        await query.answer("👀 You haven't set any deleted words !!", show_alert=True)

async def deleteall_clearwords(query: CallbackQuery):
    data = collection.find_one({"user_id": query.from_user.id})
    if data and data.get("clean_words"):
        collection.update_one({"user_id": query.from_user.id}, {"$set": {"clean_words": []}})
        await query.answer("☘️ Your deleted words have been successfully deleted.", show_alert=True)
    else:
        await query.answer("👀 You haven't set any deleted words !!", show_alert=True)

async def set_source_channel(query: CallbackQuery):
    sos = await app.ask(query.message.chat.id, text="📝 Send me the source channel username or ID.")
    source_channel = sos.text.strip()
    collection.update_one({"user_id": query.from_user.id}, {"$set": {"source_channel": source_channel}}, upsert=True)
    await query.message.reply_text(f"✅ Source channel has been set to `{source_channel}`.")

async def set_main_channel(query: CallbackQuery):
    sos = await app.ask(query.message.chat.id, text="📝 Send me the main channel username or ID.")
    main_channel = sos.text.strip()
    collection.update_one({"user_id": query.from_user.id}, {"$set": {"main_channel": main_channel}}, upsert=True)
    await query.message.reply_text(f"✅ Main channel has been set to `{main_channel}`.")

async def view_channels(query: CallbackQuery):
    data = collection.find_one({"user_id": query.from_user.id})
    source_channel = data.get("source_channel", "Not set")
    main_channel = data.get("main_channel", "Not set")
    await query.message.reply_text(f"**Channels**\n\nSource Channel: `{source_channel}`\nMain Channel: `{main_channel}`")

async def remove_source_channel(query: CallbackQuery):
    collection.update_one({"user_id": query.from_user.id}, {"$unset": {"source_channel": 1}})
    await query.message.reply_text("✅ Source channel has been removed.")

async def remove_main_channel(query: CallbackQuery):
    collection.update_one({"user_id": query.from_user.id}, {"$unset": {"main_channel": 1}})
    await query.message.reply_text("✅ Main channel has been removed.")

@app.on_message(filters.command("start"))
async def start_command(client, message: Message):
    await message.reply("Manage your settings using the buttons below:", reply_markup=words_button)

@app.on_message(filters.chat(lambda _, __, message: collection.find_one({"user_id": message.from_user.id}) and collection.find_one({"user_id": message.from_user.id}).get("source_channel")) & filters.media)
async def auto_forward(client, message):
    data = collection.find_one({"user_id": message.from_user.id})
    clean_words = data.get("clean_words", [])
    source_channel = data.get("source_channel")
    main_channel = data.get("main_channel")

    # Ensure both channels are set
    if not source_channel or not main_channel:
        return

    # Get the media caption
    caption = message.caption if message.caption else ""

    # Remove specific words from the caption
    for word in clean_words:
        caption = caption.replace(word, '')

    # Forward the media with the modified caption
    await client.send_message(
        chat_id=main_channel,
        text=caption,
        reply_to_message_id=message.message_id
    )

    # Add delay
    time.sleep(delay)

@app.on_callback_query(filters.regex("add_words"))
async def on_add_words(client, query: CallbackQuery):
    await add_clearwords(query)

@app.on_callback_query(filters.regex("view_words"))
async def on_view_words(client, query: CallbackQuery):
    await view_clearwords(query)

@app.on_callback_query(filters.regex("rm_words"))
async def on_remove_words(client, query: CallbackQuery):
    await remove_clearwords(query)

@app.on_callback_query(filters.regex("delall_words"))
async def on_delete_all_words(client, query: CallbackQuery):
    await deleteall_clearwords(query)

@app.on_callback_query(filters.regex("set_source_channel"))
async def on_set_source_channel(client, query: CallbackQuery):
    await set_source_channel(query)

@app.on_callback_query(filters.regex("set_main_channel"))
async def on_set_main_channel(client, query: CallbackQuery):
    await set_main_channel(query)

@app.on_callback_query(filters.regex("view_channels"))
async def on_view_channels(client, query: CallbackQuery):
    await view_channels(query)

@app.on_callback_query(filters.regex("rm_source_channel"))
async def on_remove_source_channel(client, query: CallbackQuery):
    await remove_source_channel(query)

@app.on_callback_query(filters.regex("rm_main_channel"))
async def on_remove_main_channel(client, query: CallbackQuery):
    await remove_main_channel(query)

@app.on_callback_query(filters.regex("c_back"))
async def on_back(client, query: CallbackQuery):
    await query.message.edit_reply_markup(reply_markup=words_button)

# Run the bot
app.run()
