import os
import re
import asyncio
from io import BytesIO
from telegram import (
    Update,
    InputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ==========================
# GLOBAL USER STORAGE
# ==========================
user_entries = {}

# ==========================
# FORMAT FUNCTION
# ==========================
def format_lines(text: str):
    lines = text.strip().splitlines()
    results = []
    count = 1

    def grab(pattern, src):
        match = re.search(pattern, src)
        return match.group(1) if match else "Unknown"

    for line in lines:
        if ":" not in line:
            continue

        email_pass = line.split(" | ")[0].strip()
        email, password = email_pass.split(":", 1)

        store = grab(r"Store: \[(.*?)\]", line)
        card_types = grab(r"CardTypes: \[(.*?)\]", line)
        last4 = grab(r"Last4Digits: \[(.*?)\]", line)
        expiry = grab(r"Expiry: \[(.*?)\]", line)
        points = grab(r"MorePoints: \[(.*?)\]", line)
        postal = grab(r"Postal: \[(.*?)\]", line)

        formatted = (
            "〰〰〰〰〰〰〰〰〰〰〰〰〰〰〰〰\n\n"
            f"( {count} )\n\n"
            f"👤 ⓊⓈⒺⓇ `{email}`\n"
            f"🔑 ⓅⒶⓈⓈ `{password}`\n\n"
            f"🌍 🅂🅃🄾🅁🄴: `{store}`\n"
            f"📝 🅃🅈🄿🄴🅂: `{card_types}]`\n"
            f"🏦 🄻🄰🅂🅃④: `{last4}]`\n"
            f"💳 🄴🅇🄿🄸🅁🅈: `{expiry}]`\n"
            f"💷 🄿🄾🄸🄽🅃🅂: `{points}]`\n"
            f"📮 🄿🄾🅂🅃🄰🄻: `{postal}]`\n\n"
            "〰〰〰〰〰〰〰〰〰〰〰〰〰〰〰〰"
        )

        results.append(formatted)
        count += 1

    return results

# ==========================
# UTIL: DELETE COMMAND
# ==========================
async def delete_command(update: Update, delay=1):
    await asyncio.sleep(delay)
    try:
        await update.message.delete()
    except:
        pass

# ==========================
# COMMANDS
# ==========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome To My Morry's Sorter!\n\n"
        "📤 Send a list as text or .txt file\n"
        "/get — grab logs one by one\n"
        "/shops — supported shops"
    )
    asyncio.create_task(delete_command(update))

async def shops(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🛍️ Supported Shops\n\n"
        "🌐 Domino's UK\n"
        "🌐 Just Eat\n"
        "🌐 ASOS\n"
        "🌐 Boohoo\n"
        "🌐 PrettyLittleThing\n"
        "🌐 Gymshark\n"
        "🌐 Boots\n"
        "🌐 Etsy\n"
        "🌐 Zalando\n"
        "🌐 Allbirds\n"
    )

    keyboard = [[InlineKeyboardButton("CLOSE MENU", callback_data="close_menu")]]
    msg = await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    context.user_data["shop_msg"] = msg.message_id

    asyncio.create_task(delete_command(update))

async def close_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.delete()

async def get_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in user_entries or not user_entries[user_id]:
        await update.message.reply_text("❌ No entries left.")
        return

    entry = user_entries[user_id].pop(0)
    remaining = len(user_entries[user_id])

    keyboard = [[InlineKeyboardButton("Grab A New Entry", callback_data="next_entry")]]

    await update.message.reply_text(
        f"{entry}\n\n📦 Remaining: {remaining}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

    asyncio.create_task(delete_command(update))

async def next_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if user_id not in user_entries or not user_entries[user_id]:
        await query.edit_message_text("❌ No entries left.")
        return

    entry = user_entries[user_id].pop(0)
    remaining = len(user_entries[user_id])

    keyboard = [[InlineKeyboardButton("Grab A New Entry", callback_data="next_entry")]]

    await query.edit_message_text(
        f"{entry}\n\n📦 Remaining: {remaining}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ==========================
# MESSAGE HANDLER
# ==========================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if update.message.document:
        file = await update.message.document.get_file()
        content = (await file.download_as_bytearray()).decode("utf-8")
    else:
        content = update.message.text
        bio = BytesIO(content.encode())
        bio.name = "Morrison's_List.txt"
        await update.message.reply_document(InputFile(bio))

    entries = format_lines(content)

    if not entries:
        await update.message.reply_text("⚠️ No valid entries found.")
        return

    user_entries[user_id] = entries

    await update.message.reply_text(
        f"✅ Logs loaded\n🎉 Total Morrison's: {len(entries)}\n/get to start"
    )

    try:
        await update.message.delete()
    except:
        pass

# ==========================
# MAIN
# ==========================
def main():
    TOKEN = os.getenv("8281759677:AAH9gWQla5s5x-U0wVvcFpsztqBOMQEWu2A") or "8281759677:AAH9gWQla5s5x-U0wVvcFpsztqBOMQEWu2A"

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("get", get_entry))
    app.add_handler(CommandHandler("shops", shops))

    app.add_handler(CallbackQueryHandler(next_entry, pattern="^next_entry$"))
    app.add_handler(CallbackQueryHandler(close_menu, pattern="^close_menu$"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.Document.FileExtension("txt"), handle_message))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
