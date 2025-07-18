from flask import Flask, request, render_template
import os
from bot.sheets_utils import get_tasks

flask_app = Flask(__name__, template_folder="templates")

@flask_app.route("/")
def index():
    password = request.args.get("password")
    if password != os.getenv("DASHBOARD_PASS"):
        return "Unauthorized", 401
    tasks = get_tasks()
    return render_template("dashboard.html", tasks=tasks)
