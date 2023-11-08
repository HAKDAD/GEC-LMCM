
from flask import Flask, render_template, request, redirect, url_for, flash,session
from twilio.rest import Client
from celery import Celery
import schedule
import time
from datetime import datetime
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import threading  # Import the threading module
import secrets
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
from twilio.base.exceptions import TwilioRestException



from flask import jsonify

app = Flask(__name__, static_url_path='/static')


app.secret_key = secrets.token_hex(16)  # Generates a 32-character (16 bytes) hex key

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://hacker:hacker@localhost/project'
db = SQLAlchemy(app)
migrate = Migrate(app, db)


#MGK19ZM9CU2H859YBKAYW2EE


# Flag to ensure the code is executed only once


is_first_request = True

# Twilio configuration (replace with your own credentials)
TWILIO_ACCOUNT_SID = 'AC81266eefc7cc9b7797a8bd0231fbf1bd'
TWILIO_AUTH_TOKEN = '400842c289217a417c61f3c46f151f24'
TWILIO_PHONE_NUMBER = '+12055063595'



# Initialize Celery
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'  # Use Redis as the message broker
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'  # Use Redis as the result backend
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


########################################################################

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.String(255), unique=True, nullable=False) 
    name = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    teacher_branch = db.Column(db.String(255))  # Add the teacher_branch field
    designation = db.Column(db.String(255))
    gender = db.Column(db.String(10))

    classes = db.relationship('Class', backref='teacher', lazy=True)
class Class(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.String(10), db.ForeignKey('teacher.teacher_id'), nullable=False)
    class_name = db.Column(db.String(255), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0 for Sunday, 1 for Monday, etc.
    class_time = db.Column(db.Time, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=True)  # Flag to indicate if the class is active
class ClassNotification(db.Model):
    __tablename__ = 'class_notifications'

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.String(10), nullable=False)  # Add teacher_id field
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    notification_sent = db.Column(db.Boolean, default=False)
    notification_datetime = db.Column(db.DateTime)

    def __init__(self, teacher_id, class_id, date, notification_sent=False, notification_datetime=None):
        self.teacher_id = teacher_id
        self.class_id = class_id
        self.date = date
        self.notification_sent = notification_sent
        self.notification_datetime = notification_datetime
    @classmethod
    def get_notification_logs_in_date_range(cls, start_date, end_date):
        return cls.query.filter(cls.date >= start_date, cls.date <= end_date).all()
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'admin' or 'teacher'

    def __init__(self, username, password, role):
        self.username = username
        self.password = password
        self.role = role
class LeaveRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.String(10),db.ForeignKey('teacher.teacher_id'), nullable=False)
    class_id = db.Column(db.Integer, nullable=False)
    leave_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='Pending')  # Pending, Approved, or Rejected
    assigned_teacher_id = db.Column(db.String(10), nullable=True)
    branch_name = db.Column(db.String(255))  # Add the teacher_branch field


###########################################################################

# Define a function to get teacher data
def get_teacher_data(teacher_id):
    # Query the database to get the teacher's data by their ID
    teacher = Teacher.query.filter_by(teacher_id=teacher_id).first()
    print(teacher)
    return teacher


@app.route('/')
def home():
    # Replace with code to fetch and display data from the database
    return render_template('base.html')

@app.route('/records')
def records():
    # Fetch records from the Teacher and Class models
    classes = Class.query.all()

    # Sorting and Filtering (example: sort by teacher name)
    sort_by = request.args.get('sort_by', 'name')
    if sort_by not in ['name', 'teacher_branch', 'designation', 'gender']:
        sort_by = 'name'

    # Filtering by branch
    branch = request.args.get('branch')
    if branch:
        teachers = Teacher.query.filter_by(teacher_branch=branch).order_by(sort_by).all()
    else:
        teachers = Teacher.query.order_by(sort_by).all()

    return render_template('records.html', teachers=teachers, classes=classes)




