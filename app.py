import os, math

from cs50 import SQL
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, desc
from flask import Flask, jsonify, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import logging

from helpers import apology, login_required, group_login_required, event_selected, usd

logging.basicConfig(level=logging.DEBUG)

# Configure application
app = Flask(__name__)
app.config["DEBUG"]= True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Confirgure database connection locally

SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://root:password123@localhost:3306/FD2024".format(
    username="root",
    password="password123",
    hostname="localhost",
    databasename="FD2024",
)


# Confirgure database connection for pythonanywhere
# SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://tjg14:TJGfd2024@tjg14.mysql.pythonanywhere-services.com:3306/tjg14$FD2024".format(
#     username="tjg14",
#     password="TJGfd2024",
#     hostname="tjg14.mysql.pythonanywhere-services.com",
#     databasename="tjg14$FD2024",
# )

app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
# Configure CS50 Library to use SQLite database
#db = SQL("sqlite:///FD2024.db")
#db = SQL("mysql://root:password123@localhost:3306/FD2024")
#db = SQL("mysql://tjg14:TJGfd2024@tjg14.mysql.pythonanywhere-services.com:3306/tjg14$FD2024")

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(30), nullable=False)
    hash = db.Column(db.String(255), nullable=False)

class GolfGroup(db.Model):
    __tablename__ = 'golf_groups'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    groupname = db.Column(db.String(50), nullable=False)
    hash = db.Column(db.String(255), nullable=False)

class GroupUserAssociation(db.Model):
    __tablename__ = 'group_user_associations'

    group_id = db.Column(db.Integer, db.ForeignKey("golf_groups.id"), primary_key=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True, nullable=False)

class Player(db.Model):
    __tablename__ = 'players'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    player_name = db.Column(db.String(50), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey("golf_groups.id"), nullable=False)

class Event(db.Model):
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_name = db.Column(db.String(50), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey("golf_groups.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)

class Team(db.Model):
    __tablename__ = 'teams'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    team_name = db.Column(db.String(50), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)

class TeamRoster(db.Model):
    __tablename__ = 'team_roster'

    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), primary_key=True, nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), primary_key=True, nullable=False)

