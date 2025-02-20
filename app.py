import pymysql
from datetime import date, timedelta, datetime
import calendar
import holidays
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# ----------------------------
# MySQL Database Helpers using pymysql
# ----------------------------
def get_db_connection():
    # Connect using pymysql with your provided credentials.
    connection = pymysql.connect(
        charset="utf8mb4",
        connect_timeout=10,
        cursorclass=pymysql.cursors.DictCursor,
        db="defaultdb",
        host="shift-sceduler-ariel7871.j.aivencloud.com",
        password="AVNS_6Nh0nnQld-uYa62tp_b",
        read_timeout=10,
        port=15003,
        user="avnadmin",
        write_timeout=10,
    )
    return connection

def init_db():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Create users table.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) UNIQUE NOT NULL
                )
            """)
            # Create shifts table with a pending flag.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shifts (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    week_start DATE NOT NULL,
                    day VARCHAR(20) NOT NULL,
                    shift_type VARCHAR(20) NOT NULL,
                    pending INT DEFAULT 0,
                    UNIQUE KEY unique_shift (user_id, week_start, day),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
        conn.commit()
        # Insert default users if not present.
        with conn.cursor() as cursor:
            for worker in ['Ariel', 'Roei', 'Ofek', 'Guy']:
                try:
                    cursor.execute("INSERT INTO users (name) VALUES (%s)", (worker,))
                except pymysql.err.IntegrityError:
                    pass
        conn.commit()
    finally:
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
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM users')
            users = cursor.fetchall()
    finally:
        conn.close()
    return render_template('choose_schedule.html', users=users)

@app.route('/schedule/<int:user_id>', methods=['GET', 'POST'])
def schedule(user_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
        if not user:
            flash("User not found!")
            return redirect(url_for('choose_schedule'))

        # For scheduling one month ahead by default, we extend the weeks list
        num_weeks = 6
        upcoming_weeks = [get_current_week_start() + timedelta(weeks=i) for i in range(num_weeks)]
        
        # Default to the week one month ahead (approximately index 4)
        week_index = request.args.get("week_index", 4, type=int)
        if week_index < 0 or week_index >= num_weeks:
            week_index = 4
        target_week = upcoming_weeks[week_index]
        
        days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday']
        
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM shifts WHERE user_id = %s AND week_start = %s",
                (user_id, target_week.isoformat())
            )
            existing_shifts = cursor.fetchall()
        
        prefill = {}
        if existing_shifts:
            for row in existing_shifts:
                prefill[row["day"]] = row["shift_type"]

        if request.method == "POST":
            action = request.form.get("action")
            with conn.cursor() as cursor:
                for day in days:
                    field_name = f"{target_week.isoformat()}_{day}"
                    shift_choice = request.form.get(field_name)
                    if shift_choice in ["Day", "Night", "OOO"]:
                        # Force Sunday to always be Day
                        if day == "Sunday":
                            shift_choice = "Day"
                        cursor.execute("""
                            INSERT INTO shifts (user_id, week_start, day, shift_type, pending)
                            VALUES (%s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE shift_type = VALUES(shift_type), pending = VALUES(pending)
                        """, (user_id, target_week.isoformat(), day, shift_choice, 1))
            conn.commit()
            flash("Your schedule has been submitted.")
            if action == "move_next" and week_index < len(upcoming_weeks) - 1:
                return redirect(url_for("schedule", user_id=user_id, week_index=week_index + 1))
            return redirect(url_for("view_schedule", user_id=user_id))
    finally:
        conn.close()

    header_text = "Set Your Shifts for " if not existing_shifts else "Update Your Shifts for "
    if week_index == 0:
        header_text += "This Week"
    elif week_index == 1:
        header_text += "Next Week"
    else:
        week_end = target_week + timedelta(days=4)
        header_text += f"{target_week.strftime('%d/%m/%y')} - {week_end.strftime('%d/%m/%y')}"

    # Build week_options for navigation
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
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
            user = cursor.fetchone()
        if not user:
            flash("User not found!")
            return redirect(url_for('choose_schedule'))
    finally:
        conn.close()
    return render_template('view_schedule.html', user=user)

# --- get_schedule_data: returns scheduling data for one month ahead ---
@app.route('/get_schedule_data')
def get_schedule_data():
    allowed_days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]
    start_date = date.today()
    end_date = start_date + timedelta(days=30)
    dates = []
    day_names = []
    current = start_date
    while current <= end_date:
        if current.strftime("%A") in allowed_days:
            dates.append(current.strftime("%d/%m/%Y"))
            day_names.append(current.strftime("%A"))
        current += timedelta(days=1)

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()

        schedule_array = []
        for user in users:
            shifts_list = []
            for d_str, d_name in zip(dates, day_names):
                d_obj = datetime.strptime(d_str, "%d/%m/%Y").date()
                week_start = get_week_start(d_obj)
                conn2 = get_db_connection()
                try:
                    with conn2.cursor() as cursor:
                        cursor.execute(
                            "SELECT shift_type FROM shifts WHERE user_id = %s AND week_start = %s AND day = %s",
                            (user["id"], week_start.isoformat(), d_name)
                        )
                        row = cursor.fetchone()
                        shift = row["shift_type"] if row else "Not set"
                finally:
                    conn2.close()
                shifts_list.append(shift)
            schedule_array.append({"name": user["name"], "shifts": shifts_list})
    finally:
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

# --- view_all_schedule: retrieves schedules from MySQL ---
@app.route('/view_all_schedule')
def view_all_schedule():
    from collections import defaultdict
    start_date = date.today()
    end_date = start_date + timedelta(days=30)
    allowed_days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]
    dates = []
    current = start_date
    while current <= end_date:
        if current.strftime("%A") in allowed_days:
            dates.append(current)
        current += timedelta(days=1)
    
    # Build user schedules: for each user, map each date to its shift (or "Not set")
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM users')
            users = cursor.fetchall()
        user_schedules = { user['name']: {} for user in users }
        for d in dates:
            week_start = get_week_start(d)
            day_name = d.strftime("%A")
            with conn.cursor() as cursor:
                for user in users:
                    cursor.execute(
                        "SELECT shift_type FROM shifts WHERE user_id = %s AND week_start = %s AND day = %s",
                        (user['id'], week_start.isoformat(), day_name)
                    )
                    row = cursor.fetchone()
                    shift = row["shift_type"] if row else "Not set"
                    user_schedules[user['name']][d] = shift
    finally:
        conn.close()

    dates.sort()
    return render_template(
        'view_all_schedule.html',
        users=users,
        user_schedules=user_schedules,
        today=date.today(),
        dates=dates
    )

@app.route('/approve_changes/<int:user_id>', methods=['POST'])
def approve_changes(user_id):
    if not session.get('admin'):
        return redirect(url_for('admin'))
    week = get_next_week_start()
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE shifts 
                SET pending = 0 
                WHERE user_id = %s AND week_start = %s AND pending = 1
            """, (user_id, week.isoformat()))
        conn.commit()
    finally:
        conn.close()
    flash("Changes approved for the user.")
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    app.run(debug=True)
