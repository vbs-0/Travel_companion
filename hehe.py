from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_sitemapper import Sitemapper
import bcrypt
import requests
import datetime
import bard, os
from dotenv import load_dotenv

# Load the environment variables
load_dotenv()
api_key = os.environ.get("Weather")
secret_key = os.environ.get("SECRET_KEY")

# Initialize the app
app = Flask(__name__)
sitemapper = Sitemapper(app=app)  # Create and initialize the sitemapper
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.secret_key = secret_key

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf8'), 
                                    bcrypt.gensalt()).decode('utf8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf8'), 
                            self.password.encode('utf8'))

with app.app_context():
    db.create_all()

def get_weather_data(api_key: str, location: str, start_date: str, end_date: str) -> dict:
    """
    Retrieves weather data from Visual Crossing Weather API for a given location and date range.
    """
    base_url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{location}/{start_date}/{end_date}?unitGroup=metric&include=days&key={api_key}&contentType=json"

    try:
        response = requests.get(base_url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print("Error:", str(e))
        raise

def login_required(f):
    """Decorator to check if user is logged in"""
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please login to access this page.", "info")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@sitemapper.include()
@app.route('/', methods=["GET", "POST"])
@login_required
def index():
    """
    Main route handling both the display of the form and form submission.
    """
    if request.method == "POST":
        # Get form data
        source = request.form.get("source")
        destination = request.form.get("destination")
        start_date = request.form.get("date")
        end_date = request.form.get("return")

        # Validate form data
        if not all([source, destination, start_date, end_date]):
            flash("Please fill in all fields.", "danger")
            return redirect(url_for("index"))

        try:
            # Calculate number of days
            no_of_day = (datetime.datetime.strptime(end_date, "%Y-%m-%d") - 
                        datetime.datetime.strptime(start_date, "%Y-%m-%d")).days
            
            if no_of_day < 0:
                flash("Return date must be after travel date.", "danger")
                return redirect(url_for("index"))

            # Get weather data
            weather_data = get_weather_data(api_key, destination, start_date, end_date)
            
            # Generate itinerary
            plan = bard.generate_itinerary(source, destination, start_date, end_date, no_of_day)
            
            return render_template("dashboard.html", 
                                 weather_data=weather_data, 
                                 plan=plan)

        except ValueError:
            flash("Invalid date format. Please use YYYY-MM-DD.", "danger")
        except requests.exceptions.RequestException:
            flash("Error fetching weather data. Please try again.", "danger")
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "danger")
        
        return redirect(url_for("index"))

    return render_template('index.html')

@sitemapper.include()
@app.route("/about")
@login_required
def about():
    """Renders the about page"""
    return render_template("about.html")

@sitemapper.include()
@app.route("/contact")
@login_required
def contact():
    """Renders the contact page"""
    user_email = session.get('user_email', "Enter your email")
    user_name = session.get('user_name', "Enter your name")
    return render_template("contact.html", 
                         user_email=user_email, 
                         user_name=user_name, 
                         message='')

@sitemapper.include()
@app.route("/login", methods=["GET", "POST"])
def login():
    """Handle user login"""
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            flash("Please provide both email and password.", "danger")
            return redirect(url_for("login"))

        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            session["user_id"] = user.id
            session["user_name"] = user.name
            session["user_email"] = user.email
            flash("Login successful!", "success")
            return redirect(url_for("index"))
        
        flash("Invalid email or password.", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")

@sitemapper.include()
@app.route("/logout")
def logout():
    """Handle user logout"""
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

@sitemapper.include()
@app.route("/register", methods=["GET", "POST"])
def register():
    """Handle user registration"""
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        password2 = request.form.get("password2")

        # Validate input
        if not all([name, email, password, password2]):
            flash("Please fill in all fields.", "danger")
            return redirect(url_for("register"))

        if password != password2:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("register"))

        # Check if user exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered. Please login.", "danger")
            return redirect(url_for("login"))

        # Create new user
        try:
            user = User(name=name, email=email, password=password)
            db.session.add(user)
            db.session.commit()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            db.session.rollback()
            flash("Registration failed. Please try again.", "danger")
            return redirect(url_for("register"))

    return render_template("register.html")

@app.route('/robots.txt')
def robots():
    """Serve robots.txt"""
    return render_template('robots.txt')

@app.route("/sitemap.xml")
def r_sitemap():
    """Generate sitemap"""
    return sitemapper.generate()

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(405)
def method_not_allowed(e):
    """Handle 405 Method Not Allowed errors"""
    flash("Invalid request method.", "danger")
    return redirect(url_for("index"))

@app.context_processor
def inject_now():
    """Inject current time into all templates"""
    return {'now': datetime.datetime.now()}

if __name__ == "__main__":
    app.run(debug=True)