class CourseTee(db.Model):
    __tablename__ = 'course_tee'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    teebox = db.Column(db.String(10), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    slope = db.Column(db.Integer, nullable=False)
    active = db.Column(db.Integer, nullable=False, server_default="1")

class Hole(db.Model):
    __tablename__ = 'holes'

    course_id = db.Column(db.Integer, db.ForeignKey("course_tee.id"), primary_key=True, nullable=False)
    hole_number = db.Column(db.Integer, primary_key=True, nullable=False)
    par = db.Column(db.Integer, nullable=False)
    hole_hcp = db.Column(db.Integer, nullable=False)

class Handicap(db.Model):
    __tablename__ = 'handicaps'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    player_id = db.Column(db.Integer, nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    player_hcp = db.Column(db.Float, db.ForeignKey("players.id"), nullable=False)

class Round(db.Model):
    __tablename__ = 'rounds'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    round_number = db.Column(db.Integer, nullable=False)
    round_name = db.Column(db.String(50), nullable=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)

class Match(db.Model):
    __tablename__ = 'matches'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    match_number = db.Column(db.Integer, nullable=False)
    match_time = db.Column(db.Time, nullable=True)
    match_starting_hole = db.Column(db.Integer, nullable=False, server_default="1")
    round_id = db.Column(db.Integer, db.ForeignKey("rounds.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course_tee.id"), nullable=False)
    team_a_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    team_b_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    status = db.Column(db.String(15), nullable=False, server_default='INCOMPLETE')

class Scores(db.Model):
    __tablename__ = 'scores'

    match_id = db.Column(db.Integer, db.ForeignKey("matches.id"), primary_key=True, nullable=False)
    match_hole_number = db.Column(db.Integer, primary_key=True, nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), primary_key=True, nullable=False)
    score = db.Column(db.Integer, nullable=False)

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
        try:
            event_id = Event.query.filter_by(event_name=event_name, group_id=session["group_id"]).first().id
        except AttributeError:
            return apology("event not found")

        
        session["event_id"] = event_id

        return redirect("/event_scoreboard")
    else:
        # Remove any specific event in session
        if session.get("event_id") is not None:
            session.pop("event_id", None)
       

        # Get groupname via session group_id
        try:
            groupname = GolfGroup.query.filter_by(id=session["group_id"]).first().groupname
        except AttributeError:
            return apology("group not found")
        
        # Get events dictionary for group_id
        events = Event.query.filter_by(group_id=session["group_id"]).all()
        
        # Get data for rendering index.html tables of events..
        # Add key to event dictionary for status of each event, showing complete if >0 matches with Complete status
        # and incomplete if any matches are incomplete
        events_with_status = []
        for event in events:
            complete_events_count = 0
            incomplete_events_count = 0
            complete_matches = db.session.query(func.count(Match.status)).filter(
                Match.status == 'COMPLETE', Match.round_id.in_(
                    db.session.query(Round.id).filter(Round.event_id == event.id)
                )
            ).scalar()
            incomplete_matches = db.session.query(func.count(Match.status)).filter(
                Match.status == 'INCOMPLETE', Match.round_id.in_(
                    db.session.query(Round.id).filter(Round.event_id == event.id)
                )
            ).scalar()
            event_dict = {**event.__dict__}
            if complete_matches > 0 and not incomplete_matches:
                event_dict["status"] = "Complete"
                complete_events_count += 1
            else:
                event_dict["status"] = "Incomplete"
                incomplete_events_count += 1
            events_with_status.append(event_dict)

        return render_template("index.html", groupname=groupname, events=events_with_status, complete_events_count=complete_events_count,
            incomplete_events_count=incomplete_events_count)
    

# USE CONTROL K + C TO COMMENT OUT BLOCKS OF CODE
# USE CONTROL K + U TO UNCOMMENT BLOCKS OF CODE
    
@app.route("/register", methods=["GET", "POST"])
def register():
    #"""Register new user"""

    if request.method == "POST":

        # Ensure all fields not blank
        if not request.form.get("username") or not request.form.get("password") or not request.form.get("confirmation"):
            return apology("must provide username and password", 400)

        # Query users table in database for username
        rows = User.query.filter_by(username=request.form.get("username")).all()

        # Check if username already exists in users table, if yes, return apology
        if len(rows) > 0:
            return apology("Username already exists", 400)

        # Check if password matches confirmation, else return apology
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords don't match", 400)

        # Register new user into users database along with hash of their password
        new_user = User(username=request.form.get("username"), 
            hash=generate_password_hash(request.form.get("password")))
        db.session.add(new_user)
        db.session.commit()

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
        rows = User.query.filter_by(username=request.form.get("username")).all()

        # Ensure username exists and password is correct, else return apology
        if len(rows) != 1:
            return apology("invalid username", 400)
        if not check_password_hash(rows[0].hash, request.form.get("password")):
            return apology("invalid password", 400)

        # Remember which user has logged in by storing user_id in session
        session["user_id"] = rows[0].id

        # Redirect user to group route, in order to choose or create a group
        return redirect("/group")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        # Render login.html showing login form
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any data in session
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/group")
@login_required
def group():
    """Show options to join group or create group"""

    # Forget any group_id and event_id in session
    session.pop("group_id", None)
    session.pop("event_id", None)

    # Render group.html showing options to join group or create group
    return render_template("group.html")


@app.route("/group_login",  methods=["GET", "POST"])
@login_required
def group_login():
    """Log into group"""

    # Forget any group_id
    session.pop("group_id", None)

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        if not request.form.get("is_associated"):
            # Ensure groupname was submitted
            groupname = request.form.get("groupname")
            if not groupname:
                return apology("Missing group name.", 400)

            # Ensure password was submitted
            password = request.form.get("password")
            if not password:
                return apology("Missing password.", 400)

            # Query database for groupname
            rows_groups = GolfGroup.query.filter(func.lower(GolfGroup.groupname) == groupname.lower()).all()

            # Ensure username exists and password is correct
            if len(rows_groups) != 1 or not check_password_hash(rows_groups[0].hash, password):
                return apology("Invalid group name and/or password.", 400)

            # Remember which user has logged in and enter into associations table if needed
            session["group_id"] = rows_groups[0].id
            rows_associations = GroupUserAssociation.query.filter_by(user_id=session["user_id"], group_id=session["group_id"]).all()
            if not len(rows_associations):
                new_association = GroupUserAssociation(group_id=session["group_id"], user_id=session["user_id"])
                db.session.add(new_association)
                db.session.commit()
        elif request.form.get("is_associated") == "yes":
            group_id = request.form.get("group_id")
            # Confirm user is associated with group
            rows_associations = GroupUserAssociation.query.filter_by(user_id=session["user_id"], group_id=group_id).all()
            if not len(rows_associations):
                return redirect("/group_login")
            # Add group id to session
            session["group_id"] = group_id

        # Redirect to group homepage
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        # Get any previous groups ids and names associated with user
        group_associations = GolfGroup.query.filter(
            GolfGroup.id.in_(
                db.session.query(GroupUserAssociation.group_id).filter(GroupUserAssociation.user_id == session["user_id"])
            )
        ).all()

        return render_template("group_login.html", group_associations=group_associations)


@app.route("/create_group",  methods=["GET", "POST"])
@login_required
def create_group():
    """ Create new group """

    if request.method == "POST":

       # Ensure all fields not blank
        groupname = request.form.get("groupname")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        if not groupname or not password or not confirmation:
            return apology("Missing group name, password, or confirmation.", 400)

        # Query database for group name
        rows = GolfGroup.query.filter(func.lower(GolfGroup.groupname) == groupname.lower()).all()

        # Check if groupname already exists
        if len(rows) > 0:
            return apology("Group name already exists", 400)

        # Check if password matches confirmation
        if password != confirmation:
            return apology("Passwords don't match.", 400)

        # Register group into groups database
        new_group = GolfGroup(groupname=groupname, hash=generate_password_hash(password)) 
        db.session.add(new_group)
        db.session.commit()

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
            return apology("Missing player name.", 400)

        #Ensure player name doesn't exist within gurrent group
        player_rows = Player.query.filter_by(group_id=session["group_id"], player_name=player_name).all()
        if len(player_rows):
            return apology("Player name already in group", 400)

        #Insert player name into players table
        new_player = Player(player_name=player_name, group_id=session["group_id"])
        db.session.add(new_player)
        db.session.commit()
        
        return redirect("/players")
    
    else:
        group = GolfGroup.query.filter_by(id=session["group_id"]).first()
        if not group:
            return apology("Group not found.", 400)
        players = Player.query.filter_by(group_id=session["group_id"]).all()
        players_with_hcp = []

        for player in players:
            player_dict = {**player.__dict__}         
            try:
                latest_hcp = (db.session.query(Handicap)
                    .join(Event, Handicap.event_id == Event.id)
                    .filter(Handicap.player_id == player.id)
                    .order_by(desc(Event.date))
                    .first())
                player_dict["latest_hcp"] = latest_hcp.player_hcp if latest_hcp else None
            except AttributeError:
                player_dict["latest_hcp"] = None
            players_with_hcp.append(player_dict)

        return render_template("players.html", groupname=group.groupname, players=players_with_hcp, num_players=len(players))
    

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
            return apology("Missing player name or edit/delete option.", 400)

       #If delete, first check retrieve if player has scores
        player = Player.query.filter_by(group_id=session["group_id"], player_name=player_name).first()
        if not player:
            return apology("Player not found.", 400)
        player_scores = Scores.query.filter_by(player_id=player.id).all()
        if len(player_scores):
            return apology("Can't delete player with score history.", 400)

 
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
       
        if not edit_or_delete or not player_name:
            return apology("Missing required fields.", 400)
        
        if edit_or_delete == "edit":
            new_player_name = request.form.get("new_player_name")
            player_to_update = Player.query.filter_by(player_name=player_name, group_id=session["group_id"]).first()
            if player_to_update:
                player_to_update.player_name = new_player_name
                db.session.commit()
        elif edit_or_delete == "delete":
            #Check again no scores
            player_to_delete = Player.query.filter_by(group_id=session["group_id"], player_name=player_name).first()
            if not player_to_delete:
                return apology("Player not found.", 400)
            player_scores = Scores.query.filter_by(player_id=player_to_delete.id).all()
            if len(player_scores):
                return apology("Can't delete player with score history.", 400)
            
            #Delete from players database
            db.session.delete(player_to_delete)
            db.session.commit()
        else:
            return apology("Invalid request. Please select either edit or delete.", 400)
       
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
            return apology("Number of players must be an integer.")
       
       #Send back if pressed enter with 0 players or no event name
        if not num_players or not event_name or not event_date:
            return redirect("/create_event")
        
        # Confim event name doesnt exist in the group already
        event_rows = Event.query.filter_by(event_name=event_name, group_id=session["group_id"]).all()
        if len(event_rows):
            return apology("Event name already exists in group.")
        
        num_teams = math.ceil(num_players / 2)
        team_names = []
        for i in range(num_teams):
            team_names.append(request.form.get("team_name_" + str(i + 1)))
        
        group_players = Player.query.filter_by(group_id=session["group_id"]).all()

        return render_template("create_event_continued.html", event_name=event_name, event_date=event_date,
            num_players=num_players, num_teams=num_teams, team_names=team_names, group_players=group_players)
    else:
        return render_template("create_event.html")

@app.route("/create_event_continued", methods=["GET", "POST"])
@login_required
@group_login_required
def create_event_continued():
    """Create Event - Team Details"""
    
    if request.method != "POST":
        return apology("Invalid request method. Only POST is supported.")

    # Get event header details and error check
    event_name = request.form.get("event_name")
    event_date = request.form.get("event_date")
    if not event_name or not event_date:
        return apology("Both event name and event date must be provided.")
    
    num_teams = int(request.form.get("num_teams"))
    if num_teams < 2:
        return apology("At least 2 teams must be provided.")
    
    # Get team details and error check
    teams = []
    for i in range(num_teams):
        team = {}
        team["team_name"] = request.form.get("team_name_" + str(i))
        team["player_a_id"] = request.form.get("player_a_team_" + str(i))
        team["hcp_player_a"] = request.form.get("hcp_player_a_team_" + str(i))
        team["player_b_id"] = request.form.get("player_b_team_" + str(i))
        team["hcp_player_b"] = request.form.get("hcp_player_b_team_" + str(i))
        teams.append(team)

        if not team["team_name"]:
            return apology("team name blank")
        elif not team["player_a_id"]:
            return apology("need at least 1 player per team")
        elif not team["hcp_player_a"]:
            return apology("player a handicap blank")
        if team["player_b_id"] and not team["hcp_player_b"]:
            return apology("player b handicap blank")

    logging.info(teams)

    # Reconfim event name doesnt exist in the group already
    event_rows = Event.query.filter_by(event_name=event_name, group_id=session["group_id"]).all()
    if len(event_rows):
        return apology("Event name already exists in group.")
    
    # Insert into events table the event name, group id, and date
    new_event = Event(event_name=event_name, group_id=session["group_id"], date=event_date)
    db.session.add(new_event)

    # Insert into teams table all the team names, and event_id
    event_id = new_event.id
    for i in range(num_teams):
        new_team = Team(team_name=teams[i]["team_name"], event_id=event_id)
        db.session.add(new_team)

    # Insert into team_roster table the players on each team; also insert into handicaps table
    # for each player id the event id and player hcp
    for i in range(num_teams):
        team_id = Team.query.filter_by(team_name=teams[i]["team_name"], event_id=event_id).first().id
        player_a_id = teams[i]["player_a_id"]
        new_team_roster_entry = TeamRoster(team_id=team_id, player_id=player_a_id)
        db.session.add(new_team_roster_entry)
        new_handicap = Handicap(player_id=player_a_id, event_id=event_id, player_hcp=teams[i]["hcp_player_a"])
        db.session.add(new_handicap)
        if teams[i]["player_b_id"]:
            player_b_id = teams[i]["player_b_id"]
            new_team_roster_entry = TeamRoster(team_id=team_id, player_id=player_b_id)
            db.session.add(new_team_roster_entry)
            new_handicap = Handicap(player_id=player_b_id, event_id=event_id, player_hcp=teams[i]["hcp_player_b"])
            db.session.add(new_handicap)
    
    db.session.commit()

    return redirect("/")


# @app.route("/event_structure", methods=["GET", "POST"])
# @login_required
# @group_login_required
# @event_selected
# def event_structure():
#     """Event Details"""

#     if request.method == "POST":
#         # Get new round name (optional)
#         new_round_name = request.form.get("new_round_name")
#         # Get course selection
#         course_id_selected = request.form.get("course_select")
#         if not course_id_selected:
#             return apology("no course selected")
#         # Get round number
#         round_number = int(request.form.get("num_rounds_input")) + 1
#         # Get teams and matches
#         num_teams = int(db.execute("SELECT COUNT(*) as count FROM teams WHERE event_id = ?", session["event_id"])[0]["count"])
#         num_matches = int(num_teams / 2)
#         matches = []
#         for i in range(num_matches):
#             team_a_id = int(request.form.get("team_a_match_" + str(i + 1)))
#             team_b_id = int(request.form.get("team_b_match_" + str(i + 1)))
#             if not team_a_id or not team_b_id:
#                 return apology("team not selected - match " + str(i + 1))
#             matches.append({"match_number": i + 1, "team_a": team_a_id, "team_b": team_b_id})
        
#         # Insert new round into rounds table
#         db.execute("INSERT INTO rounds (round_number, round_name, event_id) VALUES (?, ?, ?)",
#             round_number, new_round_name, session["event_id"])
#         # Get round id
#         round_id = db.execute("SELECT MAX(id) FROM rounds WHERE event_id = ?", session["event_id"])[0]["MAX(id)"]
#         # Insert matches into matches table
#         for match in matches:
#             db.execute("INSERT INTO matches (match_number, match_starting_hole, round_id, course_id," +
#                 "team_a_id, team_b_id) VALUES (?, ?, ?, ?, ?, ?)", match["match_number"], 1, round_id,
#                 course_id_selected, match["team_a"], match["team_b"])

#         return redirect("/event_structure")
#     else:
#         # Get event data needed to display and structure matches in rounds
#         rounds = db.execute("SELECT * FROM rounds WHERE event_id = ? ORDER BY round_number ASC", session["event_id"])
#         # Built list of dictionaries for each round with round number, round name, and matches (match number, team a, team b, team a score, team b score)
#         for round in rounds:
#             matches = db.execute("SELECT * FROM matches WHERE round_id = ?", round["id"])
#             round["matches"] = []
#             for match in matches:
#                 team_a = db.execute("SELECT * FROM teams WHERE id = ?", match["team_a_id"])[0]["team_name"]
#                 team_b = db.execute("SELECT * FROM teams WHERE id = ?", match["team_b_id"])[0]["team_name"]
#                 course_name = db.execute("SELECT * FROM course_tee WHERE id = ?", match["course_id"])[0]["name"]
#                 course_tees = db.execute("SELECT * FROM course_tee WHERE id = ?", match["course_id"])[0]["teebox"]
#                 round["matches"].append({"match_number": match["match_number"], "course_name": course_name + " - " +course_tees + " Tees",
#                      "team_a": team_a, "team_b": team_b, "team_a_score": "create fn", "team_b_score": "create fn"})
       
#         num_teams = db.execute("SELECT COUNT(*) as count FROM teams WHERE event_id = ?", session["event_id"])[0]["count"]
#         event_name = db.execute("SELECT event_name FROM events WHERE id = ?", session["event_id"])[0]["event_name"]
#         teams = db.execute("SELECT * FROM teams WHERE event_id = ?", session["event_id"])

#         return render_template("event_structure.html", rounds=rounds, num_teams=num_teams, event_name=event_name,
#             teams=teams)

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

# @app.route("/courseadmin", methods=["GET", "POST"])
# @login_required
# def course_admin():
#     """Add courses to database in admin mode"""
#     if request.method == "POST":
#         # Get course name
#         course_name = request.form.get("new_course_name")
#         if not course_name:
#             return apology("no course name")
#         # Get course tees
#         course_tees = request.form.get("course_tees")
#         if not course_tees:
#             return apology("no course tees")
#         # Get course slope
#         course_slope = request.form.get("course_tee_slope")
#         # Make sure course slope is not blank and is an integer betwee 55 and 155
#         if not course_slope:
#             return apology("no course slope")
#         try:
#             course_slope = int(course_slope)
#             if course_slope < 55 or course_slope > 155:
#                 return apology("course slope must be between 55 and 155")
#         except ValueError:
#             return apology("course slope must be an integer")
#         # Get course rating
#         course_rating = request.form.get("course_tee_rating")
#         # Make sure course rating is not blank and is a float between 50 and 80
#         if not course_rating:
#             return apology("no course rating")
#         try:
#             course_rating = float(course_rating)
#             if course_rating < 50 or course_rating > 80:
#                 return apology("course rating must be between 50 and 80")
#         except ValueError:
#             return apology("course rating must be a float")
        
#         # Loop through all 18 holes, get par and handicap for each hole
#         holes = []
#         for i in range(1, 19):
#             par = request.form.get("hole_par_" + str(i))
#             if not par:
#                 return apology("no par for hole " + str(i))
#             try:
#                 par = int(par)
#             except ValueError:
#                 return apology("par for hole " + str(i) + " must be an integer")
#             handicap = request.form.get("hole_hcp_" + str(i))
#             if not handicap:
#                 return apology("no handicap for hole " + str(i))
#             try:
#                 handicap = int(handicap)
#             except ValueError:
#                 return apology("handicap for hole " + str(i) + " must be an integer")
#             holes.append({"hole": i, "par": par, "handicap": handicap})
        
#         # Insert course into courses table
#         db.execute("INSERT INTO course_tee (name, teebox, rating, slope) VALUES (?, ?, ?, ?)",
#             course_name, course_tees, course_rating, course_slope)
#         # Get course id
#         course_id = db.execute("SELECT MAX(id) FROM course_tee WHERE name = ? AND teebox = ?", 
#             course_name, course_tees)[0]["MAX(id)"]
#         # Insert holes into holes table
#         for hole in holes:
#             db.execute("INSERT INTO holes (course_id, hole_number, par, hole_hcp) VALUES (?, ?, ?, ?)",
#                 course_id, hole["hole"], hole["par"], hole["handicap"])
             
#         return redirect("/")
#     else:
#         return render_template("course_input.html")
    
# @app.route('/api/courses', methods=['GET'])
# def get_courses():
#     # Query the database for all courses
#     courses = db.execute("SELECT * FROM course_tee")

#     # Convert the list of Course objects to a list of dictionaries
#     courses_list = [{"id": course["id"], "name": course["name"] + " - " + course["teebox"] + " " +
#         str(course["rating"]) + "/" + str(course["slope"])} for course in courses]

#     # Return the list of courses as JSON
#     return jsonify(courses_list)

# @app.route('/scorecard', methods=['GET', 'POST'])
# def scorecard():

#     if request.method == "POST":
        
#         # Get round number
#         round_number = request.form.get("round_number")
        
#         # Get match number
#         match_number = request.form.get("match_number")
        
#         # Error check for round and match number
#         if not round_number or not match_number:
#             return apology("round or match number not sent in POST request")
        
#         # Clear previous and add round number and match number to session
#         session.pop("round", None)
#         session.pop("match", None)
#         session["round_number"] = round_number
#         session["match_number"] = match_number
#     else:
#         # Get round number and match number from session
#         round_number = session["round_number"]
#         match_number = session["match_number"]

#         # If round number or match number not in session, return apology
#         if not round_number or not match_number:
#             redirect("/event_structure")

#     # Get round id and match id 
#     round_id = db.execute("SELECT id FROM rounds WHERE event_id = ? AND round_number = ?", 
#         session["event_id"], round_number)[0]["id"]
#     match_id = db.execute("SELECT id FROM matches WHERE round_id = ? AND match_number = ?", 
#         round_id, match_number)[0]["id"]
#     match_data = {"match_number": match_number, "match_id": match_id}

#     # Get event name
#     event_name = db.execute("SELECT event_name FROM events WHERE id = ?", session["event_id"])[0]["event_name"]
    
#     # Get course id and display name
#     course_id = db.execute("SELECT course_id FROM matches WHERE id = ?", match_id)[0]["course_id"]
#     course_name = db.execute("SELECT name FROM course_tee WHERE id = ?", course_id)[0]["name"]
#     course_tee = db.execute("SELECT teebox FROM course_tee WHERE id = ?", course_id)[0]["teebox"]
#     course_display_name = course_name + " - " + course_tee + " Tees"
    
#     # Get team and player names
#     team_a_id = db.execute("SELECT team_a_id FROM matches WHERE id = ?", match_id)[0]["team_a_id"]
#     team_b_id = db.execute("SELECT team_b_id FROM matches WHERE id = ?", match_id)[0]["team_b_id"]
#     team_a_name = db.execute("SELECT team_name FROM teams WHERE id = ?", team_a_id)[0]["team_name"]
#     team_b_name = db.execute("SELECT team_name FROM teams WHERE id = ?", team_b_id)[0]["team_name"]
#     team_a_players = db.execute("SELECT * FROM players WHERE id IN " +
#         "(SELECT player_id FROM team_roster WHERE team_id = ?)", team_a_id)
#     team_b_players = db.execute("SELECT * FROM players WHERE id IN " +
#         "(SELECT player_id FROM team_roster WHERE team_id = ?)", team_b_id)
#     team_data = {"team_a_name": team_a_name, "team_a_players": team_a_players, "team_b_name": team_b_name, "team_b_players": team_b_players}
    
#     # Get course holes
#     holes = db.execute("SELECT * FROM holes WHERE course_id = ? ORDER BY hole_number ASC", course_id)
#     # For each hole in holes, get the score for each player in team a and team b, keep track of total par
#     total_par = {"front_9_par": 0, "back_9_par": 0, "total_18_par": 0}
#     for hole in holes:
#         hole["team_a_scores"] = []
#         hole["team_b_scores"] = []
#         for player in team_a_players:
#             player_id = db.execute("SELECT id FROM players WHERE player_name = ? AND group_id = ?", player["player_name"],
#                 session["group_id"])[0]["id"]
#             score = db.execute("SELECT score FROM scores WHERE player_id = ? AND match_id = ? AND match_hole_number = ?", 
#                 player_id, match_id, hole["hole_number"])
#             if score:
#                 hole["team_a_scores"].append(score[0]["score"])
#             else:
#                 hole["team_a_scores"].append("-")
#         for player in team_b_players:
#             player_id = db.execute("SELECT id FROM players WHERE player_name = ? AND group_id = ?", player["player_name"],
#                 session["group_id"])[0]["id"]
#             score = db.execute("SELECT score FROM scores WHERE player_id = ? AND match_id = ? AND match_hole_number = ?", 
#                 player_id, match_id, hole["hole_number"])
#             if score:
#                 hole["team_b_scores"].append(score[0]["score"])
#             else:
#                 hole["team_b_scores"].append("-")
#         # Sum par for front 9, back 9, and total 18 holes
#         if hole["hole_number"] < 10:
#             total_par["front_9_par"] += hole["par"]
#         else:
#             total_par["back_9_par"] += hole["par"]
#         total_par["total_18_par"] += hole["par"]


#     # Calculate player totals for front 9, back 9, and total 18 holes
#     for player in team_a_players:
#         player["front_9_total"] = 0
#         player["back_9_total"] = 0
#         player["total_18"] = 0
#         for i in range(1, 19):
#             score = db.execute("SELECT score FROM scores WHERE player_id = ? AND match_id = ? AND match_hole_number = ?", 
#                 player["id"], match_id, i)
#             if score:
#                 if i < 10:
#                     player["front_9_total"] += score[0]["score"]
#                 else:
#                     player["back_9_total"] += score[0]["score"]
#                 player["total_18"] += score[0]["score"]
#     for player in team_b_players:
#         player["front_9_total"] = 0
#         player["back_9_total"] = 0
#         player["total_18"] = 0
#         for i in range(1, 19):
#             score = db.execute("SELECT score FROM scores WHERE player_id = ? AND match_id = ? AND match_hole_number = ?", 
#                 player["id"], match_id, i)
#             if score:
#                 if i < 10:
#                     player["front_9_total"] += score[0]["score"]
#                 else:
#                     player["back_9_total"] += score[0]["score"]
#                 player["total_18"] += score[0]["score"]
 
#     # Collect team data for scorecard
#     team_data = {"team_a_name": team_a_name, "team_a_players": team_a_players, "team_b_name": team_b_name, "team_b_players": team_b_players}
    
#     return render_template("scorecard.html", event_name=event_name, course_display_name=course_display_name,
#         round_number=round_number, match_data=match_data, holes=holes, team_data=team_data, total_par=total_par)
    
    
# @app.route('/scorecard_edit', methods=['GET', 'POST'])
# def scorecard_edit():
 
#     if request.method == "POST":

#         # Get match id and player id
#         match_id = request.form.get("match_id")
#         player_id = request.form.get("player_id")
#         player_name = db.execute("SELECT player_name FROM players WHERE id = ?", player_id)[0]["player_name"]

#         # Get course id and display name
#         course_id = db.execute("SELECT course_id FROM matches WHERE id = ?", match_id)[0]["course_id"]
#         course_name = db.execute("SELECT name FROM course_tee WHERE id = ?", course_id)[0]["name"]
#         course_tee = db.execute("SELECT teebox FROM course_tee WHERE id = ?", course_id)[0]["teebox"]
#         course_display_name = course_name + " - " + course_tee + " Tees"

#         # Get course holes
#         holes = db.execute("SELECT * FROM holes WHERE course_id = ? ORDER BY hole_number ASC", course_id)

#         # For each hole, append the score for the player_id if it exists, else leave blank
#         for hole in holes:
#             score = db.execute("SELECT score FROM scores WHERE player_id = ? AND match_id = ? AND match_hole_number = ?", 
#                 player_id, match_id, hole["hole_number"])
#             if score:
#                 hole["score"] = score[0]["score"]
#             else:
#                 hole["score"] = None

#         return render_template("scorecard_edit.html", holes=holes, course_display_name=course_display_name, 
#             match_id=match_id, player_id=player_id, player_name=player_name)
#     else:
#         return redirect("/event_structure")

# @app.route('/scorecard_processing', methods=['GET', 'POST'])
# def scorecard_processing():
 
#     if request.method == "POST":
            
#         # Get match id and player id and hcp
#         match_id = request.form.get("match_id")
#         player_id = request.form.get("player_id")

#         # Get course id
#         course_id = db.execute("SELECT course_id FROM matches WHERE id = ?", match_id)[0]["course_id"]

#         # For each hole, get the score and update the scores table, checking if score exits and updating if so
#         for i in range(1, 19):
#             score = int(request.form.get("score_hole_" + str(i)))
#             if score and score > 0:
#                 score_rows = db.execute("SELECT * FROM scores WHERE player_id = ? AND match_id = ? AND match_hole_number = ?", 
#                     player_id, match_id, i)
#                 if score_rows:
#                     db.execute("UPDATE scores SET score = ? WHERE player_id = ? AND match_id = ? AND match_hole_number = ?", 
#                         score, player_id, match_id, i)
#                 else:   
#                     db.execute("INSERT INTO scores (match_id, match_hole_number, player_id, score) VALUES (?, ?, ?, ?)",
#                         match_id, i, player_id, score)
        
#         return redirect("/scorecard")

#     else:
#         return redirect("/event_structure")