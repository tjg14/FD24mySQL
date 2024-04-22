To do - move complete to events?


CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(30) NOT NULL,
    hash VARCHAR(255) NOT NULL
);

CREATE TABLE golf_groups (
    id INT PRIMARY KEY AUTO_INCREMENT,
    groupname VARCHAR(50) NOT NULL,
    hash VARCHAR(255) NOT NULL
);

CREATE TABLE group_user_associations (
    group_id INT NOT NULL,
    user_id INT NOT NULL,
    FOREIGN KEY (group_id) REFERENCES groups(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    PRIMARY KEY (group_id, user_id)
);

CREATE TABLE course_tee (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,
    teebox VARCHAR(10) NOT NULL,
    rating DECIMAL(4, 1) NOT NULL,
    slope DECIMAL(3, 0) NOT NULL,
    front_9_par INT NOT NULL,
    back_9_par INT NOT NULL,
    total_18_par INT NOT NULL,
    active INT NOT NULL DEFAULT 1
);

CREATE TABLE holes (
    course_id INT NOT NULL,
    hole_number INT NOT NULL,
    par INT NOT NULL,
    hole_hcp INT NOT NULL,
    FOREIGN KEY (course_id) REFERENCES course_tee(id),
    PRIMARY KEY (course_id, hole_number)
);

CREATE TABLE events (
    id INT PRIMARY KEY AUTO_INCREMENT,
    event_name VARCHAR(50) NOT NULL,
    group_id INT NOT NULL,
    date DATE NOT NULL,
    FOREIGN KEY (group_id) REFERENCES golf_groups(id)
);

CREATE TABLE teams (
    id INT PRIMARY KEY AUTO_INCREMENT,
    team_name VARCHAR(50) NOT NULL,
    event_id INT NOT NULL,
    FOREIGN KEY (event_id) REFERENCES events(id)
);

CREATE TABLE team_roster (
    team_id INT NOT NULL,
    player_id INT NOT NULL,
    FOREIGN KEY (team_id) REFERENCES teams(id),
    FOREIGN KEY (player_id) REFERENCES players(id)
    PRIMARY KEY (team_id, player_id)
);

TO UPDATE ROSTER FOREIGN KEYSSSSs

CREATE TABLE players (
    id INT PRIMARY KEY AUTO_INCREMENT,
    player_name VARCHAR(50) NOT NULL,
    group_id INT NOT NULL,
    FOREIGN KEY (group_id) REFERENCES golf_groups(id)
);

CREATE TABLE handicaps (
    id INT PRIMARY KEY AUTO_INCREMENT,
    player_id INT NOT NULL,
    event_id INT NOT NULL,
    player_hcp DECIMAL(3, 1) NOT NULL,
    FOREIGN KEY (player_id) REFERENCES players(id),
    FOREIGN KEY (event_id) REFERENCES events(id)
);

CREATE TABLE rounds (
    id INT PRIMARY KEY AUTO_INCREMENT,
    round_number INT NOT NULL,
    round_name VARCHAR(30),
    event_id INT NOT NULL,
    FOREIGN KEY (event_id) REFERENCES events(id)
);

CREATE TABLE matches (
    id INT PRIMARY KEY AUTO_INCREMENT,
    match_number INT NOT NULL,
    match_time TIME,
    match_starting_hole INT NOT NULL DEFAULT 1,
    round_id INT NOT NULL,
    course_id INT NOT NULL,
    team_a_id INT NOT NULL,
    team_b_id INT NOT NULL,
    status VARCHAR(15) NOT NULL DEFAULT 'INCOMPLETE',
    FOREIGN KEY (round_id) REFERENCES rounds(id),
    FOREIGN KEY (course_id) REFERENCES course_tee(id),
    FOREIGN KEY (team_a_id) REFERENCES teams(id),
    FOREIGN KEY (team_b_id) REFERENCES teams(id)
);

CREATE TABLE scores (
    match_id INT NOT NULL,
    match_hole_number INT NOT NULL,
    player_id INT NOT NULL,
    score INT NOT NULL,
    FOREIGN KEY (match_id) REFERENCES matches(id),
    FOREIGN KEY (player_id) REFERENCES players(id)
    PRIMARY KEY (match_id, match_hole_number, player_id)
);

CREATE TABLE presses (
    match_id INT NOT NULL,
    match_hole_number INT NOT NULL,
    front_9_bets INT,
    back_9_bets INT,
    total_18_bets INT,
    FOREIGN KEY (match_id) REFERENCES matches(id),
    PRIMARY KEY (match_id, match_hole_number)
);