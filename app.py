from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date

app = Flask(__name__)
app.secret_key = "ecorecycle_secret_key_2026"


# ================= DATABASE =================

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def create_database():

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS pickup_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            waste_type TEXT NOT NULL,
            quantity REAL NOT NULL,
            address TEXT NOT NULL,
            pickup_date TEXT NOT NULL,
            message TEXT,
            status TEXT DEFAULT 'Pending',
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# ================= HOME =================

@app.route("/")
def index():
    return render_template("index.html")


# ================= ABOUT =================

@app.route("/about")
def about():
    return render_template("about.html")


# ================= REGISTER =================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")

        if not name or not email or not phone or not password:
            flash("Please fill all fields.")
            return redirect(url_for("register"))

        if len(password) < 6:
            flash("Password must contain at least 6 characters.")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        conn = get_db()

        try:

            conn.execute("""
                INSERT INTO users
                (name, email, phone, password)
                VALUES (?, ?, ?, ?)
            """, (
                name,
                email,
                phone,
                hashed_password
            ))

            conn.commit()

            flash("Registration successful! Please login.")

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:

            flash("This email is already registered.")

            return redirect(url_for("register"))

        finally:
            conn.close()

    return render_template("register.html")


# ================= LOGIN =================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:

            flash("Please enter email and password.")

            return redirect(url_for("login"))

        conn = get_db()

        user = conn.execute("""
            SELECT *
            FROM users
            WHERE email = ?
        """, (email,)).fetchone()

        conn.close()

        if user is None:

            flash("Email is not registered.")

            return redirect(url_for("login"))

        if not check_password_hash(user["password"], password):

            flash("Incorrect password.")

            return redirect(url_for("login"))

        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session["user_email"] = user["email"]

        flash("Login successful!")

        return redirect(url_for("dashboard"))

    return render_template("login.html")


# ================= DASHBOARD =================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = get_db()

    # Total requests
    total_requests = conn.execute("""
        SELECT COUNT(*) AS total
        FROM pickup_requests
        WHERE user_id = ?
    """, (user_id,)).fetchone()["total"]


    # Pending requests
    pending_requests = conn.execute("""
        SELECT COUNT(*) AS total
        FROM pickup_requests
        WHERE user_id = ?
        AND status = 'Pending'
    """, (user_id,)).fetchone()["total"]


    # Completed requests
    completed_requests = conn.execute("""
        SELECT COUNT(*) AS total
        FROM pickup_requests
        WHERE user_id = ?
        AND status = 'Completed'
    """, (user_id,)).fetchone()["total"]


    # Total plastic collected
    total_kg = conn.execute("""
        SELECT COALESCE(SUM(quantity), 0) AS total
        FROM pickup_requests
        WHERE user_id = ?
    """, (user_id,)).fetchone()["total"]


    # Plastic actually recycled
    recycled_kg = conn.execute("""
        SELECT COALESCE(SUM(quantity), 0) AS total
        FROM pickup_requests
        WHERE user_id = ?
        AND status = 'Completed'
    """, (user_id,)).fetchone()["total"]


    # All requests
    requests = conn.execute("""
        SELECT *
        FROM pickup_requests
        WHERE user_id = ?
        ORDER BY pickup_date ASC
    """, (user_id,)).fetchall()


    # Upcoming pickup
    upcoming_pickup = conn.execute("""
        SELECT *
        FROM pickup_requests
        WHERE user_id = ?
        AND status = 'Pending'
        AND pickup_date >= ?
        ORDER BY pickup_date ASC
        LIMIT 1
    """, (user_id, str(date.today()))).fetchone()


    conn.close()


    return render_template(
        "dashboard.html",

        user_name=session.get("user_name"),

        total_requests=total_requests,

        pending_requests=pending_requests,

        completed_requests=completed_requests,

        total_kg=round(total_kg, 1),

        recycled_kg=round(recycled_kg, 1),

        requests=requests,

        upcoming_pickup=upcoming_pickup
    )


# ================= PICKUP REQUEST =================

