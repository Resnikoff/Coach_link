import sqlite3
from flask import Flask, render_template, request, flash, redirect, url_for, session
from shared import *

from datetime import datetime

#updating caloring goal for athlete
def update_calorie_goal(athlete_id, calorie_goal):
    with sqlite3.connect("app.db") as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE athlete SET calorie_goal = ? WHERE id = ?", (calorie_goal, athlete_id))
        conn.commit()

#retrieve calorie goal from athlete
def get_calorie_goal(athlete_id):
    with sqlite3.connect("app.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT calorie_goal FROM athlete WHERE id = ?", (athlete_id,))
        return cursor.fetchone()


@app.route('/food_entry', methods=['GET', 'POST'])
@login_required
def food_entry():
    db = get_db()
    cursor = db.cursor()
    
    foods = None #placeholder
    
    if request.method == 'POST':
        food_name = request.form['food_name']
        
        # Search foods
        cursor.execute("SELECT * FROM foods WHERE name LIKE ?", ('%' + food_name + '%',))
        foods = cursor.fetchall()
        
        if not foods:
            flash('Food not found in the database.', 'warning')

    return render_template('food_entry.html', foods=foods)





def fetch_athlete_macros(athlete_username):

    """
    athlete_username --> user.id = username
    
    """

    conn = sqlite3.connect('site.db')
    cursor = conn.cursor()
    
    #date library for the day
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    #User id for the name
    cursor.execute("SELECT id FROM athlete WHERE username = ?", (athlete_username,))
    athlete_id = cursor.fetchone()
    
    #if athlete not found OR no values set, default =0, 0, 0
    if not athlete_id:
        return {"carbs": 0, "protein": 0, "fat": 0, "total_calories": 0}
    
    # agreed macros for athelte in the day from its entries 
    cursor.execute("""
        SELECT SUM(carbs), SUM(protein), SUM(fat), SUM(calories) 
        FROM food_entry 
        WHERE athlete_id = ? AND date = ?
    """, (athlete_id[0], current_date))
    
    result = cursor.fetchone()
    conn.close()
    
    # Format and return the results
    return {
        "carbs": result[0] or 0,
        "protein": result[1] or 0,
        "fat": result[2] or 0,
        "total_calories": sum(result[3]) or 0  #for sum of calories
    }

@app.route('/remove_food', methods=['POST'])
def remove_food():
    print("Remove food route triggered") 
    food_id = request.form.get('id')  # Fetch the food entry's ID from the form data
    print(f"Food ID to remove: {food_id}")  
    
    if not food_id:
        flash('Failed to remove food. Invalid ID.')
        return redirect(url_for('calorie_counter'))

    db = get_db()
    cursor = db.cursor()
    
    try:
        # Delete the food entry from the database
        cursor.execute("DELETE FROM food_entry WHERE id=?", (food_id,))
        db.commit()
        flash('Food removed successfully!')
    except Exception as e:
        flash('Error removing food: ' + str(e))
    
    return redirect(url_for('calorie_counter'))


