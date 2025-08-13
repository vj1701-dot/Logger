# Unified Telegram Bot + Dashboard (Single Cloud Run Service)

A full-stack Telegram task management bot with integrated Google Sheets and Drive support.

## What it does
- Accepts user-submitted text and media (photo/video/audio)
- Uploads media to Google Drive and logs entries to Google Sheets
- Exposes a unified FastAPI app that mounts a password-protected Flask dashboard at `/dashboard`
- Telegram bot webhook served at `/webhook`
- Admins can manage task statuses and manage who is an admin (via Google Sheets “Admins” tab)

## Architecture
- FastAPI app (entrypoint: `combined_main.py`, ASGI `app`)
- Flask dashboard mounted via WSGIMiddleware at `/dashboard`
- Google APIs via service account credentials loaded from an environment variable
- All secrets provided via environment variables (no Secret Manager dependency)

---

## Required Environment Variables
Set these for Docker and Cloud Run. All are strings unless noted.

- TELEGRAM_BOT_TOKEN: Telegram bot token
- GOOGLE_DRIVE_FOLDER_ID: Google Drive folder ID to store media (e.g. `1L1n3...`)
- GOOGLE_SHEET_ID: Google Sheet ID to log tasks (e.g. `1SPcZ5...`)
- GOOGLE_SERVICE_ACCOUNT_JSON: Entire service account JSON content (copy-paste as a single env var)
- GCP_PROJECT_ID: Your GCP project ID (used in logs/metadata; optional for core functions)
- DASHBOARD_PASS: Password required to access the dashboard login
- FLASK_SECRET_KEY: Random secret string for Flask sessions (generate with `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`)
- DASHBOARD_URL: Optional. Public dashboard URL (e.g. `https://your-run-url/dashboard`) used in bot replies. Defaults to `/dashboard`.

Notes:
- ADMIN_IDS env var is no longer required. Admins are stored in a Google Sheet tab named `Admins`.

---

## Admin Management (Dynamic)
Admins are managed in your Google Sheet, in a tab titled `Admins`:
- Column A: Telegram user IDs (numeric)
- The bot auto-creates the `Admins` tab if missing

Bot commands (only existing admins can run):
- `/admins` → list admins
- `/admin_add <telegram_user_id>` → add an admin
- `/admin_remove <telegram_user_id>` → remove an admin

Tip: Seed the first admin by manually adding your Telegram user ID (from @userinfobot) to the `Admins` tab cell A1.

---

## Docker (Local)
1) Build image:
```bash
docker build -t logger .
```
2) Run container (example):
```bash
docker run -p 8080:8080 \
  -e TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN \
  -e GOOGLE_DRIVE_FOLDER_ID=YOUR_DRIVE_FOLDER_ID \
  -e GOOGLE_SHEET_ID=YOUR_SHEET_ID \
  -e GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}' \
  -e GCP_PROJECT_ID=your-project-id \
  -e DASHBOARD_PASS=your-dashboard-pass \
  -e FLASK_SECRET_KEY=your-flask-secret \
  -e DASHBOARD_URL=http://localhost:8080/dashboard \
  logger
```
Visit:
- Health: http://localhost:8080/
- Dashboard: http://localhost:8080/dashboard (log in with `DASHBOARD_PASS`)

---

## Cloud Run (Console, no terminal)
1) Cloud Run → Create service → “Deploy from source repository” (connect GitHub) or from built image
2) Build type: Dockerfile
3) Service settings:
   - Region: your choice
   - Allow unauthenticated: enabled (if public dashboard)
   - Port: 8080 (default)
4) Environment variables: add all listed above. Paste the entire service account JSON into `GOOGLE_SERVICE_ACCOUNT_JSON`.
5) Deploy. Your service URL will be shown after deploy. Dashboard is at `<service-url>/dashboard`.

Webhook:
- Set your Telegram webhook to `<service-url>/webhook` using Telegram HTTP API.

---

## Features
- Telegram Bot:
  - `/start`, `/dashboard`, `/status <UID>` (admin only)
  - Inline status buttons: 🆕 New, 🕒 In Progress, ✅ Done, 🗑️ Delete
  - `/admins`, `/admin_add <id>`, `/admin_remove <id>`
- Dashboard:
  - Mobile-friendly, password-protected
  - Task cards with status coloring and media links
  - Filter by status or assignee

---

## Development Notes
- Python 3.11, FastAPI + Uvicorn, Flask dashboard mounted at `/dashboard`
- Entrypoint: `uvicorn combined_main:app --host 0.0.0.0 --port 8080`
- Service account must have:
  - Drive: roles/drive.file (and Editor access to the target folder)
  - Sheets: roles/sheets.editor (and Editor access to the spreadsheet)
