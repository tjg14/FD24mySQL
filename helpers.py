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
