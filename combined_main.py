import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.wsgi import WSGIMiddleware
from telegram import Update
from telegram.ext import Application
from dashboard.app import flask_app
from bot.handlers import register_handlers
from bot.config import TELEGRAM_BOT_TOKEN

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
    update = Update.de_json(await req.json(), application.bot)
    if not application.running:
        await application.initialize()
    await application.process_update(update)
    return {"ok": True}

@app.get("/")
def root():
    return {"status": "ok"}



