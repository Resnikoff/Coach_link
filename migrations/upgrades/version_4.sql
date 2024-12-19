CREATE TABLE foods (
    food_id INTEGER PRIMARY KEY,
    food_name TEXT NOT NULL,
    calories FLOAT NOT NULL,
    protein FLOAT NOT NULL,
    carbs FLOAT NOT NULL,
    fat FLOAT NOT NULL,
    created_by_athlete_id INTEGER,
    FOREIGN KEY (created_by_athlete_id) REFERENCES athlete(id)
);

CREATE TABLE meals (
    meal_id INTEGER PRIMARY KEY,
    meal_name TEXT NOT NULL,
    created_by_athlete_id INTEGER,
    created_by_coach_id INTEGER,
    FOREIGN KEY (created_by_coach_id) REFERENCES coach(id)
    FOREIGN KEY (created_by_athlete_id) REFERENCES athlete(id)
);

--added foods table and the table in verison 3, and a meals table, where athlete can group foods together or coach preassigns them

UPDATE db_version SET version = 4;