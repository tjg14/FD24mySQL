import os, math

from cs50 import SQL
from flask import Flask, jsonify, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import logging

from helpers import apology, login_required, group_login_required, event_selected, usd

logging.basicConfig(level=logging.DEBUG)

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


@app.route("/", methods=["GET", "POST"])
@login_required
@group_login_required
def index():
    """Show homepage"""
    
    if request.method == "POST":
        # Get event_name, add event id to sessions, and redirect to event page
        event_name = request.form.get("event_name")
        event_id = db.execute("SELECT * FROM events WHERE event_name = ? AND group_id = ?", event_name, session["group_id"])[0]["id"]
        session["event_id"] = event_id
        return redirect("/event_scoreboard")
    else:
        # Remove any specific event in session
        if session.get("event_id") is not None:
            session.pop("event_id", None)
       

        # Get groupname via session group_id
        groupname = db.execute("SELECT groupname FROM groups WHERE id = ?", session["group_id"])[0]["groupname"]
        
        # Get events dictionary for group_id
        events = db.execute("SELECT * FROM events WHERE group_id = ?", session["group_id"])
        
        # Get data for rendering index.html tables of events..
        # Add key to event dictionary for status of each event, showing complete if >0 matches with Complete status
        # and incomplete if any matches are incomplete
        for event in events:
            complete_events_count = 0
            incomplete_events_count = 0
            complete_matches = db.execute("SELECT COUNT(status) as count FROM matches WHERE status = 'COMPLETE' AND round_id IN " +
                "(SELECT round_id FROM rounds WHERE event_id = ?)", event["id"])[0]['count']
            incomplete_matches = db.execute("SELECT COUNT(status) as count FROM matches WHERE status = 'INCOMPLETE' AND round_id IN " +
                "(SELECT round_id FROM rounds WHERE event_id = ?)", event["id"])[0]['count']
            if complete_matches > 0 and not incomplete_matches:
                event["status"] = "Complete"
                complete_events_count += 1
            else:
                event["status"] = "Incomplete"
                incomplete_events_count += 1
            
        return render_template("index.html", groupname=groupname, events=events, complete_events_count=complete_events_count,
            incomplete_events_count=incomplete_events_count)
    


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register new user"""

    if request.method == "POST":

        # Ensure all fields not blank
        if not request.form.get("username") or not request.form.get("password") or not request.form.get("confirmation"):
            return apology("must provide username and password", 400)

        # Query users table in database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Check if username already exists in users table, if yes, return apology
        if len(rows) > 0:
            return apology("Username already exists", 400)

        # Check if password matches confirmation, else return apology
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords don't match", 400)

        # Register new user into users database along with hash of their password
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", request.form.get("username"), 
            generate_password_hash(request.form.get("password")))

        # Redirect user to home page
        return redirect("/")

    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id in session
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted, else return apology
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted, else return apology
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query users table in database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct, else return apology
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 400)

        # Remember which user has logged in by storing user_id in session
        session["user_id"] = rows[0]["id"]

        # Redirect user to group route, in order to choose or create a group
        return redirect("/group")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        # Render login.html showing login form
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id in session
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/group")
@login_required
def group():
    """Show options to join group or create group"""

    # Forget any group_id and event_id in session
    if session.get("group_id") is not None:
        session.pop("group_id", None)
    if session.get("event_id") is not None:
        session.pop("event_id", None)

    # Render group.html showing options to join group or create group
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
        rows_groups = db.execute("SELECT * FROM groups WHERE LOWER(groupname) = ?", request.form.get("groupname").lower())

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
        rows = db.execute("SELECT * FROM groups WHERE LOWER(groupname) = ?", request.form.get("groupname").lower())

        # Check if groupname already exists
        if len(rows) > 0:
            return apology("Group name already exists", 400)

        # Check if password matches confirmation
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords don't match", 400)

        # Register group into groups database
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
            try:
                players[row]["latest_hcp"] = db.execute("SELECT * FROM handicaps WHERE player_id = ? ORDER BY id DESC LIMIT 1", 
                    players[row]["id"])[0]["player_hcp"]
            except:
                players[row]["latest_hcp"] = None
            
        return render_template("players.html", groupname=groupname, players=players, num_players=len(players))
    

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
    
    if request.method == "POST":
        event_name = request.form.get("event_name")
        event_date = request.form.get("event_date")
        try:
            num_players = int(request.form.get("num_players"))
        except ValueError:
            return apology("Num Team must be integer")
       
       #Send back if pressed enter with 0 players or no event name
        if not num_players or not event_name:
            redirect("/create_event")
        
        #TODO confim event name doesnt exist in the group already
        
        num_teams = math.ceil(num_players / 2)
        team_names = []
        for i in range(num_teams):
            team_names.append(request.form.get("team_name_" + str(i + 1)))
        
        group_players = db.execute("SELECT player_name FROM players WHERE group_id = ?", session["group_id"])

        return render_template("create_event_continued.html", event_name=event_name, event_date=event_date,
            num_players=num_players, num_teams=num_teams, team_names=team_names, group_players=group_players)
    else:
        return render_template("create_event.html")

@app.route("/create_event_continued", methods=["GET", "POST"])
@login_required
@group_login_required
def create_event_continued():
    """Create Event - Team Details"""
    
    if request.method == "POST":

        # Get event header details and error check
        event_name = request.form.get("event_name")
        if not event_name:
            return apology("no event name")
        event_date = request.form.get("event_date")
        num_teams = int(request.form.get("num_teams"))
        if num_teams < 2:
            return apology("must have at least 2 teams")
        
        # Get team details and error check
        teams = []
        for i in range(num_teams):
            team = {}
            team["team_name_temp"] = request.form.get("team_name_" + str(i))
            team["player_a_temp"] = request.form.get("player_a_team_" + str(i))
            team["hcp_a_temp"] = request.form.get("hcp_player_a_team_" + str(i))
            team["player_b_temp"] = request.form.get("player_b_team_" + str(i))
            team["hcp_b_temp"] = request.form.get("hcp_player_b_team_" + str(i))
            teams.append(team)

            if not team["team_name_temp"]:
                return apology("team name blank")
            elif not team["player_a_temp"]:
                return apology("need at least 1 player per team")
            elif not team["hcp_a_temp"]:
                return apology("player a handicap blank")
            if team["player_b_temp"] and not team["hcp_b_temp"]:
                return apology("player b handicap blank")

        logging.info(teams)
    
        # Insert into events table the event name, group id, and date
        db.execute("INSERT INTO events (event_name, group_id, date) VALUES (?, ?, ?)", event_name, session["group_id"], event_date)

        # Insert into teams table all the team names, and event_id
        event_id = db.execute("SELECT * FROM events WHERE event_name = ? AND group_id = ?", event_name, session["group_id"])[0]["id"]
        for i in range(num_teams):
            db.execute("INSERT INTO teams (team_name, event_id) VALUES (?, ?)", teams[i]["team_name_temp"], event_id)

        # Insert into team_roster table the players on each team
        for i in range(num_teams):
            team_id = db.execute("SELECT * FROM teams WHERE team_name = ? AND event_id = ?", teams[i]["team_name_temp"], event_id)[0]["id"]
            player_id_a = db.execute("SELECT * FROM players WHERE player_name = ? AND group_id = ?", 
                teams[i]["player_a_temp"], session["group_id"])[0]["id"]
            db.execute("INSERT INTO team_roster (team_id, player_id) VALUES (?, ?)", 
                team_id, player_id_a)
            if teams[i]["player_b_temp"]:
                player_id_b = db.execute("SELECT * FROM players WHERE player_name = ? AND group_id = ?", 
                    teams[i]["player_b_temp"], session["group_id"])[0]["id"]
                db.execute("INSERT INTO team_roster (team_id, player_id) VALUES (?, ?)", 
                    team_id, player_id_b)
        
        # Insert into handicaps table for each player id the event id and player hcp
        for i in range(num_teams):
            player_id_a = db.execute("SELECT * FROM players WHERE player_name = ? AND group_id = ?", 
                teams[i]["player_a_temp"], session["group_id"])[0]["id"]
            db.execute("INSERT INTO handicaps (player_id, event_id, player_hcp) VALUES (?, ?, ?)", 
                player_id_a, event_id, teams[i]["hcp_a_temp"])
            if teams[i]["player_b_temp"]:
                player_id_b = db.execute("SELECT * FROM players WHERE player_name = ? AND group_id = ?", 
                    teams[i]["player_b_temp"], session["group_id"])[0]["id"]
                db.execute("INSERT INTO handicaps (player_id, event_id, player_hcp) VALUES (?, ?, ?)", 
                    player_id_b, event_id, teams[i]["hcp_b_temp"])

        return redirect("/")
    else:
        return apology("GET request??")


@app.route("/event_structure", methods=["GET", "POST"])
@login_required
@group_login_required
@event_selected
def event_structure():
    """Event Details"""

    if request.method == "POST":
        # Get new round name (optional)
        new_round_name = request.form.get("new_round_name")
        # Get course selection
        course_id_selected = request.form.get("course_select")
        if not course_id_selected:
            return apology("no course selected")
        # Get round number
        round_number = int(request.form.get("num_rounds_input")) + 1
        # Get teams and matches
        num_teams = int(db.execute("SELECT COUNT(*) as count FROM teams WHERE event_id = ?", session["event_id"])[0]["count"])
        num_matches = int(num_teams / 2)
        matches = []
        for i in range(num_matches):
            team_a_id = int(request.form.get("team_a_match_" + str(i + 1)))
            team_b_id = int(request.form.get("team_b_match_" + str(i + 1)))
            if not team_a_id or not team_b_id:
                return apology("team not selected - match " + str(i + 1))
            matches.append({"match_number": i + 1, "team_a": team_a_id, "team_b": team_b_id})
        
        # Insert new round into rounds table
        db.execute("INSERT INTO rounds (round_number, round_name, event_id) VALUES (?, ?, ?)",
            round_number, new_round_name, session["event_id"])
        # Get round id
        round_id = db.execute("SELECT MAX(id) FROM rounds WHERE event_id = ?", session["event_id"])[0]["MAX(id)"]
        # Insert matches into matches table
        for match in matches:
            db.execute("INSERT INTO matches (match_number, match_starting_hole, round_id, course_id," +
                "team_a_id, team_b_id) VALUES (?, ?, ?, ?, ?, ?)", match["match_number"], 1, round_id,
                course_id_selected, match["team_a"], match["team_b"])

        return redirect("/event_structure")
    else:
        # Get event data needed to display and structure matches in rounds
        rounds = db.execute("SELECT * FROM rounds WHERE event_id = ? ORDER BY round_number ASC", session["event_id"])
        # Built list of dictionaries for each round with round number, round name, and matches (match number, team a, team b, team a score, team b score)
        for round in rounds:
            matches = db.execute("SELECT * FROM matches WHERE round_id = ?", round["id"])
            round["matches"] = []
            for match in matches:
                team_a = db.execute("SELECT * FROM teams WHERE id = ?", match["team_a_id"])[0]["team_name"]
                team_b = db.execute("SELECT * FROM teams WHERE id = ?", match["team_b_id"])[0]["team_name"]
                course_name = db.execute("SELECT * FROM course_tee WHERE id = ?", match["course_id"])[0]["name"]
                course_tees = db.execute("SELECT * FROM course_tee WHERE id = ?", match["course_id"])[0]["teebox"]
                round["matches"].append({"match_number": match["match_number"], "course_name": course_name + " - " +course_tees + " Tees",
                     "team_a": team_a, "team_b": team_b, "team_a_score": "create fn", "team_b_score": "create fn"})
       
        num_teams = db.execute("SELECT COUNT(*) as count FROM teams WHERE event_id = ?", session["event_id"])[0]["count"]
        event_name = db.execute("SELECT event_name FROM events WHERE id = ?", session["event_id"])[0]["event_name"]
        teams = db.execute("SELECT * FROM teams WHERE event_id = ?", session["event_id"])

        return render_template("event_structure.html", rounds=rounds, num_teams=num_teams, event_name=event_name,
            teams=teams)

@app.route("/event_scoreboard", methods=["GET", "POST"])
@login_required
@group_login_required
@event_selected
def event_scoreboard():
    """Event Scoreboard
    TODO
  
    overall scoreboard
    
    """
  
    return apology("To Do Event Scoreboard")

@app.route("/courseadmin", methods=["GET", "POST"])
@login_required
def course_admin():
    """Add courses to database in admin mode"""
    if request.method == "POST":
        # Get course name
        course_name = request.form.get("new_course_name")
        if not course_name:
            return apology("no course name")
        # Get course tees
        course_tees = request.form.get("course_tees")
        if not course_tees:
            return apology("no course tees")
        # Get course slope
        course_slope = request.form.get("course_tee_slope")
        # Make sure course slope is not blank and is an integer betwee 55 and 155
        if not course_slope:
            return apology("no course slope")
        try:
            course_slope = int(course_slope)
            if course_slope < 55 or course_slope > 155:
                return apology("course slope must be between 55 and 155")
        except ValueError:
            return apology("course slope must be an integer")
        # Get course rating
        course_rating = request.form.get("course_tee_rating")
        # Make sure course rating is not blank and is a float between 50 and 80
        if not course_rating:
            return apology("no course rating")
        try:
            course_rating = float(course_rating)
            if course_rating < 50 or course_rating > 80:
                return apology("course rating must be between 50 and 80")
        except ValueError:
            return apology("course rating must be a float")
        
        # Loop through all 18 holes, get par and handicap for each hole
        holes = []
        for i in range(1, 19):
            par = request.form.get("hole_par_" + str(i))
            if not par:
                return apology("no par for hole " + str(i))
            try:
                par = int(par)
            except ValueError:
                return apology("par for hole " + str(i) + " must be an integer")
            handicap = request.form.get("hole_hcp_" + str(i))
            if not handicap:
                return apology("no handicap for hole " + str(i))
            try:
                handicap = int(handicap)
            except ValueError:
                return apology("handicap for hole " + str(i) + " must be an integer")
            holes.append({"hole": i, "par": par, "handicap": handicap})
        
        # Insert course into courses table
        db.execute("INSERT INTO course_tee (name, teebox, rating, slope) VALUES (?, ?, ?, ?)",
            course_name, course_tees, course_rating, course_slope)
        # Get course id
        course_id = db.execute("SELECT MAX(id) FROM course_tee WHERE name = ? AND teebox = ?", 
            course_name, course_tees)[0]["MAX(id)"]
        # Insert holes into holes table
        for hole in holes:
            db.execute("INSERT INTO holes (course_id, hole_number, par, hole_hcp) VALUES (?, ?, ?, ?)",
                course_id, hole["hole"], hole["par"], hole["handicap"])
             
        return redirect("/")
    else:
        return render_template("course_input.html")
    
@app.route('/api/courses', methods=['GET'])
def get_courses():
    # Query the database for all courses
    courses = db.execute("SELECT * FROM course_tee")

    # Convert the list of Course objects to a list of dictionaries
    courses_list = [{"id": course["id"], "name": course["name"] + " - " + course["teebox"] + " " +
        str(course["rating"]) + "/" + str(course["slope"])} for course in courses]

    # Return the list of courses as JSON
    return jsonify(courses_list)

@app.route('/scorecard', methods=['GET', 'POST'])
def scorecard():

    if request.method == "POST":
        
        # Get round number
        round_number = request.form.get("round_number")
        
        # Get match number
        match_number = request.form.get("match_number")
        
        # Error check for round and match number
        if not round_number or not match_number:
            return apology("round or match number not sent in POST request")
        
        # Clear previous and add round number and match number to session
        session.pop("round", None)
        session.pop("match", None)
        session["round_number"] = round_number
        session["match_number"] = match_number
    else:
        # Get round number and match number from session
        round_number = session["round_number"]
        match_number = session["match_number"]

        # If round number or match number not in session, return apology
        if not round_number or not match_number:
            redirect("/event_structure")

    # Get round id and match id 
    round_id = db.execute("SELECT id FROM rounds WHERE event_id = ? AND round_number = ?", 
        session["event_id"], round_number)[0]["id"]
    match_id = db.execute("SELECT id FROM matches WHERE round_id = ? AND match_number = ?", 
        round_id, match_number)[0]["id"]
    match_data = {"match_number": match_number, "match_id": match_id}

    # Get event name
    event_name = db.execute("SELECT event_name FROM events WHERE id = ?", session["event_id"])[0]["event_name"]
    
    # Get course id and display name
    course_id = db.execute("SELECT course_id FROM matches WHERE id = ?", match_id)[0]["course_id"]
    course_name = db.execute("SELECT name FROM course_tee WHERE id = ?", course_id)[0]["name"]
    course_tee = db.execute("SELECT teebox FROM course_tee WHERE id = ?", course_id)[0]["teebox"]
    course_display_name = course_name + " - " + course_tee + " Tees"
    
    # Get team and player names
    team_a_id = db.execute("SELECT team_a_id FROM matches WHERE id = ?", match_id)[0]["team_a_id"]
    team_b_id = db.execute("SELECT team_b_id FROM matches WHERE id = ?", match_id)[0]["team_b_id"]
    team_a_name = db.execute("SELECT team_name FROM teams WHERE id = ?", team_a_id)[0]["team_name"]
    team_b_name = db.execute("SELECT team_name FROM teams WHERE id = ?", team_b_id)[0]["team_name"]
    team_a_players = db.execute("SELECT * FROM players WHERE id IN " +
        "(SELECT player_id FROM team_roster WHERE team_id = ?)", team_a_id)
    team_b_players = db.execute("SELECT * FROM players WHERE id IN " +
        "(SELECT player_id FROM team_roster WHERE team_id = ?)", team_b_id)
    team_data = {"team_a_name": team_a_name, "team_a_players": team_a_players, "team_b_name": team_b_name, "team_b_players": team_b_players}
    
    # Get course holes
    holes = db.execute("SELECT * FROM holes WHERE course_id = ? ORDER BY hole_number ASC", course_id)
    # For each hole in holes, get the score for each player in team a and team b
    for hole in holes:
        hole["team_a_scores"] = []
        hole["team_b_scores"] = []
        for player in team_a_players:
            player_id = db.execute("SELECT id FROM players WHERE player_name = ?", player["player_name"])[0]["id"]
            score = db.execute("SELECT score FROM scores WHERE player_id = ? AND match_id = ? AND match_hole_number = ?", 
                player_id, match_id, hole["hole_number"])
            if score:
                hole["team_a_scores"].append(score[0]["score"])
            else:
                hole["team_a_scores"].append("-")
        for player in team_b_players:
            player_id = db.execute("SELECT id FROM players WHERE player_name = ?", player["player_name"])[0]["id"]
            score = db.execute("SELECT score FROM scores WHERE player_id = ? AND match_id = ? AND match_hole_number = ?", 
                player_id, match_id, hole["hole_number"])
            if score:
                hole["team_b_scores"].append(score[0]["score"])
            else:
                hole["team_b_scores"].append("-")
    
    return render_template("scorecard.html", event_name=event_name, course_display_name=course_display_name,
        round_number=round_number, match_data=match_data, holes=holes, team_data=team_data)
    
    
@app.route('/scorecard_edit', methods=['GET', 'POST'])
def scorecard_edit():
 
    if request.method == "POST":

        # Get match id and player id
        match_id = request.form.get("match_id")
        player_id = request.form.get("player_id")

        # Get course id and display name
        course_id = db.execute("SELECT course_id FROM matches WHERE id = ?", match_id)[0]["course_id"]
        course_name = db.execute("SELECT name FROM course_tee WHERE id = ?", course_id)[0]["name"]
        course_tee = db.execute("SELECT teebox FROM course_tee WHERE id = ?", course_id)[0]["teebox"]
        course_display_name = course_name + " - " + course_tee + " Tees"

        # Get course holes
        holes = db.execute("SELECT * FROM holes WHERE course_id = ? ORDER BY hole_number ASC", course_id)

        # For each hole, append the score for the player_id if it exists, else leave blank
        for hole in holes:
            score = db.execute("SELECT score FROM scores WHERE player_id = ? AND match_id = ? AND match_hole_number = ?", 
                player_id, match_id, hole["hole_number"])
            if score:
                hole["score"] = score[0]["score"]
            else:
                hole["score"] = None

        return render_template("scorecard_edit.html", holes=holes, course_display_name=course_display_name, 
            match_id=match_id, player_id=player_id)
    else:
        return redirect("/event_structure")

@app.route('/scorecard_processing', methods=['GET', 'POST'])
def scorecard_processing():
 
    if request.method == "POST":
            
        # Get match id and player id and hcp
        match_id = request.form.get("match_id")
        player_id = request.form.get("player_id")

        # Get course id
        course_id = db.execute("SELECT course_id FROM matches WHERE id = ?", match_id)[0]["course_id"]

        # For each hole, get the score and update the scores table
        for i in range(1, 19):
            score = int(request.form.get("score_hole_" + str(i)))
            if score and score > 0:
                db.execute("INSERT INTO scores (match_id, match_hole_number, player_id, score) VALUES (?, ?, ?, ?)",
                    match_id, i, player_id, score)
        
        return redirect("/scorecard")

    else:
        return redirect("/event_structure")