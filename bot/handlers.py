from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from bot.utils import generate_uid
from bot.google_utils import upload_file_to_drive, append_row_to_sheet, update_row_in_sheet
from bot.config import (
	GOOGLE_DRIVE_FOLDER_ID, GOOGLE_SHEET_ID, GOOGLE_CREDENTIALS,
	DASHBOARD_URL
)
from bot.admins import is_admin, add_admin, remove_admin, get_admin_ids
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
	logger.info(f"Appending task row to sheet {GOOGLE_SHEET_ID}: uid={uid} user={username} media={bool(media_url)}")
	append_row_to_sheet(GOOGLE_SHEET_ID, row, GOOGLE_CREDENTIALS)


def update_status(uid, status, updated_by):
	# Placeholder: update by row index is not accurate; kept for demo purposes
	now = datetime.datetime.utcnow().isoformat()
	row = ["", uid, "", "", "", "", status, updated_by, now, ""]
	logger.info(f"Updating status in sheet {GOOGLE_SHEET_ID}: uid={uid} -> {status} by {updated_by}")
	update_row_in_sheet(GOOGLE_SHEET_ID, int(uid), row, GOOGLE_CREDENTIALS)


def register_handlers(app: Application):
	logger.info("Registering Telegram command and message handlers")
	app.add_handler(CommandHandler("start", start))
	app.add_handler(CommandHandler("dashboard", dashboard))
	app.add_handler(CommandHandler("status", status))
	app.add_handler(CommandHandler("admin_add", admin_add))
	app.add_handler(CommandHandler("admin_remove", admin_remove))
	app.add_handler(CommandHandler("admins", admins_list))
	app.add_handler(CallbackQueryHandler(status_button))
	app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
	logger.info(f"/start from user_id={update.effective_user.id} username={update.effective_user.username}")
	await update.message.reply_text("Send a message or media to log a task.")


async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
	user_id = update.effective_user.id
	logger.info(f"/dashboard requested by user_id={user_id}")
	if not is_admin(user_id):
		logger.warning(f"Unauthorized /dashboard by user_id={user_id}")
		await update.message.reply_text("Unauthorized")
		return
	await update.message.reply_text(f"Dashboard: {DASHBOARD_URL}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
	uid = generate_uid()
	user = update.effective_user.username or "unknown"
	user_id = update.effective_user.id
	submitted_by = f"{update.effective_user.first_name} {update.effective_user.last_name or ''}".strip()
	msg = update.message
	media_url = ""
	file_path = None

	try:
		logger.info(f"Incoming message from user_id={user_id} username={user} uid={uid}")

		if msg.photo:
			logger.info("Photo detected")
			file = await msg.photo[-1].get_file()
			file_path = await file.download_to_drive(f"/tmp/{uid}.jpg")
			media_url = upload_file_to_drive(file_path, f"{uid}.jpg", GOOGLE_DRIVE_FOLDER_ID, GOOGLE_CREDENTIALS)
		elif msg.video:
			logger.info("Video detected")
			file = await msg.video.get_file()
			file_path = await file.download_to_drive(f"/tmp/{uid}.mp4")
			media_url = upload_file_to_drive(file_path, f"{uid}.mp4", GOOGLE_DRIVE_FOLDER_ID, GOOGLE_CREDENTIALS)
		elif msg.audio:
			logger.info("Audio detected")
			file = await msg.audio.get_file()
			file_path = await file.download_to_drive(f"/tmp/{uid}.mp3")
			media_url = upload_file_to_drive(file_path, f"{uid}.mp3", GOOGLE_DRIVE_FOLDER_ID, GOOGLE_CREDENTIALS)
		else:
			logger.info("Text-only message")

	except Exception as e:
		logger.exception("Error handling media upload")
		await msg.reply_text(f"Error uploading media: {e}")
		return

	finally:
		if file_path and os.path.exists(file_path):
			os.remove(file_path)
			logger.info(f"Cleaned up temp file: {file_path}")

	log_task(uid, user, submitted_by, msg.text or "", media_url)
	logger.info(f"Task logged uid={uid} user_id={user_id}")
	await msg.reply_text(f"✅ Task created! Your task ID is: {uid}\nView all tasks at: {DASHBOARD_URL}")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
	user_id = update.effective_user.id
	logger.info(f"/status requested by user_id={user_id} args={context.args}")
	if not is_admin(user_id):
		logger.warning(f"Unauthorized /status by user_id={user_id}")
		await update.message.reply_text("Unauthorized")
		return
	if not context.args:
		await update.message.reply_text("Usage: /status <UID>")
		return
	uid = context.args[0]
	logger.info(f"Creating status buttons for UID {uid}")
	buttons = [
		[InlineKeyboardButton("🆕 New", callback_data=f"{uid}:New"),
		 InlineKeyboardButton("🕒 In Progress", callback_data=f"{uid}:In Progress")],
		[InlineKeyboardButton("✅ Done", callback_data=f"{uid}:Done"),
		 InlineKeyboardButton("🗑️ Delete", callback_data=f"{uid}:Delete")]
	]
	markup = InlineKeyboardMarkup(buttons)
	await update.message.reply_text(f"Update status for {uid}:", reply_markup=markup)


async def status_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
	user_id = update.effective_user.id
	logger.info(f"status button by user_id={user_id} data={update.callback_query.data}")
	if not is_admin(user_id):
		await update.callback_query.answer("Unauthorized")
		return
	uid, status = update.callback_query.data.split(":")
	update_status(uid, status, update.effective_user.username)
	logger.info(f"Status for UID {uid} updated to {status} by {update.effective_user.username}")
	await update.callback_query.edit_message_text(f"✅ UID {uid} updated to {status}")


async def admin_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
	user_id = update.effective_user.id
	logger.info(f"/admin_add by user_id={user_id} args={context.args}")
	if not is_admin(user_id):
		await update.message.reply_text("Unauthorized")
		return
	if not context.args:
		await update.message.reply_text("Usage: /admin_add <telegram_user_id>")
		return
	target_id = context.args[0].strip()
	added = add_admin(target_id)
	if added:
		await update.message.reply_text(f"Added admin: {target_id}")
	else:
		await update.message.reply_text(f"{target_id} is already an admin")


async def admin_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
	user_id = update.effective_user.id
	logger.info(f"/admin_remove by user_id={user_id} args={context.args}")
	if not is_admin(user_id):
		await update.message.reply_text("Unauthorized")
		return
	if not context.args:
		await update.message.reply_text("Usage: /admin_remove <telegram_user_id>")
		return
	target_id = context.args[0].strip()
	removed = remove_admin(target_id)
	if removed:
		await update.message.reply_text(f"Removed admin: {target_id}")
	else:
		await update.message.reply_text(f"{target_id} was not an admin")


async def admins_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
	user_id = update.effective_user.id
	logger.info(f"/admins by user_id={user_id}")
	if not is_admin(user_id):
		await update.message.reply_text("Unauthorized")
		return
	admins = sorted(list(get_admin_ids()))
	if not admins:
		await update.message.reply_text("No admins set.")
		return
	await update.message.reply_text("Admins:\n" + "\n".join(admins))