import os
import json
from bot.google_utils import get_secret, get_service_account_credentials

PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
TELEGRAM_BOT_TOKEN = get_secret("TELEGRAM_BOT_TOKEN", PROJECT_ID)
GOOGLE_DRIVE_FOLDER_ID = get_secret("GOOGLE_DRIVE_FOLDER_ID", PROJECT_ID)
GOOGLE_SHEET_ID = get_secret("GOOGLE_SHEET_ID", PROJECT_ID)
ADMIN_IDS = get_secret("ADMIN_IDS", PROJECT_ID).split(",")
DASHBOARD_PASS = get_secret("DASHBOARD_PASS", PROJECT_ID)
DASHBOARD_URL = os.environ.get("DASHBOARD_URL", "/dashboard")

# Service account JSON is stored as a secret
service_account_json = get_secret("GOOGLE_SERVICE_ACCOUNT_JSON", PROJECT_ID)
service_account_info = json.loads(service_account_json)
GOOGLE_CREDENTIALS = get_service_account_credentials(service_account_info) 