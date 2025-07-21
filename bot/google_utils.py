import os
import json
import logging
from google.cloud import secretmanager
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from typing import Dict, Any

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# --- Secret Manager ---
def get_secret(secret_id: str, project_id: str) -> str:
    """
    Fetch a secret value from Google Cloud Secret Manager.
    """
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        secret = response.payload.data.decode("UTF-8")
        logger.info(f"Retrieved secret: {secret_id}")
        return secret
    except Exception as e:
        logger.exception(f"Failed to fetch secret: {secret_id}")
        return ""

# --- Google Auth ---
def get_service_account_credentials(service_account_info: Dict[str, Any]):
    """
    Return service account credentials from JSON info.
    """
    credentials = service_account.Credentials.from_service_account_info(
        service_account_info,
        scopes=[
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/spreadsheets"
        ]
    )
    return credentials

# --- Google Drive ---
def upload_file_to_drive(file_path: str, filename: str, folder_id: str, credentials) -> str:
    """
    Upload a file to Google Drive and return the shareable link.
    """
    try:
        drive_service = build('drive', 'v3', credentials=credentials)
        file_metadata = {'name': filename, 'parents': [folder_id]}
        media = MediaFileUpload(file_path, resumable=True)
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        file_id = file.get('id')
        drive_service.permissions().create(
            fileId=file_id,
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()
        shareable_link = f"https://drive.google.com/file/d/{file_id}/view"
        logger.info(f"File uploaded to Drive: {shareable_link}")
        return shareable_link
    except Exception as e:
        logger.exception("Failed to upload file to Google Drive")
        return ""

# --- Google Sheets ---
def append_row_to_sheet(sheet_id: str, row: list, credentials):
    """
    Append a row to the Google Sheet.
    """
    try:
        sheets_service = build('sheets', 'v4', credentials=credentials)
        sheets_service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range='A1',
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body={'values': [row]}
        ).execute()
        logger.info(f"Appended row to sheet {sheet_id}")
    except Exception as e:
        logger.exception("Failed to append row to Google Sheet")

def update_row_in_sheet(sheet_id: str, row_index: int, row: list, credentials):
    """
    Update a specific row in the Google Sheet (1-based index).
    """
    try:
        sheets_service = build('sheets', 'v4', credentials=credentials)
        range_ = f'A{row_index}:J{row_index}'  # Assuming 10 columns (A-J)
        sheets_service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=range_,
            valueInputOption='USER_ENTERED',
            body={'values': [row]}
        ).execute()
        logger.info(f"Updated row {row_index} in sheet {sheet_id}")
    except Exception as e:
        logger.exception("Failed to update row in Google Sheet")