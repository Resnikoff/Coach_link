-- For the `coach` table:
CREATE TABLE coach_new (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    salt TEXT NOT NULL,
    email TEXT UNIQUE
);

INSERT INTO coach_new (id, username, password, salt, email)
SELECT id, username, password, salt, 'temp_email_' || id || '@example.com' FROM coach;

DROP TABLE coach;

ALTER TABLE coach_new RENAME TO coach;

-- For the `athlete` table:
CREATE TABLE athlete_new (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    salt TEXT NOT NULL,
    coach_id INTEGER NULL,
    auth_code TEXT NOT NULL,
    calorie_goal INTEGER NOT NULL,
    email TEXT UNIQUE
);


INSERT INTO athlete_new (id, username, password, salt, coach_id, auth_code, calorie_goal, email) 
SELECT id, username, password, salt, coach_id, auth_code, calore_goal, 'temp_email_' || id || '@example.com' FROM athlete 
WHERE email IS NULL;

INSERT INTO athlete_new (id, username, password, salt, coach_id, auth_code, calorie_goal) 
SELECT id, username, password, salt, coach_id, auth_code, calore_goal FROM athlete;

DROP TABLE athlete;

ALTER TABLE athlete_new RENAME TO athlete;




--remaking databses to add the UNIQUE column

UPDATE db_version SET version = 6;
