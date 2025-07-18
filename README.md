# Telegram Task Logger Bot

This bot lets users log tasks via Telegram with optional media. Tasks are saved to Google Sheets and media to Google Drive. A web dashboard allows admins to view, filter, and update task statuses.

## 🔧 Features

- Telegram bot with media + message handling
- Google Drive uploads
- Google Sheet task logging
- Inline status updates via buttons
- Admin commands `/assign`, `/status`, `/dashboard`
- FastAPI webhook & Flask dashboard

## 🛠 Secrets to add (via Google Secret Manager)

- TELEGRAM_BOT_TOKEN
- GOOGLE_DRIVE_FOLDER_ID
- GOOGLE_SHEET_ID
- GOOGLE_SERVICE_ACCOUNT_JSON
- ADMIN_IDS
- DASHBOARD_PASS
- WEBHOOK_URL (optional)

## 🚀 Deployment (2 options)

### ✅ GitHub Actions

- Requires `GCP_PROJECT_ID`, `GCP_REGION`, `GCP_CREDENTIALS` secrets in GitHub
- Push to `main` triggers build & deploy

### ✅ Google Cloud Build

See `cloudbuild.yaml` if deploying manually or from Cloud Console

---

Dashboard: `/dashboard?password=your_password`  
Bot webhook: `/webhook`
