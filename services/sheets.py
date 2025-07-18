import os
import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SHEET_ID = os.getenv("SPREADSHEET_ID")
SHEET_NAME = "Sheet1"

def now():
    return datetime.datetime.now().strftime("%b %d, %Y %I:%M %p")

def get_service():
    credentials = service_account.Credentials.from_service_account_file(
        "credentials.json", scopes=SCOPES)
    return build("sheets", "v4", credentials=credentials)

def append_to_sheet(first, last, username, message, media_url):
    service = get_service()
    row = [[now(), username, f"{first} {last}", message, media_url, "New", "", ""]]
    service.spreadsheets().values().append(
        spreadsheetId=SHEET_ID,
        range=f"{SHEET_NAME}!A1",
        valueInputOption="RAW",
        body={"values": row}
    ).execute()

def update_task_status(username, message, status, updated_by):
    service = get_service()
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SHEET_ID, range=SHEET_NAME).execute()
    rows = result.get("values", [])

    for i, row in enumerate(rows):
        if len(row) >= 4 and row[1] == username and row[3] == message:
            row_index = i + 1
            sheet.values().update(
                spreadsheetId=SHEET_ID,
                range=f"{SHEET_NAME}!F{row_index}:H{row_index}",
                valueInputOption="RAW",
                body={"values": [[status, updated_by, now()]]}
            ).execute()
            return

def fetch_all_tasks():
    service = get_service()
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SHEET_ID, range=SHEET_NAME).execute()
    return result.get("values", [])[1:]