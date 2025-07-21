import os
import json
import logging
from bot.google_utils import get_secret, get_service_account_credentials

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
if not PROJECT_ID:
    raise EnvironmentError("GCP_PROJECT_ID environment variable is not set.")

try:
    TELEGRAM_BOT_TOKEN = get_secret("TELEGRAM_BOT_TOKEN", PROJECT_ID)
    GOOGLE_DRIVE_FOLDER_ID = get_secret("GOOGLE_DRIVE_FOLDER_ID", PROJECT_ID)
    GOOGLE_SHEET_ID = get_secret("GOOGLE_SHEET_ID", PROJECT_ID)
    ADMIN_IDS = [id.strip() for id in get_secret("ADMIN_IDS", PROJECT_ID).split(",")]
    DASHBOARD_PASS = get_secret("DASHBOARD_PASS", PROJECT_ID)
    service_account_json = get_secret("GOOGLE_SERVICE_ACCOUNT_JSON", PROJECT_ID)
    service_account_info = json.loads(service_account_json)
    GOOGLE_CREDENTIALS = get_service_account_credentials(service_account_info)
except Exception as e:
    logger.exception("Failed to load secrets or credentials")
    raise

DASHBOARD_URL = os.environ.get("DASHBOARD_URL", "/dashboard")