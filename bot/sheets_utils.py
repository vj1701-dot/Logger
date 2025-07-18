import os
import json
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

def get_sheet():
    creds = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
    credentials = service_account.Credentials.from_service_account_info(creds, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    sheet = build("sheets", "v4", credentials=credentials).spreadsheets().values()
    return sheet, os.environ["GOOGLE_SHEET_ID"]

def log_task(uid, user, message, media_url):
    sheet, sid = get_sheet()
    now = datetime.utcnow().isoformat()
    row = [[now, uid, user, user, message, media_url, "New", "", "", ""]]
    sheet.append(spreadsheetId=sid, range="Sheet1", valueInputOption="RAW", body={"values": row}).execute()

def update_status(uid, status, updated_by):
    sheet, sid = get_sheet()
    values = sheet.get(spreadsheetId=sid, range="Sheet1").execute().get("values", [])
    for i, row in enumerate(values):
        if len(row) > 1 and row[1] == uid:
            sheet.update(spreadsheetId=sid, range=f"G{i+1}", valueInputOption="RAW", body={"values": [[status]]}).execute()
            sheet.update(spreadsheetId=sid, range=f"H{i+1}", valueInputOption="RAW", body={"values": [[updated_by]]}).execute()
            sheet.update(spreadsheetId=sid, range=f"I{i+1}", valueInputOption="RAW", body={"values": [[datetime.utcnow().isoformat()]]}).execute()
            break

def assign_task(uid, assignee, updated_by):
    sheet, sid = get_sheet()
    values = sheet.get(spreadsheetId=sid, range="Sheet1").execute().get("values", [])
    for i, row in enumerate(values):
        if len(row) > 1 and row[1] == uid:
            sheet.update(spreadsheetId=sid, range=f"J{i+1}", valueInputOption="RAW", body={"values": [[assignee]]}).execute()
            sheet.update(spreadsheetId=sid, range=f"H{i+1}", valueInputOption="RAW", body={"values": [[updated_by]]}).execute()
            sheet.update(spreadsheetId=sid, range=f"I{i+1}", valueInputOption="RAW", body={"values": [[datetime.utcnow().isoformat()]]}).execute()
            break
