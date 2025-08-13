import os
import json
import logging
from bot.google_utils import get_service_account_credentials

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
if not PROJECT_ID:
    raise EnvironmentError("GCP_PROJECT_ID environment variable is not set.")

# Read all secrets from environment variables
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
GOOGLE_DRIVE_FOLDER_ID = os.environ.get("GOOGLE_DRIVE_FOLDER_ID", "")
GOOGLE_SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "")
ADMIN_IDS = os.environ.get("ADMIN_IDS", "").split(",") if os.environ.get("ADMIN_IDS") else []
DASHBOARD_PASS = os.environ.get("DASHBOARD_PASS", "")
DASHBOARD_URL = os.environ.get("DASHBOARD_URL", "/dashboard")

# Service account JSON is provided directly via env var
service_account_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "{}")
service_account_info = json.loads(service_account_json)
GOOGLE_CREDENTIALS = get_service_account_credentials(service_account_info) if service_account_info else None