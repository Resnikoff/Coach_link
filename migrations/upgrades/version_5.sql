CREATE TABLE weight_log (
    id INTEGER PRIMARY KEY,
    athlete_id INTEGER NOT NULL,
    date DATE NOT NULL,
    weight REAL NOT NULL,
    image_path TEXT,
    FOREIGN KEY (athlete_id) REFERENCES athlete(id)
);

UPDATE db_version SET version = 5;