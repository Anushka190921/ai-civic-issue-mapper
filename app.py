# ============================================================
# AI Civic Issue Mapper - Main Application File
# Backend: Python Flask | Database: MySQL
# ============================================================

from flask import Flask, request, render_template, redirect, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import os
import time
import socket
socket.getfqdn = lambda name="": "localhost"
from dotenv import load_dotenv
from flask_dance.contrib.google import make_google_blueprint, google
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
import requests

# Load environment variables from .env file
load_dotenv()

# Allow OAuth over HTTP for local development (remove in production)
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# Initialize Flask app
app = Flask(__name__)

# ---------------- RATE LIMITER ----------------
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)
app.secret_key = os.getenv("SECRET_KEY")


# ---------------- EMAIL CONFIGURATION ----------------
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_USERNAME")

mail = Mail(app)
serializer = URLSafeTimedSerializer(app.secret_key)

# Configure Google OAuth blueprint
google_bp = make_google_blueprint(
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    redirect_to="google_login",
    scope=[
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
        "openid"
    ]
)
# Register Google login blueprint with /login prefix
app.register_blueprint(google_bp, url_prefix="/login")

# Folder to store uploaded complaint images
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- DATABASE CONNECTION ----------------
def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", 3306)),
        ssl_disabled=False
    )


# ---------- Health Check (keeps Aiven DB + Render awake) ----------
@app.route("/healthz")
def healthz():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        return "OK", 200
    except Exception as e:
        print("Health check DB error:", e)
        return "DB unreachable", 500

# ---------------- HOME ----------------
@app.route("/")
def home():
    if "user_id" not in session:
        return render_template("landing.html")
    return render_template("form.html")   # or redirect to wherever the form lives


# ---------------- SUBMIT COMPLAINT ----------------
@app.route("/submit", methods=["POST"])
@limiter.limit("10 per hour")
def submit():
    # Only logged in users can submit complaints
    if "user_id" not in session:
        return redirect("/login")

    try:
        # Get form data submitted by citizen
        user_id = session["user_id"]
        issue_type = request.form.get("issue_type")
        description = request.form.get("description")
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")

        # Handle image upload
        image = request.files.get("image")
        image_name = None

        if image and image.filename != "":
            # Create unique filename using timestamp
            filename = str(int(time.time())) + "_" + image.filename
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            # Save image to uploads folder
            image.save(filepath)
            image_name = filename

        # Connect to database and save complaint
        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO civic_issues
            (issue_type, description, latitude, longitude, image, user_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (issue_type, description, latitude, longitude, image_name, user_id))

        db.commit()
        cursor.close()
        db.close()

        return redirect(f"/success/{cursor.lastrowid}")

    except Exception as e:
        return f"Error: {e}"

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def register():
    if request.method == "POST":

        # Get registration form data
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        email = request.form["email"]
        password = request.form["password"]

        # Validate email format
        if "@" not in email or "." not in email:
            return render_template("register.html", error="Invalid email format!")

        # Validate password length
        if len(password) < 8:
            return render_template("register.html", error="Password must be at least 8 characters!")

        # Validate password contains a number
        if not any(char.isdigit() for char in password):
            return render_template("register.html", error="Password must contain at least one number!")

        # Validate password contains a special character
        if not any(char in "!@#$%^&*" for char in password):
            return render_template("register.html", error="Password must contain at least one special character (!@#$%^&*)!")

        # Connect to database
        db = get_db()
        cursor = db.cursor()

        # Hash password before saving for security
        hashed_password = generate_password_hash(password)

        # Save new user to database
        cursor.execute(
            "INSERT INTO users (first_name, last_name, email, password) VALUES (%s, %s, %s, %s)",
            (first_name, last_name, email, hashed_password)
        )

        db.commit()
        cursor.close()
        db.close()

        return redirect("/login")

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    if request.method == "POST":
        # Connect to database and find user by email
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE email=%s", (request.form["email"],))
        user = cursor.fetchone()

        cursor.close()
        db.close()

        # Verify password and create session
        if user and check_password_hash(user["password"], request.form["password"]):
            session["user_id"] = user["id"]
            return redirect("/")

        # Show error if login fails
        return render_template("login.html", error="Invalid email or password!")

    return render_template("login.html")

