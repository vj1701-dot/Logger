import asyncio
import logging
import mimetypes
from datetime import datetime
from io import BytesIO
from typing import List, Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, User as TelegramUserObj
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram.constants import ParseMode

from src.storage.gcs_client import GCSClient
from src.services.task_service import TaskService
from src.services.user_service import UserService
from src.models.task import Task, TaskStatus, TelegramUser, MediaType
from src.models.user import UserRole
from src.config import settings

logger = logging.getLogger(__name__)

class BotHandlers:
    def __init__(self, gcs_client: GCSClient):
        self.gcs_client = gcs_client
        self.task_service = TaskService(gcs_client)
        self.user_service = UserService(gcs_client)
        self.media_groups = {}  # Store media groups temporarily
    
    async def get_or_create_user(self, telegram_user: TelegramUserObj) -> TelegramUser:
        """Get or create user from Telegram user object"""
        user = await self.user_service.get_or_create_user(
            telegram_id=telegram_user.id,
            name=telegram_user.full_name,
            username=telegram_user.username
        )
        
        return TelegramUser(
            telegram_id=user.telegram_id,
            name=user.name,
            username=user.username
        )
    
    async def is_admin(self, telegram_id: int) -> bool:
        """Check if user is admin"""
        return await self.user_service.is_admin(telegram_id)
    
    def create_task_keyboard(self, uid: str, is_admin: bool = False) -> InlineKeyboardMarkup:
        """Create inline keyboard for task actions"""
        keyboard = []
        
        if is_admin:
            keyboard.extend([
                [
                    InlineKeyboardButton("✅ Done", callback_data=f"status_{uid}_done"),
                    InlineKeyboardButton("🔄 In Progress", callback_data=f"status_{uid}_in_progress")
                ],
                [
                    InlineKeyboardButton("⏸️ On Hold", callback_data=f"status_{uid}_on_hold"),
                    InlineKeyboardButton("❌ Cancel", callback_data=f"status_{uid}_canceled")
                ]
            ])
        else:
            keyboard.extend([
                [
                    InlineKeyboardButton("🔄 Start Working", callback_data=f"status_{uid}_in_progress"),
                    InlineKeyboardButton("⏸️ Put On Hold", callback_data=f"status_{uid}_on_hold")
                ],
                [
                    InlineKeyboardButton("✅ Request Review", callback_data=f"status_{uid}_done_pending_review")
                ]
            ])
        
        return InlineKeyboardMarkup(keyboard)
    
    async def handle_message(self, update: Update, context):
        """Handle incoming messages to create tasks"""
        try:
            message = update.message
            user = await self.get_or_create_user(message.from_user)
            
            # Check if this is part of a media group
            if message.media_group_id:
                await self.handle_media_group(update, context, user)
                return
            
            # Handle single message (text only or single media)
            await self.create_single_task(message, user, context)
            
        except Exception as e:
            logger.error(f"Failed to handle message: {e}")
            await message.reply_text(
                "❌ Sorry, there was an error creating your task. Please try again."
            )
    
    async def handle_media_group(self, update: Update, context, user: TelegramUser):
        """Handle media group messages (multiple photos/videos together)"""
        message = update.message
        media_group_id = message.media_group_id
        
        # Initialize media group if not exists
        if media_group_id not in self.media_groups:
            self.media_groups[media_group_id] = {
                'messages': [],
                'user': user,
                'timer': None
            }
        
        # Add message to group
        self.media_groups[media_group_id]['messages'].append(message)
        
        # Cancel previous timer if exists
        if self.media_groups[media_group_id]['timer']:
            self.media_groups[media_group_id]['timer'].cancel()
        
        # Set timer to process group after 2 seconds (to collect all messages)
        self.media_groups[media_group_id]['timer'] = asyncio.create_task(
            self.process_media_group_delayed(media_group_id, context)
        )
    
    async def process_media_group_delayed(self, media_group_id: str, context):
        """Process media group after delay to ensure all messages are collected"""
        await asyncio.sleep(2)  # Wait for all media in group
        
        if media_group_id not in self.media_groups:
            return
        
        group_data = self.media_groups[media_group_id]
        messages = group_data['messages']
        user = group_data['user']
        
        # Get text from first message with caption or use first message
        text = ""
        for msg in messages:
            if msg.caption:
                text = msg.caption
                break
        
        if not text and messages:
            text = messages[0].text or ""
        
        # Extract title and description
        lines = text.strip().split('\n', 1) if text else []
        title = lines[0][:100] if lines and lines[0] else f"Task {datetime.now().strftime('%H:%M')}"
        description = lines[1] if len(lines) > 1 else (lines[0] if len(lines) == 1 and lines[0] else "")
        
        # Collect all media files
        media_files = []
        for msg in messages:
            media_file = await self.extract_media_from_message(msg, context)
            if media_file:
                media_files.append(media_file)
        
        # Create single task with all media
        task = await self.task_service.create_task(
            title=title,
            description=description,
            created_by=user,
            media_files=media_files if media_files else None
        )
        
        is_admin = await self.is_admin(user.telegram_id)
        keyboard = self.create_task_keyboard(task.uid, is_admin)
        
        # Send response to first message
        if messages:
            response_text = f"✅ *Task Created*\\n\\n"
            response_text += f"🆔 *UID:* `{task.uid}`\\n"
            response_text += f"📝 *Title:* {task.title}\\n"
            response_text += f"📄 *Description:* {task.description}\\n"
            response_text += f"📊 *Status:* {task.status.value.replace('_', ' ').title()}\\n"
            response_text += f"📎 *Media:* {len(media_files)} file(s) attached\\n"
            
            await messages[0].reply_text(
                response_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
        
        # Clean up
        del self.media_groups[media_group_id]
    
    async def create_single_task(self, message, user: TelegramUser, context):
        """Create task from single message"""
        # Extract title and description
        text = message.text or message.caption or ""
        lines = text.strip().split('\n', 1) if text else []
        title = lines[0][:100] if lines and lines[0] else f"Task {datetime.now().strftime('%H:%M')}"
        description = lines[1] if len(lines) > 1 else (lines[0] if len(lines) == 1 and lines[0] else "")
        
        # Handle single media file
        media_files = []
        media_file = await self.extract_media_from_message(message, context)
        if media_file:
            media_files.append(media_file)
        
        # Create task
        task = await self.task_service.create_task(
            title=title,
            description=description,
            created_by=user,
            media_files=media_files if media_files else None
        )
        
        is_admin = await self.is_admin(user.telegram_id)
        keyboard = self.create_task_keyboard(task.uid, is_admin)
        
        # Build response message
        response_text = f"✅ *Task Created*\\n\\n"
        response_text += f"🆔 *UID:* `{task.uid}`\\n"
        response_text += f"📝 *Title:* {task.title}\\n"
        response_text += f"📄 *Description:* {task.description}\\n"
        response_text += f"📊 *Status:* {task.status.value.replace('_', ' ').title()}\\n"
        
        if media_files:
            response_text += f"📎 *Media:* {len(media_files)} file(s) attached\\n"
        
        await message.reply_text(
            response_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
    
    async def extract_media_from_message(self, message, context):
        """Extract media file from message"""
        try:
            if message.photo:
                # Get highest resolution photo
                photo = message.photo[-1]
                file = await context.bot.get_file(photo.file_id)
                file_data = BytesIO()
                await file.download_to_memory(file_data)
                
                return {
                    'type': MediaType.PHOTO.value,
                    'filename': f"{photo.file_id}.jpg",
                    'content_type': 'image/jpeg',
                    'data': file_data.getvalue()
                }
            
            elif message.video:
                file = await context.bot.get_file(message.video.file_id)
                file_data = BytesIO()
                await file.download_to_memory(file_data)
                
                return {
                    'type': MediaType.VIDEO.value,
                    'filename': f"{message.video.file_id}.mp4",
                    'content_type': 'video/mp4',
                    'data': file_data.getvalue()
                }
            
            elif message.audio:
                file = await context.bot.get_file(message.audio.file_id)
                file_data = BytesIO()
                await file.download_to_memory(file_data)
                
                return {
                    'type': MediaType.AUDIO.value,
                    'filename': message.audio.file_name or f"{message.audio.file_id}.mp3",
                    'content_type': 'audio/mpeg',
                    'data': file_data.getvalue()
                }
            
            elif message.voice:
                file = await context.bot.get_file(message.voice.file_id)
                file_data = BytesIO()
                await file.download_to_memory(file_data)
                
                return {
                    'type': MediaType.VOICE.value,
                    'filename': f"{message.voice.file_id}.ogg",
                    'content_type': 'audio/ogg',
                    'data': file_data.getvalue()
                }
            
            elif message.document:
                file = await context.bot.get_file(message.document.file_id)
                file_data = BytesIO()
                await file.download_to_memory(file_data)
                
                content_type = message.document.mime_type or 'application/octet-stream'
                
                return {
                    'type': MediaType.DOCUMENT.value,
                    'filename': message.document.file_name or f"{message.document.file_id}",
                    'content_type': content_type,
                    'data': file_data.getvalue()
                }
        
        except Exception as e:
            logger.error(f"Failed to extract media: {e}")
        
        return None
    
    async def handle_assign_command(self, update: Update, context):
        """Handle /assign command (admin only)"""
        try:
            user = await self.get_or_create_user(update.message.from_user)
            
            if not await self.is_admin(user.telegram_id):
                await update.message.reply_text("❌ This command is only available to admins.")
                return
            
            args = context.args
            if len(args) < 2:
                await update.message.reply_text(
                    "Usage: `/assign <UID> <@username or telegram_id>`",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            uid = args[0]
            assignee_identifier = args[1]
            
            # Try to parse as telegram ID or username
            assignee_id = None
            if assignee_identifier.startswith('@'):
                # Username - we'd need to lookup by username
                # For now, ask for telegram ID
                await update.message.reply_text(
                    "Please use Telegram ID instead of username for now."
                )
                return
            else:
                try:
                    assignee_id = int(assignee_identifier)
                except ValueError:
                    await update.message.reply_text("Invalid Telegram ID format.")
                    return
            
            # Get assignee user
            assignee_user_obj = await self.user_service.get_user(assignee_id)
            if not assignee_user_obj:
                await update.message.reply_text("❌ User not found.")
                return
            
            assignee = TelegramUser(
                telegram_id=assignee_user_obj.telegram_id,
                name=assignee_user_obj.name,
                username=assignee_user_obj.username
            )
            
            # Assign task
            success = await self.task_service.assign_task(uid, assignee)
            
            if success:
                await update.message.reply_text(
                    f"✅ Task `{uid}` assigned to {assignee.name}",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await update.message.reply_text(f"❌ Failed to assign task `{uid}`")
            
        except Exception as e:
            logger.error(f"Failed to handle assign command: {e}")
            await update.message.reply_text("❌ Error processing assignment.")
    
    async def handle_status_command(self, update: Update, context):
        """Handle /status command"""
        try:
            args = context.args
            if not args:
                await update.message.reply_text(
                    "Usage: `/status <UID>`",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            uid = args[0]
            task = await self.task_service.get_task(uid)
            
            if not task:
                await update.message.reply_text(f"❌ Task `{uid}` not found.")
                return
            
            user = await self.get_or_create_user(update.message.from_user)
            is_admin = await self.is_admin(user.telegram_id)
            
            # Build status message
            response_text = f"📋 *Task Status*\\n\\n"
            response_text += f"🆔 *UID:* `{task.uid}`\\n"
            response_text += f"📝 *Title:* {task.title}\\n"
            response_text += f"📊 *Status:* {task.status.value.replace('_', ' ').title()}\\n"
            response_text += f"⚡ *Priority:* {task.priority.value.title()}\\n"
            
            if task.assignees:
                assignee_names = [a.name for a in task.assignees]
                response_text += f"👥 *Assignees:* {', '.join(assignee_names)}\\n"
            
            if task.on_hold_reason:
                response_text += f"⏸️ *On Hold Reason:* {task.on_hold_reason}\\n"
            
            response_text += f"📅 *Created:* {task.created_at.strftime('%Y-%m-%d %H:%M')}\\n"
            response_text += f"🔄 *Updated:* {task.updated_at.strftime('%Y-%m-%d %H:%M')}\\n"
            
            if task.media:
                response_text += f"📎 *Media:* {len(task.media)} file(s)\\n"
            
            if task.notes:
                response_text += f"💬 *Notes:* {len(task.notes)} note(s)\\n"
            
            keyboard = self.create_task_keyboard(task.uid, is_admin)
            
            await update.message.reply_text(
                response_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Failed to handle status command: {e}")
            await update.message.reply_text("❌ Error retrieving task status.")
    
    async def handle_note_command(self, update: Update, context):
        """Handle /note command or reply to add notes"""
        try:
            user = await self.get_or_create_user(update.message.from_user)
            
            # Check if this is a reply to a task message
            if update.message.reply_to_message:
                # Extract UID from replied message
                reply_text = update.message.reply_to_message.text or ""
                uid_line = [line for line in reply_text.split('\\n') if 'UID:' in line]
                if uid_line:
                    uid = uid_line[0].split('`')[1]
                    note_content = update.message.text
                    
                    success = await self.task_service.add_task_note(
                        uid, note_content, user
                    )
                    
                    if success:
                        await update.message.reply_text(f"✅ Note added to task `{uid}`")
                    else:
                        await update.message.reply_text(f"❌ Failed to add note to task `{uid}`")
                    return
            
            # Handle /note command format
            args = context.args
            if len(args) < 2:
                await update.message.reply_text(
                    "Usage: `/note <UID> <note text>` or reply to a task message",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            uid = args[0]
            note_content = ' '.join(args[1:])
            
            success = await self.task_service.add_task_note(
                uid, note_content, user
            )
            
            if success:
                await update.message.reply_text(f"✅ Note added to task `{uid}`")
            else:
                await update.message.reply_text(f"❌ Failed to add note to task `{uid}`")
            
        except Exception as e:
            logger.error(f"Failed to handle note command: {e}")
            await update.message.reply_text("❌ Error adding note.")
    
    async def handle_callback_query(self, update: Update, context):
        """Handle inline keyboard button callbacks"""
        try:
            query = update.callback_query
            await query.answer()
            
            user = await self.get_or_create_user(query.from_user)
            
            # Parse callback data
            if query.data.startswith("status_"):
                parts = query.data.split("_")
                if len(parts) >= 3:
                    uid = parts[1]
                    new_status_str = "_".join(parts[2:])
                    
                    try:
                        new_status = TaskStatus(new_status_str)
                    except ValueError:
                        await query.edit_message_text("❌ Invalid status.")
                        return
                    
                    # Check permissions
                    is_admin = await self.is_admin(user.telegram_id)
                    
                    # Non-admins can only set certain statuses
                    if not is_admin and new_status in [TaskStatus.CANCELED, TaskStatus.DONE]:
                        await query.edit_message_text("❌ You don't have permission for this action.")
                        return
                    
                    # Handle on_hold status (requires reason)
                    reason = None
                    if new_status == TaskStatus.ON_HOLD:
                        # For simplicity, we'll ask for reason in a follow-up
                        # In a full implementation, you might use a conversation handler
                        reason = "Put on hold via bot"
                    
                    # Update status
                    success = await self.task_service.change_task_status(
                        uid, new_status, user, reason
                    )
                    
                    if success:
                        status_display = new_status.value.replace('_', ' ').title()
                        await query.edit_message_text(
                            f"✅ Task `{uid}` status changed to: {status_display}",
                            parse_mode=ParseMode.MARKDOWN
                        )
                        
                        # Notify if task is done
                        if new_status == TaskStatus.DONE:
                            await context.bot.send_message(
                                chat_id=query.message.chat_id,
                                text=f"🗑️ Media for task `{uid}` will be deleted in 7 days.",
                                parse_mode=ParseMode.MARKDOWN
                            )
                    else:
                        await query.edit_message_text(f"❌ Failed to update task `{uid}` status.")
            
        except Exception as e:
            logger.error(f"Failed to handle callback query: {e}")
            await query.edit_message_text("❌ Error processing request.")
    
    async def handle_start_command(self, update: Update, context):
        """Handle /start command"""
        try:
            user = await self.get_or_create_user(update.message.from_user)
            
            welcome_text = f"👋 Welcome to the Maintenance Task System!\\n\\n"
            welcome_text += f"📝 Send any message with text/media to create a task\\n"
            welcome_text += f"🔍 Use `/status <UID>` to check task status\\n"
            welcome_text += f"💬 Use `/note <UID> <text>` or reply to add notes\\n"
            
            if await self.is_admin(user.telegram_id):
                welcome_text += f"⚡ *Admin Commands:*\\n"
                welcome_text += f"👥 `/assign <UID> <telegram_id>` - assign tasks\\n"
                welcome_text += f"🌐 Dashboard: {settings.APP_BASE_URL}\\n"
            
            await update.message.reply_text(
                welcome_text,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Failed to handle start command: {e}")
            await update.message.reply_text("Welcome to the Maintenance Task System!")


def setup_bot_handlers(app: Application, gcs_client: GCSClient):
    """Setup all bot handlers"""
    handlers = BotHandlers(gcs_client)
    
    # Command handlers
    app.add_handler(CommandHandler("start", handlers.handle_start_command))
    app.add_handler(CommandHandler("status", handlers.handle_status_command))
    app.add_handler(CommandHandler("assign", handlers.handle_assign_command))
    app.add_handler(CommandHandler("note", handlers.handle_note_command))
    
    # Message handler for creating tasks (all media types and text)
    app.add_handler(MessageHandler(
        filters.TEXT | filters.PHOTO | filters.VIDEO | filters.AUDIO | 
        filters.VOICE | filters.Document.ALL,
        handlers.handle_message
    ))
    
    # Callback query handler for inline keyboards
    app.add_handler(CallbackQueryHandler(handlers.handle_callback_query))
    
    logger.info("Bot handlers setup complete")