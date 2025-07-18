from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram import Update
from bot.utils import generate_uid
from bot.drive_utils import upload_to_drive
from bot.sheets_utils import log_task, update_status
import os

DASHBOARD_URL = os.environ.get("DASHBOARD_URL", "/dashboard")
ADMINS = os.environ.get("ADMIN_IDS", "").split(",")

def register_handlers(app: Application):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("dashboard", dashboard))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send a message or media to log a task.")

async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) not in ADMINS:
        await update.message.reply_text("Unauthorized")
        return
    await update.message.reply_text(f"Dashboard: {DASHBOARD_URL}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = generate_uid()
    user = update.effective_user.username or "unknown"
    msg = update.message
    media_url = ""

    if msg.photo:
        file = await msg.photo[-1].get_file()
        media_url = await upload_to_drive(file, f"{uid}.jpg")
    elif msg.video:
        file = await msg.video.get_file()
        media_url = await upload_to_drive(file, f"{uid}.mp4")
    elif msg.audio:
        file = await msg.audio.get_file()
        media_url = await upload_to_drive(file, f"{uid}.mp3")

    log_task(uid, user, msg.text or "", media_url)
    await msg.reply_text(f"✅ Task created! Your task ID is: {uid}\nView all tasks at: {DASHBOARD_URL}")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) not in ADMINS:
        await update.message.reply_text("Unauthorized")
        return
    if not context.args:
        await update.message.reply_text("Usage: /status <UID>")
        return
    uid = context.args[0]
    buttons = [
        [InlineKeyboardButton("🆕 New", callback_data=f"{uid}:New"),
         InlineKeyboardButton("🕒 In Progress", callback_data=f"{uid}:In Progress")],
        [InlineKeyboardButton("✅ Done", callback_data=f"{uid}:Done"),
         InlineKeyboardButton("🗑️ Delete", callback_data=f"{uid}:Delete")]
    ]
    markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(f"Update status for {uid}:", reply_markup=markup)

async def status_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) not in ADMINS:
        await update.callback_query.answer("Unauthorized")
        return
    uid, status = update.callback_query.data.split(":")
    update_status(uid, status, update.effective_user.username)
    await update.callback_query.edit_message_text(f"✅ UID {uid} updated to {status}")

def register_handlers(app: Application):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("dashboard", dashboard))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CallbackQueryHandler(status_button))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