@app.route('/teacher-dashboard')
def teacher_dashboard():
    # Check if the teacher is logged in
    teacher_id = session.get('teacher_id')
    if not teacher_id:
        flash('You must log in as a teacher to access this page', 'error')
        return redirect(url_for('teacher_login'))

    # Fetch the teacher's weekly schedule using the provided function
    classes = get_teacher_weekly_schedule(teacher_id)
    assigned_classes = get_assigned_classes(teacher_id)

    # Fetch the teacher's details
    teacher = get_teacher_data(teacher_id)
    leave_requests = LeaveRequest.query.filter_by(teacher_id=teacher_id).all()

    return render_template('teacher_dashboard.html', assigned_classes=assigned_classes, classes=classes, leave_requests=leave_requests, day_names=day_names, teacher=teacher)

@app.route('/teacher-login', methods=['GET', 'POST'])
def teacher_login():
    if request.method == 'POST':
        teacher_id = str(request.form['teacher_id'])  # Ensure teacher_id is a string
        password = request.form['teacher_password']
        print(teacher_id, password)
        # Check the provided credentials and retrieve the user from the database
        user = User.query.filter_by(username=teacher_id, role='teacher').first()
        if user and user.password == password:
            # Teacher credentials are correct
            session['teacher_id'] = teacher_id  # Store teacher ID in the session
            return redirect(url_for('teacher_dashboard'))
        else:
            flash('Invalid teacher ID or password', 'error')

    return render_template('teacher_login.html')  # Assuming 'teacher_login.html' as your login page




# ...

@app.route('/apply_for_leave', methods=['GET', 'POST'])
def apply_for_leave():
    if request.method == 'POST':
        teacher_id = session.get('teacher_id')
        class_id = request.form.get('class_id')
        leave_date = request.form.get('leave_date')
        print(teacher_id)

        # Create a new leave request and add it to the database
        leave_request = LeaveRequest(teacher_id=teacher_id, class_id=class_id, leave_date=leave_date)
        db.session.add(leave_request)
        db.session.commit()

        flash('Leave request submitted successfully', 'success')
        print(teacher_id)
    teacher = get_teacher_data(teacher_id)

    assigned_classes = get_assigned_classes(teacher_id)
    return redirect(url_for('teacher_dashboard'))

@app.route('/view_leave_requests', methods=['GET'])
def view_leave_requests():
    teacher_id = session.get('teacher_id')
    
    # Query leave requests for the logged-in teacher
    leave_requests = LeaveRequest.query.filter_by(teacher_id=teacher_id).all()

    return render_template('view_leave_requests.html', leave_requests=leave_requests)


def get_available_leave_dates(teacher_id):
    # Fetch the teacher's assigned classes
    assigned_classes = get_assigned_classes(teacher_id)
    
    # Filter dates that are not the same as the assigned class dates
    available_dates = [str(today + timedelta(days=i)) for i in range(7)]
    available_leave_dates = [date for date in available_dates if date not in assigned_classes]
    return available_leave_dates


    return render_template('apply_for_leave.html', assigned_classes=assigned_classes, available_leave_dates=available_leave_dates)

# def get_assigned_classes(teacher_id, day_of_week):
#     assigned_classes = []
#     today = (day_of_week + 1) % 7  # Adjust for Sunday as 0

#     # Query for classes happening today
#     classes = Class.query.filter_by(teacher_id=teacher_id, day_of_week=today, is_active=True).all()
    
#     for class_data in classes:
#         class_time = class_data.class_time
#         class_datetime = datetime.combine(datetime.now().date(), class_time)
#         assigned_classes.append({
#             'class_name': class_data.class_name,
#             'class_time': class_time.strftime('%H:%M'),
#             'day_name': day_names[today],
#         })

    return assigned_classes

def get_assigned_classes(teacher_id):
    # Get all leave requests for the teacher
    leave_requests = LeaveRequest.query.filter_by(assigned_teacher_id=teacher_id).all()

    assigned_classes = []

    for leave_request in leave_requests:
        # Get the class details from the Class table
        class_data = Class.query.get(leave_request.class_id)

        assigned_classes.append({
            'leave_request_id': leave_request.id,
            'class_name': class_data.class_name,
            'day_of_week': class_data.day_of_week,
            'class_time': class_data.class_time.strftime('%H:%M'),
            'year': class_data.year,
            'status': leave_request.status,
            'assigned_teacher_id': leave_request.assigned_teacher_id,
            "date": leave_request.leave_date,
        })

    return assigned_classes


# ...

