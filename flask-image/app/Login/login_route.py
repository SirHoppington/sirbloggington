from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session
from flask_login import login_user, login_required, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from app.User.user_model import User
from app.Subscriber.subscriber_model import Subscriber
from app import db
import hashlib, hmac

login = Blueprint('login', __name__)

@login.route('/signup', methods=['POST',"GET", "POST"])
def signup_post():

    if request.method == 'POST':

        email = "nickhopgood@gmail.com"
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database

        if user: # if a user is found, we want to redirect back to signup page so user can try again
            flash('Email address signed up.')
            return redirect(url_for('login.signup_post'))

        # create a new user with the form data. Hash the password so the plaintext version isn't saved.
        new_user = User(email=email, password=generate_password_hash(password, method='sha256'), firstname="nick", lastname="hopgood", role="admin")

        # add the new user to the database
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login.log_in'))
    return render_template('signup.html')

@login.route('/register', methods=['POST',"GET", "POST"])
@login_required
def register():

    if request.method == 'POST':

        email = "nickhopgood@gmail.com"
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database

        if user: # if a user is found, we want to redirect back to signup page so user can try again
            flash('Email address signed up.')
            return redirect(url_for('login.signup_post'))

        # create a new user with the form data. Hash the password so the plaintext version isn't saved.
        new_user = User(email=email, password=generate_password_hash(password, method='sha256'), firstname="nick", lastname="hopgood", role="admin")

        # add the new user to the database
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login.log_in'))
    return render_template('signup.html')


@login.route('/login', methods=["GET", "POST"])
def log_in():

    if request.method == 'POST':

        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(email=email).first()

        if user.password.startswith("sha256$"):
            user.password = generate_password_hash(password)
            db.session.commit()

        # check if the user actually exists
        # take the user-supplied password, hash it, and compare it to the hashed password in the database
        if not user or not check_password_hash(user.password, password):
            flash('Please check your login details and try again.')
            return redirect(url_for('login.log_in')) # if the user doesn't exist or password is wrong, reload the page

    # if the above check passes, then we know the user has the right credentials
        login_user(user, remember=remember)
        return redirect('/admin')

    return render_template('login.html')

@login.route('/logout')
@login_required
def logout():
    logout_user()
    if session.get('was_once_logged_in'):
        # prevent flashing automatically logged out message
        del session['was_once_logged_in']
    flash('You have successfully logged yourself out.')
    return redirect('/login')

@login.route('/subscribe', methods=['POST'])
def subscribe():

    if request.method == 'POST':

        name = request.form.get('name')
        email = request.form.get('email')

        subscriber = Subscriber.query.filter_by(email=email).first() # if this returns a email, then the email already exists in database

        if subscriber: # if an email is found, we want advise email is already signed up
            flash('Email address signed up.')
            return redirect(request.referrer)

        # create a new user with the form data. Hash the password so the plaintext version isn't saved.
        new_subscriber = Subscriber(name=name, email=email)

        # add the new user to the database
        db.session.add(new_subscriber)
        db.session.commit()

        return "Welcome {} thanks for subscribing!".format(name)

@login.route('/test')
def test():
    if current_user.is_authenticated:
        return f"Logged in as: {current_user.email}"
    return "Not logged in"

def verify_password(stored_hash, password):
    """
    Supports both:
    - Modern Werkzeug hashes (pbkdf2:sha256:260000$...)
    - Old legacy hashes (sha256$<salt>$<hash>)
    """
    try:
        return check_password_hash(stored_hash, password)
    except ValueError:
        # Handle legacy hashes
        if stored_hash.startswith("sha256$"):
            try:
                _, salt, hash_val = stored_hash.split("$")
            except ValueError:
                return False

            test_hash = hashlib.sha256((salt + password).encode()).hexdigest()
            return hmac.compare_digest(test_hash, hash_val)

        # Unrecognised format
        return False