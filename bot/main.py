from fastapi import FastAPI, Request
import logging
from telegram import Update
from telegram.ext import Application
from bot.handlers import register_handlers
import os

app = FastAPI()

logging.basicConfig(level=logging.INFO)
TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
application = Application.builder().token(TELEGRAM_TOKEN).build()
register_handlers(application)

@app.post("/webhook")
async def webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}


@app.get("/")
def root():
    return {"status": "ok"}