@app.route('/manage-leave-requests', methods=['GET', 'POST'])
def manage_leave_requests():
    print(session)
    if 1==1:
        if request.method == 'POST':
            pending_leave_requests = LeaveRequest.query.filter_by(status='Pending').all()
            print(pending_leave_requests)
            for leave_request in pending_leave_requests:
                # Sample code to assign leave class to another teacher (for demonstration purposes):
                available_teachers = Teacher.query.filter_by(teacher_branch=leave_request.teacher_branch).all()
                for teacher in available_teachers:
                    if not is_teacher_busy(teacher, leave_request.leave_date, leave_request.class_id):
                        leave_request.status = 'Approved'
                        leave_request.assigned_teacher_id = teacher.teacher_id
                        db.session.commit()
                        flash(f'Leave class assigned to {teacher.name}', 'success')
                        break
        
        teachers = Teacher.query.all()
        leave_requests = LeaveRequest.query.all()
        return render_template('manage_leave_requests.html', leave_requests=leave_requests,teachers=teachers)
    else:
        flash('You must log in as an administrator to access this page', 'error')
        return redirect(url_for('admin_login'))

# Modify the approve_leave route
@app.route('/approve-leave/<int:leave_request_id>', methods=['POST'])
def approve_leave(leave_request_id):
    if 'admin' in session.get('teacher_id'):
        leave_request = LeaveRequest.query.get(leave_request_id)
        if leave_request:
            # Add code here to approve the leave request
            leave_request.status = 'Approved'
            db.session.commit()
            
            # Find an available teacher
            new_teacher = find_available_teacher(leave_request.class_id, leave_request.leave_date,leave_request.teacher_id)
            
            if new_teacher:
                # Assign the new teacher to the class
                leave_request.assigned_teacher_id = new_teacher.teacher_id
                db.session.commit()
                send_sms_notification(new_teacher.phone_number, f'You have been assigned to teach a new class on {leave_request.leave_date}')
                print("sent success")
                flash(f'Leave class assigned to {new_teacher.name}', 'success')
            else:
                flash('No available teacher found', 'error')
        else:
            flash('Leave request not found', 'error')
    return redirect(url_for('manage_leave_requests'))

def send_sms_notification(phone_number, message):
    client.messages.create(
        to=phone_number,
        from_=TWILIO_PHONE_NUMBER,
        body=message
    )
# Create a function to find an available teacher
import random

def find_available_teacher(class_id, leave_date, leave_teacher_id):
    assigned_class = Class.query.get(class_id)
    class_time = assigned_class.class_time
    day_of_week = leave_date.weekday()
    teacher_branch = assigned_class.teacher.teacher_branch

    # Query teachers who are available at the given class time and date
    available_teachers = Teacher.query.filter_by(teacher_branch=teacher_branch).all()

    # Shuffle the list of available teachers randomly
    random.shuffle(available_teachers)

    for teacher in available_teachers:
        # Check if the teacher is not already busy at that time and is not the teacher who applied for leave
        if not is_teacher_busy(teacher, leave_date, class_time) and teacher.teacher_id != leave_teacher_id:
            return teacher

    return None

# Create a function to check if a teacher is busy at a given time
def is_teacher_busy(teacher, leave_date, class_time):
    day_of_week = leave_date.weekday()
    assigned_classes = get_assigned_classes(teacher.teacher_id)
    
    for assigned_class in assigned_classes:
        assigned_class_time = datetime.strptime(assigned_class['class_time'], '%H:%M').time()
        if assigned_class_time == class_time:
            return True
    
    return False


@app.route('/reject-leave/<int:leave_request_id>', methods=['POST'])
def reject_leave(leave_request_id):
    if 'admin' in session.get('teacher_id'):
        leave_request = LeaveRequest.query.get(leave_request_id)
        if leave_request:
            # Add code here to reject the leave request
            leave_request.status = 'Rejected'
            db.session.commit()
                
            flash('Leave request rejected successfully', 'success')
        else:
            flash('Leave request not found', 'error')
    return redirect(url_for('manage_leave_requests'))





def get_teacher_weekly_schedule(teacher_id):
    # Fetch the teacher's weekly classes based on their teacher_id and the current day of the week
    today = datetime.now().weekday()  # 0 for Monday, 1 for Tuesday, etc.
    classes = Class.query.filter_by(teacher_id=teacher_id).all()
    print(classes)
    return classes


