import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.wsgi import WSGIMiddleware
from telegram import Update
from telegram.ext import Application
from dashboard.app import flask_app
from bot.handlers import register_handlers

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
application = Application.builder().token(TELEGRAM_TOKEN).build()
register_handlers(application)

fastapi_app = FastAPI()
fastapi_app.mount("/dashboard", WSGIMiddleware(flask_app))

@fastapi_app.post("/webhook")
async def webhook(req: Request):
    update = Update.de_json(await req.json(), application.bot)
    await application.process_update(update)
    return {"ok": True}

@fastapi_app.get("/")
def root():
    return {"status": "ok"}
