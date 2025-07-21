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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
register_handlers(application)


app = FastAPI()
app.mount("/dashboard", WSGIMiddleware(flask_app))

# Ensure application is initialized on startup
@app.on_event("startup")
async def startup():
    try:
        await application.initialize()
        logger.info("Telegram bot initialized successfully at startup.")
    except Exception as e:
        logger.exception("Startup initialization failed.")

@app.post("/webhook")
async def webhook(req: Request):
    try:
        body = await req.json()
        logger.info(f"Incoming webhook: {body}")
        if not isinstance(body, dict) or "update_id" not in body:
            logger.warning("Malformed Telegram update received.")
            return {"error": "Invalid update payload."}
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
    return {"status": "ok", "service": "Logger Bot", "version": "1.0"}