# Define the teacher dashboard route
# @app.route('/teacher_dashboard')
# def teacher_dashboard():
#     print("ok")
#     # Check if the teacher is logged in
#     if 'teacher_id' in session:
#         teacher_id = session['teacher_id']
#         teacher = get_teacher_data(teacher_id)  # Fetch the teacher's data

#         # Fetch the teacher's weekly schedule - You need to implement this logic
#         classes = get_teacher_weekly_schedule(teacher_id)  # Replace with your function to fetch classes

#         return render_template('teacher_dashboard.html', teacher=teacher, classes=classes)
        
#     else:
#         flash('You must log in as a teacher first.', 'error')
#         return redirect(url_for('teacher_login'))

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if 'teacher_id' in session:  # Check if a teacher is logged in
        if request.method == 'POST':
            new_password = request.form['new_password']
            # Update the teacher's password in the database
            user = User.query.filter_by(username=session['teacher_id']).first()
            user.password = new_password
            db.session.commit()
            flash('Password updated successfully', 'success')
            return redirect(url_for('teacher_login'))
        return render_template('reset_password.html')
    else:
        return redirect(url_for('teacher_login'))

def ok():
      for i in range(1):
            run_check_upcoming_classes_continuously()
            break
    
@app.route('/add_teacher', methods=['GET', 'POST'])
def add_teacher():
    if request.method == 'POST':
        name = request.form['name']
        phone_number = request.form['phone_number']
        teacher_id = request.form['teacher_id']
        teacher_branch = request.form['teacher_branch']
        designation = request.form['designation']
        gender = request.form['gender']

        teacher = Teacher(
            teacher_id=teacher_id,
            name=name,
            phone_number=phone_number,
            teacher_branch=teacher_branch,
            designation=designation,
            gender=gender
        )

        db.session.add(teacher)
        db.session.commit()
        ok
        new_user = User(username=teacher_id, password='password',role='teacher')

        # Add the new user to the database
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('add_teacher'))
    return render_template('add_teacher.html')


################################################################

@app.route('/add_class', methods=['GET', 'POST'])
def add_class():
    if request.method == 'POST':
        teacher_id = request.form['teacher_id']
        class_name = request.form['class_name']
        day_of_week = request.form['day_of_week']
        class_time = request.form['class_time']
        year_of_students = request.form['year']
        class_activity = 'class_activity' in request.form  # Check if the checkbox is selected

        # Verify that the selected teacher_id exists in the teacher table
      
        class_data = Class(
                teacher_id=teacher_id,
                class_name=class_name,
                day_of_week=day_of_week,
                class_time=class_time,
                year=year_of_students,
                is_active=class_activity
            )
        db.session.add(class_data)
        db.session.commit()
        flash("Class Added Successfully")
       # for i in range(1):
        #    run_check_upcoming_classes_continuously()
        ok()
        return redirect(url_for('add_class'))

        
    teachers = Teacher.query.all()

    return render_template('add_class.html', teachers=teachers)

################################################################

