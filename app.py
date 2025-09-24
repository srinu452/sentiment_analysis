import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
from models import init_db, create_user, find_user, verify_password

# ML: Hugging Face pipeline
from transformers import pipeline

load_dotenv()  # loads .env if present

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-me")

# Ensure DB exists
init_db()

# Lazy-load the sentiment pipeline (so boot is fast and model loads on first use)
_sentiment = None
def get_classifier():
    global _sentiment
    if _sentiment is None:
        _sentiment = pipeline("sentiment-analysis")  # distilbert sst-2
    return _sentiment

def login_required(view):
    def wrapper(*args, **kwargs):
        if "user_email" not in session:
            flash("Please log in to access that page.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    wrapper.__name__ = view.__name__
    return wrapper

@app.route("/")
def home():
    if "user_email" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("about"))

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        user = find_user(email)
        if not user or not verify_password(user["password_hash"], password):
            flash("Invalid email or password", "danger")
            return render_template("login.html", email=email)
        session["user_email"] = user["email"]
        flash("Welcome back!", "success")
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        confirm  = request.form.get("confirm") or ""
        if not email or not password:
            flash("Email and password are required.", "warning")
            return render_template("register.html", email=email)
        if password != confirm:
            flash("Passwords do not match.", "warning")
            return render_template("register.html", email=email)
        try:
            create_user(email, password)
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            # likely unique constraint
            flash(f"Could not register: {e}", "danger")
            return render_template("register.html", email=email)
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("login"))

@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    result = None
    text = ""
    if request.method == "POST":
        text = (request.form.get("text") or "").strip()
        # inside dashboard() where you set `result`
        if text:
            clf = get_classifier()
            out = clf(text)[0]  # {'label': 'POSITIVE'|'NEGATIVE', 'score': ...}
            lbl = out["label"].lower()
            badge = "pos" if lbl == "positive" else "neg" if lbl == "negative" else "neu"
            result = {"label": out["label"], "score": float(out["score"]), "badge": badge}

        else:
            flash("Please enter some text.", "warning")
    return render_template("dashboard.html", result=result, text=text)

if __name__ == "__main__":
    # dev server
    app.run(host="0.0.0.0", port=5000, debug=True)
