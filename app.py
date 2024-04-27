import os, math

from cs50 import SQL
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from flask import Flask, jsonify, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import logging

from helpers import (apology, login_required, 
                     group_login_required, event_selected, usd, 
                     format_positive, format_none, playing_hcp, 
                     check_bet_availability)

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

# SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://root:password123@localhost:3306/FD2024".format(
#     username="root",
#     password="password123",
#     hostname="localhost",
#     databasename="FD2024",
# )


# Confirgure database connection for pythonanywhere
SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://tjg14:TJGfd2024@tjg14.mysql.pythonanywhere-services.com:3306/tjg14$FD2024".format(
    username="tjg14",
    password="TJGfd2024",
    hostname="tjg14.mysql.pythonanywhere-services.com",
    databasename="tjg14$FD2024",
)

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
    username = db.Column(db.String(30), unique=True, nullable=False)
    hash = db.Column(db.String(255), nullable=False)

class GolfGroup(db.Model):
    __tablename__ = 'golf_groups'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    groupname = db.Column(db.String(50), unique=True, nullable=False)
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

    handicaps = db.relationship('Handicap', backref='players')

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

    # Define a relationship to the Player model
    players = db.relationship('Player', secondary='team_roster', backref='teams')

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
    front_9_par = db.Column(db.Integer, nullable=False)
    back_9_par = db.Column(db.Integer, nullable=False)
    total_18_par = db.Column(db.Integer, nullable=False)

    holes = db.relationship('Hole', backref='coursetee')

class Hole(db.Model):
    __tablename__ = 'holes'

    course_id = db.Column(db.Integer, db.ForeignKey("course_tee.id"), primary_key=True, nullable=False)
    hole_number = db.Column(db.Integer, primary_key=True, nullable=False)
    par = db.Column(db.Integer, nullable=False)
    hole_hcp = db.Column(db.Integer, nullable=False)

class Handicap(db.Model):
    __tablename__ = 'handicaps'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    player_hcp = db.Column(db.Float, nullable=False)

class Round(db.Model):
    __tablename__ = 'rounds'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    round_number = db.Column(db.Integer, nullable=False)
    round_name = db.Column(db.String(50), nullable=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)

    matches = db.relationship('Match', backref='round')

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

    team_a = db.relationship('Team', foreign_keys=[team_a_id])
    team_b = db.relationship('Team', foreign_keys=[team_b_id])
    course_tee = db.relationship('CourseTee')

class Scores(db.Model):
    __tablename__ = 'scores'

    match_id = db.Column(db.Integer, db.ForeignKey("matches.id"), primary_key=True, nullable=False)
    match_hole_number = db.Column(db.Integer, primary_key=True, nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), primary_key=True, nullable=False)
    score = db.Column(db.Integer, nullable=False)

class Bets(db.Model):
    __tablename__ = 'bets'

    match_id = db.Column(db.Integer, db.ForeignKey("matches.id"), primary_key=True, nullable=False)
    match_hole_number = db.Column(db.Integer, primary_key=True, nullable=False)
    front_9_bets = db.Column(db.Integer)
    back_9_bets = db.Column(db.Integer)
    total_18_bets = db.Column(db.Integer)


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
        # Add key to event dictionary for status of each event, 
        # showing complete if >0 matches with Complete status
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

        return render_template("index.html", 
                               groupname=groupname, 
                               events=events_with_status, 
                               complete_events_count=complete_events_count,
                               incomplete_events_count=incomplete_events_count
                               )
    
    
