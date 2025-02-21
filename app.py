import pymysql
from datetime import date, timedelta, datetime
import calendar
import holidays
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, Response

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
        
        # Insert default users if not present, with deadlock prevention
        with conn.cursor() as cursor:
            for worker in ['Ariel', 'Roei', 'Ofek', 'Guy']:
                try:
                    # Check if user exists first to avoid lock contention
                    cursor.execute("SELECT id FROM users WHERE name = %s", (worker,))
                    if cursor.fetchone() is None:
                        cursor.execute("INSERT INTO users (name) VALUES (%s)", (worker,))
                except pymysql.err.IntegrityError:
                    pass
                except pymysql.err.OperationalError as e:
                    if "Deadlock" in str(e):
                        # Log the error but continue - the user might already exist
                        print(f"Deadlock while inserting user {worker}, continuing...")
                    else:
                        raise
                conn.commit()  # Commit after each user to reduce transaction size
    finally:
        conn.close()

# Run init_db only when the application starts, not when imported
if __name__ == '__main__':
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

# --- Export calendar as CSV file for Google Calendar ---
@app.route('/export_calendar/<int:user_id>')
def export_calendar(user_id):
    """Generate CSV file for Google Calendar export based on user's schedule"""
    # Get user info
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
            user = cursor.fetchone()
        if not user:
            return "User not found", 404
            
        # Set date range (next 3 months)
        start_date = date.today()
        end_date = start_date + timedelta(days=90)
        allowed_days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]
        
        # Get all the user's shifts
        shifts = []
        current = start_date
        while current <= end_date:
            if current.strftime("%A") in allowed_days:
                week_start = get_week_start(current)
                day_name = current.strftime("%A")
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT shift_type FROM shifts WHERE user_id = %s AND week_start = %s AND day = %s",
                        (user_id, week_start.isoformat(), day_name)
                    )
                    row = cursor.fetchone()
                    # Handle special case for Sunday (always Day)
                    shift_type = row["shift_type"] if row else ("Day" if day_name == "Sunday" else "Not set")
                    
                    # Only add events for scheduled shifts
                    if shift_type in ["Day", "Night", "OOO"]:
                        shifts.append({
                            "date": current,
                            "day": day_name,
                            "shift_type": shift_type
                        })
            current += timedelta(days=1)
        
        # Generate CSV
        csv_content = "Subject,Start Date,Start Time,End Date,End Time,All Day,Description\n"
        
        for shift in shifts:
            event_date = shift['date']
            event_date_str = event_date.strftime("%m/%d/%Y")
            
            if shift['shift_type'] == "Day":
                subject = "Day Shift"
                start_time = "08:00 AM"
                end_time = "04:00 PM"
                all_day = "False"
                description = f"Day Shift for {user['name']}"
                csv_content += f'"{subject}",{event_date_str},{start_time},{event_date_str},{end_time},{all_day},"{description}"\n'
            elif shift['shift_type'] == "Night":
                subject = "Night Shift"
                start_time = "04:00 PM"
                end_time = "12:00 AM"
                all_day = "False"
                description = f"Night Shift for {user['name']}"
                csv_content += f'"{subject}",{event_date_str},{start_time},{event_date_str},{end_time},{all_day},"{description}"\n'
            else:  # OOO
                subject = "Out of Office"
                all_day = "True"
                description = f"{user['name']} is out of office"
                csv_content += f'"{subject}",{event_date_str},,{event_date_str},,{all_day},"{description}"\n'
    finally:
        conn.close()
    
    # Return as downloadable CSV file
    response = Response(csv_content, mimetype='text/csv')
    response.headers['Content-Disposition'] = f'attachment; filename="{user["name"]}_schedule.csv"'
    return response

