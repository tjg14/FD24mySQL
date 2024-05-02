import csv
import datetime
import pytz
import requests
import subprocess
import urllib
import uuid
import math

from flask import redirect, render_template, session
from functools import wraps
from sqlalchemy.orm import joinedload
from models import Round, Team, Match, CourseTee, Handicap, Scores, Event

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def group_login_required(f):
    """ Decorate routes to require login to a group."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("group_id") is None:
            return redirect("/group")
        return f(*args, **kwargs)
    return decorated_function

def event_selected(f):
    """ Decorate routes to require event in session."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("event_id") is None:
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function

def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"

def format_positive(number):
    """Format positive numbers with a plus sign, or a dash if the number is None."""
    if number is None:
        return "-"
    elif number == 0:
        return "E"
    else:
        return f"+{number}" if number > 0 else str(number)
    
def format_none(number):
    """Format dash if the number is None."""
    if number is None:
        return "-"
    else:
        return number

def playing_hcp(index, slope, rating, par):
    """Calculate playing handicap for a player."""
    course_hcp = index * float(slope) / 113 + (rating - par)
    return int(min(__builtins__["round"](course_hcp * 0.85, 0), 18))

def check_bet_availability(holes_data, hole_number, bet_type):
    """Check if a bet is available for a hole."""
    check_answer = True
    # For each hole there is a bet, check if match score has changed since last bet
    if bet_type == "F9":
        latest_bet_hole = 1
        latest_match_score = 0
        for i in range(2, 10):
            if i == hole_number or holes_data[i][bet_type]["current_bets"] == 1:
                if holes_data[i - 1]["match_net"] != latest_match_score:
                    latest_bet_hole = i
                    latest_match_score = holes_data[i - 1]["match_net"]
                else:
                    check_answer = False
                    break
    elif bet_type == "B9":
        latest_bet_hole = 10
        latest_match_score = holes_data[9]["match_net"]
        for i in range(11, 19):
            if i == hole_number or holes_data[i][bet_type]["current_bets"] == 1:
                if holes_data[i - 1]["match_net"] != latest_match_score:
                    latest_bet_hole = i
                    latest_match_score = holes_data[i - 1]["match_net"]
                else:
                    check_answer = False
                    break
    elif bet_type == "18":
        latest_bet_hole = 1
        latest_match_score = 0
        for i in range(2, 19):
            if i == hole_number or holes_data[i][bet_type]["current_bets"] == 1:
                if holes_data[i - 1]["match_net"] != latest_match_score:
                    latest_bet_hole = i
                    latest_match_score = holes_data[i - 1]["match_net"]
                else:
                    check_answer = False
                    break
    return check_answer


def calculate_event_scores(event_id):
    """Calculate team that won an event"""
  
        # Get event name
    event = Event.query.get(event_id)
    if not event:
        return {"error": "Event not found"}

    event_name = event.event_name
    event_status = event.status

    # Get all rounds for the event
    rounds = (Round.query
              .filter_by(event_id=event_id)
              .order_by(Round.round_number)
              .all())


    # Get all teams and players for the event
    teams = (Team.query
             .filter_by(event_id=event_id)
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
                    .filter_by(event_id=event_id)
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
                    player["playing_hcp"] = playing_hcp(player_index, course_for_match.slope, course_for_match.rating, course_for_match.total_18_par)
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

    return_data = {
        "event_id": event_id,
        "event_name": event_name,
        "event_status": event_status,
        "rounds_data": rounds_data,
        "teams": teams,
        "cumulative_totals": cumulative_totals
    }
    
    
    return return_data