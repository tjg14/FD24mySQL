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
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", request.form.get("username"), 
            generate_password_hash(request.form.get("password")))

        return redirect("/")

    else:
        return render_template("register.html")


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

        # Query database for groupname
        rows_groups = db.execute("SELECT * FROM groups WHERE groupname = ?", request.form.get("groupname"))

        # Ensure username exists and password is correct
        if len(rows_groups) != 1 or not check_password_hash(rows_groups[0]["hash"], request.form.get("password")):
            return apology("invalid group name and/or password", 400)

        # Remember which user has logged in and enter into associations table if needed
        session["group_id"] = rows_groups[0]["id"]
        rows_associations = db.execute("SELECT * FROM group_user_associations WHERE user_id = ? AND group_id = ?", 
            session["user_id"], session["group_id"])
        if not len(rows_associations):
            db.execute("INSERT INTO group_user_associations (group_id, user_id) VALUES(?, ?)", 
                session["group_id"], session["user_id"])

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
        db.execute("INSERT INTO groups (groupname, hash) VALUES (?, ?)", request.form.get("groupname"), 
            generate_password_hash(request.form.get("password")))

        return redirect("/")

    else:
        return render_template("create_group.html")
    

@app.route("/players", methods=["GET", "POST"])
@login_required
@group_login_required
def players():
    """For now, render list of players, and allow add new player"""
    
    if request.method == "POST":

        #Ensure player name is not blank
        player_name = request.form.get("player_name")
        if not player_name:
            return apology("must input player name", 400)

        #Ensure player name doesn't exist within gurrent group
        player_rows = db.execute("SELECT * FROM players WHERE group_id = ? AND player_name =?", session["group_id"], player_name)
        if len(player_rows):
            return apology("player name already in group", 400)

        #Insert player name into players table
        db.execute("INSERT INTO players (player_name, group_id) VALUES (?, ?)", player_name, session["group_id"])
        return redirect("/players")
    
    else:
        groupname = db.execute("SELECT groupname FROM groups WHERE id = ?", session["group_id"])[0]["groupname"]
        players = db.execute("SELECT * FROM players WHERE group_id = ?", session["group_id"])
        for row in range(len(players)):
            players[row]["latest_hcp"] = db.execute("SELECT player_hcp FROM handicaps WHERE player_id = ? ORDER BY id DESC LIMIT 1", 
                players[row]["id"])

        return render_template("players.html", groupname=groupname, players=players)
    

@app.route("/edit_delete_player", methods=["GET", "POST"])
@login_required
@group_login_required
def edit_delete_player():
    """Edit or Delete Player"""
    
    if request.method == "POST":

        #Ensure player name or edit / delete is not blank
        player_name = request.form.get("player_name")
        edit_or_delete = request.form.get("edit_or_delete")
        if not player_name or not edit_or_delete:
            return apology("error player name or edit/delete option didnt go through", 400)

        #If delete, first check retrieve if player has scores
        player_id = db.execute("SELECT * FROM players WHERE group_id = ? AND player_name =?", session["group_id"], player_name)[0]["id"]
        player_scores = db.execute("SELECT * FROM scores WHERE player_id = ?", player_id)
        if len(player_scores):
            return apology("can't delete player with score history", 400)

 
        return render_template("edit_delete_player.html",player_name=player_name, edit_or_delete=edit_or_delete)
    
    else:
        return redirect("/players")
    
@app.route("/edit_delete_player_complete", methods=["POST"])
@login_required
@group_login_required
def edit_delete_player_complete():
    """Complete the Edit or Delete Player"""
    
    if request.method == "POST":

        # Check if edit or delete request
        edit_or_delete = request.form.get("edit_or_delete")
        player_name = request.form.get("player_name")
       
        if edit_or_delete == "edit":
            new_player_name = request.form.get("new_player_name")
            db.execute("UPDATE players SET player_name = ? WHERE player_name = ? AND group_id = ?",
                new_player_name, player_name, session["group_id"])
        elif edit_or_delete == "delete":
            #Check again no scores
            player_id = db.execute("SELECT * FROM players WHERE group_id = ? AND player_name =?", session["group_id"], player_name)[0]["id"]
            player_scores = db.execute("SELECT * FROM scores WHERE player_id = ?", player_id)
            if len(player_scores):
                return apology("can't delete player with score history", 400)
            
            #Delete from players database
            db.execute("DELETE FROM players WHERE id = ?", player_id)
        else:
            return apology("no edit or delete request")
       
        return redirect("/players")
    else:
        return redirect("/players")


@app.route("/create_event", methods=["GET", "POST"])
@login_required
@group_login_required
def create_event():
    """Create Event"""
    
    return render_template("create_event.html")

      