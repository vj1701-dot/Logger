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

# Note: Miniapp feature removed as per requirements

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
    """Root endpoint - serves the dashboard login"""
    from fastapi.responses import HTMLResponse
    
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Maintenance Task System</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100 min-h-screen flex items-center justify-center">
        <div class="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
            <h1 class="text-2xl font-bold text-center mb-6">Admin Login</h1>
            <form id="loginForm" class="space-y-4">
                <div>
                    <label for="username" class="block text-sm font-medium text-gray-700">Username</label>
                    <input type="text" id="username" class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                </div>
                <div>
                    <label for="password" class="block text-sm font-medium text-gray-700">Password</label>
                    <input type="password" id="password" class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                </div>
                <button type="submit" class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                    Sign In
                </button>
            </form>
            <div id="error" class="mt-4 text-red-600 text-center hidden"></div>
        </div>

        <script>
            document.getElementById('loginForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;
                const errorDiv = document.getElementById('error');
                
                const credentials = btoa(username + ':' + password);
                
                try {
                    const response = await fetch('/api/tasks', {
                        headers: {
                            'Authorization': 'Basic ' + credentials
                        }
                    });
                    
                    if (response.ok) {
                        // Store credentials and redirect to dashboard
                        localStorage.setItem('auth', credentials);
                        window.location.href = '/dashboard';
                    } else {
                        errorDiv.textContent = 'Invalid credentials';
                        errorDiv.classList.remove('hidden');
                    }
                } catch (error) {
                    errorDiv.textContent = 'Login failed';
                    errorDiv.classList.remove('hidden');
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/dashboard")
async def dashboard():
    """Dashboard endpoint"""
    from fastapi.responses import HTMLResponse
    
    # Read the new dashboard HTML file
    try:
        import os
        dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard_new.html")
        with open(dashboard_path, "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        # Fallback to simple dashboard
        return HTMLResponse(content="<h1>Dashboard not found</h1>")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)