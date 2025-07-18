from flask import Flask, render_template, request, Response
import os

app = Flask(__name__)

USERNAME = os.environ.get("DASHBOARD_USER", "admin")
PASSWORD = os.environ.get("DASHBOARD_PASS", "password")

def check_auth(user, pwd):
    return user == USERNAME and pwd == PASSWORD

def authenticate():
    return Response("Unauthorized", 401, {"WWW-Authenticate": "Basic realm='Login Required'"})

@app.route("/")
def dashboard():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()
    # TODO: Fetch data from Google Sheets
    data = []
    return render_template("dashboard.html", tasks=data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