@celery.task
def send_notification(teacher_id, class_name):
    with app.app_context():
        print("Sending notification task started")
        session = db.session
        now = datetime.now()
        try:
            teacher = Teacher.query.filter_by(teacher_id=teacher_id).first()
            if teacher:
                class_data = Class.query.filter_by(teacher_id=teacher_id, class_name=class_name).first()
                if class_data:
                    class_time = class_data.class_time
                    class_day = class_data.day_of_week

                    # Check if a notification has already been sent for this class today
                    class_notification = ClassNotification.query.filter_by(
                        teacher_id=teacher_id,
                        class_id=class_data.id,
                        date=now.date(),
                        notification_sent=True
                    ).first()

                    # Check if the class is assigned to another teacher
                    leave_request = LeaveRequest.query.filter_by(
                        class_id=class_data.id,
                        leave_date=now.date(),
                        status='Approved'
                    ).filter(LeaveRequest.assigned_teacher_id != teacher_id).first()

                    if not class_notification and not leave_request:
                        # Send the SMS
                        message = f"Upcoming class: {class_data.class_name}\n"
                        message += f"Teacher: {teacher.designation} {teacher.name} of Teacher Id {teacher.teacher_id}\n"
                        message += f"Time: {class_data.class_time.strftime('%H:%M')}\n"
                        message += f"Branch: {teacher.teacher_branch}"

                        try:
                            message = client.messages.create(
                                body=message,
                                from_=TWILIO_PHONE_NUMBER,
                                to=teacher.phone_number
                            )
                            print("SMS sent successfully")

                            # Mark the notification as sent after a successful SMS
                            class_notification = ClassNotification(
                                teacher_id=teacher_id,
                                class_id=class_data.id,
                                date=now.date(),
                                notification_sent=True,
                                notification_datetime=datetime.now()
                            )
                            db.session.add(class_notification)
                            db.session.commit()
                            print("Notification added to the database")
                        except TwilioRestException as e:
                            print(f"Error sending SMS: {str(e)}")
                    elif leave_request:
                        assigned_teacher = Teacher.query.filter_by(teacher_id=leave_request.assigned_teacher_id).first()

                        # Check if a reminder has already been sent to the assigned teacher today
                        reminder_notification = ClassNotification.query.filter_by(
                            teacher_id=assigned_teacher.teacher_id,
                            class_id=class_data.id,
                            date=now.date(),
                            notification_sent=True
                        ).first()

                        if not reminder_notification:
                            reminder_message = f"You were assigned to teach on behalf of {teacher.name} for class: {class_data.class_name}\n"
                            reminder_message += f"Teacher: {teacher.designation} {teacher.name} of Teacher Id {teacher.teacher_id}\n"
                            reminder_message += f"Time: {class_data.class_time.strftime('%H:%M')}\n"
                            reminder_message += f"Branch: {teacher.teacher_branch}"

                            try:
                                reminder_message = client.messages.create(
                                    body=reminder_message,
                                    from_=TWILIO_PHONE_NUMBER,
                                    to=assigned_teacher.phone_number
                                )
                                print(f"Reminder sent to assigned teacher: {assigned_teacher.name}")

                                # Mark the reminder notification as sent
                                reminder_notification = ClassNotification(
                                    teacher_id=assigned_teacher.teacher_id,
                                    class_id=class_data.id,
                                    date=now.date(),
                                    notification_sent=True,
                                    notification_datetime=datetime.now()
                                )
                                db.session.add(reminder_notification)
                                db.session.commit()
                                print("Reminder added to the database")
                            except TwilioRestException as e:
                                print(f"Error sending reminder to assigned teacher: {str(e)}")
                        else:
                            print(f"Reminder already sent to assigned teacher for {class_name} today")
                    else:
                        print(f"Notification already sent for {class_name} today or class is assigned to another teacher")
                else:
                    print("Class not found")
            else:
                print("Teacher not found")
        except Exception as ex:
            print(f"Error fetching teacher: {str(ex)}")
        print("Sending notification task completed")



def run_check_upcoming_classes_continuously():

    with app.app_context():
        while True:

            schedule.run_pending()
            time.sleep(5)
            now = datetime.now()
            today = (now.weekday() + 1) % 7  # Adjust for Sunday as 0
            classes = Class.query.filter_by(day_of_week=today).all()
#	    print(now)
            # Query for classes happening today

            print("TODAY CLASSES")
            print(classes)
            for class_data in classes:
                class_time = class_data.class_time
                class_id = class_data.id
                teacher_id = class_data.teacher_id
                class_name = class_data.class_name

                # Query the ClassNotification table for the specific class today
                class_notification = ClassNotification.query.filter_by(
                    class_id=class_id,
                    teacher_id=teacher_id,
                    date=now.date()
                ).first()

                if not class_notification:
                    # Check if notification is needed and the class is active
                    class_datetime = datetime.combine(now.date(), class_time)
                    time_until_class = class_datetime - now

                    if timedelta(0) <= time_until_class <= timedelta(minutes=10):
                        send_notification(teacher_id, class_name)
                        print("had class in next 10 mins")
                        print(teacher_id,':',class_name)

                    # Update the ClassNotification table to mark the notification as sent
                    # Update the ClassNotification table to mark the notification as sent
                    
########################################################



