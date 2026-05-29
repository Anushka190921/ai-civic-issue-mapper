from flask import Flask, request, render_template, redirect, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import os


app = Flask(__name__)
app.secret_key = "secret123"

# Upload folder
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Anu@1909",
        database="civic_issues"
    )

# ---------------- HOME ----------------
@app.route("/")
def home():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("form.html")

# ---------------- SUBMIT ----------------
@app.route("/submit", methods=["POST"])
def submit():
    if "user_id" not in session:
        return redirect("/login")

    try:
        print("SUBMIT HIT")

        user_id = session["user_id"]
        issue_type = request.form.get("issue_type")
        description = request.form.get("description")
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")

        image = request.files.get("image")
        image_name = None

        if image and image.filename != "":
            import time
            filename = str(int(time.time())) + "_" + image.filename
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            image.save(filepath)
            image_name = filename

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

        return redirect("/success")

    except Exception as e:
        return f"Error: {e}"

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        db = get_db()
        cursor = db.cursor()

        hashed_password = generate_password_hash(request.form["password"])

        cursor.execute(
            "INSERT INTO users (first_name, last_name, email, password) VALUES (%s, %s, %s, %s)",
            (
                request.form["first_name"],
                request.form["last_name"],
                request.form["email"],
                hashed_password
            )
        )

        db.commit()
        cursor.close()
        db.close()

        return redirect("/login")

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE email=%s", (request.form["email"],))
        user = cursor.fetchone()

        cursor.close()
        db.close()

        if user and check_password_hash(user["password"], request.form["password"]):
            session["user_id"] = user["id"]
            return redirect("/")

        return "Login Failed"

    return render_template("login.html")


# ---------------- ADMIN LOGIN ----------------


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        print("ADMIN LOGIN HIT")  # debug

        username = request.form.get("username")
        password = request.form.get("password")

        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM admins WHERE username=%s", (username,))
        admin = cursor.fetchone()

        cursor.close()
        db.close()

        if admin:
            # if using plain password
            if admin["password"] == password:
                session["admin"] = admin["id"]
                return redirect("/dashboard")

            # if using hashed password (better)
            # if check_password_hash(admin["password"], password):
            #     session["admin"] = admin["id"]
            #     return redirect("/dashboard")

        return render_template("admin_login.html", error="Invalid Credentials")

    return render_template("admin_login.html")

#------------------my_issues-------------------

@app.route("/my_issues")
def my_issues():
    if "user_id" not in session:
        return redirect("/login")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM civic_issues WHERE user_id=%s", (session["user_id"],))
    issues = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("my_issues.html", issues=issues)


# ---------------- ADMIN DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "admin" not in session:
        return redirect("/admin")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT civic_issues.*, users.first_name, users.email
        FROM civic_issues
        JOIN users ON civic_issues.user_id = users.id
        ORDER BY civic_issues.id DESC
    """)

    complaints = cursor.fetchall()

    print(complaints)  # 🔥 DEBUG

    cursor.close()
    db.close()

    return render_template("admin.html", complaints=complaints)
#--------------user can delete their own complaint--------

@app.route("/delete_my_issue/<int:id>")
def delete_my_issue(id):
    if "user_id" not in session:
        return redirect("/login")

    db = get_db()
    cursor = db.cursor()

    # Check complaint belongs to logged-in user
    cursor.execute("SELECT * FROM civic_issues WHERE id=%s AND user_id=%s", (id, session["user_id"]))
    issue = cursor.fetchone()

    if issue:
        cursor.execute("DELETE FROM civic_issues WHERE id=%s", (id,))
        db.commit()

    cursor.close()
    db.close()

    return redirect("/my_issues")

#---------update button in the admin dashboard------------

@app.route("/update_status/<int:id>", methods=["POST"])
def update_status(id):
    if "admin" not in session:
        return redirect("/admin")

    new_status = request.form["status"]

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "UPDATE civic_issues SET status=%s WHERE id=%s",
        (new_status, id)
    )

    db.commit()
    cursor.close()
    db.close()

    return redirect("/dashboard")

#-----------------GOOGLE LOGIN---------------------



 

#------------------ submit ----------------
@app.route("/success")
def success():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("success.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)


