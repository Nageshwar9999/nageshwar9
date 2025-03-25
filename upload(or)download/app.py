import os
import logging
from github import Github
from flask import Flask, request, redirect, url_for, render_template, session, flash, send_file
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
from io import BytesIO

# Load environment variables from .env file
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Flask app setup
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")  
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO = os.getenv('GITHUB_REPO')

# Database configuration
DB_CONFIG = {
    "host": os.getenv('DB_HOST'),
    "user": os.getenv('DB_USER'),
    "password": os.getenv('DB_PASSWORD'),
    "database": os.getenv('DB_NAME'),
    "port": int(os.getenv('DB_PORT', 3306))
}

# Database connection using context manager
def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        logging.error(f"Database Connection Error: {e}")
        return None

# Check user credentials (Login)
def check_credentials(key, password):
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT password FROM login WHERE `key` = %s', (key,))
            user = cursor.fetchone()
        return user and check_password_hash(user[0], password)
    except Error as e:
        logging.error(f"Database Query Error: {e}")
        return False
    finally:
        conn.close()

# Add user to database (Signup)
def add_user(key, password):
    conn = get_db_connection()
    if conn is None:
        return
    hashed_password = generate_password_hash(password)
    try:
        with conn.cursor() as cursor:
            cursor.execute('INSERT INTO login (`key`, `password`) VALUES (%s, %s)', (key, hashed_password))
            conn.commit()
    except Error as e:
        logging.error(f"Database Insert Error: {e}")
    finally:
        conn.close()

# Add document info to database
def add_document_to_db(key, filename):
    conn = get_db_connection()
    if conn is None:
        return
    try:
        with conn.cursor() as cursor:
            cursor.execute('INSERT INTO file (`key`, filename) VALUES (%s, %s)', (key, filename))
            conn.commit()
    except Error as e:
        logging.error(f"Database Insert Error: {e}")
    finally:
        conn.close()

# Upload file to GitHub
def upload_to_github(file, filename):
    if not GITHUB_TOKEN or not GITHUB_REPO:
        logging.error("GitHub token or repository is not set in environment variables.")
        return False

    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)
        content = file.read()
        file.seek(0)
        repo.create_file(f"uploads/{filename}", "Upload file", content, branch="main")
        return True
    except Exception as e:
        logging.error(f"GitHub Upload Error: {e}")
        return False

# Flask routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    key = request.form['key']
    password = request.form['password']
    if check_credentials(key, password):
        session['user'] = key
        flash("Login successful!", "success")
        return redirect(url_for('dashboard'))
    else:
        flash("Invalid credentials. Try again.", "danger")
        return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'user' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('index'))

    file = request.files.get('file')
    if file:
        filename = secure_filename(file.filename)
        if upload_to_github(file, filename):
            add_document_to_db(session['user'], filename)
            flash(f"File '{filename}' uploaded successfully!", "success")
        else:
            flash("File upload failed.", "danger")
    return redirect(url_for('dashboard'))

# Additional Routes (Dashboard, View File, Delete File) remain unchanged
