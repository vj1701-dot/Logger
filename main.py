import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from telegram import Update
from telegram.ext import Application

from src.bot.handlers import setup_bot_handlers
from src.api.routes import router as api_router
from src.auth.middleware import jwt_middleware
from src.config import settings
from src.storage.gcs_client import GCSClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global bot application
bot_app = None
gcs_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global bot_app, gcs_client
    
    # Initialize GCS client
    gcs_client = GCSClient(settings.BUCKET_NAME)
    app.state.gcs_client = gcs_client
    
    # Initialize Telegram bot
    bot_app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    setup_bot_handlers(bot_app, gcs_client)
    
    try:
        await bot_app.initialize()
        logger.info("Telegram bot initialized successfully")
    except Exception as e:
        logger.exception("Failed to initialize Telegram bot")
        raise
    
    yield
    
    # Cleanup
    if bot_app:
        await bot_app.shutdown()
    logger.info("Application shutdown complete")

app = FastAPI(
    title="Maintenance Task System",
    description="Telegram-first task management with GCS storage",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT middleware for protected routes
app.middleware("http")(jwt_middleware)

# Mount static files for dashboard
app.mount("/static", StaticFiles(directory="dashboard/static"), name="static")

# API routes
app.include_router(api_router, prefix="/api")

@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    """Handle Telegram webhook updates"""
    try:
        body = await request.json()
        logger.info(f"Received webhook: {body.get('update_id', 'unknown')}")
        
        update = Update.de_json(body, bot_app.bot)
        if not update:
            raise HTTPException(status_code=400, detail="Invalid update")
            
        await bot_app.process_update(update)
        return {"ok": True}
        
    except Exception as e:
        logger.exception("Webhook processing failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "maintenance-task-system",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint - serves the dashboard"""
    return {"message": "Maintenance Task System API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)