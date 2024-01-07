# FD24

Things to consider

login as user first
- navbar includes Register, Login
-   

then login/join a group page?
-   navbar includes logout
- page options create new group, or login in to group
-   show history of groups previously assocaited with you below login, if clicked link, take to you pre-filled login page
    (Ie FD or Nick,pete,brendan to keep scores and events)

-Once logged in to group
-   left navbar includes group name, "event setup", right bar includes switch group, logout 
-   page shows list
    - events & winners
    - players 

    - create new event button or nav 



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
    hash TEXT NOT NULL
);

CREATE TABLE groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    group_name TEXT NOT NULL,
    hash TEXT NOT NULL,
);

CREATE TABLE group_users (
    group_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (group_id) REFERENCES groups(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
);

CREATE TABLE course_tee (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    name TEXT NOT NULL,
    teebox TEXT NOt NULL,
    rating NUMERIC NOT NULL,
    slope NUMERIC NOT NULL,
);

CREATE TABLE holes (
    course_id INTEGER NOT NULL,
    hole_number INTEGER NOT NULL,
    par INTEGER NOT NULL,
    hole_hcp INTEGER NOT NULL,
    FOREIGN KEY (course_id) REFERENCES course_tee(id),
);

CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    event_name TEXT NOT NULL,
    group_id INT NOT NULL,
    date TEXT NOT NULL,
    FOREIGN KEY (group_id) REFERENCES groups(id),
);

CREATE TABLE teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    team_name TEXT NOT NULL,
    event_id INTEGER NOT NULL,
    FOREIGN KEY (event_id) REFERENCES events(id),
);

CREATE TABLE team_roster (
    team_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
);

CREATE TABLE players (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    player_name TEXT NOT NULL,
    group_id INTEGER NOT NULL,
    FOREIGN KEY (group_id) REFERENCES groups(id),
);

CREATE TABLE handicaps (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    player_id INTEGER NOT NULL,
    event_id INTEGER NOT NULL,
    player_hcp NUMERIC NOT NULL,
    FOREIGN KEY (player_id) REFERENCES players(id),
    FOREIGN KEY (event_id) REFERENCES events(id),
);

CREATE TABLE rounds (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL;
    round_number INTEGER NOT NULL;
    round_name TEXT,
    event_id INTEGER NOT NULL;
    FOREIGN KEY (event_id) REFERENCES events(id),
);

CREATE TABLE matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    match_number INTEGER NOT NULL,
    match_name TEXT,
    round_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    team_a_id INTEGER NOT NULL,
    team_b_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT INCOMPLETE,
    FOREIGN KEY (round_id) REFERENCES rounds(id),
    FOREIGN KEY (course_id) REFERENCES courses(id),
    FOREIGN KEY (team_a_id) REFERENCES teams(id),
    FOREIGN KEY (team_b_id) REFERENCES teams(id),

CREATE TABLE scores (
    match_id INTEGER NOT NULL,
    hole_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    score INTEGER NOT NULL,
    FOREIGN KEY (match_id) REFERENCES matches(id),
    FOREIGN KEY (player_id) REFERENCES players(id),
    FOREIGN KEY (hole_id) REFERENCES holes(id),
);

