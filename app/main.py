from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from services.telegram import handle_telegram_update, handle_callback
from services.sheets import fetch_all_tasks
import os

app = FastAPI()

@app.post("/webhook")
async def telegram_webhook(request: Request):
    payload = await request.json()
    if "callback_query" in payload:
        await handle_callback(payload["callback_query"])
    elif "message" in payload:
        await handle_telegram_update(payload)
    return {"ok": True}

@app.get("/api/tasks")
async def api_tasks():
    rows = fetch_all_tasks()
    return JSONResponse(content=rows)

@app.get("/dashboard")
async def dashboard():
    return FileResponse("public/index.html")

@app.get("/app.js")
async def serve_js():
    return FileResponse("public/app.js")