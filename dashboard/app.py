from flask import Flask, request, render_template, redirect, url_for, session
import os
from bot.sheets_utils import get_tasks
from bot.config import DASHBOARD_PASS

flask_app = Flask(__name__, template_folder="templates")
flask_app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change_this_secret")

@flask_app.route("/", methods=["GET", "POST"])
def index():
    # Password protection
    if request.method == "POST":
        if request.form.get("password") == DASHBOARD_PASS:
            session["authed"] = True
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="Wrong password")
    if not session.get("authed"):
        return render_template("login.html")

    # Filtering
    filter_val = request.args.get("filter", "").lower()
    tasks = get_tasks()
    if filter_val:
        tasks = [
            t for t in tasks
            if filter_val in (t[6] or "").lower() or filter_val in (t[9] or "").lower()
        ]
    return render_template("dashboard.html", tasks=tasks, filter_val=filter_val)

@flask_app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))
