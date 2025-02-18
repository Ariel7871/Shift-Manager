import sqlite3
from datetime import date, timedelta, datetime
import calendar
import holidays
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
DATABASE = 'database.db'

# ----------------------------
# Database Helpers
# ----------------------------
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    with conn:
        # Create users table.
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        # Create shifts table with a pending flag.
        conn.execute('''
            CREATE TABLE IF NOT EXISTS shifts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                week_start DATE NOT NULL,
                day TEXT NOT NULL,
                shift_type TEXT NOT NULL,
                pending INTEGER DEFAULT 0,
                UNIQUE(user_id, week_start, day),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
    # Insert default users if not present.
    for worker in ['Ariel', 'Roei', 'Ofek', 'Guy']:
        try:
            conn.execute('INSERT INTO users (name) VALUES (?)', (worker,))
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()

init_db()

# ----------------------------
# Helper Functions for Weeks and Months
# ----------------------------
def get_current_week_start():
    """Return the date of the most recent Sunday (or today if Sunday)."""
    today = date.today()
    days_since_sunday = (today.weekday() + 1) % 7
    return today - timedelta(days=days_since_sunday)

def get_next_week_start():
    return get_current_week_start() + timedelta(weeks=1)

def get_week_start(dt):
    """Return the Sunday of the week for the given date dt."""
    days_since_sunday = (dt.weekday() + 1) % 7
    return dt - timedelta(days=days_since_sunday)

# ----------------------------
# Routes
# ----------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/choose_schedule')
def choose_schedule():
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    return render_template('choose_schedule.html', users=users)

@app.route('/schedule/<int:user_id>', methods=['GET', 'POST'])
def schedule(user_id):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        flash("User not found!")
        return redirect(url_for('choose_schedule'))
    
    num_weeks = 4
    upcoming_weeks = [get_current_week_start() + timedelta(weeks=i) for i in range(num_weeks)]
    
    week_options = []
    for i, ws in enumerate(upcoming_weeks):
        if i == 0:
            label = "This Week"
        elif i == 1:
            label = "Next Week"
        else:
            week_end = ws + timedelta(days=4)
            label = f"{ws.strftime('%d/%m/%y')} - {week_end.strftime('%d/%m/%y')}"
        week_options.append({"index": i, "label": label, "week_start": ws})
    
    week_index = request.args.get("week_index", 0, type=int)
    if week_index < 0 or week_index >= num_weeks:
        week_index = 0
    target_week = upcoming_weeks[week_index]
    
    days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday']
    
    existing_shifts = conn.execute(
        "SELECT * FROM shifts WHERE user_id = ? AND week_start = ?",
        (user_id, target_week.isoformat())
    ).fetchall()
    
    prefill = {}
    if existing_shifts:
        for row in existing_shifts:
            prefill[row["day"]] = row["shift_type"]

    if request.method == "POST":
        move_next = request.form.get("nextWeekCheck") == "on"

        for day in days:
            field_name = f"{target_week.isoformat()}_{day}"
            shift_choice = request.form.get(field_name)

            if shift_choice in ["Day", "Night", "OOO"]:
                if day == "Sunday" and shift_choice == "Night":
                    shift_choice = "Day"

                conn.execute("""
                    INSERT OR REPLACE INTO shifts (user_id, week_start, day, shift_type, pending)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, target_week.isoformat(), day, shift_choice, 1))

        conn.commit()
        conn.close()
        
        flash("Your schedule has been submitted.")

        if move_next and week_index < len(upcoming_weeks) - 1:
            return redirect(url_for("schedule", user_id=user_id, week_index=week_index + 1))

        return redirect(url_for("view_schedule", user_id=user_id))

    conn.close()
    header_text = "Set Your Shifts for " if not existing_shifts else "Update Your Shifts for "
    if week_index == 0:
        header_text += "This Week"
    elif week_index == 1:
        header_text += "Next Week"
    else:
        week_end = target_week + timedelta(days=4)
        header_text += f"{target_week.strftime('%d/%m/%y')} - {week_end.strftime('%d/%m/%y')}"

    return render_template("schedule_week.html",
                           user=user,
                           week=target_week,
                           days=days,
                           prefill=prefill,
                           header_text=header_text,
                           week_index=week_index,
                           week_options=week_options)

@app.route('/view_schedule/<int:user_id>')
def view_schedule(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        flash("User not found!")
        return redirect(url_for('choose_schedule'))
    conn.close()
    return render_template('view_schedule.html', user=user)

@app.route('/view_schedule')
def view_schedule_global():
    return redirect(url_for('view_all_schedule'))

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

@app.route('/approve_changes/<int:user_id>', methods=['POST'])
def approve_changes(user_id):
    if not session.get('admin'):
        return redirect(url_for('admin'))
    week = get_next_week_start()
    conn = get_db_connection()
    conn.execute('''
        UPDATE shifts 
        SET pending = 0 
        WHERE user_id = ? AND week_start = ? AND pending = 1
    ''', (user_id, week.isoformat()))
    conn.commit()
    conn.close()
    flash("Changes approved for the user.")
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    app.run(debug=True)
