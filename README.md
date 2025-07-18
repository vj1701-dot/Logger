

## 🚀 Deploying to Google Cloud Run

### Enable Required APIs:
```
gcloud services enable run.googleapis.com secretmanager.googleapis.com sheets.googleapis.com drive.googleapis.com
```

### Store Secrets in Google Secret Manager:
```
gcloud secrets create TELEGRAM_BOT_TOKEN --data-file=- <<< "your_telegram_bot_token"
gcloud secrets create GOOGLE_SHEET_ID --data-file=- <<< "your_google_sheet_id"
gcloud secrets create GOOGLE_DRIVE_FOLDER_ID --data-file=- <<< "your_drive_folder_id"
gcloud secrets create DASHBOARD_USER --data-file=- <<< "admin"
gcloud secrets create DASHBOARD_PASS --data-file=- <<< "password"
gcloud secrets create GOOGLE_SERVICE_ACCOUNT_JSON --data-file=path/to/service_account.json
```

### Deploy Bot Service:
```
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/telegram-bot --file Dockerfile.bot
gcloud run deploy telegram-bot \
  --image gcr.io/YOUR_PROJECT_ID/telegram-bot \
  --region us-central1 \
  --platform managed \
  --set-secrets TELEGRAM_BOT_TOKEN=TELEGRAM_BOT_TOKEN:latest,GOOGLE_SHEET_ID=GOOGLE_SHEET_ID:latest,GOOGLE_DRIVE_FOLDER_ID=GOOGLE_DRIVE_FOLDER_ID:latest,GOOGLE_SERVICE_ACCOUNT_JSON=GOOGLE_SERVICE_ACCOUNT_JSON:latest \
  --allow-unauthenticated
```

### Deploy Dashboard Service:
```
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/telegram-dashboard --file Dockerfile.dashboard
gcloud run deploy telegram-dashboard \
  --image gcr.io/YOUR_PROJECT_ID/telegram-dashboard \
  --region us-central1 \
  --platform managed \
  --set-secrets DASHBOARD_USER=DASHBOARD_USER:latest,DASHBOARD_PASS=DASHBOARD_PASS:latest,GOOGLE_SHEET_ID=GOOGLE_SHEET_ID:latest,GOOGLE_SERVICE_ACCOUNT_JSON=GOOGLE_SERVICE_ACCOUNT_JSON:latest \
  --allow-unauthenticated
```
