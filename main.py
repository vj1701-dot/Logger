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

# Mount miniapp static files
app.mount("/miniapp", StaticFiles(directory="miniapp/dist", html=True), name="miniapp")

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
    
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Task Dashboard</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-50">
        <div class="min-h-screen">
            <nav class="bg-white shadow-sm border-b">
                <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div class="flex justify-between h-16">
                        <div class="flex items-center">
                            <h1 class="text-xl font-semibold">Task Dashboard</h1>
                        </div>
                        <div class="flex items-center space-x-4">
                            <button onclick="showAdminPanel()" class="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700">
                                Admin Panel
                            </button>
                            <button onclick="logout()" class="text-gray-500 hover:text-gray-700">Logout</button>
                        </div>
                    </div>
                </div>
            </nav>

            <div class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
                <div class="mb-6">
                    <button onclick="loadTasks()" class="bg-green-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-green-700">
                        Refresh Tasks
                    </button>
                </div>

                <div id="adminPanel" class="hidden mb-6 bg-white p-6 rounded-lg shadow">
                    <h2 class="text-lg font-semibold mb-4">Admin Management</h2>
                    <div class="space-y-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Make User Admin</label>
                            <div class="flex space-x-2">
                                <input type="number" id="adminTelegramId" placeholder="Telegram ID" class="flex-1 px-3 py-2 border border-gray-300 rounded-md">
                                <button onclick="promoteToAdmin()" class="bg-red-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-red-700">
                                    Promote to Admin
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <div id="taskList" class="bg-white shadow overflow-hidden sm:rounded-md">
                    <div class="p-4 text-center text-gray-500">Loading tasks...</div>
                </div>
            </div>
        </div>

        <script>
            const auth = localStorage.getItem('auth');
            if (!auth) {
                window.location.href = '/';
            }

            async function apiRequest(url, options = {}) {
                const response = await fetch(url, {
                    ...options,
                    headers: {
                        'Authorization': 'Basic ' + auth,
                        'Content-Type': 'application/json',
                        ...options.headers
                    }
                });
                if (!response.ok && response.status === 401) {
                    localStorage.removeItem('auth');
                    window.location.href = '/';
                }
                return response;
            }

            async function loadTasks() {
                try {
                    const response = await apiRequest('/api/tasks');
                    const data = await response.json();
                    displayTasks(data.tasks);
                } catch (error) {
                    console.error('Error loading tasks:', error);
                }
            }

            function displayTasks(tasks) {
                const taskList = document.getElementById('taskList');
                if (tasks.length === 0) {
                    taskList.innerHTML = '<div class="p-4 text-center text-gray-500">No tasks found</div>';
                    return;
                }

                const html = tasks.map(task => `
                    <div class="border-b border-gray-200 p-4">
                        <div class="flex items-center justify-between">
                            <div class="flex-1">
                                <h3 class="text-sm font-medium text-gray-900">${task.title}</h3>
                                <p class="text-sm text-gray-500">${task.uid} - ${task.status}</p>
                                <p class="text-sm text-gray-600 mt-1">${task.description}</p>
                            </div>
                            <div class="ml-4">
                                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(task.status)}">
                                    ${task.status.replace('_', ' ')}
                                </span>
                            </div>
                        </div>
                    </div>
                `).join('');
                taskList.innerHTML = html;
            }

            function getStatusColor(status) {
                switch (status) {
                    case 'new': return 'bg-blue-100 text-blue-800';
                    case 'in_progress': return 'bg-yellow-100 text-yellow-800';
                    case 'done': return 'bg-green-100 text-green-800';
                    case 'canceled': return 'bg-red-100 text-red-800';
                    default: return 'bg-gray-100 text-gray-800';
                }
            }

            function showAdminPanel() {
                const panel = document.getElementById('adminPanel');
                panel.classList.toggle('hidden');
            }

            async function promoteToAdmin() {
                const telegramId = document.getElementById('adminTelegramId').value;
                if (!telegramId) {
                    alert('Please enter a Telegram ID');
                    return;
                }

                try {
                    const response = await apiRequest('/api/admin/promote', {
                        method: 'POST',
                        body: JSON.stringify({ telegram_id: parseInt(telegramId) })
                    });

                    if (response.ok) {
                        alert('User promoted to admin successfully');
                        document.getElementById('adminTelegramId').value = '';
                    } else {
                        const error = await response.json();
                        alert('Failed to promote user: ' + error.detail);
                    }
                } catch (error) {
                    alert('Error promoting user');
                }
            }

            function logout() {
                localStorage.removeItem('auth');
                window.location.href = '/';
            }

            // Load tasks on page load
            loadTasks();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)