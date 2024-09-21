from flask import Flask, render_template, request, redirect, session, url_for,flash,jsonify
import pymysql,sqlite3,MySQLdb,mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
import uuid,random,logging,smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from apscheduler.schedulers.background import BackgroundScheduler


app = Flask(__name__)
app.secret_key = "hello"  # Secret key for session management

# MySQL Database connection
db = pymysql.connect(
    host="127.0.0.1",
    user="root",
    password="909969@dady17",
    database="mydb"
)

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Mail server
app.config['MAIL_PORT'] = 587  # Mail port
app.config['MAIL_USERNAME'] = 'praneethapuppet1@gmail.com'  # Your email
app.config['MAIL_PASSWORD'] = 'yvss zfcy oghg jkln'  # Your email password
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

mail = Mail(app)

# Route for home page
@app.route('/')
def index():
    return render_template('home.html')

# Route for registration page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        if not name or not email or not password:
            return "All fields are required!", 400

        hashed_password = generate_password_hash(password)
        cursor = db.cursor()
        query = "INSERT INTO user (name, email, password) VALUES (%s, %s, %s)"
        values = (name, email, hashed_password)

        try:
            cursor.execute(query, values)
            db.commit()
            return redirect('/login')
        except pymysql.IntegrityError:
            return "Email already registered!", 400

    return render_template('register.html')

