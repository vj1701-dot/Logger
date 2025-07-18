import os
import io
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

async def upload_to_drive(file, filename):
    creds = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
    credentials = service_account.Credentials.from_service_account_info(creds, scopes=["https://www.googleapis.com/auth/drive"])
    drive = build("drive", "v3", credentials=credentials)

    bio = io.BytesIO()
    await file.download_to_memory(out=bio)
    media = MediaIoBaseUpload(bio, mimetype=file.mime_type)

    metadata = {"name": filename, "parents": [os.environ["GOOGLE_DRIVE_FOLDER_ID"]]}
    uploaded = drive.files().create(body=metadata, media_body=media, fields="id").execute()

    drive.permissions().create(fileId=uploaded["id"], body={"role": "reader", "type": "anyone"}).execute()

    return f"https://drive.google.com/file/d/{uploaded['id']}/view"
