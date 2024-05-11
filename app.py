import os, math

from cs50 import SQL
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy import func, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from flask import Flask, jsonify, flash, redirect, render_template, request, session
from flask_mail import Mail, Message
import json
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import logging
from database import db, SQLALCHEMY_DATABASE_URI
from models import User, GolfGroup, GroupUserAssociation, Player, Event, Team, TeamRoster, CourseTee, Handicap, Match, Round, Scores, Hole, Bets

from helpers import (apology, login_required, 
                     group_login_required, event_selected, usd, 
                     format_positive, format_none, playing_hcp, 
                     check_bet_availability, calculate_event_scores)

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

app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'tgrigg2010@gmail.com'
app.config['MAIL_PASSWORD'] = 'nhsgolfer'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
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
        events = (db.session.query(Event, func.count(Round.id).label('rounds_count'))
                    .outerjoin(Round, Event.id == Round.event_id)
                    .filter(Event.group_id == session["group_id"])
                    .group_by(Event.id)
                    .all())

        events_with_status = []
        complete_events_count = 0
        incomplete_events_count = 0
        for event, rounds_count in events:
            #event_dict = {**event.__dict__, 'rounds_count': rounds_count}
            event_dict = {
                "event_id": event.id,
                "event_name": event.event_name,
                "date": event.date,
                "status": event.status,
                "rounds_count": rounds_count,
                "winner": None
            }
            if event.status == "COMPLETE":
                complete_events_count += 1
                event_score_data = calculate_event_scores(event.id)
                lowest_scoring_team = min(event_score_data["cumulative_totals"], key=event_score_data["cumulative_totals"].get)
                lowest_score = event_score_data["cumulative_totals"][lowest_scoring_team]
                event_dict["winner"] = lowest_scoring_team + ": " + str(lowest_score)

            else:
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
        email = request.form.get("email")
        # Ensure all fields not blank
        if not username or not password or not confirmation:
            return apology("Missing username, password, or confirmation.", 400)
        if not email:
            return apology("Missing email.", 400)
        # Convert username to lowercase
        username = username.lower()
        email = email.lower()

        # Check if password matches confirmation, else return apology
        if password != confirmation:
            return apology("Passwords don't match", 400)

        # Register new user into users database along with hash of their password
        # Using unique constraint to make sure username doesn't already exist
        try:
            new_user = User(username=username, 
                            hash=generate_password_hash(password),
                            email=email)
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
                try:
                    new_association = GroupUserAssociation(
                        group_id=session["group_id"], 
                        user_id=session["user_id"])
                    db.session.add(new_association)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    print("Failed to add new association. Error: ", str(e))
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
        if len(player_scores) and edit_or_delete == "delete":
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
    
    play_off_min = request.form.get("play_off_min")
    play_off_min = True if play_off_min == "on" else False
    
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
                  date=event_date,
                  play_off_min=play_off_min)
    db.session.add(new_event)
    db.session.commit()

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
        try:
            new_round = Round(round_number=round_number, 
                            round_name=new_round_name, 
                            event_id=session["event_id"])
            db.session.add(new_round)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return apology("Round number already exists")
        
        round_id = new_round.id
        
        # Insert matches into matches table
        try:
            for match in matches:
                new_match = Match(match_number=match["match_number"], 
                                match_starting_hole=1,
                                round_id=round_id, 
                                course_id=course_id_selected, 
                                team_a_id=match["team_a"], 
                                team_b_id=match["team_b"])
                db.session.add(new_match)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return apology("Match number already exists")
        
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
                    "team_a_score": "", 
                    "team_b_score": ""
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
  
    event_data = calculate_event_scores(session["event_id"])

    if event_data.get("error"):
        return apology(event_data["error"])


    return render_template("leaderboard.html",
                           event_name=event_data["event_name"],
                           event_id = session["event_id"],
                           event_status=event_data["event_status"],
                           rounds_data=event_data["rounds_data"],
                           teams=event_data["teams"],
                           cumulative_totals=event_data["cumulative_totals"]
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


   
   # Find match in round returned
    match = next((m for m in round.matches if m.match_number == int(match_number)), None)
    if not match:
        return apology("Match not found")

    match_data = {"match_number": match_number, "match_id": match.id}

    event = Event.query.get(session["event_id"])
    if not event:
        return apology("Event not found")
    event_name = event.event_name
    play_off_min = event.play_off_min
    
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


    # Get all the handicaps for players in the event and get the minimum handicap index
    hcp_indexes_all = (Handicap.query
                    .filter_by(event_id=event.id)
                    .all())
    
    min_index = min([hcp.player_hcp for hcp in hcp_indexes_all])
    low_CH = playing_hcp(min_index, course.slope, course.rating, course.total_18_par)
    
    
    # Add handicap for each player on team a and team b
    for player in team_data["team_a_players"] + team_data["team_b_players"]:
        hcp_index = (Handicap.query
                     .filter_by(player_id=player["id"], event_id=session["event_id"])
                     .first()
                     .player_hcp
                    )
        if not hcp_index:
            return apology("Missing handicap index")
        
        player_CH = playing_hcp(hcp_index, course.slope, course.rating, course.total_18_par)
        if play_off_min:
            if player_CH > low_CH:
                player["hcp"] = player_CH - low_CH
            else:
                player["hcp"] = player_CH
        else:
            player["hcp"] = player_CH
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

        event = Event.query.get(session["event_id"])
        event_status = event.status
        if event_status == "COMPLETE":
            return apology("Event is complete. Go to scoreboard to edit.")
        
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

        return render_template("scorecard_input.html", 
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
                           play_off_min=event.play_off_min,
                           format_positive=format_positive,
                           )



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

    event = Event.query.get(session["event_id"])
    play_off_min = event.play_off_min
     # Get all the handicaps for players in the event
    hcp_indexes = (Handicap.query
                    .filter_by(event_id=event.id)
                    .all())
    min_index = min([hcp.player_hcp for hcp in hcp_indexes])
    low_CH = playing_hcp(min_index, match.course_tee.slope, match.course_tee.rating, match.course_tee.total_18_par)

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
                    player_CH = playing_hcp(player_index, course.slope, course.rating, course.total_18_par)
                    if play_off_min:
                        if player_CH > low_CH:
                            player["playing_hcp"] = player_CH - low_CH
                        else:
                            player["playing_hcp"] = player_CH
                    else:
                        player["playing_hcp"] = player_CH
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
            if check_bet_availability(holes_data, i, "F9"):
                holes_data[i]["F9"]["available_bets"] = 1
        if i > 10:
            if check_bet_availability(holes_data, i, "B9"):
                holes_data[i]["B9"]["available_bets"] = 1
        if check_bet_availability(holes_data, i, "18"):
             holes_data[i]["18"]["available_bets"] = 1
    

    return jsonify(holes_data)


@app.route('/process_bets', methods=['POST'])
def process_bets():
    
    match_data = request.get_json()

    # Save match_id
    match_id = match_data.pop("match_id", None)

    #Convert keys to ints
    match_data = {int(k): v for k, v in match_data.items()}
    
    # Reconfirm current bets are valid
    for i in range(2, 19):
        if i < 10:
            if match_data[i]["F9"]["current_bets"] == 1:
                if not check_bet_availability(match_data, i, "F9"):
                    return jsonify({"error": True, "message": "Invalid bet on hole " + str(i) + " front 9"})
        if i > 10:
            if match_data[i]["B9"]["current_bets"] == 1:
                if not check_bet_availability(match_data, i, "B9"):
                    return jsonify({"error": True, "message": "Invalid bet on hole " + str(i) + " back 9"})
        if match_data[i]["18"]["current_bets"] == 1:
            if not check_bet_availability(match_data, i, "18"):
                    return jsonify({"error": True, "message": "Invalid bet on hole " + str(i) + " 18"})

    # Pull bets in database for the match id
    bets = (Bets.query
            .filter_by(match_id=match_id)
            .all()
            )
    # Create a dictionary for each hole in bets
    bets_dict = {bet.match_hole_number: bet for bet in bets}
    
    # For holes 1-18, check if bets exist in database, if not, add them
    for i in range(1, 19):
        if (i < 10):    
            if match_data[i]["F9"]["current_bets"] == 1:
                if i not in bets_dict:
                    new_bet = Bets(match_id=match_id, match_hole_number=i, front_9_bets=1)
                    db.session.add(new_bet)
                    bets_dict[i] = new_bet
                elif not bets_dict[i].front_9_bets:
                    bets_dict[i].front_9_bets = 1
        if (i > 10):
            if match_data[i]["B9"]["current_bets"] == 1:
                if i not in bets_dict:
                    new_bet = Bets(match_id=match_id, match_hole_number=i, back_9_bets=1)
                    db.session.add(new_bet)
                    bets_dict[i] = new_bet
                elif not bets_dict[i].back_9_bets:
                    bets_dict[i].back_9_bets = 1
        if match_data[i]["18"]["current_bets"] == 1:
            if i not in bets_dict:
                new_bet = Bets(match_id=match_id, match_hole_number=i, total_18_bets=1)
                db.session.add(new_bet)
            elif not bets_dict[i].total_18_bets:
                bets_dict[i].total_18_bets = 1
    db.session.commit()
    
    return jsonify({"error": False, "message": "Bets data saved"})

@app.route('/apology')
def apology_route():
    message = request.args.get("message")
    return apology(message)


@app.route('/bets_results', methods=['GET'])
@login_required
@group_login_required
@event_selected
def betting_results():

    # Get all rounds for the event    
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

    return render_template("bets_results.html", 
                           rounds=rounds_data,
                           event_name=event.event_name
                           )

@app.route('/api/bet_results_data/<int:match_id>')
def get_bet_results_data(match_id):
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
    
    event = Event.query.get(session["event_id"])
    play_off_min = event.play_off_min
     # Get all the handicaps for players in the event
    hcp_indexes = (Handicap.query
                    .filter_by(event_id=event.id)
                    .all())
    min_index = min([hcp.player_hcp for hcp in hcp_indexes])
    low_CH = playing_hcp(min_index, match.course_tee.slope, match.course_tee.rating, match.course_tee.total_18_par)

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
                        player_CH = playing_hcp(player_index, course.slope, course.rating, course.total_18_par)
                        if play_off_min:
                            if player_CH > low_CH:
                                player["playing_hcp"] = player_CH - low_CH
                            else:
                                player["playing_hcp"] = player_CH
                        else:
                            player["playing_hcp"] = player_CH
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
                "current_bets": 0,
            },
            "B9": {
                "current_bets": 0,
            },
            "18": {
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
                holes_data[hole_number]["B9"]["current_bets"] = bet.back_9_bets
                holes_data[hole_number]["18"]["current_bets"] = bet.total_18_bets
    else:
        # Add to bets table hole 1, 1 front 9 bet and 1 18 bet, and to hole 10, 1 back 9 bet
        new_bet = Bets(match_id=match_id, match_hole_number=1, front_9_bets=1, back_9_bets = None, total_18_bets=1)
        db.session.add(new_bet)
        new_bet = Bets(match_id=match_id, match_hole_number=10, front_9_bets=None, back_9_bets = 1, total_18_bets=None)
        db.session.add(new_bet)
        db.session.commit()
        holes_data[1]["F9"]["current_bets"] = 1
        holes_data[1]["18"]["current_bets"] = 1
        holes_data[10]["B9"]["current_bets"] = 1
 
    # Use holes data, calculate winning bets
    bets_results_data = {
        "F9": {
            "total_bets": 0,
            "team_a_wins": 0,
            "team_b_wins": 0,
            "ties": 0,
            "team_a_net": 0
        },
        "B9": {
            "total_bets": 0,
            "team_a_wins": 0,
            "team_b_wins": 0,
            "ties": 0,
            "team_a_net": 0,
        },
        "18": {
            "total_bets": 0,
            "team_a_wins": 0,
            "team_b_wins": 0,
            "ties": 0,
            "team_a_net": 0,
        },
        "total": {
            "total_bets": 0,
            "team_a_wins": 0,
            "team_b_wins": 0,
            "ties": 0,
            "team_a_net": 0,
        }
    }

    def update_bets_results(bets_results_data, holes_data, hole_number, hole_key):
        bets_results_data[hole_key]["total_bets"] += 1
        bets_results_data["total"]["total_bets"] += 1
        ending_AvsB = (holes_data[18 if hole_key != "F9" else 9]["team_a_net_cumulative"] - 
                       holes_data[18 if hole_key != "F9" else 9]["team_b_net_cumulative"])
        if hole_number == 1:
            bet_start_AvsB = 0
        else:
            bet_start_AvsB = (holes_data[hole_number - 1]["team_a_net_cumulative"] - 
                            holes_data[hole_number - 1]["team_b_net_cumulative"])
        if ending_AvsB < bet_start_AvsB:
            bets_results_data[hole_key]["team_a_wins"] += 1
            bets_results_data[hole_key]["team_a_net"] += 1
            bets_results_data["total"]["team_a_wins"] += 1
            bets_results_data["total"]["team_a_net"] += 1
        elif ending_AvsB > bet_start_AvsB:
            bets_results_data[hole_key]["team_b_wins"] += 1
            bets_results_data[hole_key]["team_a_net"] -= 1
            bets_results_data["total"]["team_b_wins"] += 1
            bets_results_data["total"]["team_a_net"] -= 1
        else:
            bets_results_data[hole_key]["ties"] += 1
            bets_results_data["total"]["ties"] += 1
    
    
    for i in range(1, 19):
        if i < 10 and holes_data[i]["F9"]["current_bets"] == 1:
            update_bets_results(bets_results_data, holes_data, i, "F9")
        elif i >= 10 and holes_data[i]["B9"]["current_bets"] == 1:
            update_bets_results(bets_results_data, holes_data, i, "B9")
        if holes_data[i]["18"]["current_bets"] == 1:
            update_bets_results(bets_results_data, holes_data, i, "18")
           
   
    return jsonify(bets_results_data)

@app.route('/mark_event_as_complete', methods=['POST'])
def mark_event_as_complete():
    data = request.get_json()
    event_id = data['event_id']
    is_complete = data['is_complete']
    
    # Get all rounds and their matches for the event in one query
    rounds = (Round.query
                .options(joinedload(Round.matches))
                .filter_by(event_id=event_id)
                .all())

    for round in rounds:
        for match in round.matches:
            match.status = "COMPLETE" if is_complete else "INCOMPLETE"

    # Change status in events table also to complete
    event = Event.query.get(event_id)
    event.status = "COMPLETE" if is_complete else "INCOMPLETE"
    
    db.session.commit()
   
    return 'Success', 200

@app.route('/event_settings', methods=['GET', 'POST'])
@login_required
@group_login_required
@event_selected
def event_settings():
    
    if request.method == "POST":
      
        team_name_new = request.form.get("team_name_new")
        team_id = request.form.get("team_id")
        if team_name_new:
            # Update team name in database
            team = Team.query.get(team_id)
            team.team_name = team_name_new
            db.session.commit()
            return redirect("/")
      
        def update_handicap(player_id, player_hcp):
            if player_id:
                handicap = (Handicap.query
                            .filter_by(player_id=player_id, event_id=session["event_id"])
                            .first()
                            )
                if handicap:
                    handicap.player_hcp = player_hcp
                else:
                    return apology(f"Handicap not found for player {player_id}")

        handicaps = Handicap.query.filter_by(event_id=session["event_id"]).all()
        hcp_form_submitted = request.form.get("player_a_id_team_0")
        num_teams = request.form.get("num_teams")

        if hcp_form_submitted:
            for i in range(0, int(num_teams)):
                first_player_id = request.form.get(f"player_a_id_team_{i}")
                first_player_handicap = request.form.get(f"player_a_hcp_team_{i}")
                second_player_id = request.form.get(f"player_b_id_team_{i}")
                second_player_handicap = request.form.get(f"player_b_hcp_team_{i}")

                update_handicap(first_player_id, first_player_handicap)
                update_handicap(second_player_id, second_player_handicap)

        db.session.commit()
        return redirect("/")
    
    else:
        event = Event.query.get(session["event_id"])
        if not event:
            return apology("Event not found")
        event_name = event.event_name
        play_off_min = event.play_off_min
        # Get all teams and players for the event
        teams = (Team.query
                .filter_by(event_id=session["event_id"])
                .options(joinedload(Team.players))
                .all())

        handicaps = Handicap.query.filter_by(event_id=session["event_id"]).all()
        
        teams_data = []
        
        for team in teams:
            players_data = []
            for player in team.players:
                hcp_index = next(
                    (
                        handicap.player_hcp 
                        for handicap in handicaps 
                        if handicap.player_id == player.id
                    ), 
                    None
                )
                players_data.append({
                    "player_id": player.id,
                    "player_name": player.player_name,
                    "hcp_index": hcp_index
                })
        
            team = {
                "team_id": team.id,
                "team_name": team.team_name,
                "players": players_data
            }
            teams_data.append(team)

        num_teams = len(teams_data)
        group_players = Player.query.filter_by(group_id=session["group_id"]).all()


        return render_template("event_settings.html", 
                               event_name=event_name,
                               event_id=session["event_id"], 
                               num_teams=num_teams, 
                               teams_data=teams_data,
                               group_players=group_players,
                               play_off_min=play_off_min
                               )
    

@app.route('/course_handicaps')
@login_required
@group_login_required
@event_selected
def course_handicaps():
    
    # Using session event id to get all rouunds, and round ids to get all matches, and matches to get all course ids, get all courses
    event = Event.query.get(session["event_id"])
    if not event:
        return apology("Event not found")
    # Use joined load to get all matches in one query
    rounds = (Round.query
                .options(joinedload(Round.matches))
                .filter_by(event_id=session["event_id"])
                .all())

    # Get all course ids from matches
    course_ids = set()
    for round in rounds:
        for match in round.matches:
            course_ids.add(match.course_id)
    # Get all course data from course ids
    courses = (CourseTee.query
                .filter(CourseTee.id.in_(course_ids))
                .all())
    # Get all teams in the event
    teams = (Team.query
             .filter_by(event_id=session["event_id"])
             .all())
    # Get all player ids from team roster with those team ids
    player_ids = set()
    for team in teams:
        for player in team.players:
            player_ids.add(player.id)
    
    # Get all players in the event and their handicaps
    
    players = (Player.query
                .options(joinedload(Player.handicaps))
                .filter(Player.id.in_(player_ids))
                .all())

    handicap_data = []
    if rounds:
        for course in courses:
            players_data = {}
            for player in players:
                hcp_index = next(
                    (
                        handicap.player_hcp 
                        for handicap in player.handicaps 
                        if handicap.event_id == session["event_id"]
                    ), 
                    None
                )

                players_data[player.id] = {
                    "player_name": player.player_name,
                    "player_hcp": hcp_index,
                    "course_hcp": playing_hcp(hcp_index, course.slope, course.rating, course.total_18_par),
                }

            handicap_for_course = {
                "course_name": course.name + " - " + course.teebox + " Tees",
                "players_data": players_data
            }
            handicap_data.append(handicap_for_course)
        
        print(handicap_data)
        return render_template("course_handicaps.html", 
                            handicap_data=handicap_data,
                            players=players, 
                            event_name=event.event_name
                            )
    else:
        players_data = {}
        for player in players:
            hcp_index = next(
                (
                    handicap.player_hcp 
                    for handicap in player.handicaps 
                    if handicap.event_id == session["event_id"]
                ), 
                None
            )

            players_data[player.id] = {
                "player_name": player.player_name,
                "player_hcp": hcp_index,
                "course_hcp": None
            }

        handicap_data = [{
            "course_name": None,
            "players_data": players_data
        }]
        return render_template("course_handicaps.html", 
                            handicap_data=handicap_data,
                            players=players, 
                            event_name=event.event_name
                            )

@app.route('/api/course_hcp', methods=['POST'])
@login_required
@group_login_required
@event_selected
def course_hcp():
    data = request.get_json()  # Get JSON data from the request

    player_id = data["player_id"]
    player_name = data["player_name"]
    player_hcp = float(data["player_hcp"])
    course_id = data["course_id"]

    course = CourseTee.query.get(course_id)
    
    # Calculate course handicap
    course_handicap = playing_hcp(player_hcp, course.slope, course.rating, course.total_18_par)

    # Return a response
    return jsonify(course_hcp=course_handicap)


@app.route('/api/bet_amt/<int:match_id>', methods=['GET', 'POST'])
@login_required
@group_login_required
@event_selected
def get_bet_amt(match_id):
    
    if request.method == "POST":
        bet_amt = request.get_json().get("bet_amt")
        if not bet_amt:
            return jsonify(error="Bet amount not sent in POST request")
        try:
            int(bet_amt)
        except ValueError:
            return jsonify(error="Bet amount must be an integer")
        match = Match.query.get(match_id)
        if not match:
            return jsonify(error="Match not found")
        match.bet_amt = bet_amt
        db.session.commit()
        return jsonify(success="Bet amount saved")
    else:
        match = Match.query.get(match_id)
        if not match:
            return jsonify(error="Match not found")
        return jsonify(bet_amt=match.bet_amt)


@app.route('/update_play_off_min', methods=['POST'])
def play_off_low():
    data = request.get_json()
    event_id = data['event_id']
    play_off_min = data['play_off_min']
    if not event_id:
        return jsonify(error="Event id not sent in POST request")
    if not play_off_low:
        return jsonify(error="Play off low not sent in POST request")
    
    
    event = Event.query.get(event_id)

    # Get all matches in the event
    rounds = (Round.query
                .options(joinedload(Round.matches))
                .filter_by(event_id=event_id)
                .all())
    
    # For each match in each round, check if sum of f9, b9, 18 bets is > 3 
    for round in rounds:
        for match in round.matches:
            bets = (Bets.query
                    .filter_by(match_id=match.id)
                    .all()
                    )
            for bet in bets:
                if ((bet.match_hole_number != 1 and bet.front_9_bets is not None and bet.front_9_bets > 0) or
                     (bet.match_hole_number != 10 and bet.back_9_bets is not None and bet.back_9_bets > 0) or
                     (bet.match_hole_number != 1 and bet.total_18_bets is not None and bet.total_18_bets > 0)):
                    return jsonify(error="Cannot change since bets have been placed on match")


    event.play_off_min = play_off_min
    db.session.commit()

   
    return jsonify(success="Play off low updated")


@app.route("/delete_round_request", methods=["POST"])
@login_required
@group_login_required
@event_selected
def delete_round_check():

    event_id = session["event_id"]
    event = Event.query.get(event_id)
    event_status = event.status
    if event_status == "COMPLETE":
        return apology("Event is complete. Go to scoreboard to edit.")
    round_number = request.form.get("round_number")

    return render_template("delete_round_request.html", 
                           event_id=event_id,
                           event_name=event.event_name, 
                           round_number=round_number)


@app.route("/delete_round_complete", methods=["POST"])
@login_required
@group_login_required
@event_selected
def delete_round_complete():
    event_id = request.form.get("event_id")
    round_number = request.form.get("round_number")
    # Get the round id, then delete the round, matches, scores, and bets in all matches in the round
    round = (Round.query
            .filter_by(event_id=event_id, round_number=round_number)
            .first()
            )
    if not round:
        return apology("Round not found")
    round_id = round.id
    # Get all matches in the round
    try:
        matches = (Match.query
                .filter_by(round_id=round_id)
                .all()
                )
        for match in matches:
            # Delete scores
            scores = (Scores.query
                    .filter_by(match_id=match.id)
                    .all()
                    )
            for score in scores:
                db.session.delete(score)
            # Delete bets
            bets = (Bets.query
                    .filter_by(match_id=match.id)
                    .all()
                    )
            for bet in bets:
                db.session.delete(bet)
            db.session.delete(match)
        db.session.delete(round)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return apology(f"Error deleting round: {e}")
    
    return redirect("/event_structure")

