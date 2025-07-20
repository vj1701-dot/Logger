import logging
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.wsgi import WSGIMiddleware
from telegram import Update
from telegram.ext import Application
from dashboard.app import flask_app
from bot.handlers import register_handlers
from bot.config import TELEGRAM_BOT_TOKEN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
register_handlers(application)


app = FastAPI()
app.mount("/dashboard", WSGIMiddleware(flask_app))

# Ensure application is initialized on startup
@app.on_event("startup")
async def startup():
    await application.initialize()

@app.post("/webhook")
async def webhook(req: Request):
    try:
        body = await req.json()
        logger.info(f"Incoming webhook: {body}")
        update = Update.de_json(body, application.bot)
        if not application.running:
            await application.initialize()
        await application.process_update(update)
        return {"ok": True}
    except Exception as e:
        logger.exception("Webhook handling failed")
        return {"error": str(e)}

@app.get("/")
def root():
    return {"status": "ok"}



