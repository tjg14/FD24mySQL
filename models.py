from app import db
from sqlalchemy import UniqueConstraint

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(60), nullable=False)

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
    status = db.Column(db.String(15), nullable=False, server_default='INCOMPLETE')
    play_off_min = db.Column(db.Boolean, nullable=False, server_default='0')
    hcp_allowance = db.Column(db.Float, nullable=False, server_default='0.85')
    max_strokes = db.Column(db.Integer, nullable=False, server_default='50')

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

    __table_args__ = (UniqueConstraint('event_id', 'round_number', name='uix_event_id_round_number'),)

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
    bet_amt = db.Column(db.Integer)

    team_a = db.relationship('Team', foreign_keys=[team_a_id])
    team_b = db.relationship('Team', foreign_keys=[team_b_id])
    course_tee = db.relationship('CourseTee')

    __table_args__ = (UniqueConstraint('round_id', 'match_number', name='uix_round_id_match_number'),)

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