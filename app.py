from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3, os, datetime, json

# Resolve paths relative to this file so app works from any directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'static')
)
app.secret_key = 'campus-secret-2024'
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

DB = os.path.join(BASE_DIR, 'campus.db')

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'student',
        department TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS issues (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        category TEXT NOT NULL,
        location TEXT NOT NULL,
        priority TEXT DEFAULT 'Medium',
        status TEXT DEFAULT 'Open',
        image_path TEXT,
        user_id INTEGER,
        assigned_to TEXT,
        resolution_note TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        resolved_at TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        issue_id INTEGER,
        user_id INTEGER,
        comment TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(issue_id) REFERENCES issues(id),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    # Seed admin
    try:
        c.execute("INSERT INTO users (name, email, password, role, department) VALUES (?, ?, ?, ?, ?)",
            ('Admin', 'admin@campus.edu', generate_password_hash('admin123'), 'admin', 'Administration'))
    except: pass
    # Seed student
    try:
        c.execute("INSERT INTO users (name, email, password, role, department) VALUES (?, ?, ?, ?, ?)",
            ('John Student', 'student@campus.edu', generate_password_hash('student123'), 'student', 'Computer Science'))
    except: pass
    # Seed sample issues
    try:
        c.execute("SELECT COUNT(*) FROM issues")
        if c.fetchone()[0] == 0:
            sample_issues = [
                ('Broken AC in Lab 3', 'The air conditioning unit in Lab 3 has been non-functional for 3 days.', 'Infrastructure', 'Lab 3, Block A', 'High', 'In Progress', 2),
                ('WiFi Not Working', 'WiFi connectivity is very poor near the library entrance.', 'IT', 'Library, Ground Floor', 'Medium', 'Open', 2),
                ('Water Leakage in Corridor', 'There is a water leakage from the ceiling in the main corridor.', 'Maintenance', 'Block B, 2nd Floor', 'High', 'Resolved', 2),
                ('Projector Malfunction', 'Projector in seminar hall is showing distorted images.', 'IT', 'Seminar Hall', 'Low', 'Open', 2),
                ('Broken Bench in Cafeteria', 'Multiple benches in the cafeteria are broken and need replacement.', 'Infrastructure', 'Cafeteria', 'Medium', 'Closed', 2),
            ]
            for title, desc, cat, loc, pri, status, uid in sample_issues:
                resolved = 'CURRENT_TIMESTAMP' if status in ('Resolved', 'Closed') else None
                c.execute("INSERT INTO issues (title, description, category, location, priority, status, user_id, resolved_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (title, desc, cat, loc, pri, status, uid, datetime.datetime.now().isoformat() if resolved else None))
    except: pass
    conn.commit()
    conn.close()

# ---- ROUTES ----

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_role'] = user['role']
            return redirect(url_for('dashboard'))
        flash('Invalid credentials. Please try again.', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        department = request.form.get('department', '')
        try:
            conn = get_db()
            conn.execute("INSERT INTO users (name, email, password, department) VALUES (?, ?, ?, ?)",
                (name, email, generate_password_hash(password), department))
            conn.commit()
            conn.close()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already registered.', 'error')
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    if session['user_role'] == 'admin':
        issues = conn.execute('SELECT i.*, u.name as reporter FROM issues i LEFT JOIN users u ON i.user_id=u.id ORDER BY i.created_at DESC').fetchall()
        stats = {
            'total': conn.execute('SELECT COUNT(*) FROM issues').fetchone()[0],
            'open': conn.execute("SELECT COUNT(*) FROM issues WHERE status='Open'").fetchone()[0],
            'in_progress': conn.execute("SELECT COUNT(*) FROM issues WHERE status='In Progress'").fetchone()[0],
            'resolved': conn.execute("SELECT COUNT(*) FROM issues WHERE status IN ('Resolved','Closed')").fetchone()[0],
        }
    else:
        issues = conn.execute('SELECT * FROM issues WHERE user_id=? ORDER BY created_at DESC', (session['user_id'],)).fetchall()
        stats = {
            'total': conn.execute('SELECT COUNT(*) FROM issues WHERE user_id=?', (session['user_id'],)).fetchone()[0],
            'open': conn.execute("SELECT COUNT(*) FROM issues WHERE user_id=? AND status='Open'", (session['user_id'],)).fetchone()[0],
            'in_progress': conn.execute("SELECT COUNT(*) FROM issues WHERE user_id=? AND status='In Progress'", (session['user_id'],)).fetchone()[0],
            'resolved': conn.execute("SELECT COUNT(*) FROM issues WHERE user_id=? AND status IN ('Resolved','Closed')", (session['user_id'],)).fetchone()[0],
        }
    conn.close()
    return render_template('dashboard.html', issues=issues, stats=stats)

@app.route('/report', methods=['GET','POST'])
def report_issue():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        category = request.form['category']
        location = request.form['location']
        priority = request.form.get('priority', 'Medium')
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"{datetime.datetime.now().timestamp()}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_path = filename
        conn = get_db()
        conn.execute("INSERT INTO issues (title, description, category, location, priority, user_id, image_path) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (title, description, category, location, priority, session['user_id'], image_path))
        conn.commit()
        conn.close()
        flash('Issue reported successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('report.html')

@app.route('/issue/<int:issue_id>')
def issue_detail(issue_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    issue = conn.execute('SELECT i.*, u.name as reporter, u.department FROM issues i LEFT JOIN users u ON i.user_id=u.id WHERE i.id=?', (issue_id,)).fetchone()
    comments = conn.execute('SELECT c.*, u.name as commenter, u.role FROM comments c LEFT JOIN users u ON c.user_id=u.id WHERE c.issue_id=? ORDER BY c.created_at ASC', (issue_id,)).fetchall()
    conn.close()
    if not issue:
        flash('Issue not found.', 'error')
        return redirect(url_for('dashboard'))
    if session['user_role'] != 'admin' and issue['user_id'] != session['user_id']:
        flash('Unauthorized.', 'error')
        return redirect(url_for('dashboard'))
    return render_template('issue_detail.html', issue=issue, comments=comments)

@app.route('/issue/<int:issue_id>/update', methods=['POST'])
def update_issue(issue_id):
    if 'user_id' not in session or session['user_role'] != 'admin':
        return redirect(url_for('login'))
    status = request.form['status']
    assigned_to = request.form.get('assigned_to', '')
    resolution_note = request.form.get('resolution_note', '')
    resolved_at = datetime.datetime.now().isoformat() if status in ('Resolved', 'Closed') else None
    conn = get_db()
    conn.execute("UPDATE issues SET status=?, assigned_to=?, resolution_note=?, updated_at=?, resolved_at=? WHERE id=?",
        (status, assigned_to, resolution_note, datetime.datetime.now().isoformat(), resolved_at, issue_id))
    conn.commit()
    conn.close()
    flash('Issue updated successfully!', 'success')
    return redirect(url_for('issue_detail', issue_id=issue_id))

@app.route('/issue/<int:issue_id>/comment', methods=['POST'])
def add_comment(issue_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    comment = request.form.get('comment', '').strip()
    if comment:
        conn = get_db()
        conn.execute("INSERT INTO comments (issue_id, user_id, comment) VALUES (?, ?, ?)",
            (issue_id, session['user_id'], comment))
        conn.commit()
        conn.close()
    return redirect(url_for('issue_detail', issue_id=issue_id))

@app.route('/analytics')
def analytics():
    if 'user_id' not in session or session['user_role'] != 'admin':
        return redirect(url_for('login'))
    conn = get_db()
    by_category = conn.execute("SELECT category, COUNT(*) as count FROM issues GROUP BY category").fetchall()
    by_status = conn.execute("SELECT status, COUNT(*) as count FROM issues GROUP BY status").fetchall()
    by_priority = conn.execute("SELECT priority, COUNT(*) as count FROM issues GROUP BY priority").fetchall()
    by_location = conn.execute("SELECT location, COUNT(*) as count FROM issues GROUP BY location ORDER BY count DESC LIMIT 8").fetchall()
    monthly = conn.execute("SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as count FROM issues GROUP BY month ORDER BY month DESC LIMIT 6").fetchall()
    conn.close()
    return render_template('analytics.html',
        by_category=json.dumps([dict(r) for r in by_category]),
        by_status=json.dumps([dict(r) for r in by_status]),
        by_priority=json.dumps([dict(r) for r in by_priority]),
        by_location=json.dumps([dict(r) for r in by_location]),
        monthly=json.dumps([dict(r) for r in monthly])
    )

@app.route('/all-issues')
def all_issues():
    if 'user_id' not in session or session['user_role'] != 'admin':
        return redirect(url_for('login'))
    category = request.args.get('category', '')
    status = request.args.get('status', '')
    priority = request.args.get('priority', '')
    query = 'SELECT i.*, u.name as reporter FROM issues i LEFT JOIN users u ON i.user_id=u.id WHERE 1=1'
    params = []
    if category: query += ' AND i.category=?'; params.append(category)
    if status: query += ' AND i.status=?'; params.append(status)
    if priority: query += ' AND i.priority=?'; params.append(priority)
    query += ' ORDER BY i.created_at DESC'
    conn = get_db()
    issues = conn.execute(query, params).fetchall()
    conn.close()
    return render_template('all_issues.html', issues=issues, filters={'category': category, 'status': status, 'priority': priority})

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    init_db()
    app.run(debug=True, port=5000)
