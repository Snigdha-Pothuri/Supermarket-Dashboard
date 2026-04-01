from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

# ---------- DATABASE ----------
def get_db_connection():
    conn = sqlite3.connect("supermarket.db")
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db_connection()

    # Users table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT
        )
    """)

    # Supermarket data table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS supermarket (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            product_name TEXT,
            category TEXT,
            price INTEGER,
            quantity_sold INTEGER,
            stock_left INTEGER
        )
    """)

    # Insert default user
    conn.execute("INSERT OR IGNORE INTO users (id, username, password) VALUES (1, 'admin', 'admin')")

    conn.commit()
    conn.close()

create_tables()

# ---------- LOGIN ----------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()
        conn.close()

        if user:
            session["user"] = username
            return redirect("/home")
        else:
            return "Invalid Credentials"

    return render_template("login.html")
# ---------------REGISTER-----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # ✅ ADD THIS HERE
        if not username or not password:
            return "Invalid input"

        conn = get_db_connection()

        # Check if user already exists
        existing = conn.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        ).fetchone()

        if existing:
            conn.close()
            return "User already exists"

        # Insert new user
        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )
        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("register.html")

# ---------- DATA ENTRY ----------
@app.route("/home", methods=["GET", "POST"])
def home():
    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        date = request.form["date"]
        product = request.form["product"]
        category = request.form["category"]
        price = request.form["price"]
        qty = request.form["quantity"]
        stock = request.form["stock"]

        conn = get_db_connection()
        conn.execute("""
            INSERT INTO supermarket 
            (date, product_name, category, price, quantity_sold, stock_left)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (date, product, category, price, qty, stock))
        conn.commit()
        conn.close()

        return redirect("/dashboard")

    return render_template("index.html")

# ---------- DASHBOARD ----------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    data = conn.execute("SELECT * FROM supermarket").fetchall()
    conn.close()

    total_sales = sum(row["price"] * row["quantity_sold"] for row in data)
    total_items = sum(row["quantity_sold"] for row in data)

    # LOW STOCK
    low_stock = [row for row in data if row["stock_left"] < 20]

    # CATEGORY-WISE SALES
    category_sales = {}
    for row in data:
        cat = row["category"]
        category_sales[cat] = category_sales.get(cat, 0) + row["quantity_sold"]

    # DAILY SALES
    daily_sales = {}
    for row in data:
        d = row["date"]
        daily_sales[d] = daily_sales.get(d, 0) + (row["price"] * row["quantity_sold"])

    return render_template(
        "dashboard.html",
        data=data,
        total_sales=total_sales,
        total_items=total_items,
        low_stock=low_stock,
        category_sales=category_sales,
        daily_sales=daily_sales
    )

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)