# Route for editing or deleting a class
@app.route('/edit_or_delete_class', methods=['GET', 'POST'])
def edit_or_delete_class():
    if request.method == 'POST':
        teacher_id = request.form['teacher_id']
        class_id = request.form['class_id']
        
        if 'edit' in request.form:
            # Redirect to the edit_class route with the selected class_id
            return redirect(url_for('edit_class', class_id=class_id))
        elif 'delete' in request.form:
            # Delete the selected class (you need to implement this logic)
            class_data = Class.query.get(class_id)
            if class_data:
                db.session.delete(class_data)
                db.session.commit()
            return redirect(url_for('edit_or_delete_class'))  # Redirect to the same page

    teachers = Teacher.query.all()
    classes = Class.query.all()
    return render_template('edit_or_delete_class.html', teachers=teachers, classes=classes)

# Route for editing or deleting a teacher
@app.route('/edit_or_delete_teacher', methods=['GET', 'POST'])
def edit_or_delete_teacher():
    if request.method == 'POST':
        teacher_id = request.form['teacher_id']
        
        if 'edit' in request.form:
            # Redirect to the edit_teacher route with the selected teacher_id
            return redirect(url_for('edit_teacher', teacher_id=teacher_id))
        elif 'delete' in request.form:
            # Delete the selected teacher (you need to implement this logic)
            teacher = Teacher.query.get(teacher_id)
            if teacher:
                db.session.delete(teacher)
                db.session.commit()
            return redirect(url_for('edit_or_delete_teacher'))  # Redirect to the same page

    teachers = Teacher.query.all()
    return render_template('edit_or_delete_teacher.html', teachers=teachers)


@app.route('/edit_teacher/<string:teacher_id>', methods=['GET', 'POST'])
def edit_teacher(teacher_id):
    teacher = Teacher.query.get(teacher_id)

    if request.method == 'POST':
        name = request.form['name']
        phone_number = request.form['phone_number']
        teacher_id = request.form['teacher_id']
        teacher_branch = request.form['teacher_branch']
        designation = request.form['designation']
        gender = request.form['gender']

        teacher.teacher_id = teacher_id
        teacher.name = name
        teacher.phone_number = phone_number
        teacher.teacher_branch = teacher_branch
        teacher.designation = designation
        teacher.gender = gender

        db.session.commit()
        flash('Teacher details updated successfully')
        return redirect(url_for('edit_or_delete_teacher'))

    return render_template('edit_teacher.html', teacher=teacher)



@app.route('/delete_teacher/<int:teacher_id>', methods=['POST'])
def delete_teacher(teacher_id):
    teacher = Teacher.query.get(teacher_id)
    if teacher:
        db.session.delete(teacher)
        db.session.commit()
        flash('Teacher deleted successfully')
    return redirect(url_for('add_teacher'))

@app.route('/edit_class/<int:class_id>', methods=['GET', 'POST'])
def edit_class(class_id):
    class_data = Class.query.get(class_id)
    print(class_data)

    if request.method == 'POST':
        try:
            print(request.form)
            teacher_id = request.form['teacher_id']
            class_name = request.form['class_name']
            day_of_week = request.form['day_of_week']
            class_time = request.form['new_class_time']
            year_of_students = request.form['year']
            class_activity = 'class_activity' in request.form  # Check if the checkbox is selected

            # Verify that the selected teacher_id exists in the teacher table

            class_data.teacher_id = teacher_id
            class_data.class_name = class_name
            class_data.day_of_week = day_of_week
            class_data.class_time = class_time
            class_data.year_of_students = year_of_students
            class_data.class_activity = class_activity

            db.session.add(class_data)
            db.session.commit()

            print('Class details updated successfully')
            run_check_upcoming_classes_continuously

            return redirect(url_for('edit_class', class_id=class_id))
        
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Error updating class details: {str(e)}")

    teachers = Teacher.query.all()  # Retrieve a list of all teachers
    return render_template('edit_class.html', class_data=class_data, teachers=teachers)


@app.route('/delete_class/<int:class_id>', methods=['POST'])
def delete_class(class_id):
    class_data = Class.query(class_id)
    if class_data:
        db.session.delete(class_data)
        db.session.commit()
        flash('Class deleted successfully')
    return redirect(url_for('add_class'))


######################################################################################

