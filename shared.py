from flask import Flask, flash, redirect, render_template, request, url_for, session
import os
import sqlite3
from functools import wraps

#flask settings and setup (for webapp to launch)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'site.db')
app.config['SECRET_KEY'] = '123456789'  # needed for section to work

#classes
class Coach:
    def __init__(self, id, username, password, salt, email):
        self.id = id
        self.username = username
        self.password = password
        self.salt = salt
        self.email = email

class Athlete:
    def __init__(self, id, username, password, salt, auth_code, coach_id, calorie_goal, email):
        self.id = id
        self.username = username
        self.password = password
        self.salt = salt
        self.auth_code = auth_code
        self.coach_id = coach_id
        self.calorie_goal = calorie_goal
        self.email = email


#function to restrict access if in login restricted area
def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        user = current_user()
        if not user:  # Check if the user is not logged in
            flash('You need to be logged in to view this page.', 'warning')
            return redirect(url_for('login'))
        return view(user=user, **kwargs)  # Pass the user object to the views
    return wrapped_view

#!!! futurely apply this to the login restricted areas
#needs to be updated to separate coach and athlete

#current user funtion
def current_user():
    user_id = session.get('user_id')
    user_role = session.get('user_role')
    
    db = get_db()
    cursor = db.cursor()
    
    if user_role == 'coach':
        cursor.execute("SELECT * FROM coach WHERE id=?", (user_id,))
        user = cursor.fetchone()
        if user:
            return Coach(*user)
    
    elif user_role == 'athlete':
        cursor.execute("SELECT * FROM athlete WHERE id=?", (user_id,))
        user = cursor.fetchone()
        if user:
            return Athlete(*user)
    
    return None

def get_db():
    db = sqlite3.connect('site.db')
    return db
