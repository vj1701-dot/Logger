from flask import Flask, request, render_template, redirect, url_for, session
import os
import logging
from bot.sheets_utils import get_tasks
from bot.config import DASHBOARD_PASS
from collections import Counter

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

flask_app = Flask(__name__, template_folder="templates")
flask_app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change_this_secret")

@flask_app.route("/", methods=["GET", "POST"])
def index():
    # Password protection
    if request.method == "POST":
        if request.form.get("password") == DASHBOARD_PASS:
            session["authed"] = True
            logger.info("Dashboard login successful")
            return redirect(url_for("index"))
        else:
            logger.warning("Dashboard login failed")
            return render_template("login.html", error="Incorrect password. Please try again.")
    if not session.get("authed"):
        return render_template("login.html")

    status_filter = request.args.get("status", "").lower()
    assigned_filter = request.args.get("assigned", "").lower()
    try:
        tasks = get_tasks()
    except Exception as e:
        tasks = []
        logger.exception("Error loading tasks from Google Sheets")

    status_counts = Counter(t[6] for t in tasks if len(t) > 6)

    if status_filter:
        tasks = [t for t in tasks if status_filter in (t[6] or "").lower()]
    if assigned_filter:
        tasks = [t for t in tasks if assigned_filter in (t[9] or "").lower()]

    return render_template(
        "dashboard.html",
        tasks=tasks,
        status_filter=status_filter,
        assigned_filter=assigned_filter,
        status_counts=status_counts
    )

@flask_app.route("/logout")
def logout():
    session.clear()
    logger.info("Dashboard logout")
    return redirect(url_for("index"))
