from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application
import os

# Initialize FastAPI
app = FastAPI()

# Create the Telegram application
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
application = Application.builder().token(TELEGRAM_TOKEN).build()

@app.post("/webhook")
async def webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}