def validate_user(email):
    db = None
    cursor = None
    try:
        db = pymysql.connect(host="127.0.0.1", user="root", password="909969@dady17", database="mydb")
        cursor = db.cursor()

        cursor.execute("SELECT * FROM user WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user:
            return True, user
        else:
            return False, None
    except pymysql.MySQLError as e:
        print(f"Database error: {e}")
        return False, None
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()
            
def validate_payment(email):
    db = None
    cursor = None
    try:
        db = pymysql.connect(host="127.0.0.1", user="root", password="909969@dady17", database="mydb")
        cursor = db.cursor()

        cursor.execute("SELECT * FROM payments WHERE email = %s AND validation = 'yes'", (email,))
        payment = cursor.fetchone()

        return bool(payment)
    except pymysql.MySQLError as e:
        print(f"Database error: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


def assign_personal_trainer(user_id):
    connection = None
    cursor = None
    try:
        # Establish the database connection
        connection = pymysql.connect(host="127.0.0.1", user="root", password="909969@dady17", database="mydb")
        cursor = connection.cursor()

        # Retrieve user's training type from the payments table using the email from the user_id
        cursor.execute("""
            SELECT training_type 
            FROM payments 
            WHERE email = (SELECT email FROM user WHERE id = %s) 
              AND validation = 'yes'
        """, (user_id,))
        user_training = cursor.fetchone()

        if user_training:
            training_type = user_training[0]  # Access the first item in the tuple

            # Check if the user already has a trainer
            cursor.execute("""
                SELECT trainer_id 
                FROM user 
                WHERE id = %s
            """, (user_id,))
            existing_trainer = cursor.fetchone()

            if existing_trainer[0] is None:  # No trainer assigned yet
                # Select a random trainer that matches the user's training type
                cursor.execute("""
                    SELECT id 
                    FROM trainers 
                    WHERE expertise = %s
                    ORDER BY RAND() 
                    LIMIT 1
                """, (training_type,))
                random_trainer = cursor.fetchone()

                if random_trainer:
                    trainer_id = random_trainer[0]

                    # Assign the selected trainer to the user
                    cursor.execute("""
                        INSERT INTO user_trainers (user_id, trainer_id) 
                        VALUES (%s, %s)
                    """, (user_id, trainer_id))
                    
                    # Also update the trainer_id in the user table
                    cursor.execute("""
                        UPDATE user 
                        SET trainer_id = %s 
                        WHERE id = %s
                    """, (trainer_id, user_id))
                    
                    connection.commit()  # Save changes to the database
                    print(f"Assigned trainer {trainer_id} to user {user_id} with {training_type} training.")
                else:
                    print(f"No trainers available for {training_type} training.")
            else:
                print("Trainer already assigned.")
        else:
            print("User's training type not found or validation is not 'yes'.")
    except Exception as e:
        print(f"Error assigning trainer: {e}")
    finally:
        if cursor:
            cursor.close()  # Close the cursor
        if connection:
            connection.close()  # Close the database connection



@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        user_valid, user = validate_user(email)
        
        if not user_valid:
            flash("User not found. Please register.")
            return redirect(url_for('register'))
        
        payment_valid = validate_payment(email)
        if not payment_valid:
            flash("Payment validation failed. Please update your payment information.")
            return redirect(url_for('membership'))
        assign_personal_trainer(user[0])  # Access first item in tuple (user_id)
        
        # Set session to track logged-in user
        session['logged_in'] = True
        session['user_email'] = email
        session['user_id'] = user[0]  # Access first item in tuple (user_id)
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')

@app.route('/trainer_details')
def trainer_details():
    user_id = session.get('user_id')
    if not user_id:
        return "User not logged in or session expired."

    connection = db
    try:
        with connection.cursor() as cursor:
            # Get the assigned trainer details
            query = """
            SELECT trainers.full_name, trainers.email, trainers.expertise, trainers.certifications
            FROM user_trainers
            JOIN trainers ON user_trainers.trainer_id = trainers.id
            WHERE user_trainers.user_id = %s
            """
            cursor.execute(query, (user_id,))
            trainer = cursor.fetchone()

            if trainer:
                print(f"Trainer Details: {trainer}")  # Debugging line
                return render_template('trainer_details.html', trainer=trainer)
            else:
                return "No trainer assigned yet."
    except Exception as e:
        print(f"Error: {e}")  # Debugging line
        return "An error occurred while retrieving trainer details."
    
    return render_template('trainer_details.html')



@app.route('/dashboard')
def dashboard():
    if 'logged_in' in session and session['logged_in']:
        return render_template('dashboard.html')
    else:
        flash("Please log in to access the dashboard.")
        return redirect(url_for('login'))


# Route for "Forgot Password" page
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')

        cursor = db.cursor()
        query = "SELECT * FROM user WHERE email=%s"
        cursor.execute(query, (email,))
        user = cursor.fetchone()

        if user:
            token = str(uuid.uuid4())
            cursor.execute("INSERT INTO password_reset (email, token) VALUES (%s, %s)", (email, token))
            db.commit()

            reset_link = f"http://127.0.0.1:5000/reset_password/{token}"
            msg = Message("Password Reset Request", sender="praneethapuppet1@gmail.com", recipients=[email])
            msg.body = f"Please click the following link to reset your password: {reset_link}"
            mail.send(msg)

            return "<h1>Check your email for a link to reset your password.</h1>"
        else:
            return "<h1>Email not found.</h1>"

    return render_template('forgot_password.html')


# Route for password reset form
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if request.method == 'POST':
        new_password = request.form.get('password')

        cursor = db.cursor()
        query = "SELECT email FROM password_reset WHERE token=%s"
        cursor.execute(query, (token,))
        result = cursor.fetchone()

        if result:
            email = result[0]
            hashed_password = generate_password_hash(new_password)
            cursor.execute("UPDATE user SET password=%s WHERE email=%s", (hashed_password, email))
            cursor.execute("DELETE FROM password_reset WHERE token=%s", (token,))
            db.commit()

            return redirect('/login')
        else:
            return "<h1>Invalid or expired token.</h1>"

    return render_template('reset_password.html', token=token)




@app.route('/feedback_thank_you')
def feedback_thank_you():
    return "Thank you for your feedback!"

@app.route('/feedback')
def feedback():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('feedback.html')

@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    if 'user_id' not in session:
        return redirect('/login')

    # Get the form data
    user_id = session['user_id']
    rating = request.form.get('rating')
    category = request.form.get('category')
    feedback = request.form.get('feedback')
    
    # Get current timestamp for 'created_at'
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Insert feedback into the database
    cursor = db.cursor()
    query = """
        INSERT INTO feedback (user_id, rating, category, feedback, created_at)
        VALUES (%s, %s, %s, %s, %s)
    """
    values = (user_id, rating, category, feedback, created_at)

    try:
        cursor.execute(query, values)
        db.commit()
    except Exception as e:
        print(f"Error: {e}")
        return "An error occurred while submitting feedback", 500

    return redirect(url_for('feedback_thank_you'))



@app.route('/nutrition')
def nutrition():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('nutrition_main.html')

@app.route('/nutrition_plan1')
def nutrition_plan1():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('nutrition_plan1.html')

@app.route('/nutrition_plan2')
def nutrition_plan2():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('nutrition_plan2.html')

@app.route('/nutrition_plan3')
def nutrition_plan3():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('nutrition_plan3.html')

@app.route('/nutrition_plan4')
def nutrition_plan4():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('nutrition_plan4.html')

@app.route('/nutrition_plan5')
def nutrition_plan5():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('nutrition_plan5.html')

@app.route('/nutrition_plan6')
def nutrition_plan6():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('nutrition_plan6.html')

@app.route('/nutrition_plan7')
def nutrition_plan7():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('nutrition_plan7.html')

@app.route('/workout_plans')
def workout_plans():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('workout_plans.html')

@app.route('/training-type1')
def training_type1():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('training1.html')

@app.route('/training-type2')
def training_type2():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('training2.html')

@app.route('/understand_cardio')
def understand_cardio():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('understand_cardio.html')

@app.route('/cardio_equipment')
def cardio_equipment():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('cardio_equipment.html')

@app.route('/cardio_routine')
def cardio_routine():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('cardio_routine.html')

@app.route('/cardio_monitoring')
def cardio_monitoring():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('cardio_monitoring.html')

@app.route('/cardio_with_other')
def cardio_with_other():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('cardio_with_other.html')

@app.route('/training-type3')
def training_type3():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('training3.html')

@app.route('/bodybuilding_goals')
def bodybuilding_goals():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('bodybuilding_goals.html')

@app.route('/bodybuilding_warmup')
def bodybuilding_warmup():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('bodybuilding_warmup.html')


@app.route('/strength_training')
def strength_training():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('strength_training.html')


@app.route('/beginner_strength')
def beginner_strength():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('beginner_strength.html')

@app.route('/medium_strength')
def medium_strength():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('medium_strength.html')

@app.route('/pro_strength')
def pro_strength():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('pro_strength.html')

@app.route('/bodybuilding_recovery')
def bodybuilding_recovery():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('bodybuilding_recovery.html')


@app.route('/progress_tracking')
def progress_tracking():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('progress_tracking.html')


@app.route('/training-type4')
def training_type4():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('training4.html')

@app.route('/understand_crossfit')
def understand_crossfit():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('understand_crossfit.html')

@app.route('/warm_up_mobility')
def warm_up_mobility():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('warm_up_mobility.html')

@app.route('/wod_structure')
def wod_structure():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('wod_structure.html')

@app.route('/cooldown_recovery')
def cooldown_recovery():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('cooldown_recovery.html')

@app.route('/progress_tracking4')
def progress_tracking4():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('progress_tracking4.html')

@app.route('/training-type5')
def training_type5():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('training5.html')

@app.route('/understand_olympic')
def understand_olympic():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('understand_olympic.html')

@app.route('/snatch_technique')
def snatch_technique():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('snatch_technique.html')

@app.route('/clean_and_jerk')
def clean_and_jerk():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('clean_and_jerk.html')

@app.route('/warmup_mobility')
def warmup_mobility():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('warmup_mobility.html')

@app.route('/safety_progression')
def safety_progression():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('safety_progression.html')


@app.route('/training-type6')
def training_type6():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('training6.html')

@app.route('/definition_purpose6')
def definition_purpose6():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('definition_purpose6.html')

@app.route('/circuit_structure')
def circuit_structure():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('circuit_structure.html')

@app.route('/circuit_benefits')
def circuit_benefits():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('circuit_benefits.html')

@app.route('/circuit_types')
def circuit_types():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('circuit_types.html')

@app.route('/circuit_tips')
def circuit_tips():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('circuit_tips.html')

@app.route('/training-type7')
def training_type7():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('training7.html')

@app.route('/definition_purpose7')
def definition_purpose7():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('definition_purpose7.html')

@app.route('/core_lifts')
def core_lifts():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('core_lifts.html')

@app.route('/training_principles')
def training_principles():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('training_principles.html')

@app.route('/competitions')
def competitions():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('competitions.html')

@app.route('/beginner_tips')
def beginner_tips():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('beginner_tips.html')


@app.route('/benefits')
def benefits():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('benefits.html')

@app.route('/principles')
def principles():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('principles.html')

@app.route('/types')
def types():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('types.html')

@app.route('/repetitions_sets')
def repetitions_sets():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('repetitions_sets.html')

@app.route('/techniques')
def techniques():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('techniques.html')

@app.route('/weekly_progress_tracking')
def weekly_progress_tracking():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('weekly_progress_tracking.html')




@app.route('/check_email', methods=['GET', 'POST'])
def check_email():
    if request.method == 'POST':
        email = request.form.get('email')

        if not email:
            flash("Email is required.")
            return redirect('/check_email')
        
        conn = None
        cursor = None
        try:
            conn = db
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM user WHERE email = %s', (email,))
            user = cursor.fetchone()
            
            if user:
                session['user_email'] = email
                return redirect('/membership')
            else:
                return redirect('/register')
        except pymysql.MySQLError as e:
            # Log the error message for debugging
            app.logger.error(f"Database error: {e}")
            return render_template('error.html', error_message=str(e))
        

    return render_template('check_email.html')


@app.route('/membership')
def membership():
    user_email = session.get('user_email')
    
    if user_email:
        return render_template('membership_types.html')
    else:
        flash("Please provide your email to access this page.")
        return redirect('/check_email')

@app.route('/upi_payment')
def upi_payment():
    return render_template('upi_payment.html')

@app.route('/handle_upi_payment', methods=['GET', 'POST'])
def handle_upi_payment():
    if request.method == 'POST':
        # Capture payment details from the form
        training_type = request.form.get('training_type')
        tier = request.form.get('tier')
        upi_id = request.form.get('upi_id')
        amount = request.form.get('amount')
        email = request.form.get('email')

        conn = None
        cursor = None
        try:
            conn = db
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO payments (training_type, tier, amount, upi_id, email) VALUES (%s, %s, %s, %s, %s)',
                (training_type, tier, amount, upi_id, email)
            )
            conn.commit()
            return render_template('thank_payment.html')
        except pymysql.MySQLError as e:
            flash("An error occurred while processing your payment.")
            conn.rollback()
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    return render_template('upi_payment.html')



@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.")
    return render_template('home.html')




def send_workout_reminder(email, name):
    try:
        # Email configuration
        sender_email = 'praneethapuppet1@gmail.com'
        sender_password = 'yvss zfcy oghg jkln'
        receiver_email = email

        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = 'Workout Reminder'

        # Email body
        body = f"Hi {name}, it's time to get ready for your workout!"
        msg.attach(MIMEText(body, 'plain'))

        # Send email
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
        print(f'Email sent to {email}!')
    except Exception as e:
        print(f"Failed to send email to {email}. Error: {str(e)}")

def workout_reminder_job():
    # Database connection to fetch user details
    conn = pymysql.connect(host='localhost', user='your_user', password='your_password', db='gym')
    cursor = conn.cursor()
    cursor.execute("SELECT name, email FROM user")  # Query users
    users = cursor.fetchall()
    conn.close()

    # Send reminders to all users
    for user in users:
        name, email = user
        send_workout_reminder(email, name)

    # Schedule the workout reminders
    scheduler = BackgroundScheduler()
    scheduler.add_job(workout_reminder_job, 'cron', hour=23)
    scheduler.start()

@app.route('/community_features')
def community_features():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('community_features.html')

@app.route('/engage')
def engage():
    if 'logged_in' not in session and session['logged_in']:
        return redirect('/login')
    return render_template('engage.html')

@app.route('/personal_info')
def personal_info():
    print("Session Data: ", session)
    if 'logged_in' not in session or not session['logged_in']:
        flash("Session expired. Please log in again.")
        return redirect('/login')
    
    user_id = session.get('user_id')
    if not user_id:
        flash("Session expired. Please log in again.")
        return redirect('/login')
    
    user = fetch_user_from_database(user_id)
    if not user:
        flash("User not found. Please log in again.")
        return redirect('/login')
    
    user_email = user[2]  # Assuming email is the third item in the user tuple
    payments = fetch_payments_from_database(user_email)
    
    return render_template('personal_info.html', user=user, payments=payments)

def fetch_user_from_database(user_id):
    try:
        cur = db.cursor()
        cur.execute('SELECT id, name, email, trainer_id FROM user WHERE id = %s', (user_id,))
        user = cur.fetchone()
        return user
    except pymysql.Error as e:
        flash("An error occurred while retrieving user information. Please try again later.")
        return None
    finally:
        cur.close()

def fetch_payments_from_database(email):
    try:
        cur = db.cursor()
        cur.execute('''
            SELECT id, training_type, tier, amount, upi_id, email, payment_date, validation
            FROM payments
            WHERE email = %s
            ORDER BY payment_date DESC
        ''', (email,))
        payments = cur.fetchall()
        return payments
    except pymysql.Error as e:
        flash("An error occurred while retrieving payment information. Please try again later.")
        return []
    finally:
        cur.close()

@app.route('/user_edit_profile')
def user_edit_profile():
    try:
        user_id = session.get('user_id')  # Fetch user_id from session
        if not user_id:
            flash('User not logged in!')
            return redirect(url_for('login'))
        
        connection = db  # Initialize connection
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("SELECT * FROM user WHERE id=%s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            flash('User not found!')
            return redirect(url_for('login'))
        
        return render_template('user_edit_profile.html', user=user)
    
    except pymysql.err.InterfaceError as e:
        print(f"Database connection error: {e}")
        flash("A database error occurred. Please try again.")
        return redirect(url_for('login'))
    

@app.route('/update_profile', methods=['POST'])
def update_profile():
    user_id = request.form['user_id']
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']  
    
    try:
        with db.cursor() as cursor:
            if password:
                hashed_password = generate_password_hash(password)
                cursor.execute("UPDATE user SET name=%s, email=%s, password=%s WHERE id=%s", 
                               (name, email, hashed_password, user_id))
            else:
                cursor.execute("UPDATE user SET name=%s, email=%s WHERE id=%s", 
                               (name, email, user_id))
            
            db.commit()
    
    except pymysql.err.InterfaceError as e:
        print(f"Database connection error: {e}")
        flash("Failed to update profile. Please try again.")
    
    return redirect(url_for('personal_info'))

@app.route('/submit-progress', methods=['POST'])
def submit_progress():
    user_id = session.get('user_id')  # Assuming you store user ID in session after login
    
    if not user_id:
        flash('User not logged in')
        return redirect(url_for('login'))  # Redirect to login if not logged in
    
    connection = db
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    
    # Fetch the trainer_id associated with the user_id
    cursor.execute('SELECT trainer_id FROM user_trainers WHERE user_id = %s', (user_id,))
    trainer_record = cursor.fetchone()
    
    if not trainer_record:
        flash('Trainer not assigned to user')
        connection.close()
        return redirect(url_for('some_page'))  # Redirect to an appropriate page if no trainer is found
    
    trainer_id = trainer_record['trainer_id']
    
    # Get the progress data from the form
    progress_date = request.form['progress_date']
    workout_details = request.form['workout_details']
    issues = request.form['issues']
    
    # Insert the progress data into the progress_tracking table
    cursor.execute('INSERT INTO progress_tracking (user_id, trainer_id, progress_date, workout_details, issues) VALUES (%s, %s, %s, %s, %s)', 
                   (user_id, trainer_id, progress_date, workout_details, issues))
    connection.commit()
    connection.close()
    
    flash('Progress submitted successfully')
    return redirect(url_for('dashboard'))  # Redirect to an appropriate page after submission


@app.route('/trainer-progress')
def trainer_progress():
    trainer_id = session.get('trainer_id')  # Get trainer ID from session
    
    if not trainer_id:
        flash('Trainer not logged in')
        return redirect(url_for('login'))  # Redirect to login if no trainer ID in session

    connection = db
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    
    # Fetch progress tracking entries for the trainer
    cursor.execute('SELECT * FROM progress_tracking WHERE trainer_id = %s', (trainer_id,))
    progress_entries = cursor.fetchall()
    connection.close()

    return render_template('trainer_progress.html', progress_entries=progress_entries)


@app.route('/trainer-profile')
def trainer_profile():
    trainer_id = session.get('trainer_id')  # Get trainer ID from session
    
    if not trainer_id:
        flash('Trainer not logged in')
        return redirect(url_for('login'))  # Redirect to login if no trainer ID in session

    connection = db
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    
    # Fetch trainer details from the trainers table
    cursor.execute('SELECT full_name, email, expertise, certifications FROM trainers WHERE id = %s', (trainer_id,))
    trainer_details = cursor.fetchone()
    connection.close()
    
    if not trainer_details:
        flash('Trainer details not found')
        return redirect(url_for('some_page'))  # Redirect if no details are found

    return render_template('trainer_profile.html', 
                           trainer_name=trainer_details['full_name'],
                           trainer_email=trainer_details['email'],
                           trainer_expertise=trainer_details['expertise'],
                           trainer_certifications=trainer_details['certifications'])



@app.route('/trainer_register', methods=['GET', 'POST'])
def trainer_register():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        expertise = request.form.get('expertise')
        certifications = request.form.get('certifications')

        if not all([full_name, email, password, confirm_password, expertise, certifications]):
            flash('All fields are required.', 'danger')
            return redirect(url_for('trainer_register'))

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('trainer_register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        connection = None
        cursor = None
        try:
            connection = db
            cursor = connection.cursor()

            check_query = "SELECT * FROM trainers WHERE email = %s"
            cursor.execute(check_query, (email,))
            existing_trainer = cursor.fetchone()

            if existing_trainer:
                check_expertise_query = "SELECT * FROM trainers WHERE email = %s AND expertise = %s"
                cursor.execute(check_expertise_query, (email, expertise))
                existing_expertise = cursor.fetchone()

                if existing_expertise:
                    flash('This expertise is already registered for this email.', 'warning')
                    return redirect(url_for('trainer_register'))

                insert_query = """
                    INSERT INTO trainers (full_name, email, password, expertise, certifications)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(insert_query, (full_name, email, existing_trainer['password'], expertise, certifications))
                connection.commit()
                flash('New expertise added successfully!', 'success')
                return redirect(url_for('trainer_login'))
            else:
                insert_query = """
                    INSERT INTO trainers (full_name, email, password, expertise, certifications)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(insert_query, (full_name, email, hashed_password, expertise, certifications))
                connection.commit()
                flash('Registration successful!', 'success')
                return redirect(url_for('trainer_login'))

        except pymysql.MySQLError as err:
            if connection:
                connection.rollback()
            flash(f'Error: {err}', 'danger')
            logging.error(f"Database error during trainer registration: {err}")
        except Exception as e:
            if connection:
                connection.rollback()
            flash('An unexpected error occurred. Please try again.', 'danger')
            logging.error(f"Unexpected error during trainer registration: {e}")
    

    return render_template('trainer_register.html')




# Function to send password reset email
def send_reset_email(email, token):
    try:
        # Replace with actual server details
        MAIL_SERVER = 'smtp.gmail.com'  # For Gmail
        MAIL_PORT = 587  # TLS port
        MAIL_USERNAME = 'praneethapuppet1@gmail.com'
        MAIL_PASSWORD = 'yvss zfcy oghg jkln'

        # Connect to the SMTP server
        smtp_server = smtplib.SMTP(MAIL_SERVER, MAIL_PORT)
        smtp_server.starttls()  # Upgrade connection to TLS
        smtp_server.login(MAIL_USERNAME, MAIL_PASSWORD)
        
        # Generate the reset password URL
        reset_url = url_for('reset_password2', token=token, _external=True)

        # Create email content
        message = MIMEText(f"Click the following link to reset your password: {reset_url}")
        message["Subject"] = "Password Reset"
        message["From"] = MAIL_USERNAME
        message["To"] = email

        # Send the email
        smtp_server.sendmail(MAIL_USERNAME, email, message.as_string())
        smtp_server.quit()

        print(f"Password reset email sent to {email}.")
    
    except smtplib.SMTPException as e:
        print(f"Failed to send email: {e}")
        flash("Failed to send email. Please try again.", "danger")

# Trainer login route
@app.route('/trainer_login', methods=['GET', 'POST'])
def trainer_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        conn = None
        cursor = None
        try:
            # Open a new connection for this request
            conn = db
            
            # Use DictCursor to get the result as a dictionary
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            # Execute the query to get the trainer by email
            cursor.execute("SELECT * FROM trainers WHERE email = %s", (email,))
            trainer = cursor.fetchone()

            if trainer and check_password_hash(trainer['password'], password):
                # Set session data for the trainer
                session['trainer_id'] = trainer['id']
                session['trainer_name'] = trainer['full_name']

                # Debug: Check if session is set properly
                print(f"Trainer ID: {session['trainer_id']}")
                print(f"Trainer Name: {session['trainer_name']}")

                return redirect(url_for('trainer_dashboard'))
            else:
                flash('Invalid email or password', 'danger')

        except pymysql.MySQLError as e:
            # Log the error and render an error page
            app.logger.error(f"Database error: {e}")
            flash('A database error occurred. Please try again.', 'danger')
            return render_template('error.html', error_message=str(e))
        

    return render_template('trainer_login.html')



# Trainer dashboard route
@app.route('/trainer_dashboard')
def trainer_dashboard():
    trainer_id = session.get('trainer_id')

    if not trainer_id:
        flash('Trainer not logged in.')
        return redirect(url_for('trainer_login'))

    try:
        cursor = db.cursor(pymysql.cursors.DictCursor)
        cursor.execute('SELECT full_name, email, expertise, certifications FROM trainers WHERE id = %s', (trainer_id,))
        trainer_details = cursor.fetchone()

        if not trainer_details:
            flash('Trainer details not found')
            return redirect(url_for('trainer_login'))

        cursor.execute('SELECT * FROM progress_tracking WHERE trainer_id = %s', (trainer_id,))
        progress_entries = cursor.fetchall()

    except pymysql.Error as e:
        flash(f'An error occurred: {str(e)}', 'danger')
        return redirect(url_for('trainer_login'))

    return render_template('trainer_dashboard.html',
                           trainer_name=trainer_details['full_name'],
                           trainer_email=trainer_details['email'],
                           trainer_expertise=trainer_details['expertise'],
                           trainer_certifications=trainer_details['certifications'],
                           progress_entries=progress_entries)


# Route for "Forgot Password" page
@app.route('/forgot_password2', methods=['GET', 'POST'])
def forgot_password2():
    if request.method == 'POST':
        email = request.form.get('email')

        cursor = db.cursor()
        query = "SELECT * FROM trainers WHERE email=%s"
        cursor.execute(query, (email,))
        user = cursor.fetchone()

        if user:
            token = str(uuid.uuid4())
            cursor.execute("INSERT INTO password_reset (email, token) VALUES (%s, %s)", (email, token))
            db.commit()

            reset_link = f"http://127.0.0.1:5000/reset_password2/{token}"
            msg = Message("Password Reset Request", sender="praneethapuppet1@gmail.com", recipients=[email])
            msg.body = f"Please click the following link to reset your password: {reset_link}"
            mail.send(msg)

            return "<h1>Check your email for a link to reset your password.</h1>"
        else:
            return "<h1>Email not found.</h1>"

    return render_template('forgot_password2.html')

# Route for password reset form
@app.route('/reset_password2/<token>', methods=['GET', 'POST'])
def reset_password2(token):
    if request.method == 'POST':
        new_password = request.form.get('password')

        cursor = db.cursor()
        query = "SELECT email FROM password_reset WHERE token=%s"
        cursor.execute(query, (token,))
        result = cursor.fetchone()

        if result:
            email = result[0]
            hashed_password = generate_password_hash(new_password)
            cursor.execute("UPDATE trainers SET password=%s WHERE email=%s", (hashed_password, email))
            cursor.execute("DELETE FROM password_reset WHERE token=%s", (token,))
            db.commit()

            return redirect('/trainer_login')
        else:
            return "<h1>Invalid or expired token.</h1>"

    return render_template('reset_password2.html', token=token)

@app.route('/trainer_logout')
def trainer_logout():
    session.clear()
    flash('You have been logged out successfully.', 'success')
   
    return redirect(url_for('trainer_login'))

@app.route('/blog')
def blog():
    return render_template('blog.html')

@app.route('/contactUs')
def contactUs():
    return render_template('contactUs.html')

@app.route('/aboutUs')
def aboutUs():
    return render_template('aboutUs.html')

if __name__ == '__main__':
    app.run(debug=True)
