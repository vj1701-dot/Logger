import os
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from google.cloud import secretmanager
import json

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def access_secret(secret_id):
    client = secretmanager.SecretManagerServiceClient()
    project_id = os.environ["GCP_PROJECT_ID"]
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

def get_sheet():
    creds_json = access_secret("GOOGLE_SERVICE_ACCOUNT_JSON")
    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet_id = access_secret("GOOGLE_SHEET_ID")
    return client.open_by_key(sheet_id).sheet1

def log_task_to_sheet(uid, username, submitted_by, message, media_url):
    sheet = get_sheet()
    now = datetime.utcnow().isoformat()
    row = [
        now,         # Timestamp
        uid,
        username,
        submitted_by,
        message,
        media_url,
        "New",       # Status
        "",          # Updated By
        "",          # Updated Time
        ""           # Assigned To
    ]
    sheet.append_row(row)


def update_task_status(uid, new_status, updated_by):
    sheet = get_sheet()
    now = datetime.utcnow().isoformat()
    records = sheet.get_all_records()
    for i, row in enumerate(records, start=2):
        if row["UID"] == uid:
            sheet.update(f"G{i}", new_status)
            sheet.update(f"H{i}", updated_by)
            sheet.update(f"I{i}", now)
            break

def update_task_assignee(uid, assigned_to, updated_by):
    sheet = get_sheet()
    now = datetime.utcnow().isoformat()
    records = sheet.get_all_records()
    for i, row in enumerate(records, start=2):
        if row["UID"] == uid:
            sheet.update(f"J{i}", assigned_to)
            sheet.update(f"H{i}", updated_by)
            sheet.update(f"I{i}", now)
            break
