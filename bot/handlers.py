from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from bot.utils import generate_uid
from bot.google_utils import upload_file_to_drive, append_row_to_sheet, update_row_in_sheet
from bot.config import (
    GOOGLE_DRIVE_FOLDER_ID, GOOGLE_SHEET_ID, GOOGLE_CREDENTIALS,
    DASHBOARD_URL, ADMIN_IDS
)
import datetime
import os
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def log_task(uid, username, submitted_by, message, media_url):
    now = datetime.datetime.utcnow().isoformat()
    row = [
        now, uid, username, submitted_by, message, media_url,
        "New", "", "", ""  # Status, Updated By, Updated Time, Assigned To
    ]
    append_row_to_sheet(GOOGLE_SHEET_ID, row, GOOGLE_CREDENTIALS)


def update_status(uid, status, updated_by):
    # This is a placeholder. In production, you would search for the row with UID and update it.
    # For demo, let's assume UID is the row number (not true in real Sheets, but for brevity).
    now = datetime.datetime.utcnow().isoformat()
    row = ["", uid, "", "", "", "", status, updated_by, now, ""]
    update_row_in_sheet(GOOGLE_SHEET_ID, int(uid), row, GOOGLE_CREDENTIALS)


def register_handlers(app: Application):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("dashboard", dashboard))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CallbackQueryHandler(status_button))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send a message or media to log a task.")


async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) not in ADMIN_IDS:
        await update.message.reply_text("Unauthorized")
        return
    await update.message.reply_text(f"Dashboard: {DASHBOARD_URL}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = generate_uid()
    user = update.effective_user.username or "unknown"
    submitted_by = f"{update.effective_user.first_name} {update.effective_user.last_name or ''}".strip()
    msg = update.message
    media_url = ""
    file_path = None

    try:
        logger.info(f"Received message from {submitted_by} ({user})")

        if msg.photo:
            file = await msg.photo[-1].get_file()
            file_path = await file.download_to_drive(f"/tmp/{uid}.jpg")
            media_url = upload_file_to_drive(file_path, f"{uid}.jpg", GOOGLE_DRIVE_FOLDER_ID, GOOGLE_CREDENTIALS)
        elif msg.video:
            file = await msg.video.get_file()
            file_path = await file.download_to_drive(f"/tmp/{uid}.mp4")
            media_url = upload_file_to_drive(file_path, f"{uid}.mp4", GOOGLE_DRIVE_FOLDER_ID, GOOGLE_CREDENTIALS)
        elif msg.audio:
            file = await msg.audio.get_file()
            file_path = await file.download_to_drive(f"/tmp/{uid}.mp3")
            media_url = upload_file_to_drive(file_path, f"{uid}.mp3", GOOGLE_DRIVE_FOLDER_ID, GOOGLE_CREDENTIALS)

    except Exception as e:
        logger.exception("Error handling media upload")
        await msg.reply_text(f"Error uploading media: {e}")
        return

    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up temp file: {file_path}")

    log_task(uid, user, submitted_by, msg.text or "", media_url)
    logger.info(f"Task logged with UID: {uid}")
    await msg.reply_text(f"✅ Task created! Your task ID is: {uid}\nView all tasks at: {DASHBOARD_URL}")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) not in ADMIN_IDS:
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
    if str(update.effective_user.id) not in ADMIN_IDS:
        await update.callback_query.answer("Unauthorized")
        return
    uid, status = update.callback_query.data.split(":")
    update_status(uid, status, update.effective_user.username)
    logger.info(f"Status for UID {uid} updated to {status} by {update.effective_user.username}")
    await update.callback_query.edit_message_text(f"✅ UID {uid} updated to {status}")