# ---------------- ADMIN LOGIN ----------------
@app.route("/admin", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def admin():
    if request.method == "POST":
        username = request.form.get("admin_username")
        password = request.form.get("admin_password")

        # Connect to database and find admin by username
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM admins WHERE username=%s", (username,))
        admin = cursor.fetchone()

        cursor.close()
        db.close()

        # Verify admin credentials
        if admin and check_password_hash(admin["password"], password):
            session["admin"] = admin["id"]
            return redirect("/dashboard")

        return render_template("admin_login.html", error="Invalid Credentials")

    return render_template("admin_login.html")


# ---------------- ADMIN DELETE COMPLAINT ----------------
@app.route("/delete_admin_issue/<int:id>")
def delete_admin_issue(id):
    # Only admin can delete any complaint
    if "admin" not in session:
        return redirect("/admin")

    db = get_db()
    cursor = db.cursor()

    # Delete related records first (foreign key constraints)
    cursor.execute("DELETE FROM notifications WHERE issue_id=%s", (id,))
    cursor.execute("DELETE FROM feedback WHERE issue_id=%s", (id,))
    cursor.execute("DELETE FROM civic_issues WHERE id=%s", (id,))
    db.commit()

    cursor.close()
    db.close()

    return redirect("/dashboard")

# ---------------- MY ISSUES ----------------
@app.route("/my_issues")
def my_issues():
    # Only logged in users can view their issues
    if "user_id" not in session:
        return redirect("/login")

    # Fetch all complaints submitted by logged in user
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM civic_issues WHERE user_id=%s", (session["user_id"],))
    issues = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("my_issues.html", issues=issues)


# ---------------- ADMIN DASHBOARD ---------------
@app.route("/view_map")
def view_map():
    return render_template("view_map.html")

   # if "admin" not in session:
       # return redirect("/admin")

    
@app.route("/view_map/<int:id>")
def view_map_single(id):

    if "admin" not in session:
        return redirect("/admin")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT latitude, longitude FROM civic_issues WHERE id=%s",
        (id,)
    )

    complaint = cursor.fetchone()

    cursor.close()
    db.close()

    if complaint is None:
        return "Complaint not found"

    return render_template(
        "view_map.html",
        lat=complaint["latitude"],
        lng=complaint["longitude"]
    )
@app.route("/dashboard")
def dashboard():
    # Only admin can access dashboard
    if "admin" not in session:
        return redirect("/admin")
    
    search = request.args.get("search", "").strip()

    # Fetch all complaints with user details
    db = get_db()
    cursor = db.cursor(dictionary=True)
    if search:
       cursor.execute(""" 
         SELECT civic_issues.*, users.first_name, users.email
         FROM civic_issues
         JOIN users ON civic_issues.user_id = users.id
         WHERE civic_issues.issue_type LIKE %s
            OR CAST(civic_issues.id AS CHAR) LIKE %s
            OR civic_issues.description LIKE %s
        ORDER BY civic_issues.id DESC
        """, (f"%{search}%", f"%{search}%", f"%{search}%"))
    else:
        cursor.execute("""
           SELECT civic_issues.*, users.first_name, users.email
           FROM civic_issues
           JOIN users ON civic_issues.user_id = users.id
            ORDER BY civic_issues.id DESC
        """)
    
    complaints = cursor.fetchall()

    # Count total complaints
    cursor.execute("SELECT COUNT(*) AS count FROM civic_issues")
    total = cursor.fetchone()["count"]

    # Count pending complaints
    cursor.execute("SELECT COUNT(*) AS count FROM civic_issues WHERE status='Pending'")
    pending = cursor.fetchone()["count"]

    # Count in-progress complaints
    cursor.execute("SELECT COUNT(*) AS count FROM civic_issues WHERE status='In Progress'")
    in_progress = cursor.fetchone()["count"]

    # Count resolved complaints
    cursor.execute("SELECT COUNT(*) AS count FROM civic_issues WHERE status='Resolved'")
    resolved = cursor.fetchone()["count"]

    cursor.close()
    db.close()

    stats = {
        "total": total,
        "pending": pending,
        "in_progress": in_progress,
        "resolved": resolved
    }

    return render_template(
    "admin.html",
    complaints=complaints,
    stats=stats
)

