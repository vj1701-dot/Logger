# Unified Telegram Bot + Dashboard (Single Cloud Run Service)

A full-stack Telegram task management bot with integrated Google Sheets and Drive support.

## Deployment

### 🚀 Prerequisites
- Enable these GCP APIs: Cloud Run, Secret Manager, Google Sheets API, Google Drive API
- Store secrets in Google Secret Manager:
  - TELEGRAM_BOT_TOKEN
  - GOOGLE_SHEET_ID
  - GOOGLE_DRIVE_FOLDER_ID
  - GOOGLE_SERVICE_ACCOUNT_JSON (entire JSON content)
  - DASHBOARD_PASS
  - ADMIN_IDS (comma-separated Telegram user IDs)
  - DASHBOARD_URL (optional)

### 🐳 Deploy via Cloud Run
- Clone the repo and connect to Google Cloud Build
- Ensure Dockerfile and .dockerignore are present
- Set the entrypoint to: `uvicorn combined_main:app --host 0.0.0.0 --port 8080`

## Usage

- Bot receives messages at `/webhook`
- Dashboard is served at `/dashboard?password=YOUR_PASSWORD`

### Telegram Bot Features
- Anyone can send messages with text, photo, video, or audio
- Tasks get logged to Google Sheets with UID, status, media URL, timestamps
- Admins can update tasks using:
  - `/status UID` → inline buttons for ✅ Done, 🕒 In Progress, 🗑️ Delete, 🆕 New
  - `/assign UID Name` to assign tasks

### Dashboard Features
- Mobile-friendly, password-protected
- View task cards with media previews
- Filter by status or assignee
- "My Tasks" filter by Telegram handle
- Inline status update buttons
- Real-time Sheets + Drive sync

## Dev Notes

- Python 3.11, Uvicorn, FastAPI + Flask combo
- Cloud Run expects port 8080 and entrypoint must mount `app`
- Combined app lives in `combined_main.py`
