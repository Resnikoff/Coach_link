CREATE TABLE athlete_temp (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    salt TEXT NOT NULL,
    coach_id INTEGER,
    auth_code TEXT,
    calorie_goal INTEGER,  -- This is now nullable
    email TEXT UNIQUE
);

INSERT INTO athlete_temp SELECT * FROM athlete;

DROP TABLE athlete;

ALTER TABLE athlete_temp RENAME TO athlete;


UPDATE db_version SET version = 7;
