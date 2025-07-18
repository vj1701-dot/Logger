from flask import Flask, render_template, request
import logging
import os

app = Flask(__name__, template_folder="templates")

logging.basicConfig(level=logging.INFO)

@app.route("/dashboard")
def dashboard():
    password = request.args.get("password")
    if password != os.getenv("DASHBOARD_PASS"):
        return "Unauthorized", 401
    return render_template("dashboard.html", tasks=[])


@app.route("/")
def health():
    return {"status": "ok"}
