CREATE TABLE food_entry (
    id INTEGER PRIMARY KEY,
    athlete_id INTEGER NOT NULL,
    food_name TEXT NOT NULL,
    calories INTEGER NOT NULL,
    protein INTEGER NOT NULL,
    carbs INTEGER NOT NULL,
    fats INTEGER NOT NULL,
    entry_date DATE NOT NULL,
    FOREIGN KEY (athlete_id) REFERENCES athlete(id)
);

