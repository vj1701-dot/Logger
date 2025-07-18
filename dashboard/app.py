from flask import Flask, render_template, request
import os

app = Flask(__name__, template_folder="templates")

@app.route("/dashboard")
def dashboard():
    password = request.args.get("password")
    if password != os.getenv("DASHBOARD_PASS"):
        return "Unauthorized", 401
    return render_template("dashboard.html", tasks=[])