# ---------------- DELETE COMPLAINT ----------------
@app.route("/delete_my_issue/<int:id>")
def delete_my_issue(id):
    # Only logged in users can delete their own complaints
    if "user_id" not in session:
        return redirect("/login")

    db = get_db()
    cursor = db.cursor()

    # Check complaint belongs to logged in user before deleting
    cursor.execute("SELECT * FROM civic_issues WHERE id=%s AND user_id=%s", (id, session["user_id"]))
    issue = cursor.fetchone()

    if issue:
        # Delete related records first (foreign key constraints)
        cursor.execute("DELETE FROM notifications WHERE issue_id=%s", (id,))
        cursor.execute("DELETE FROM feedback WHERE issue_id=%s", (id,))
        cursor.execute("DELETE FROM civic_issues WHERE id=%s", (id,))
        db.commit()

    cursor.close()
    db.close()

    return redirect("/my_issues")

# ---------------- UPDATE COMPLAINT STATUS ----------------
@app.route("/update_status/<int:id>", methods=["POST"])
def update_status(id):
    # Only admin can update complaint status
    if "admin" not in session:
        return redirect("/admin")

    # Get new status from form
    new_status = request.form["status"]

    # Handle resolution proof image (only relevant when marking Resolved)
    resolution_image_name = None
    resolution_image = request.files.get("resolution_image")

    if resolution_image and resolution_image.filename != "":
        filename = "resolved_" + str(int(time.time())) + "_" + resolution_image.filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        resolution_image.save(filepath)
        resolution_image_name = filename

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Update status, and resolution image only if one was uploaded
    if resolution_image_name:
        cursor.execute(
            "UPDATE civic_issues SET status=%s, resolution_image=%s WHERE id=%s",
            (new_status, resolution_image_name, id)
        )
    else:
        cursor.execute(
            "UPDATE civic_issues SET status=%s WHERE id=%s",
            (new_status, id)
        )

    # Get the complaint's owner so we know who to notify
    cursor.execute("SELECT user_id FROM civic_issues WHERE id=%s", (id,))
    issue = cursor.fetchone()

    if issue:
        message = f"Your complaint #{id} status has been updated to '{new_status}'."
        cursor.execute(
            "INSERT INTO notifications (user_id, issue_id, message) VALUES (%s, %s, %s)",
            (issue["user_id"], id, message)
        )

    db.commit()
    cursor.close()
    db.close()

    return redirect("/dashboard")

# ---------------- VIEW NOTIFICATIONS ----------------
@app.route("/notifications")
def notifications():
    if "user_id" not in session:
        return redirect("/login")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM notifications WHERE user_id=%s ORDER BY created_at DESC",
        (session["user_id"],)
    )
    user_notifications = cursor.fetchall()

    # Mark all as read once viewed
    cursor.execute(
        "UPDATE notifications SET is_read=TRUE WHERE user_id=%s",
        (session["user_id"],)
    )
    db.commit()

    cursor.close()
    db.close()

    return render_template("notifications.html", notifications=user_notifications)


# ---------------- PUBLIC STATUS TRACKER ----------------
@app.route("/track_status", methods=["GET", "POST"])
@limiter.limit("20 per hour")
def track_status():
    complaint = None
    error = None

    if request.method == "POST":
        complaint_id = request.form.get("complaint_id")

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, issue_type, status, department, created_at, resolution_image FROM civic_issues WHERE id=%s",
            (complaint_id,)
        )
        complaint = cursor.fetchone()
        cursor.close()
        db.close()

        if not complaint:
            error = "No complaint found with that ID. Please check and try again."

    return render_template("track_status.html", complaint=complaint, error=error)


# ---------------- ASSIGN DEPARTMENT ----------------
@app.route("/assign_department/<int:id>", methods=["POST"])
def assign_department(id):
    # Only admin can assign department
    if "admin" not in session:
        return redirect("/admin")

    # Get selected department from form
    department = request.form["department"]

    db = get_db()
    cursor = db.cursor()

    # Update department in database
    cursor.execute(
        "UPDATE civic_issues SET department=%s WHERE id=%s",
        (department, id)
    )

    db.commit()
    cursor.close()
    db.close()

    return redirect("/dashboard")