@app.route("/register", methods=["GET", "POST"])
def register():
    #"""Register new user"""

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        # Ensure all fields not blank
        if not username or not password or not confirmation:
            return apology("Missing username, password, or confirmation.", 400)

        # Convert username to lowercase
        username = username.lower()

        # Check if password matches confirmation, else return apology
        if password != confirmation:
            return apology("Passwords don't match", 400)

        # Register new user into users database along with hash of their password
        # Using unique constraint to make sure username doesn't already exist
        try:
            new_user = User(username=username, 
                            hash=generate_password_hash(password))
            db.session.add(new_user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return apology("Username already exists", 400)

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
            rows_groups = (GolfGroup.query
                           .filter(func.lower(GolfGroup.groupname) == groupname.lower())
                           .all()
                           )

            # Ensure username exists and password is correct
            if (len(rows_groups) != 1 
                or not check_password_hash(rows_groups[0].hash, password)):
                return apology("Invalid group name and/or password.", 400)

            # Remember which user has logged in 
            # and enter into associations table if needed
            session["group_id"] = rows_groups[0].id
            rows_associations = (GroupUserAssociation.query
                                 .filter_by(user_id=session["user_id"], group_id=session["group_id"])
                                 .all()
                                 )
            if not len(rows_associations):
                new_association = GroupUserAssociation(
                    group_id=session["group_id"], 
                    user_id=session["user_id"])
                db.session.add(new_association)
                db.session.commit()
        elif request.form.get("is_associated") == "yes":
            group_id = request.form.get("group_id")
            # Confirm user is associated with group
            rows_associations = (GroupUserAssociation.query
                                 .filter_by(user_id=session["user_id"], group_id=group_id)
                                 .all()
                                 )
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

        # Convert groupname to lower case
        groupname = groupname.lower()

        # Check if password matches confirmation
        if password != confirmation:
            return apology("Passwords don't match.", 400)

        # Register group into groups database, using unique constraint to catch if already exists
        try:    
            new_group = GolfGroup(groupname=groupname, hash=generate_password_hash(password)) 
            db.session.add(new_group)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return apology("Group name already exists", 400)

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

        return render_template("players.html", 
                               groupname=group.groupname, 
                               players=players_with_hcp, 
                               num_players=len(players)
                               )
    

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

 
        return render_template("edit_delete_player.html", 
                               player_name=player_name, 
                               edit_or_delete=edit_or_delete
                               )
    
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
            player_to_update = (Player.query
                                .filter_by(player_name=player_name, group_id=session["group_id"])
                                .first()
                                )
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
    event_rows = (Event.query
                  .filter_by(event_name=event_name, group_id=session["group_id"])
                  .all())
    if len(event_rows):
        return apology("Event name already exists in group.")
    
    # Insert into events table the event name, group id, and date
    new_event = Event(event_name=event_name, 
                  group_id=session["group_id"], 
                  date=event_date)
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


@app.route("/event_structure", methods=["GET", "POST"])
@login_required
@group_login_required
@event_selected
def event_structure():
    """Event Details"""

    if request.method == "POST":
        
        new_round_name = request.form.get("new_round_name")
        course_id_selected = request.form.get("course_select")
        if not course_id_selected:
            return apology("No course selected")
        
        num_rounds_input = request.form.get("num_rounds_input")
        if num_rounds_input is not None:
            round_number = int(num_rounds_input) + 1
        else:
            return apology("Round number not sent in POST request")
        
        num_teams = Team.query.filter_by(event_id=session["event_id"]).count()
        num_matches = int(num_teams / 2)
        matches = []
        for i in range(num_matches):
            team_a_id = int(request.form.get("team_a_match_" + str(i + 1)))
            team_b_id = int(request.form.get("team_b_match_" + str(i + 1)))
            if not team_a_id or not team_b_id:
                return apology("Team not selected in match " + str(i + 1))
            matches.append({
                "match_number": i + 1, 
                "team_a": team_a_id, 
                "team_b": team_b_id
            })
        
        # Insert new round details into rounds table
        new_round = Round(round_number=round_number, 
                          round_name=new_round_name, 
                          event_id=session["event_id"])
        db.session.add(new_round)
        db.session.commit()
        
        round_id = new_round.id
        
        # Insert matches into matches table
        for match in matches:
            new_match = Match(match_number=match["match_number"], 
                              match_starting_hole=1,
                              round_id=round_id, 
                              course_id=course_id_selected, 
                              team_a_id=match["team_a"], 
                              team_b_id=match["team_b"])
            db.session.add(new_match)
        db.session.commit()
        
        return redirect("/event_structure")
    else:
        # Get event data needed to display and structure matches in rounds

        rounds = (Round.query
                  .filter_by(event_id=session["event_id"])
                  .order_by(Round.round_number)
                  .all())
        
        rounds_data = []
        for round in rounds:
            matches = (Match.query
               .options(
                   joinedload(Match.team_a), 
                   joinedload(Match.team_b), 
                   joinedload(Match.course_tee)
                )
               .filter_by(round_id=round.id)
               .all())
            
            matches_data = []
            for match in matches:
                team_a = match.team_a.team_name
                team_b = match.team_b.team_name
                course_name = match.course_tee.name
                course_tees = match.course_tee.teebox
                matches_data.append({
                    "match_number": match.match_number, 
                    "course_name": course_name + " - " +course_tees + " Tees",
                    "team_a": team_a, 
                    "team_b": team_b, 
                    "team_a_score": "create fn", 
                    "team_b_score": "create fn"
                })
            
            round_data = {
                "round_number": round.round_number, 
                "round_name": round.round_name, 
                "matches": matches_data
            }
            rounds_data.append(round_data)
       
        num_teams = Team.query.filter_by(event_id=session["event_id"]).count()
        event_name = Event.query.filter_by(id=session["event_id"]).first().event_name
        teams = Team.query.filter_by(event_id=session["event_id"]).all()

        if not rounds_data:
            return apology("No rounds found")
        
        return render_template("event_structure.html", 
                               rounds=rounds_data, 
                               num_teams=num_teams, 
                               event_name=event_name,
                               teams=teams)

@app.route("/event_scoreboard", methods=["GET", "POST"])
@login_required
@group_login_required
@event_selected
def event_scoreboard():
    """Event Scoreboard"""
  
    # Get event name
    event = Event.query.get(session["event_id"])
    if not event:
        return apology("Event not found")
    event_name = event.event_name

    # Get all rounds for the event
    rounds = (Round.query
              .filter_by(event_id=session["event_id"])
              .order_by(Round.round_number)
              .all())
    if not rounds:
        return apology("No Rounds Found")
    
    # Get all teams and players for the event
    teams = (Team.query
             .filter_by(event_id=session["event_id"])
             .options(joinedload(Team.players))
             .all())
    
    # Get all matches for the rounds in the event
    matches = (Match.query
               .filter(Match.round_id.in_([round.id for round in rounds]))
               .all())

    # Get all courses played in all the matches in the event's rounds
    courses = (CourseTee.query
                .filter(CourseTee.id.in_([match.course_id for match in matches]))
                .all())
    
    # Get all the handicaps for players in the event
    hcp_indexes = (Handicap.query
                    .filter_by(event_id=session["event_id"])
                    .all())
    
    # Get all the scores in all the matches in the event's rounds
    scores = (Scores.query
                .filter(Scores.match_id.in_([match.id for match in matches]))
                .all())

    # Initialize an empty list to store round data
    rounds_data = []
    cumulative_totals = {}

    # For each round in rounds
    for round in rounds:
        # Initialize an empty dictionary to store team data
        team_data = {}
        # For each team in teams
        for team in teams:
            # Initialize total net score for team
            team_total_net_score = 0
            # Find the match in matches object that corresponds to the team and round
            match = next((match for match in matches if match.round_id == round.id and (match.team_a_id == team.id or match.team_b_id == team.id)), None)
            # Find what course the team played during this round
            course_for_match = next((course for course in courses if course.id == match.course_id), None)
            # Create a list of dictionaries for each player in the team, and add the player's playing handicap
            players = [{"player_id": player.id, "player_name": player.player_name} for player in team.players]
            for player in players:
                player_index = next((hcp.player_hcp for hcp in hcp_indexes if hcp.player_id == player["player_id"]), None)
                if player_index:
                    course_hcp = player_index * float(course_for_match.slope) / 113 + (course_for_match.rating - course_for_match.total_18_par)
                    player["playing_hcp"] = int(min(__builtins__["round"](course_hcp * 0.85, 0), 18))
                else:
                    player["playing_hcp"] = None
            
            # For each hole in holes
            for hole in course_for_match.holes:
                # Get hole hcp
                hole_hcp = hole.hole_hcp
                net_scores_on_hole = []
                for player in players:
                    # Get player hcp
                    player_hcp = player["playing_hcp"]
                    # Calculate player strokes
                    player_strokes = 1 if hole_hcp <= player_hcp else 0
                    # Get player net score (needs match id, hole number, player id)
                    score = next((score for score in scores if score.match_id == match.id and score.match_hole_number == hole.hole_number and score.player_id == player["player_id"]), None)
                    if score:
                        player_net = score.score - player_strokes - hole.par
                    else:
                        player_net = None
                    # Add to net scores on hole list
                    net_scores_on_hole.append(player_net)
                # Add lowest of two net scores to team total net score
                # Filter out None values from net_scores_on_hole
                filtered_scores = [score for score in net_scores_on_hole if score is not None]
                if filtered_scores:
                    team_total_net_score += min(filtered_scores)
                    
            # Store the total net score for the team in team_data
            team_data[team.team_name] = team_total_net_score
            # Update the cumulative total for the team
            if team.team_name in cumulative_totals:
                cumulative_totals[team.team_name] += team_total_net_score
            else:
                cumulative_totals[team.team_name] = team_total_net_score

        # Store the round number and team data in rounds_data
        rounds_data.append({
            "round_number": round.round_number,
            "team_data": team_data
        })

    
    return render_template("leaderboard.html",
                           event_name=event_name,
                           rounds_data=rounds_data,
                           teams=teams,
                           cumulative_totals=cumulative_totals
    )

@app.route("/courseadmin", methods=["GET", "POST"])
@login_required
def course_admin():
    """Add courses to database in admin mode"""
    
    if request.method == "POST":
        course_name = request.form.get("new_course_name")
        if not course_name:
            return apology("no course name")

        course_tees = request.form.get("course_tees")
        if not course_tees:
            return apology("no course tees")

        course_slope = request.form.get("course_tee_slope")
        if not course_slope:
            return apology("no course slope")
        
        try:
            course_slope = int(course_slope)
            if course_slope < 55 or course_slope > 155:
                return apology("Course slope must be between 55 and 155")
        except ValueError:
            return apology("Course slope must be an integer")
       
        course_rating = request.form.get("course_tee_rating")
        if not course_rating:
            return apology("no course rating")
        
        try:
            course_rating = float(course_rating)
            if course_rating < 50 or course_rating > 80:
                return apology("Course rating must be between 50 and 80")
        except ValueError:
            return apology("Course rating must be a float")
        
        # Loop through all 18 holes, get par and handicap for each hole
        front_9_par = 0
        back_9_par = 0
        total_18_par = 0
        holes = []
        for i in range(1, 19):
            par = request.form.get("hole_par_" + str(i))
            if not par:
                return apology("Must have par for hole " + str(i))
            try:
                par = int(par)
            except ValueError:
                return apology("Par for hole " + str(i) + " must be an integer")
            # Keep track of total par for front 9, back 9, and 18 holes
            if i <= 9:
                front_9_par += par
            else:
                back_9_par += par
            total_18_par += par

            handicap = request.form.get("hole_hcp_" + str(i))
            if not handicap:
                return apology("Must have handicap for hole " + str(i))
            try:
                handicap = int(handicap)
            except ValueError:
                return apology("Handicap for hole " + str(i) + " must be an integer")
            holes.append({"hole_number": i, "par": par, "hole_hcp": handicap})
            
        # Insert course into courses table
        new_course = CourseTee(name=course_name, 
                               teebox=course_tees, 
                               rating=course_rating, 
                               slope=course_slope,
                               front_9_par=front_9_par,
                               back_9_par=back_9_par,
                               total_18_par=total_18_par
                               )
        db.session.add(new_course)
        db.session.commit()
        course_id = new_course.id

        # Insert holes into holes table
        for hole in holes:
            new_hole = Hole(course_id=course_id, 
                            hole_number=hole["hole_number"], 
                            par=hole["par"], 
                            hole_hcp=hole["hole_hcp"]
                            ) 
            db.session.add(new_hole)
        db.session.commit()
        
        return redirect("/")
    else:
        return render_template("course_input.html")
    
@app.route('/api/courses', methods=['GET'])
def get_courses():
    """Get a list of courses and their teeboxes, ratings, and slopes"""
    
    courses = CourseTee.query.filter_by(active=1).all()

    # Convert the list of Course objects to a list of dictionaries
    courses_list = [
        {
            "id": course.id, 
            "name": (
                course.name + " - " + course.teebox + " " +
                str(course.rating) + "/" + str(course.slope)
            )
        } 
        for course in courses
    ]

    # Return the list of courses as JSON
    return jsonify(courses_list)

@app.route('/scorecard', methods=['GET', 'POST'])
@login_required
@group_login_required
@event_selected
def scorecard():

    if request.method == "POST":

        round_number = request.form.get("round_number")
        match_number = request.form.get("match_number")
        print("running post")
        print("round_number:", round_number)
        print("match_number:", match_number)
        if not round_number or not match_number:
            return apology("Round or match number not sent in POST request")
        
        # Clear previous and add round number and match number to session
        session.pop("round_number", None)
        session.pop("match_number", None)
        session["round_number"] = round_number
        session["match_number"] = match_number
    else:
        round_number = session["round_number"]
        match_number = session["match_number"]
        if not round_number or not match_number:
            return redirect("/event_structure")

    round = (Round.query
         .options(joinedload(Round.matches))
         .filter_by(event_id=session["event_id"], round_number=round_number)
         .first())
    if not round:
        return apology("Round not found")

   # Print out round.matches and match_number for debugging
    print("round.matches:", [m.match_number for m in round.matches])
    print("match_number:", match_number)

   
   # Find match in round returned
    match = next((m for m in round.matches if m.match_number == int(match_number)), None)
    if not match:
        return apology("Match not found")

    match_data = {"match_number": match_number, "match_id": match.id}

    event = Event.query.get(session["event_id"])
    if not event:
        return apology("Event not found")
    event_name = event.event_name
    
    course = CourseTee.query.get(match.course_id)
    if not course:
        return apology("Course not found")
    
    # Get team and player names for match
    team_a = Team.query.options(joinedload(Team.players)).get(match.team_a_id)
    if not team_a:
        return apology("Team A not found")

    team_b = Team.query.options(joinedload(Team.players)).get(match.team_b_id)
    if not team_b:
        return apology("Team B not found")

    team_data = {
        "team_a_name": team_a.team_name, 
        "team_a_players": [{**player.__dict__} for player in team_a.players], 
        "team_b_name": team_b.team_name, 
        "team_b_players": [{**player.__dict__} for player in team_b.players]
    }
    
    # Get scores for all players in the match
    scores = (Scores.query
              .filter(Scores.player_id.in_([p.id for p in team_a.players + team_b.players]), 
                      Scores.match_id == match.id)
              .all()
             )
    # Create a dictionary to easily look up scores
    scores_dict = {(s.player_id, s.match_hole_number): s for s in scores}

    # Add handicap for each player on team a and team b
    for player in team_data["team_a_players"] + team_data["team_b_players"]:
        hcp_index = (Handicap.query
                     .filter_by(player_id=player["id"], event_id=session["event_id"])
                     .first()
                     .player_hcp
                    )
        course_hcp = hcp_index * float(course.slope) / 113 + (course.rating - course.total_18_par)
        playing_hcp = int(min(__builtins__["round"](course_hcp * 0.85, 0), 18))
        player["hcp"] = playing_hcp
        player["front_9_total"] = 0
        player["back_9_total"] = 0
        player["total_18"] = 0
        
    
    # Get course holes
    holes = (Hole.query
             .filter_by(course_id=course.id)
             .order_by(Hole.hole_number.asc())
             .all()
             )
    
    # For each hole in holes, get the score for each player in team a and team b
    holes_dicts = []
    for hole in holes:
        hole_dict = {**hole.__dict__, 
                     "team_a_scores": [], 
                     "team_a_net": None,
                     "team_b_scores": [],
                     "team_b_net": None
                     }
        hole_hcp = int(hole_dict["hole_hcp"])
        hole_par = int(hole_dict["par"])
        if not hole_hcp:
            return apology("Missing hole hcp reference")
        
        
        team_players_keys = [
            (team_data["team_a_players"], "team_a"), 
            (team_data["team_b_players"], "team_b")
        ]
        for team_players, team_key in team_players_keys:
            for player in team_players:
                score = scores_dict.get((player["id"], hole.hole_number))
                strokes = 1 if player["hcp"] >= hole_hcp else 0
                if score:
                    hole_dict[f"{team_key}_scores"].append(score.score)
                    new_net = score.score - strokes - hole_par
                    team_net = hole_dict[f"{team_key}_net"]
                    if team_net is None or new_net < team_net:
                        hole_dict[f"{team_key}_net"] = new_net
                    # Calculate player totals
                    if hole.hole_number < 10:
                        player["front_9_total"] += score.score
                    else:
                        player["back_9_total"] += score.score
                    player["total_18"] += score.score
                else:
                    hole_dict[f"{team_key}_scores"].append("-")
        holes_dicts.append(hole_dict)

    # Initialize net score totals
    team_a_net_totals = {"front_9": 0, "back_9": 0, "total_18": 0}
    team_b_net_totals = {"front_9": 0, "back_9": 0, "total_18": 0}

    # Calculate net score totals
    for hole in holes_dicts:
        if hole["team_a_net"] is not None:
            if hole["hole_number"] <= 9:
                team_a_net_totals["front_9"] += hole["team_a_net"]
            else:
                team_a_net_totals["back_9"] += hole["team_a_net"]
            team_a_net_totals["total_18"] += hole["team_a_net"]
        if hole["team_b_net"] is not None:
            if hole["hole_number"] <= 9:
                team_b_net_totals["front_9"] += hole["team_b_net"]
            else:
                team_b_net_totals["back_9"] += hole["team_b_net"]
            team_b_net_totals["total_18"] += hole["team_b_net"]


    return render_template("scorecard_view.html", 
                           event_name=event_name, 
                           course=course,
                           round_number=round_number, 
                           match_data=match_data, 
                           holes=holes_dicts, 
                           team_data=team_data,
                           format_positive=format_positive,
                           format_none=format_none,
                           team_a_net_totals=team_a_net_totals,
                           team_b_net_totals=team_b_net_totals
                           )
    
    
@app.route('/scorecard_edit', methods=['GET', 'POST'])
@login_required
@group_login_required
@event_selected
def scorecard_edit():
 
    if request.method == "POST":

        match_id = request.form.get("match_id")
        player_id = request.form.get("player_id")
        if not match_id or not player_id:
            return apology("Match or player id not sent in POST request")
        
        player = Player.query.get(player_id)
        match = Match.query.get(match_id)
        course_tee = CourseTee.query.get(match.course_id)

        player_name = player.player_name
        course_display_name = course_tee.name + " - " + course_tee.teebox + " Tees"

        holes = (Hole.query
                 .filter_by(course_id=course_tee.id)
                 .order_by(Hole.hole_number)
                 .all()
                )
        scores = (Scores.query
                  .filter_by(player_id=player_id, match_id=match_id)
                  .all()
                 )

        # Create a dictionary mapping hole numbers to scores
        score_dict = {score.match_hole_number: score.score for score in scores}

        holes_data = []
        for hole in holes:
            hole_data = {"hole_number": hole.hole_number, 
                         "par": hole.par, 
                         "hole_hcp": hole.hole_hcp,
                         "score": score_dict.get(hole.hole_number, None)
                         }
            holes_data.append(hole_data)

        return render_template("scorecard_edit.html", 
                               holes=holes_data, 
                               course_display_name=course_display_name, 
                               match_id=match_id, 
                               player_id=player_id, 
                               player_name=player_name
                               )
    else:
        return redirect("/event_structure")

@app.route('/scorecard_processing', methods=['GET', 'POST'])
@login_required
@group_login_required
@event_selected
def scorecard_processing():
 
    if request.method == "POST":
            
        match_id = request.form.get("match_id")
        player_id = request.form.get("player_id")
        if not match_id or not player_id:
            return apology("Match or player id not sent in POST request")

        action = request.form.get("action")
        if not action:
            return apology("No action sent in POST request")

        if action == "update":
            # Update the scores table
            for i in range(1, 19):
                score = int(request.form.get("score_hole_" + str(i)))
                if score and score > 0:
                    score_row = (Scores.query
                                .filter_by(player_id=player_id, 
                                            match_id=match_id, 
                                            match_hole_number=i
                                            )
                                .first()
                                )
                    if score_row:
                        score_row.score = score
                    else:   
                        new_score = Scores(match_id=match_id, 
                                        match_hole_number=i, 
                                        player_id=player_id, 
                                        score=score
                                        )
                        db.session.add(new_score)
                else:
                    return apology("Score for hole " + str(i) + 
                                " must be an integer greater than 0")
            db.session.commit()
            
            return redirect("/scorecard")
        elif action == "clear":
            # Clear the scores table for player and current match
            scores = (Scores.query
                      .filter_by(player_id=player_id, match_id=match_id)
                      .all()
                      )
            for score in scores:
                db.session.delete(score)
            db.session.commit()
            
            return redirect("/scorecard")
        else:
            return apology("Invalid action")

    else:
        return redirect("/event_structure")
    

@app.route('/bets', methods=['GET'])
@login_required
@group_login_required
@event_selected
def bets():
    return render_template("bets.html")

@app.route('/bets_input', methods=['GET'])
@login_required
@group_login_required
@event_selected
def bets_input():
    
    # Send to template the rounds in the event (id, and number: name)
    event = Event.query.get(session["event_id"])
    if not event:
        return apology("Event not found")
    rounds = (Round.query
                .filter_by(event_id=session["event_id"])
                .all())
    
    rounds_data = [{"id": round.id, 
                    "round_name": "R" + str(round.round_number) + " " + round.round_name} 
                    for round in rounds]

    return render_template("bets_input.html", 
                           rounds=rounds_data,
                           event_name=event.event_name,
                           format_positive=format_positive,
                           )


@app.route('/bets_results', methods=['GET'])
@login_required
@group_login_required
@event_selected
def betting_results():
 
    return apology("Not yet implemented")


@app.route('/api/matches/<int:round_id>')
@login_required
@group_login_required
@event_selected
def get_matches(round_id):
    matches = (Match.query
               .options(
                   joinedload(Match.team_a), 
                   joinedload(Match.team_b)
                   )
               .filter_by(round_id=round_id)
               .all()
              )
    matches_data = [{'id': match.id, 
                    'team_a_name': match.team_a.team_name,
                    'team_b_name': match.team_b.team_name,
                     'matchup': f"{match.team_a.team_name} vs. {match.team_b.team_name}"
                     } 
                     for match in matches]
    return jsonify(matches=matches_data)


@app.route('/api/match_data/<int:match_id>')
def get_match_data(match_id):
    # Get match, team a and team b players and course from match joined load
    
    match = (Match.query
            .options(
                joinedload(Match.team_a).joinedload(Team.players).joinedload(Player.handicaps), 
                joinedload(Match.team_b).joinedload(Team.players).joinedload(Player.handicaps), 
                joinedload(Match.course_tee)
            )
            .filter_by(id=match_id)
            .first()
            )

    scores = (Scores.query
                .filter_by(match_id=match_id)
                .all()
                )
    
    team_a = {
        "key": "team_a", 
        "players": [
            {
                "id": player.id, 
                "handicap_index": next(
                    (
                        handicap.player_hcp 
                        for handicap in player.handicaps 
                        if handicap.event_id == session["event_id"]
                    ), 
                    None
                ),
                "playing_hcp": None
            } 
            for player in match.team_a.players
        ]
    }
    team_b = {
        "key": "team_b", 
        "players": [
            {
                "id": player.id, 
                "handicap_index": next(
                    (
                        handicap.player_hcp 
                        for handicap in player.handicaps 
                        if handicap.event_id == session["event_id"]
                    ), 
                    None
                ),
                "playing_hcp": None
            } 
            for player in match.team_b.players
        ]
    }

    course = match.course_tee
    
    for team in [team_a, team_b]:
            for player in team["players"]:
                player_index = player["handicap_index"]
                if player_index:
                    player["playing_hcp"] = playing_hcp(player_index, course.slope, course.rating, course.total_18_par)
                else:
                    player["playing_hcp"] = None

    

    # Get holes from course_tee
    holes = (Hole.query
             .filter_by(course_id=course.id)
             .order_by(Hole.hole_number)
             .all()
            )
    
    holes_data = {}
    team_a_net_cumulative = 0
    team_b_net_cumulative = 0
    match_net_cumulative = 0

    
    for hole in holes:
        hole_number = hole.hole_number
        hole_hcp = hole.hole_hcp

        for team in [team_a, team_b]:
    
            # Initialize total net score for team
            team_total_net_score = 0
            net_scores_on_hole = []
            for player in team["players"]:
                # Get player hcp
                player_hcp = player["playing_hcp"]
                # Calculate player strokes
                player_strokes = 1 if hole_hcp <= player_hcp else 0
                # Get player net score (needs match id, hole number, player id)
                score = next((score for score in scores if score.match_hole_number == hole.hole_number and score.player_id == player["id"]), None)
                if score:
                    player_net = score.score - player_strokes - hole.par
                else:
                    player_net = None
                # Add to net scores on hole list
                net_scores_on_hole.append(player_net)
            # Add lowest of two net scores to team total net score
            # Filter out None values from net_scores_on_hole
            filtered_scores = [score for score in net_scores_on_hole if score is not None]
            if filtered_scores:
                team_total_net_score += min(filtered_scores)
                
            # Update the team cumulative net score
            if team["key"] == "team_a":
                team_a_net_cumulative += team_total_net_score
                match_net_cumulative -= team_total_net_score
            else:
                team_b_net_cumulative += team_total_net_score
                match_net_cumulative += team_total_net_score

        holes_data[hole_number] = {
            "team_a_net_cumulative": team_a_net_cumulative, 
            "team_b_net_cumulative": team_b_net_cumulative,
            "match_net": match_net_cumulative,
            "F9": {
                "available_bets": 0,
                "current_bets": 0,
            },
            "B9": {
                "available_bets": 0,
                "current_bets": 0,
            },
            "18": {
                "available_bets": 0,
                "current_bets": 0,
            }
        }

    # Load bets in the match
    bets = (Bets.query
            .filter_by(match_id=match_id)
            .all()
            )
    if bets:
        for bet in bets:
            hole_number = bet.match_hole_number
            if hole_number in holes_data:
                holes_data[hole_number]["F9"]["current_bets"] = bet.front_9_bets
                holes_data[hole_number]["F9"]["available_bets"] = bet.front_9_bets
                holes_data[hole_number]["B9"]["current_bets"] = bet.back_9_bets
                holes_data[hole_number]["B9"]["available_bets"] = bet.back_9_bets
                holes_data[hole_number]["18"]["current_bets"] = bet.total_18_bets
                holes_data[hole_number]["18"]["available_bets"] = bet.total_18_bets
    else:
        # Add to bets table hole 1, 1 front 9 bet and 1 18 bet, and to hole 10, 1 back 9 bet
        new_bet = Bets(match_id=match_id, match_hole_number=1, front_9_bets=1, back_9_bets = None, total_18_bets=1)
        db.session.add(new_bet)
        new_bet = Bets(match_id=match_id, match_hole_number=10, front_9_bets=None, back_9_bets = 1, total_18_bets=None)
        db.session.add(new_bet)
        db.session.commit()
        holes_data[1]["F9"]["current_bets"] = 1
        holes_data[1]["F9"]["available_bets"] = 1
        holes_data[1]["18"]["current_bets"] = 1
        holes_data[1]["18"]["available_bets"] = 1
        holes_data[10]["B9"]["current_bets"] = 1
        holes_data[10]["B9"]["available_bets"] = 1
 
    # Calculate available bets and update 
    for i in range(2, 19):
        if i < 10:
            if holes_data[i]["F9"]["current_bets"] == 0:
                if check_bet_availability(holes_data, i, "F9"):
                    holes_data[i]["F9"]["available_bets"] = 1
        if i > 10:
            if holes_data[i]["B9"]["current_bets"] == 0:
                if check_bet_availability(holes_data, i, "B9"):
                    holes_data[i]["B9"]["available_bets"] = 1
        
        if holes_data[i]["18"]["current_bets"] == 0:
            if check_bet_availability(holes_data, i, "18"):
                holes_data[i]["18"]["available_bets"] = 1
    

    return jsonify(holes_data)




