import os
import json
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from bot.config import GOOGLE_CREDENTIALS, GOOGLE_SHEET_ID
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def get_sheet():
    sheets_service = build('sheets', 'v4', credentials=GOOGLE_CREDENTIALS)
    return sheets_service.spreadsheets().values(), GOOGLE_SHEET_ID

def log_task(uid, user, message, media_url):
    sheet, sid = get_sheet()
    now = datetime.utcnow().isoformat()
    row = [[now, uid, user, user, message, media_url, "New", "", "", ""]]
    logger.info(f"Logging task to sheet: UID={uid}, User={user}")
    sheet.append(spreadsheetId=sid, range="Sheet1", valueInputOption="RAW", body={"values": row}).execute()

def get_tasks():
    sheet, sid = get_sheet()
    try:
        result = sheet.get(spreadsheetId=sid, range="Sheet1").execute()
        logger.info(f"Fetched {len(result.get('values', [])) - 1} tasks from sheet.")
        return result.get("values", [])[1:]  # skip headers
    except Exception as e:
        logger.exception("Failed to retrieve tasks from Google Sheet")
        return []


def update_status(uid, status, updated_by):
    sheet, sid = get_sheet()
    values = sheet.get(spreadsheetId=sid, range="Sheet1").execute().get("values", [])
    for i, row in enumerate(values):
        if len(row) > 1 and row[1] == uid:
            logger.info(f"Updating status for UID={uid} to '{status}' by {updated_by}")
            sheet.update(spreadsheetId=sid, range=f"G{i+1}", valueInputOption="RAW", body={"values": [[status]]}).execute()
            sheet.update(spreadsheetId=sid, range=f"H{i+1}", valueInputOption="RAW", body={"values": [[updated_by]]}).execute()
            sheet.update(spreadsheetId=sid, range=f"I{i+1}", valueInputOption="RAW", body={"values": [[datetime.utcnow().isoformat()]]}).execute()
            break
