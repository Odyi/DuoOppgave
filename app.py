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
                        title TEXT NOT NULL,
                        creator_id INTEGER)''')
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
    cursor.execute('''CREATE TABLE IF NOT EXISTS winners (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        points INTEGER,
                        quiz_id INTEGER,
                        FOREIGN KEY (user_id) REFERENCES users(id),
                        FOREIGN KEY (quiz_id) REFERENCES quizzes(id))''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    """Redirect users to login/register if they are not authenticated."""
    if 'user_id' not in session:
        return redirect(url_for('register'))
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM quizzes")
    quizzes = cursor.fetchall()
    conn.close()
    return render_template('index.html', quizzes=quizzes)

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
            session['username'] = user[1]
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
    return redirect(url_for('index'))

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

@app.route('/create_quiz', methods=['GET', 'POST'])
def create_quiz():
    """Allow registered users to create quizzes."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        user_id = session['user_id']
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO quizzes (title, creator_id) VALUES (?, ?)", (title, user_id))
        quiz_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return redirect(url_for('add_questions', quiz_id=quiz_id))
    return render_template('create_quiz.html')

@app.route('/add_questions/<int:quiz_id>', methods=['GET', 'POST'])
def add_questions(quiz_id):
    """Allow users to add questions to a quiz."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        question = request.form['question']
        option1 = request.form['option1']
        option2 = request.form['option2']
        option3 = request.form['option3']
        option4 = request.form['option4']
        correct_option = request.form['correct_option']
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO questions (quiz_id, question, option1, option2, option3, option4, correct_option) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                       (quiz_id, question, option1, option2, option3, option4, correct_option))
        conn.commit()
        conn.close()
        return redirect(url_for('add_questions', quiz_id=quiz_id))
    return render_template('add_questions.html', quiz_id=quiz_id)

@app.route('/quiz/<int:quiz_id>')
def quiz(quiz_id):
    """Retrieve and display the quiz."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, question, option1, option2, option3, option4 FROM questions WHERE quiz_id = ?", (quiz_id,))
    questions = cursor.fetchall()
    conn.close()
    return render_template('quiz.html', questions=questions, quiz_id=quiz_id)

@app.route('/api/questions/<int:quiz_id>')
def api_questions(quiz_id):
    """API endpoint to retrieve questions for a specific quiz."""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, question, option1, option2, option3, option4 FROM questions WHERE quiz_id = ?", (quiz_id,))
    questions = cursor.fetchall()
    conn.close()
    return jsonify(questions)

@app.route('/submit_quiz/<int:quiz_id>', methods=['POST'])
def submit_quiz(quiz_id):
    """Handle the submission of quiz answers and calculate score."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    answers = request.json.get('answers')  # Get answers from the request
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    score = 0
    for qid, answer in answers.items():
        cursor.execute("SELECT correct_option FROM questions WHERE id = ?", (qid,))
        correct_option = cursor.fetchone()[0]
        if correct_option == answer:
            score += 1
    
    cursor.execute("INSERT INTO scores (user_id, quiz_id, score) VALUES (?, ?, ?)", (user_id, quiz_id, score))
    cursor.execute("INSERT INTO winners (user_id, quiz_id, points) VALUES (?, ?, ?)", (user_id, quiz_id, score))
    conn.commit()
    conn.close()
    
    return jsonify({'score': score})

@app.route('/scoreboard')
def scoreboard():
    """Retrieve and display scores from the database."""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT users.username, quizzes.title, winners.points
        FROM winners
        JOIN users ON winners.user_id = users.id
        JOIN quizzes ON winners.quiz_id = quizzes.id
        ORDER BY winners.points DESC
    ''')
    scores = cursor.fetchall()
    conn.close()
    
    return render_template('scoreboard.html', scores=scores)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)