# ---------------- SUBMIT FEEDBACK ----------------
@app.route("/submit_feedback/<int:id>", methods=["POST"])
def submit_feedback(id):
    # Only logged in users can submit feedback
    if "user_id" not in session:
        return redirect("/login")

    rating = request.form.get("rating")
    comment = request.form.get("comment")

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO feedback (issue_id, rating, comment) VALUES (%s, %s, %s)",
        (id, rating, comment)
    )
    db.commit()
    cursor.close()
    db.close()

    return redirect("/my_issues")

# ---------------- GOOGLE LOGIN ----------------
@app.route("/google_login")
def google_login():
    # Redirect to Google if not authorized
    if not google.authorized:
        return redirect("/login/google")

    # Get user info from Google
    resp = google.get("/oauth2/v2/userinfo")
    info = resp.json()

    email = info["email"]
    first_name = info.get("given_name", "")
    last_name = info.get("family_name", "")

    # Connect to database
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Check if user already exists
    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()

    if not user:
        # Register new Google user automatically
        cursor.execute(
            "INSERT INTO users (first_name, last_name, email, password, login_type) VALUES (%s, %s, %s, %s, %s)",
            (first_name, last_name, email, "google_login", "google")
        )
        db.commit()
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

    # Create session for logged in user
    session["user_id"] = user["id"]

    cursor.close()
    db.close()

    return redirect("/")

# ---------------- SUCCESS PAGE ----------------
@app.route("/success/<int:id>")
def success(id):
    # Only logged in users can see success page
    if "user_id" not in session:
        return redirect("/login")
    return render_template("success.html", issue={"id": id})

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    # Clear session and redirect to login
    session.clear()
    return redirect("/login")


# ---------------- SEND EMAIL VIA BREVO API ----------------
def send_reset_email(to_email, reset_link):
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": os.getenv("BREVO_API_KEY"),
        "content-type": "application/json"
    }
    payload = {
        "sender": {"name": "Civic Issue Portal", "email": os.getenv("MAIL_USERNAME")},
        "to": [{"email": to_email}],
        "subject": "Password Reset Request - Civic Issue Portal",
        "htmlContent": f"<p>Click the link below to reset your password:</p><p><a href='{reset_link}'>{reset_link}</a></p><p>This link expires in 30 minutes.</p>"
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.status_code == 201


# ---------------- FORGOT PASSWORD ----------------
@app.route("/forgot_password", methods=["GET", "POST"])
@limiter.limit("5 per hour")
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user:
            token = serializer.dumps(email, salt="password-reset")
            reset_link = f"https://ai-civic-issue-mapper.onrender.com/reset_password/{token}"

            send_reset_email(email, reset_link)

        return render_template("forgot_password.html", message="If that email is registered, a reset link has been sent.")

    return render_template("forgot_password.html")


# ---------------- RESET PASSWORD ----------------
@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        email = serializer.loads(token, salt="password-reset", max_age=1800)
        expired = False
    except Exception:
        expired = True
        email = None

    if request.method == "POST" and not expired:
        new_password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if new_password != confirm_password:
            return render_template("reset_password.html", error="Passwords do not match!", expired=False)

        if len(new_password) < 8:
            return render_template("reset_password.html", error="Password must be at least 8 characters!", expired=False)
        if not any(char.isdigit() for char in new_password):
            return render_template("reset_password.html", error="Password must contain at least one number!", expired=False)
        if not any(char in "!@#$%^&*" for char in new_password):
            return render_template("reset_password.html", error="Password must contain at least one special character!", expired=False)

        hashed_password = generate_password_hash(new_password)

        db = get_db()
        cursor = db.cursor()
        cursor.execute("UPDATE users SET password=%s WHERE email=%s", (hashed_password, email))
        db.commit()
        cursor.close()
        db.close()

        return redirect("/login")

    return render_template("reset_password.html", expired=expired)

# ---------------- ERROR HANDLERS ----------------
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500

@app.errorhandler(429)
def rate_limit_exceeded(e):
    return render_template("429.html"), 429

# ---------------- RUN APPLICATION ----------------
if __name__ == "__main__":
    app.run(debug=True)