@app.route("/request", methods=["GET", "POST"])
def pickup_request():

    if "user_id" not in session:
        return redirect(url_for("login"))


    if request.method == "POST":

        waste_type = request.form.get("waste_type", "").strip()

        quantity = request.form.get("quantity", "").strip()

        address = request.form.get("address", "").strip()

        pickup_date = request.form.get("pickup_date", "").strip()

        message = request.form.get("message", "").strip()


        if not waste_type or not quantity or not address or not pickup_date:

            flash("Please fill all required fields.")

            return redirect(url_for("pickup_request"))


        try:

            quantity = float(quantity)

            if quantity <= 0:

                flash("Quantity must be greater than 0.")

                return redirect(url_for("pickup_request"))

        except ValueError:

            flash("Please enter a valid quantity.")

            return redirect(url_for("pickup_request"))


        conn = get_db()

        conn.execute("""
            INSERT INTO pickup_requests
            (
                user_id,
                waste_type,
                quantity,
                address,
                pickup_date,
                message,
                status
            )

            VALUES (?, ?, ?, ?, ?, ?, 'Pending')
        """, (
            session["user_id"],
            waste_type,
            quantity,
            address,
            pickup_date,
            message
        ))

        conn.commit()

        conn.close()


        flash("Plastic pickup request submitted successfully!")

        return redirect(url_for("dashboard"))


    return render_template("request.html")


# ================= CONTACT =================

@app.route("/contact")
def contact():

    return render_template("contact.html")

# ================= ADMIN LOGIN =================

ADMIN_EMAIL = "admin@ecorecycle.com"
ADMIN_PASSWORD = "admin123"


@app.route("/admin", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:

            session["admin"] = True

            return redirect(url_for("admin_dashboard"))

        flash("Invalid admin email or password.")

    return render_template("admin_login.html")


# ================= ADMIN DASHBOARD =================

@app.route("/admin/dashboard")
def admin_dashboard():

    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    conn = get_db()

    requests = conn.execute("""
        SELECT
            pickup_requests.*,
            users.name,
            users.email,
            users.phone
        FROM pickup_requests
        JOIN users
        ON pickup_requests.user_id = users.id
        ORDER BY pickup_requests.id DESC
    """).fetchall()

    total_requests = conn.execute("""
        SELECT COUNT(*) AS total
        FROM pickup_requests
    """).fetchone()["total"]

    pending_requests = conn.execute("""
        SELECT COUNT(*) AS total
        FROM pickup_requests
        WHERE status = 'Pending'
    """).fetchone()["total"]

    completed_requests = conn.execute("""
        SELECT COUNT(*) AS total
        FROM pickup_requests
        WHERE status = 'Completed'
    """).fetchone()["total"]

    recycled_kg = conn.execute("""
        SELECT COALESCE(SUM(quantity), 0) AS total
        FROM pickup_requests
        WHERE status = 'Completed'
    """).fetchone()["total"]

    conn.close()

    return render_template(
        "admin_dashboard.html",
        requests=requests,
        total_requests=total_requests,
        pending_requests=pending_requests,
        completed_requests=completed_requests,
        recycled_kg=round(recycled_kg, 1)
    )


# ================= COMPLETE PICKUP =================

@app.route("/admin/complete/<int:request_id>", methods=["POST"])
def complete_pickup(request_id):

    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    conn = get_db()

    conn.execute("""
        UPDATE pickup_requests
        SET status = 'Completed'
        WHERE id = ?
    """, (request_id,))

    conn.commit()
    conn.close()

    flash("Pickup marked as completed successfully.")

    return redirect(url_for("admin_dashboard"))


# ================= ADMIN LOGOUT =================

@app.route("/admin/logout")
def admin_logout():

    session.pop("admin", None)

    return redirect(url_for("admin_login"))
# ================= LOGOUT =================

@app.route("/logout")
def logout():

    session.clear()

    flash("You have been logged out.")

    return redirect(url_for("index"))


# ================= START SERVER =================

create_database()

if __name__ == "__main__":
    app.run(debug=True)