from flask import Flask, render_template, request, Response
import os
from google.oauth2.service_account import Credentials
import gspread
from google.cloud import secretmanager
from datetime import datetime

app = Flask(__name__)

USERNAME = os.environ.get("DASHBOARD_USER", "admin")
PASSWORD = os.environ.get("DASHBOARD_PASS", "password")
PROJECT_ID = os.environ.get("GCP_PROJECT_ID")

def check_auth(user, pwd):
    return user == USERNAME and pwd == PASSWORD

def authenticate():
    return Response("Unauthorized", 401, {"WWW-Authenticate": "Basic realm='Login Required'"})

def access_secret(secret_id):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

def get_sheet():
    creds_json = access_secret("GOOGLE_SERVICE_ACCOUNT_JSON")
    creds_dict = Credentials.from_service_account_info(eval(creds_json), scopes=["https://www.googleapis.com/auth/spreadsheets"])
    client = gspread.authorize(creds_dict)
    sheet_id = access_secret("GOOGLE_SHEET_ID")
    return client.open_by_key(sheet_id).sheet1

@app.route("/")
def dashboard():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()

    sheet = get_sheet()
    records = sheet.get_all_records()

    status_filter = request.args.get("status")
    sort_by = request.args.get("sort", "timestamp")

    data = records
    if status_filter:
        data = [row for row in data if row.get("Status") == status_filter]
    if sort_by == "status":
        data.sort(key=lambda x: x.get("Status", ""))
    else:
        data.sort(key=lambda x: x.get("Timestamp", ""), reverse=True)

    return render_template("dashboard.html", tasks=data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)


@app.route("/my")
def my_tasks():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()

    sheet = get_sheet()
    records = sheet.get_all_records()

    username = request.args.get("user")
    if not username:
        return Response("Missing ?user=username in URL", 400)

    filtered = [
        row for row in records
        if row.get("Submitted By") == username or row.get("Assigned To") == username
    ]

    sort_by = request.args.get("sort", "timestamp")
    if sort_by == "status":
        filtered.sort(key=lambda x: x.get("Status", ""))
    else:
        filtered.sort(key=lambda x: x.get("Timestamp", ""), reverse=True)

    return render_template("dashboard.html", tasks=filtered)
