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
    
    # Increase the number of weeks and set the default week to one month ahead (index 4)
    num_weeks = 6
    upcoming_weeks = [get_current_week_start() + timedelta(weeks=i) for i in range(num_weeks)]
    
    # Default to the week one month from today (index 4)
    week_index = request.args.get("week_index", 4, type=int)
    if week_index < 0 or week_index >= num_weeks:
        week_index = 4
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
        action = request.form.get("action")
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
        if action == "move_next" and week_index < len(upcoming_weeks) - 1:
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
                           week_options=[{"index": i, "label": ("This Week" if i == 0 else "Next Week" if i == 1 else f"{(upcoming_weeks[i]).strftime('%d/%m/%y')} - {(upcoming_weeks[i] + timedelta(days=4)).strftime('%d/%m/%y')}"), "week_start": ws} for i, ws in enumerate(upcoming_weeks)]
                           )

@app.route('/view_schedule/<int:user_id>')
def view_schedule(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        flash("User not found!")
        return redirect(url_for('choose_schedule'))
    conn.close()
    return render_template('view_schedule.html', user=user)

# --- New get_schedule_data route returns real data for one month ahead ---
@app.route('/get_schedule_data')
def get_schedule_data():
    allowed_days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]
    start = date.today()
    end = start + timedelta(days=30)
    dates = []
    day_names = []
    current = start
    while current <= end:
        if current.strftime("%A") in allowed_days:
            dates.append(current.strftime("%d/%m/%Y"))
            day_names.append(current.strftime("%A"))
        current += timedelta(days=1)

    conn = get_db_connection()
    users = conn.execute("SELECT * FROM users").fetchall()
    
    schedule_array = []
    for user in users:
        shifts_list = []
        for d_str, d_name in zip(dates, day_names):
            d_obj = datetime.strptime(d_str, "%d/%m/%Y").date()
            week_start = get_week_start(d_obj)
            row = conn.execute(
                "SELECT shift_type FROM shifts WHERE user_id = ? AND week_start = ? AND day = ?",
                (user["id"], week_start.isoformat(), d_name)
            ).fetchone()
            shift = row["shift_type"] if row else "Not set"
            shifts_list.append(shift)
        schedule_array.append({"name": user["name"], "shifts": shifts_list})
    conn.close()

    data = {
        "dates": dates,
        "days": day_names,
        "schedule": schedule_array
    }
    return jsonify(data)

@app.route('/view_schedule')
def view_schedule_global():
    return redirect(url_for('view_all_schedule'))

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

# --- Updated view_all_schedule route: only one month ahead ---
@app.route('/view_all_schedule')
def view_all_schedule():
    from collections import defaultdict
    start = date.today()
    end = start + timedelta(days=30)
    allowed_days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]
    dates = []
    current = start
    while current <= end:
        if current.strftime("%A") in allowed_days:
            dates.append(current)
        current += timedelta(days=1)
    
    # Build month grouping for the standard table
    month_dates = defaultdict(list)
    for d in dates:
        month_label = d.strftime("%B %Y")
        month_dates[month_label].append(d)
    
    # Build user schedules: for each user, map each date to its shift (or "Not set")
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    user_schedules = { user['name']: {} for user in users }
    for d in dates:
        week_start = get_week_start(d)
        day_name = d.strftime("%A")
        for user in users:
            row = conn.execute(
                "SELECT shift_type FROM shifts WHERE user_id = ? AND week_start = ? AND day = ?",
                (user['id'], week_start.isoformat(), day_name)
            ).fetchone()
            shift = row["shift_type"] if row else "Not set"
            user_schedules[user['name']][d] = shift
    conn.close()

    return render_template(
        'view_all_schedule.html',
        users=users,
        user_schedules=user_schedules,
        today=date.today(),
        month_dates=month_dates
    )

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
