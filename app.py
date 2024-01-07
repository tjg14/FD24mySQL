import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, group_login_required, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///FD2024.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
@group_login_required
def index():
    """Show homepage"""
    groupname = db.execute("SELECT groupname FROM groups WHERE id = ?", session["group_id"])[0]["groupname"]
    return render_template("index.html", groupname=groupname)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to group options
        return redirect("/group")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/group",  methods=["GET", "POST"])
@login_required
def group():
    """Show options to join group or create group"""

    # Forget any group_id
    if session.get("group_id") is not None:
        session.pop("group_id", None)

    if request.method == "POST":
        if request.form.get("group_action") == "create_group":
            return redirect("/create_group")
        elif request.form.get("group_action") == "login_group":
            return redirect("/group_login")
        else:
            return apology("Posted without valid group action")   
    else:
        return render_template("group.html")


@app.route("/group_login",  methods=["GET", "POST"])
@login_required
def group_login():
    """Log into group"""

    # Forget any group_id
    if session.get("group_id") is not None:
        session.remove("group_id")

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("groupname"):
            return apology("must provide groupname", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM groups WHERE groupname = ?", request.form.get("groupname"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid group name and/or password", 400)

        # Remember which user has logged in
        session["group_id"] = rows[0]["id"]

        # Redirect to group homepage
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("group_login.html")


@app.route("/create_group",  methods=["GET", "POST"])
@login_required
def create_group():
    """xxxx"""

    if request.method == "POST":

        # Ensure all fields not blank
        if not request.form.get("groupname") or not request.form.get("password") or not request.form.get("confirmation"):
            return apology("must provide group name and password", 400)

        # Query database for group name
        rows = db.execute("SELECT * FROM groups WHERE groupname = ?", request.form.get("groupname"))

        # Check if groupname already exists
        if len(rows) > 0:
            return apology("Group name already exists", 400)

        # Check if password matches confirmation
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords don't match", 400)

        # Register group into gruops database
        db.execute("INSERT INTO groups (groupname, hash) VALUES (?, ?)", request.form.get("groupname"), generate_password_hash(request.form.get("password")))

        return redirect("/")

    else:
        return render_template("create_group.html")
    

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":

        # Ensure all fields not blank
        if not request.form.get("username") or not request.form.get("password") or not request.form.get("confirmation"):
            return apology("must provide username and password", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Check if username already exists
        if len(rows) > 0:
            return apology("Username already exists", 400)

        # Check if password matches confirmation
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords don't match", 400)

        # Register user into users database
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", request.form.get("username"), generate_password_hash(request.form.get("password")))

        return redirect("/")

    else:
        return render_template("register.html")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    return apology("TODO")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    return apology("TODO")
      