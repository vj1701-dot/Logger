# Telegram Task Logger Bot with Dashboard

This project is a full-stack Telegram bot + web dashboard that allows users to submit tasks with media and messages. Admins can view, assign, and update tasks via the dashboard or Telegram inline buttons.

## 🧩 Features

- Telegram bot with support for text, photo, video, audio
- Logs tasks to Google Sheets
- Uploads media to Google Drive
- Dashboard with filtering, sorting, and live updates
- Inline status controls for Admins
- Secret Manager support for all keys

## 🛠 Setup

1. Enable these APIs in Google Cloud:
   - Secret Manager
   - Cloud Run
   - Cloud Build
   - Google Drive
   - Google Sheets

2. Add secrets to Secret Manager:
   - TELEGRAM_TOKEN
   - GOOGLE_DRIVE_FOLDER_ID
   - GOOGLE_SHEET_ID
   - GOOGLE_SERVICE_ACCOUNT_JSON
   - ADMIN_IDS
   - DASHBOARD_PASS
   - DASHBOARD_URL (optional)

3. Push to GitHub. Set up the following GitHub secrets:
   - GCP_PROJECT
   - GCP_REGION
   - GCP_CREDENTIALS (service account key)

4. The GitHub Actions workflow auto-deploys both:
   - `/webhook` endpoint for bot
   - `/dashboard?password=...` view for admins

## 📁 Structure

- `bot/`: Telegram logic + webhook
- `dashboard/`: Web dashboard with password auth
- `Dockerfile.bot`: Deploys FastAPI bot
- `Dockerfile.dashboard`: Deploys Flask dashboard
