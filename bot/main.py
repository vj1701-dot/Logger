import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from .uid_utils import generate_uid
from .drive_utils import upload_media_to_drive
from .sheets_utils import log_task_to_sheet

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler

async def send_status_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ You are not authorized to update status.")
        return
    try:
        uid = context.args[0]
        keyboard = [
            [InlineKeyboardButton("New", callback_data=f"status:{uid}:New"),
             InlineKeyboardButton("In Progress", callback_data=f"status:{uid}:In Progress")],
            [InlineKeyboardButton("Done", callback_data=f"status:{uid}:Done"),
             InlineKeyboardButton("Delete", callback_data=f"status:{uid}:Delete")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(f"Select status for UID {uid}:", reply_markup=reply_markup)
    except IndexError:
        await update.message.reply_text("Usage: /status <UID>")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data  # format: status:UID:New
    if not await is_admin(query.from_user.id):
        await query.edit_message_text("⛔ You are not authorized.")
        return
    try:
        _, uid, new_status = data.split(":")
        from .sheets_utils import update_task_status
        update_task_status(uid, new_status, query.from_user.username)
        await query.edit_message_text(f"✅ UID {uid} status updated to {new_status}")
    except Exception as e:
        await query.edit_message_text("Error updating status.")


async def is_admin(user_id: int) -> bool:
    # Replace with actual admin ID list or check from environment
    admin_ids = os.getenv("ADMIN_IDS", "").split(",")
    return str(user_id) in admin_ids

async def status_command_UNUSED(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ You are not authorized to update status.")
        return
    try:
        uid, status = context.args
        # TODO: Implement actual update in Google Sheets
        await update.message.reply_text(f"✅ Status for {uid} updated to {status}")
    except ValueError:
        await update.message.reply_text("Usage: /status <UID> <New|In Progress|Done|Delete>")

async def assign_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ You are not authorized to assign tasks.")
        return
    try:
        uid, assignee = context.args
        # TODO: Implement actual assignment update in Google Sheets
        await update.message.reply_text(f"✅ {uid} assigned to {assignee}")
    except ValueError:
        await update.message.reply_text("Usage: /assign <UID> <Name>")


# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to the Task Bot!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = update.message
        uid = generate_uid()
        username = message.from_user.username or "Unknown"
        submitted_by = f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
        text = message.text or ""
        media_url = ""

        if message.photo:
            file = await message.photo[-1].get_file()
            file_path = f"tmp/{uid}.jpg"
            await file.download_to_drive(file_path)
            media_url = upload_media_to_drive(file_path, f"{uid}.jpg")
        elif message.video:
            file = await message.video.get_file()
            file_path = f"tmp/{uid}.mp4"
            await file.download_to_drive(file_path)
            media_url = upload_media_to_drive(file_path, f"{uid}.mp4")
        elif message.audio:
            file = await message.audio.get_file()
            file_path = f"tmp/{uid}.mp3"
            await file.download_to_drive(file_path)
            media_url = upload_media_to_drive(file_path, f"{uid}.mp3")

        log_task_to_sheet(uid, username, submitted_by, text, media_url)
                await update.message.reply_text(
            f"✅ Task created! Your task ID is: {uid}\n\n"
            f"View all tasks at: [Dashboard](https://your-cloudrun-service-url.a.run.app)",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.exception("Error handling message")
        await update.message.reply_text("Something went wrong while processing your message.")

def main():
    from telegram.ext import Application
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(CommandHandler("status", send_status_buttons))
    app.add_handler(CommandHandler("assign", assign_command))

    app.add_handler(MessageHandler(filters.ALL, handle_message))

    # Webhook mode
    port = int(os.environ.get("PORT", 8080))
    webhook_url = os.environ["WEBHOOK_URL"]
    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        webhook_url=webhook_url
    )

if __name__ == "__main__":
    main()
