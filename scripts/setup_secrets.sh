#!/bin/bash
# Helper script to set up Google Secret Manager and grant access to Cloud Run

# Set this to your GCP project ID
PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable secretmanager.googleapis.com run.googleapis.com cloudbuild.googleapis.com

# Create secrets
declare -A secrets=(
  ["TELEGRAM_BOT_TOKEN"]="your-telegram-bot-token"
  ["GOOGLE_SHEET_ID"]="your-google-sheet-id"
  ["GOOGLE_DRIVE_FOLDER_ID"]="your-drive-folder-id"
  ["ADMIN_IDS"]="12345678,98765432"
  ["DASHBOARD_USER"]="admin"
  ["DASHBOARD_PASS"]="password"
  ["GCP_PROJECT_ID"]=$PROJECT_ID
  ["WEBHOOK_URL"]="https://your-bot-service-name.a.run.app/webhook"
)

for name in "${!secrets[@]}"; do
  echo "Creating secret: $name"
  echo -n "${secrets[$name]}" | gcloud secrets create "$name" --data-file=- --quiet ||   echo -n "${secrets[$name]}" | gcloud secrets versions add "$name" --data-file=- --quiet
done

# Upload JSON service account (manually place it before running)
if [ -f "./secrets/service_account.json" ]; then
  echo "Uploading GOOGLE_SERVICE_ACCOUNT_JSON"
  gcloud secrets create GOOGLE_SERVICE_ACCOUNT_JSON --data-file=./secrets/service_account.json --quiet ||   gcloud secrets versions add GOOGLE_SERVICE_ACCOUNT_JSON --data-file=./secrets/service_account.json --quiet
else
  echo "⚠️  Missing service_account.json. Place it at ./secrets/service_account.json before running."
fi

# Grant access to Cloud Run default service account
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
SA="$PROJECT_NUMBER-compute@developer.gserviceaccount.com"

for secret in $(gcloud secrets list --format="value(name)"); do
  echo "Granting access to $SA for secret $secret"
  gcloud secrets add-iam-policy-binding "$secret"     --member="serviceAccount:$SA"     --role="roles/secretmanager.secretAccessor" --quiet
done

echo "✅ Secrets created and permissions granted."
