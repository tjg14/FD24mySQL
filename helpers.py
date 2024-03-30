import csv
import datetime
import pytz
import requests
import subprocess
import urllib
import uuid

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

# Function to remove round number and match number from session
def remove_round_match():
    session.pop("round", None)
    session.pop("match", None)