@app.route('/get_classes/<string:teacher_id>')
def get_classes(teacher_id):

    classes = Class.query.filter_by(teacher_id=teacher_id).all()

    classes_data = [{'id': Class.id, 'class_name': Class.class_name} for Class in classes]
    return jsonify({'classes': classes_data})


@app.route('/teacher_details_by_branch/<int:teacher_id>')
def teacher_details_by_branch(teacher_id):
    teacher = Teacher.query.get(teacher_id)

    if teacher is None:
        flash('Teacher not found')
        return redirect(url_for('teachers_by_branch'))

    branch = teacher.teacher_branch
    classes = Class.query.filter_by(teacher_id=teacher_id).all()

    return render_template('teacher_details_by_branch.html', teacher=teacher, branch=branch, classes=classes,day_names=day_names)


##############################################################################
day_names = {
    0: "Sunday",
    1: "Monday",
    2: "Tuesday",
    3: "Wednesday",
    4: "Thursday",
    5: "Friday",
    6: "Saturday"
}

def organize_teachers_by_branch(teachers):
    teachers_by_branch = {}
    for teacher in teachers:
        branch = teacher.teacher_branch
        if branch not in teachers_by_branch:
            teachers_by_branch[branch] = []
        teachers_by_branch[branch].append(teacher)
    return teachers_by_branch

def get_all_branches():
    branches = db.session.query(Teacher.teacher_branch).distinct().all()
    return [branch[0] for branch in branches]


@app.route('/teachers_by_branch', methods=['GET'])
def teachers_by_branch():
    branch = request.args.get('branch')
    if branch == 'all':
        # Retrieve all teachers
        teachers = Teacher.query.all()
    else:
        # Retrieve teachers for the selected branch
        teachers = Teacher.query.filter_by(teacher_branch=branch).all()

    # Organize teachers by branch
    teachers_by_branch = organize_teachers_by_branch(teachers)
    
    # Retrieve the list of all branches
    branches = get_all_branches()

    return render_template('teachers_by_branch.html', teachers_by_branch=teachers_by_branch,day_names=day_names,branches=branches)

######################################################################################

@app.route('/notification-logs', methods=['GET'])
def notification_logs():
    filter_option = request.args.get('filter', 'day')  # Get the selected filter from the URL

    # Determine the date range based on the filter option
    if filter_option == 'day':
        start_date = datetime.now().replace(day=1).date()  # Start of the month
        end_date = datetime.now().date()  # Today
    elif filter_option == 'week':
        today = datetime.now().date()
        start_date = today - timedelta(days=today.weekday())  # Start of the week
        end_date = start_date + timedelta(days=6)  # End of the week
    elif filter_option == 'month':
        today = datetime.now().date()
        start_date = today.replace(day=1)  # Start of the month
        end_date = today.replace(day=28)  # End of the month (considering February)
    
    # Query the database for notification logs within the date range
    notification_logs = ClassNotification.query.filter(
        ClassNotification.date >= start_date,
        ClassNotification.date <= end_date
    ).all()

    return render_template('notification_logs.html', filter=filter_option, logs=notification_logs)


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    return render_template('home.html')



@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if 'teacher_id' in session:
        # If a session is already active, redirect to 'home.html'
        return render_template('home.html')

    if request.method == 'POST':
        username = request.form['admin_username']
        password = request.form['admin_password']

        if username == 'admin' and password == 'admin':
            # Admin credentials are correct; you can use a more secure authentication method
            session['teacher_id'] = "admin"
            return redirect(url_for('admin'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('admin_login.html')



@app.route('/logout')
def logout():
    if 'user_id' in session:
        session.pop('user_id', None)  # Remove the user_id from the session
    return redirect(url_for('home'))  # Redirect to the home page after logging out
@app.route('/admin_log')
def admin_log():
    return render_template('admin_login.html')
@app.route('/teacher_log')
def teacher_log():
    return render_template('teacher_login.html')
######################################################################################


if __name__ == '__main__':
    # Start a timer that runs the check_upcoming_classes function continuously
    timer_thread = threading.Thread(target=run_check_upcoming_classes_continuously)
    timer_thread.daemon = True  # Run the thread as a daemon to allow the main program to exit
    timer_thread.start()

    app.run(debug=True)
