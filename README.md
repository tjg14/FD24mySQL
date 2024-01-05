# FD24

Things to consider

login as user first
show history of groups assocaited with?

then login/join a group page?
-Ie FD or Nick,pete,brendan to keep scores and events


user-> trevor
group-> FD
event-> FD24
course_tee -> fd black
round -> 1
match->a
player->trevor
team->LH
hole->1



CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    username TEXT NOT NULL,
    hash TEXT NOT NULL,
);

CREATE TABLE groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    group_name TEXT NOT NULL,
    hash TEXT NOT NULL,
);

CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    event_name TEXT NOT NULL,
    group_id INT NOT NULL,
    course_id INT NOT NULL,
    date TEXT NOT NULL,
    FOREIGN KEY (group_id) REFERENCES groups(id),
    FOREIGN KEY (course_id) REFERENCES course_tee_(id),
);

CREATE TABLE course_tee (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    name TEXT NOT NULL,
    teebox TEXT NOt NULL,
    rating NUMERIC NOT NULL,
    slope NUMERIC NOT NULL,
);

CREATE TABLE holes (
    hole_number INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    par INTEGER NOT NULL,
    FOREIGN KEY (course_id) REFERENCES course_tee(id),
);

CREATE TABLE rounds (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL;
    round_number INTEGER NOT NULL;
    round_name TEXT,
    event_id INTEGER NOT NULL;
    FOREIGN KEY (event_id) REFERENCES events(id),
);

CREATE TABLE teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    team_name TEXT NOT NULL,
    event_id INTEGER NOT NULL,
    player_a_id INTEGER NOT NULL,
    player_b_id INTEGER,
    FOREIGN KEY (event_id) REFERENCES events(id),
    FOREIGN KEY (player_a_id) REFERENCES players(id),
    FOREIGN KEY (player_b_id) REFERENCES players(id),
);

CREATE TABLE matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    match_name TEXT NOT NULL,
    round_id INTEGER NOT NULL,
    event_id INTEGER NOT NULL,
    team_a_id INTEGER NOT NULL,
    team_b_id INTEGER NOT NULL,
    winner_id INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (round_id) REFERENCES rounds(id),
    FOREIGN KEY (event_id) REFERENCES events(id),
    FOREIGN KEY (team_a_id) REFERENCES teams(id),
    FOREIGN KEY (team_b_id) REFERENCES teams(id),
    FOREIGN KEY (winner_id) REFERENCES teams(id),
);

#TODOOOOOOO

            CREATE TABLE scores (
                event_id
                round_id
                CourseID
                MatchID
                RoundID
                HoleID
                PlayerID
                NumPutts
                NumStrokes - you can add more specifics if you want (fairway, rough)
            );

CREATE TABLE players (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    player_name TEXT NOT NULL,
    hcp_current NUMERIC NOT NULL,
    hcp_TML NUMERIC,
    event_id INTEGER NOT NULL,
    FOREIGN KEY (event_id) REFERENCES events(id),
);