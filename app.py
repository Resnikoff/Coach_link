from flask import render_template, request, redirect, url_for, flash, session, send_from_directory
from werkzeug.utils import secure_filename
import os
import random
import string 
from datetime import date, datetime
import hashlib #efficiency to prevent circular imports

from calorie_counter import *
from shared import *
from database_manager import *
from api_utils import search_food_in_cache, search_food_in_usda_api, save_to_cache
from forgot_password_API import *
 

#password hashing
def hash_password(password, salt=None):
    if not salt:
        salt = os.urandom(16).hex()
    password_salt_combo = password + salt
    hashed_password = hashlib.sha256(password_salt_combo.encode()).hexdigest()
    return hashed_password, salt

#Auth code generator function
def generate_auth_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))


#registration and login routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role = request.form['role']
        username = request.form['username']
        password = request.form['password']
        email = request.form.get('email')

        db = get_db()
        cursor = db.cursor()

        # Check if username or email already exists for both coach and athlete
        cursor.execute("SELECT * FROM coach WHERE username=? OR email=?", (username, email))
        existing_coach = cursor.fetchone()

        cursor.execute("SELECT * FROM athlete WHERE username=? OR email=?", (username, email))
        existing_athlete = cursor.fetchone()

        if existing_coach or existing_athlete:
            flash('Username or email already exists. Please choose different ones.', 'warning')
            return redirect(url_for('register'))

        hashed_password, salt = hash_password(password)

        if role == 'coach':
            cursor.execute("INSERT INTO coach (username, password, salt, email) VALUES (?, ?, ?, ?)", 
                           (username, hashed_password, salt, email))
            db.commit()

        elif role == 'athlete':
            auth_code = generate_auth_code()
            calorie_goal = None
            cursor.execute("INSERT INTO athlete (username, password, salt, auth_code, calorie_goal, email) VALUES (?, ?, ?, ?, ?, ?)", 
                           (username, hashed_password, salt, auth_code, calorie_goal, email))
            db.commit()

        else:
            flash('Invalid role selected!', 'danger')
            return redirect(url_for('register'))
            
        flash(f'Registration successful for {role}. Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None  # Variable to store the error message

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form.get('role')

        # Initialize database connection
        db = get_db()
        cursor = db.cursor()

        # Load details based on username and role
        if role == 'coach':
            cursor.execute("SELECT * FROM coach WHERE username=?", (username,))
        elif role == 'athlete':
            cursor.execute("SELECT * FROM athlete WHERE username=?", (username,))
        else:
            error = 'Invalid role selected!'
            return render_template('login.html', error=error)

        user = cursor.fetchone()

        if user:
            stored_password = user[2]  # Assuming 3rd column is password
            salt = user[3]  # Assuming 4th column is salt

            hashed_password, _ = hash_password(password, salt)

            if hashed_password == stored_password:
                # Login successful. Store user details in session
                session['user_id'] = user[0]  
                session['user_role'] = role
                if role == 'coach':
                    return redirect(url_for('coach_dashboard'))
                elif role == 'athlete':
                    return redirect(url_for('athlete_dashboard'))
            else:
                error = 'Incorrect username or password.'

        else:
            error = 'Incorrect username or password.'

    return render_template('login.html', error=error)


#coach dashboard
@app.route('/coach_dashboard', methods=['GET', 'POST'])
def coach_dashboard(user=None):
    user = current_user()  # Get the current logged-in user
    if not user or not isinstance(user, Coach):  # Ensure it's a coach
        flash('You do not have permission to access this page.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        auth_code = request.form['auth_code']

        # Use the manual ORM method to fetch athlete with the provided auth code
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM athlete WHERE auth_code=?", (auth_code,))
        athlete = cursor.fetchone()

        if athlete:
            print(f"Found athlete with ID: {athlete[0]} and current coach ID: {athlete[5]}")
            if athlete[4]:  # Check if athlete already has a coach (coach_id is not None)
                flash('Athlete is already associated with a coach.', 'warning')
            else:
                # Associate the athlete with the currently logged-in coach
                cursor.execute("UPDATE athlete SET coach_id=? WHERE auth_code=?", (user.id, auth_code))
                db.commit()
                flash('Athlete added successfully!', 'success')
        else:
            print(f"No athlete found with auth_code: {auth_code}")
            flash('Invalid authentication code.', 'danger')

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM athlete WHERE coach_id=?", (user.id,))
    athletes = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    athletes_list = [dict(zip(columns, athlete)) for athlete in athletes]

    # Fetch macro and calorie data for each athlete
    today = date.today()
    for athlete_dict in athletes_list:
        athlete_id = athlete_dict['id']
        # Get total macros and calories for the day
        cursor.execute(
            "SELECT SUM(calories), SUM(carbs), SUM(protein), SUM(fats) FROM food_entry WHERE athlete_id = ? AND entry_date = ?", 
            (athlete_id, today)
        )
        total_values = cursor.fetchone()
        athlete_dict['total_calories'] = total_values[0] or 0
        athlete_dict['total_carbs'] = total_values[1] or 0
        athlete_dict['total_protein'] = total_values[2] or 0
        athlete_dict['total_fats'] = total_values[3] or 0

    return render_template('coach_dashboard.html', athletes=athletes_list)



@app.route('/update_calorie_goal', methods=['POST'])
def update_calorie_goal(user=None): # <-- Add the 'user' parameter here
    athlete_id = request.form.get('athlete_id')
    new_calorie_goal = request.form.get('calorie_goal')

    if not athlete_id or not new_calorie_goal:
        flash('Invalid request. Please try again.', 'danger')
        return redirect(url_for('coach_dashboard'))

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("UPDATE athlete SET calorie_goal=? WHERE id=?", (new_calorie_goal, athlete_id))
        db.commit()
        flash('Calorie goal updated successfully!', 'success')
    except Exception as e:
        flash('An error occurred: ' + str(e), 'danger')

    return redirect(url_for('coach_dashboard'))



@app.route('/athlete_dashboard')
def athlete_dashboard(): 
    db = get_db()
    cursor = db.cursor()

    athlete_id = session.get('user_id')
    if not athlete_id:
        flash('Athlete ID not found. Please log in again.')
        return redirect(url_for('login'))

    cursor.execute("SELECT * FROM athlete WHERE id=?", (athlete_id,))
    athlete = cursor.fetchone()

    # Convert the athlete tuple to a dictionary
    columns = [desc[0] for desc in cursor.description]
    athlete = dict(zip(columns, athlete))

    # Get the current date
    today = date.today()

    # Fetch food entries for the current day
    cursor.execute(
        "SELECT food_name, calories, carbs, protein, fats, id FROM food_entry WHERE athlete_id = ? AND entry_date = ?", 
        (athlete_id, today)
    )

    # Get total macros and calories for the day
    cursor.execute(
        "SELECT SUM(calories), SUM(carbs), SUM(protein), SUM(fats) FROM food_entry WHERE athlete_id = ? AND entry_date = ?", 
        (athlete_id, today)
    )
    total_values = cursor.fetchone()
    total_calories = total_values[0] or 0
    total_carbs = total_values[1] or 0
    total_protein = total_values[2] or 0
    total_fats = total_values[3] or 0

    # Get coach details if there's an associated coach
    coach = None
    if athlete['coach_id']:  # If athlete has a coach_id
        cursor.execute("SELECT * FROM coach WHERE id=?", (athlete['coach_id'],))
        coach = cursor.fetchone()
    
    # For the weight scatter plot
    cursor.execute("SELECT date, weight FROM weight_log WHERE athlete_id=?", (athlete_id,))
    weight_entries = cursor.fetchall()

    # Convert to only date portion for the graph
    athlete_weight_data = [{"x": entry[0], "y": entry[1]} for entry in weight_entries]

    return render_template('athlete_dashboard.html', athlete=athlete, coach=coach, total_calories=total_calories, total_carbs=total_carbs, total_protein=total_protein, 
    total_fats=total_fats, athlete_weight_data=athlete_weight_data)


@app.route('/calorie_counter')
def calorie_counter():
    athlete_id = session.get('user_id')
    if not athlete_id:
        flash('Athlete ID not found. Please log in again.')
        return redirect(url_for('login'))  # Adjust to your login route if different

    # Get the current date
    today = date.today()

    db = get_db()
    cursor = db.cursor()

    # Fetch food entries for the current day
    cursor.execute(
        "SELECT food_name, calories, carbs, protein, fats, id FROM food_entry WHERE athlete_id = ? AND entry_date = ?", 
        (athlete_id, today)
    )
    daily_foods = cursor.fetchall()

    # Get total macros and calories for the day
    cursor.execute(
        "SELECT SUM(calories), SUM(carbs), SUM(protein), SUM(fats) FROM food_entry WHERE athlete_id = ? AND entry_date = ?", 
        (athlete_id, today)
    )
    total_values = cursor.fetchone()
    total_calories = total_values[0] or 0
    total_carbs = total_values[1] or 0
    total_protein = total_values[2] or 0
    total_fats = total_values[3] or 0
    # Get macro goals from the 'athlete' table
    cursor.execute(
        "SELECT calorie_goal FROM athlete WHERE id=?", 
        (athlete_id,)
    )
    goal = cursor.fetchone()
    calorie_goal = goal if goal else (0)

    return render_template(
        'calorie_counter.html', 
        daily_foods=daily_foods, 
        total_calories=total_calories, 
        total_carbs=total_carbs, 
        total_protein=total_protein, 
        total_fats=total_fats, 
        calorie_goal=calorie_goal, 
    )

@app.route('/search_food', methods=['POST'])
def search_food():
    query = request.form.get('food_query')
    
    # First, check the local cache
    foods_from_cache = search_food_in_cache(query)
    
    foods_to_display = foods_from_cache  # Start with cached results

    # If less than 10 results from cache, fetch more from USDA API
    if len(foods_from_cache) < 10:
        num_results_needed = 10 - len(foods_from_cache)
        foods_from_api = search_food_in_usda_api(query, limit=num_results_needed)
        foods_to_display.extend(foods_from_api)  # Add API results to the list

    return render_template('calorie_counter.html', foods=foods_to_display)


@app.route('/add_food', methods=['POST'])
def add_selected_food():
    # Step 1: Ensure athlete_id is available in the session
    athlete_id = session.get('user_id')
    if not athlete_id:
        flash('Athlete ID not found. Please log in again.')
        return redirect(url_for('login'))  # Adjust to your login route if different

    food_name = request.form.get('food_name')
    calories = float(request.form.get('calories', 0.0)) # Adjusted the order here
    protein = float(request.form.get('protein', 0.0)) # Adjusted the order here
    carbs = float(request.form.get('carbs', 0.0))     # Adjusted the order here
    fats = float(request.form.get('fats', 0.0))       # Adjusted the order here
    

     
    # Step 2: Check if the food is in the cache
    cached_food = search_food_in_cache(food_name)
    
    if not cached_food:
        # If not in cache (meaning it came from the USDA API), save it to cache
        food_details = {
            'food_name': food_name,
            'calories': calories,
            'protein': protein,
            'carbs': carbs,
            'fats': fats
        }
        save_to_cache(food_details)
    
    # Add the food to the athlete's daily intake
    db = get_db()
    cursor = db.cursor()
    
    today = date.today()

    # Including the 'calories' column in the SQL INSERT statement
    cursor.execute(
    "INSERT INTO food_entry (food_name, calories, carbs, protein, fats, athlete_id, entry_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
    (food_name, calories, carbs, protein, fats, athlete_id, today)
    )
    db.commit()
    
    flash('Food added successfully!')
    return redirect(url_for('calorie_counter'))



#logout
@app.route('/logout')
def logout():
    # Remove user data from session
    session.pop('user_id', None)
    session.pop('user_role', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


UPLOAD_FOLDER = '/Users/danielresnikoff/Desktop/Comp. Sci IA/IA_FLASK/static/uploads' #change to run in any device
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/add_weight', methods=['POST'])
def add_weight():
    weight = request.form.get('weight')
    entry_date = request.form.get('date') or date.today().strftime('%Y-%m-%d')
    image = request.files['image']

    if image and allowed_file(image.filename):
        filename = secure_filename(image.filename)
        
        # Save the image to the local directory
        image_path_local = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path_local)

        # Store only the relative path in the database
        relative_image_path = os.path.join('static', 'uploads', filename)

        db = get_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO weight_log (athlete_id, date, weight, image_path) VALUES (?, ?, ?, ?)",
                       (session['user_id'], entry_date, weight, relative_image_path))
        db.commit()

    return redirect(url_for('athlete_dashboard'))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/weight_log', methods=['GET', 'POST'])
def weight_log():
    db = get_db()
    cursor = db.cursor()

    athlete_id = session.get('user_id')
    if not athlete_id:
        flash('Athlete ID not found. Please log in again.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Handle the removal of a log
        log_id = request.form.get('remove_log')
        if log_id:
            cursor.execute("DELETE FROM weight_log WHERE id=?", (log_id,))
            db.commit()
            flash('Log removed successfully!')

    # Fetch the logs
    cursor.execute("SELECT id, date, weight, image_path FROM weight_log WHERE athlete_id = ? ORDER BY date ASC", (athlete_id,))
    logs = cursor.fetchall()

    return render_template('weight_log.html', logs=logs)

@app.route('/coach_view_weight_log/<int:athlete_id>')
def coach_view_weight_log(athlete_id):
    db = get_db()
    cursor = db.cursor()

    # Fetch the weight logs of the given athlete
    cursor.execute("SELECT id, date, weight, image_path FROM weight_log WHERE athlete_id = ? ORDER BY date ASC", (athlete_id,))
    logs = cursor.fetchall()

    return render_template('coach_view_weight_log.html', logs=logs)


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        role = request.form.get('role')  # Either 'athlete' or 'coach'
        print(f"Received email: {email} with role: {role}")  # Debug print
        
        # Check if email exists in the database
        db = get_db()
        cursor = db.cursor()
        
        # Depending on the role, check the respective table
        if role == "coach":
            cursor.execute("SELECT id FROM coach WHERE email=?", (email,))
        else:
            cursor.execute("SELECT id FROM athlete WHERE email=?", (email,))
        
        user = cursor.fetchone()
        
        if user:
            print("User found in the database. Attempting to send email.")  # Debug print
            # Send email with the reset link
            send_reset_email(email)
            
            flash('A reset link has been sent to your email.', 'info')
            return redirect(url_for('login'))
        
        else:
            print("User not found in the database.")  # Debug print
            flash('Email not found.', 'danger')
            return redirect(url_for('forgot_password'))
    
    # This is for the GET request
    return render_template('forgot_password.html')  

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form.get('email')
    else:
        email = request.args.get('email')

    print(f"Reset password for email: {email}")

    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if new_password == confirm_password:
            hashed_password, salt = hash_password(new_password)
            try:
                conn = sqlite3.connect('site.db')
                cursor = conn.cursor()

                cursor.execute("SELECT id FROM coach WHERE email=?", (email,))
                user = cursor.fetchone()
                print(f"User in coach table: {user}")

                if not user:
                    cursor.execute("SELECT id FROM athlete WHERE email=?", (email,))
                    user = cursor.fetchone()
                    table_name = "athlete"
                    print(f"User in athlete table: {user}")
                else:
                    table_name = "coach"

                if user:
                    cursor.execute(f"UPDATE {table_name} SET password=?, salt=? WHERE email=?", (hashed_password, salt, email))
                    conn.commit()

                    cursor.execute(f"SELECT password, salt FROM {table_name} WHERE email=?", (email,))
                    updated_user = cursor.fetchone()
                    if updated_user:
                        print("Updated password:", updated_user[0])
                        print("Updated salt:", updated_user[1])

                    flash('Your password has been updated!', 'success')
                    return redirect(url_for('login'))
                else:
                    print("No user found in either table.")
                    flash('Invalid reset link or email not found.', 'danger')
                    return redirect(url_for('login'))

            except sqlite3.Error as e:
                print("Database error:", e)
                flash('An error occurred while updating your password.', 'danger')

            finally:
                conn.close()

        else:
            flash('Passwords do not match!', 'danger')

    return render_template('reset_password.html')
