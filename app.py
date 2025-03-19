from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import uuid  

app = Flask(__name__)
app.secret_key = 'supersecretkey'

def init_db():
    """Initialize the database with required tables."""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS quizzes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS questions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        quiz_id INTEGER,
                        question TEXT NOT NULL,
                        option1 TEXT NOT NULL,
                        option2 TEXT NOT NULL,
                        option3 TEXT NOT NULL,
                        option4 TEXT NOT NULL,
                        correct_option INTEGER NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS scores (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        quiz_id INTEGER,
                        score INTEGER)''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    """Redirect users to login/register if they are not authenticated."""
    if 'user_id' not in session:
        return redirect(url_for('register'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route."""
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Username already exists."
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login route."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['is_guest'] = False
            return redirect(url_for('index'))
        else:
            return "Invalid credentials."
    return render_template('login.html')

@app.route('/guest')
def guest():
    """Create a guest account and log the user in."""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    guest_name = f"Guest_{uuid.uuid4().hex[:6]}"  # Generate unique guest name
    cursor.execute("INSERT INTO users (username, password) VALUES (?, NULL)", (guest_name,))
    conn.commit()
    
    cursor.execute("SELECT id FROM users WHERE username = ?", (guest_name,))
    guest_id = cursor.fetchone()[0]

    session['user_id'] = guest_id
    session['is_guest'] = True  # Mark this session as a guest session

    conn.close()
    return redirect(url_for('quiz'))

@app.route('/logout')
def logout():
    """Log out the user and remove guest accounts."""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    if session.get('is_guest'):
        # Delete guest account from database
        cursor.execute("DELETE FROM users WHERE id = ?", (session['user_id'],))
        conn.commit()

    session.pop('user_id', None)
    session.pop('is_guest', None)
    
    conn.close()
    return redirect(url_for('index'))

@app.route('/quiz')
def quiz():
    """Only allow logged-in users or guests to access the quiz."""
    if 'user_id' not in session:
        return redirect(url_for('register'))
    return render_template('quiz.html')

@app.route('/scoreboard')
def scoreboard():
    """Retrieve and display scores from the database."""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT users.username, IFNULL(quizzes.title, 'Ukjent Quiz'), scores.score
        FROM scores
        JOIN users ON scores.user_id = users.id
        LEFT JOIN quizzes ON scores.quiz_id = quizzes.id
        ORDER BY scores.score DESC
    ''')
    scores = cursor.fetchall()
    conn.close()
    
    return render_template('scoreboard.html', scores=scores)


if __name__ == '__main__':
    init_db()
    app.run(debug=True)

#fix scoreboard
