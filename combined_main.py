import logging
import os
from fastapi import FastAPI, Request, HTTPException
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

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not set. Provide it via environment variable.")

application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
register_handlers(application)

app = FastAPI()
app.mount("/dashboard", WSGIMiddleware(flask_app))

# Debug env snapshot
logger.info("Startup env snapshot: PUBLIC_BASE_URL=%s, WEBHOOK_SECRET_SET=%s", os.environ.get("PUBLIC_BASE_URL"), bool(os.environ.get("TELEGRAM_WEBHOOK_SECRET")))

# Ensure application is initialized on startup
@app.on_event("startup")
async def startup():
    try:
        await application.initialize()
        logger.info("Telegram bot initialized successfully at startup.")
    except Exception:
        logger.exception("Startup initialization failed.")


def _derive_base_url(req: Request) -> str:
    public = os.environ.get("PUBLIC_BASE_URL")
    if public:
        return public.rstrip("/")
    # Derive from request headers (works on Cloud Run)
    proto = req.headers.get("x-forwarded-proto", "https")
    host = req.headers.get("host")
    logger.info("Deriving base URL from headers: x-forwarded-proto=%s host=%s", proto, host)
    if not host:
        raise HTTPException(status_code=400, detail="Cannot determine host for webhook URL. Set PUBLIC_BASE_URL.")
    return f"{proto}://{host}"


@app.post("/webhook")
async def webhook(req: Request):
    try:
        # Optional secret token validation
        expected_secret = os.environ.get("TELEGRAM_WEBHOOK_SECRET")
        header_secret = req.headers.get("x-telegram-bot-api-secret-token")
        logger.info("/webhook headers: secret_present=%s content_type=%s", bool(header_secret), req.headers.get("content-type"))
        if expected_secret:
            if header_secret != expected_secret:
                logger.warning("Invalid webhook secret: expected=%s got_present=%s", bool(expected_secret), bool(header_secret))
                raise HTTPException(status_code=403, detail="Invalid webhook secret token")

        body = await req.json()
        logger.info("Incoming webhook body keys: %s", list(body.keys()) if isinstance(body, dict) else type(body))
        if not isinstance(body, dict) or "update_id" not in body:
            logger.warning("Malformed Telegram update received.")
            return {"error": "Invalid update payload."}
        update = Update.de_json(body, application.bot)
        if not application.running:
            await application.initialize()
        await application.process_update(update)
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Webhook handling failed")
        return {"error": str(e)}


@app.post("/set_webhook")
async def set_webhook(req: Request):
    base = _derive_base_url(req)
    url = f"{base}/webhook"
    secret = os.environ.get("TELEGRAM_WEBHOOK_SECRET")
    try:
        if not application.running:
            await application.initialize()
        logger.info("Setting webhook url=%s secret_set=%s", url, bool(secret))
        await application.bot.set_webhook(url=url, secret_token=secret)
        info = await application.bot.get_webhook_info()
        logger.info("Webhook set: %s", info.to_dict())
        return {"ok": True, "webhook": info.to_dict()}
    except Exception as e:
        logger.exception("Failed to set webhook")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/delete_webhook")
async def delete_webhook():
    try:
        if not application.running:
            await application.initialize()
        logger.info("Deleting webhook")
        await application.bot.delete_webhook(drop_pending_updates=False)
        info = await application.bot.get_webhook_info()
        return {"ok": True, "webhook": info.to_dict()}
    except Exception as e:
        logger.exception("Failed to delete webhook")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/webhook_info")
async def webhook_info():
    try:
        if not application.running:
            await application.initialize()
        info = await application.bot.get_webhook_info()
        return info.to_dict()
    except Exception as e:
        logger.exception("Failed to get webhook info")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def root():
    return {"status": "ok", "service": "Logger Bot", "version": "1.0"}
