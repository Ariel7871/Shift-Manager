import sqlite3
from datetime import date, timedelta
import calendar
import holidays  # pip install holidays
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

# Home Page: Welcome page with two big buttons.
@app.route('/')
def index():
    return render_template('index.html')

# Choose Schedule Page: Let user select his name to schedule shifts.
@app.route('/choose_schedule')
def choose_schedule():
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    return render_template('choose_schedule.html', users=users)

# Weekly scheduling route.
@app.route('/schedule/<int:user_id>', methods=['GET', 'POST'])
def schedule(user_id):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        flash("User not found!")
        return redirect(url_for('choose_schedule'))
    
    # Compute upcoming week start dates for 4 weeks (about one month).
    num_weeks = 4
    upcoming_weeks = [get_current_week_start() + timedelta(weeks=i) for i in range(num_weeks)]
    
    # Build week options with labels.
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
    
    # Get the selected week index from the query parameters.
    week_index = request.args.get("week_index", 0, type=int)
    if week_index < 0 or week_index >= num_weeks:
        week_index = 0
    target_week = upcoming_weeks[week_index]
    
    # Define work days (Sunday to Thursday).
    days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday']
    
    # Query existing schedule for this week.
    existing_shifts = conn.execute(
        "SELECT * FROM shifts WHERE user_id = ? AND week_start = ?",
        (user_id, target_week.isoformat())
    ).fetchall()
    
    prefill = {}
    if existing_shifts:
        for row in existing_shifts:
            prefill[row["day"]] = row["shift_type"]
    
    if request.method == "POST":
        for day in days:
            field_name = f"{target_week.isoformat()}_{day}"
            shift_choice = request.form.get(field_name)
            if shift_choice in ["Day", "Night"]:
                # For Sundays, enforce morning (Day) shift.
                if day == "Sunday" and shift_choice == "Night":
                    shift_choice = "Day"
                conn.execute("""
                    INSERT OR REPLACE INTO shifts (user_id, week_start, day, shift_type, pending)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, target_week.isoformat(), day, shift_choice, 1))
        conn.commit()
        conn.close()
        flash("Your schedule has been submitted.")
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


# View individual schedule (weekly view) for a user.
@app.route('/view_schedule/<int:user_id>')
def view_schedule(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        flash("User not found!")
        return redirect(url_for('choose_schedule'))
    days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday']
    week_current = get_current_week_start()
    week_next = get_next_week_start()
    rows_current = conn.execute(
        'SELECT day, shift_type FROM shifts WHERE user_id = ? AND week_start = ?',
        (user_id, week_current.isoformat())
    ).fetchall()
    schedules_current = {row['day']: row['shift_type'] for row in rows_current}
    rows_next = conn.execute(
        'SELECT day, shift_type FROM shifts WHERE user_id = ? AND week_start = ?',
        (user_id, week_next.isoformat())
    ).fetchall()
    schedules_next = {row['day']: row['shift_type'] for row in rows_next}
    conn.close()
    return render_template('view_schedule.html',
                           user=user,
                           schedules_current=schedules_current,
                           schedules_next=schedules_next,
                           week_current=week_current,
                           week_next=week_next,
                           days=days)

# View all users' schedules in a monthly view (30-day period from current week start)
@app.route('/get_schedule_data')
def get_schedule_data():
    start_date = get_current_week_start()
    end_date = start_date + timedelta(days=30)

    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()

    shifts = conn.execute("""
        SELECT users.name AS user_name, week_start, day, shift_type
        FROM shifts 
        JOIN users ON shifts.user_id = users.id
        WHERE week_start BETWEEN ? AND ?
    """, (start_date.isoformat(), end_date.isoformat())).fetchall()
    conn.close()

    shift_data = {}
    for shift in shifts:
        key = (shift["week_start"], shift["day"])
        if key not in shift_data:
            shift_data[key] = {}
        shift_data[key][shift["user_name"]] = shift["shift_type"]

    dates = []
    schedule = []
    
    for i in range(30):
        current_date = start_date + timedelta(days=i)
        if current_date.strftime("%A") not in ["Friday", "Saturday"]:
            dates.append(current_date.strftime("%d/%m/%Y"))

    for user in users:
        user_shifts = []
        from datetime import datetime  # Ensure this is imported at the top

        for current_date in dates:
            # Convert `current_date` from string to `datetime.date`
            if isinstance(current_date, str):
                current_date = datetime.strptime(current_date, "%d/%m/%Y").date()

            week_start = get_week_start(current_date).isoformat()
            day_name = current_date.strftime("%A")

            shift = shift_data.get((week_start, day_name), {}).get(user["name"], "—")
            
            # Apply "Day" shift default for Sundays
            if day_name == "Sunday" and shift == "—":
                shift = "Day"
            
            user_shifts.append(shift)

        schedule.append({
            "name": user["name"],
            "shifts": user_shifts
        })

    return jsonify({"dates": dates, "schedule": schedule})


    
@app.route('/view_all_schedule')
def view_all_schedule():
    import calendar
    # Adjust the schedule period to start from the current week's start.
    start_date = get_current_week_start()
    end_date = start_date + timedelta(days=30)
    
    # Build list of dates from start_date to end_date, omitting Fridays and Saturdays.
    dates = []
    current_date = start_date
    while current_date <= end_date:
        if current_date.strftime("%A") not in ["Friday", "Saturday"]:
            dates.append(current_date)
        current_date += timedelta(days=1)
    
    # Load Israeli public holidays for the relevant years.
    israel_holidays = holidays.Israel(years=[start_date.year, end_date.year])
    
    # Fetch all users.
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    
    # For each user, load schedule rows for the period.
    user_schedules = {}
    for user in users:
        rows = conn.execute("""
            SELECT week_start, shift_type, day FROM shifts 
            WHERE user_id = ? AND week_start BETWEEN ? AND ?
        """, (user['id'], start_date.isoformat(), end_date.isoformat())).fetchall()
        schedule = {}
        # Build a nested dict: { week_start (as ISO string): { day: shift_type, ... } }
        for row in rows:
            week = row['week_start']  # kept as ISO string
            day = row['day']
            shift = row['shift_type']
            if week not in schedule:
                schedule[week] = {}
            schedule[week][day] = shift
        user_schedules[user['name']] = schedule
    conn.close()
    
    # Build schedule_data: one entry per date.
    schedule_data = []
    for dt in dates:
        is_holiday = dt in israel_holidays
        holiday_name = israel_holidays.get(dt) if is_holiday else ""
        week_start_iso = get_week_start(dt).isoformat()  # Compute the week's Sunday as an ISO string
        schedule_data.append({
            "date": dt,
            "day_name": dt.strftime("%A"),
            "is_holiday": is_holiday,
            "holiday_name": holiday_name,
            "week_start": week_start_iso
        })
    
    # Group schedule_data by month label.
    grouped_schedule_data = {}
    for entry in schedule_data:
        month_label = entry["date"].strftime("%B %Y")
        if month_label not in grouped_schedule_data:
            grouped_schedule_data[month_label] = []
        grouped_schedule_data[month_label].append(entry)
    
    today = date.today()  # Pass today's date to the template
    return render_template("view_all_schedule.html",
                           users=users,
                           grouped_schedule_data=grouped_schedule_data,
                           user_schedules=user_schedules,
                           today=today)

# Global view schedule (alternative route)
@app.route('/view_schedule')
def view_schedule_global():
    return redirect(url_for('view_all_schedule'))

# Admin login and dashboard routes.
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == '123123':
            session['admin'] = True
            return redirect(url_for('admin_panel'))
        else:
            flash("Invalid credentials!")
    return render_template('admin.html')

@app.route('/admin_panel', methods=['GET', 'POST'])
def admin_panel():
    if not session.get('admin'):
        return redirect(url_for('admin'))
    conn = get_db_connection()
    week = get_next_week_start()
    days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday']
    users = conn.execute('SELECT * FROM users').fetchall()
    schedules = {}
    pending_changes = []
    for user in users:
        rows = conn.execute('''
            SELECT day, shift_type, pending FROM shifts 
            WHERE user_id = ? AND week_start = ?
        ''', (user['id'], week.isoformat())).fetchall()
        user_schedule = {row['day']: row['shift_type'] for row in rows}
        schedules[user['id']] = user_schedule
        pending_rows = conn.execute('''
            SELECT day, shift_type FROM shifts 
            WHERE user_id = ? AND week_start = ? AND pending = 1
        ''', (user['id'], week.isoformat())).fetchall()
        if pending_rows:
            pending_changes.append({
                'user': user['name'],
                'user_id': user['id'],
                'changes': {row['day']: row['shift_type'] for row in pending_rows}
            })
    conn.close()
    return render_template('admin_panel.html', users=users, schedules=schedules, week=week, days=days, pending_changes=pending_changes)

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