# --- get_schedule_data: returns scheduling data for one month ahead ---
@app.route('/get_schedule_data')
def get_schedule_data():
    print("get_schedule_data called")
    allowed_days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]
    start_date = date.today()
    end_date = start_date + timedelta(days=30)
    
    # These lists must remain in sync
    dates = []         # Formatted as strings: "DD/MM/YYYY"
    day_names = []     # Day names: "Sunday", "Monday", etc.
    date_objects = []  # Python date objects for calculations
    
    current = start_date
    while current <= end_date:
        if current.strftime("%A") in allowed_days:
            # Format the date as DD/MM/YYYY for JavaScript
            dates.append(current.strftime("%d/%m/%Y"))
            day_names.append(current.strftime("%A"))
            date_objects.append(current)
        current += timedelta(days=1)

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name FROM users ORDER BY name")
            users = cursor.fetchall()
        
        # Initialize schedule arrays for each user
        schedule_array = []
        for user in users:
            shifts_list = ["Not set"] * len(dates)  # Initialize all shifts as "Not set"
            
            # Handle Sundays - always "Day"
            for i, day_name in enumerate(day_names):
                if day_name == "Sunday":
                    shifts_list[i] = "Day"
            
            schedule_array.append({
                "name": user["name"],
                "shifts": shifts_list
            })
        
        # Map user IDs to their position in the schedule array for quick lookup
        user_id_to_index = {user['id']: i for i, user in enumerate(users)}
        
        # Prepare date lookups for quick matching
        date_lookups = {}
        for i, d_obj in enumerate(date_objects):
            week_start = get_week_start(d_obj)
            day_name = day_names[i]
            key = (week_start.isoformat(), day_name)
            date_lookups[key] = i
        
        # Fetch shifts for all users in the date range
        min_date = min(date_objects)
        max_date = max(date_objects)
        min_week_start = get_week_start(min_date).isoformat()
        max_week_start = get_week_start(max_date).isoformat()
        
        print(f"Fetching shifts between {min_week_start} and {max_week_start}")
        
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT s.user_id, s.week_start, s.day, s.shift_type
                FROM shifts s
                WHERE s.week_start BETWEEN %s AND %s
            """, (min_week_start, max_week_start))
            
            shifts = cursor.fetchall()
            print(f"Found {len(shifts)} shifts")
            
        # Update the schedule array with actual shifts
        for shift in shifts:
            user_id = shift['user_id']
            week_start = shift['week_start']
            day = shift['day']
            shift_type = shift['shift_type']
            
            # Get the array index for this user
            user_index = user_id_to_index.get(user_id)
            if user_index is None:
                print(f"Warning: Shift for unknown user ID {user_id}")
                continue
                
            # Get the array index for this date
            date_index = date_lookups.get((week_start.isoformat(), day))
            if date_index is None:
                # This shift doesn't match any of our dates
                continue
                
            # Update the shift in the schedule array
            schedule_array[user_index]["shifts"][date_index] = shift_type
    except Exception as e:
        print(f"Error in get_schedule_data: {e}")
        # Return minimal data to prevent JavaScript errors
        return jsonify({
            "error": str(e),
            "dates": dates,
            "days": day_names,
            "schedule": []
        })
    finally:
        conn.close()

    data = {
        "dates": dates,
        "days": day_names,
        "schedule": schedule_array
    }
    
    # Print the first few entries for debugging
    print("API Response Structure:")
    print(f"dates: {dates[:3]}...")
    print(f"days: {day_names[:3]}...")
    if schedule_array:
        user = schedule_array[0]["name"]
        shifts = schedule_array[0]["shifts"][:3]
        print(f"First user '{user}' shifts: {shifts}...")
    
    return jsonify(data)

@app.route('/view_schedule')
def view_schedule_global():
    return redirect(url_for('view_all_schedule'))

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

# Route to get all users in JSON format
@app.route('/get_users')
def get_users():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT id, name FROM users ORDER BY name')
            users = cursor.fetchall()
    finally:
        conn.close()
    return jsonify(users)

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
    
    # Group dates by month for template rendering
    month_dates = defaultdict(list)
    for d in dates:
        month_name = d.strftime("%B %Y")
        month_dates[month_name].append(d)
    
    # Build user schedules more efficiently
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM users ORDER BY name')
            users = cursor.fetchall()
            
        # Initialize schedules with default values
        user_schedules = {user['name']: {} for user in users}
        for user_name in user_schedules:
            for d in dates:
                # Default to 'Day' for Sundays, 'Not set' for others
                if d.strftime("%A") == "Sunday":
                    user_schedules[user_name][d] = "Day"
                else:
                    user_schedules[user_name][d] = "Not set"
        
        # Fetch all shifts in one query with date ranges
        min_date = min(dates)
        max_date = max(dates)
        min_week_start = get_week_start(min_date).isoformat()
        max_week_start = get_week_start(max_date).isoformat()
        
        with conn.cursor() as cursor:
            # Get all shifts for all users in the date range in a single query
            cursor.execute("""
                SELECT s.user_id, s.week_start, s.day, s.shift_type, u.name 
                FROM shifts s 
                JOIN users u ON s.user_id = u.id
                WHERE s.week_start BETWEEN %s AND %s
            """, (min_week_start, max_week_start))
            
            shifts = cursor.fetchall()
            
        # Process all shifts - override the defaults with actual shift values
        for shift in shifts:
            week_start = shift['week_start']
            name = shift['name']
            day_name = shift['day']
            
            # Find matching dates for this shift
            for d in dates:
                if get_week_start(d) == week_start and d.strftime("%A") == day_name:
                    user_schedules[name][d] = shift['shift_type']
    finally:
        conn.close()

    dates.sort()
    return render_template(
        'view_all_schedule.html',
        users=users,
        user_schedules=user_schedules,
        today=date.today(),
        dates=dates,
        month_dates=month_dates
    )

# --- Admin routes ---
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == 'admin123':  # Simple password for demonstration
            session['admin'] = True
            return redirect(url_for('admin_panel'))
        else:
            flash('Invalid password')
    return render_template('admin_login.html')

@app.route('/admin/panel')
def admin_panel():
    if not session.get('admin'):
        return redirect(url_for('admin'))
    
    # Get users with pending shifts for next week
    next_week = get_next_week_start()
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT u.id, u.name, COUNT(s.id) as pending_count
                FROM users u
                INNER JOIN shifts s ON u.id = s.user_id
                WHERE s.week_start = %s AND s.pending = 1
                GROUP BY u.id, u.name
            """, (next_week.isoformat(),))
            pending_users = cursor.fetchall()
    finally:
        conn.close()
    
    return render_template('admin_panel.html', pending_users=pending_users, next_week=next_week)

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

# Initialize database on application startup
with app.app_context():
    try:
        init_db()
    except Exception as e:
        print(f"Error during database initialization: {e}")
        # Continue anyway - the app might still work if tables already exist

if __name__ == '__main__':
    app.run(debug=True)