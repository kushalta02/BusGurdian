import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
from flask import Flask, render_template, request, redirect, session,jsonify,url_for
from cloudant_setup import users_db
from cloudant_setup import alerts_db
from cloudant_setup import buses_db
from cloudant_setup import attendance_db
from cloudant_setup import students_db
from cloudant_setup import complaints_db
from datetime import datetime
from werkzeug.utils import secure_filename
from face_recognition.recognizer import match_face
from cloudant.error import CloudantException
from uuid import uuid4


app = Flask(__name__)
app.secret_key = 'mysecretkey'  # required for session
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create the folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return redirect(url_for('login'))

# from flask import request, render_template, redirect, session
# from cloudant.query import Query  # if needed
# from cloudant.document import Document

# from flask import Flask, render_template, request, session, redirect, url_for

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            error = "⚠️ Please enter both email and password."
        else:
            # Query using 'email' field since _id is not the email
            result = users_db.get_query_result({'email': {'$eq': email}})
            user_docs = list(result)

            if not user_docs:
                error = "❌ User does not exist. Please sign up."
            else:
                user = user_docs[0]
                if user['password'] == password:
                    session['email'] = user['email']
                    session['role'] = user['role']
                    session['user'] = dict(user)
                    return redirect(f"/{user['role']}_dashboard")
                else:
                    error = "❌ Incorrect password."

    return render_template('login.html', error=error)




# ---------------------- SIGNUP ROUTE ----------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.form
        student_id = data['student_id']
        student_name = data['student_name']
        parent_name = data['parent_name']
        email = data['email']
        password = data['password']
        contact = data['parent_contact']
        bus_id = data['bus_id']

        try:
            # 1. Check if email already exists
            existing_user = list(users_db.get_query_result({'email': {'$eq': email}}))
            if existing_user:
                return "❌ Email already registered. Please login."

            # 2. Create student document
            students_db.create_document({
                "_id": student_id,
                "name": student_name,
                "parent_contact": contact,
                "bus_id": bus_id
            })

            # 3. Create user document with random UUID as _id
            users_db.create_document({
                "_id": str(uuid4()),  # random _id
                "email": email,
                "password": password,
                "role": "parent",
                "student_id": student_id,
                "parent_name": parent_name
            })

            return redirect(url_for('login'))

        except CloudantException as e:
            return f"❌ An error occurred: {str(e)}"

    return render_template('signup.html')

@app.route('/simulate_fatigue', methods=['GET', 'POST'])
def simulate_fatigue():
    if 'user' not in session or session['user']['role'] != 'admin':
        return redirect('/login')

    if request.method == 'POST':
        bus_no = request.form['bus_number']
        timestamp = datetime.datetime.now().isoformat()
        doc = {
            "bus_number": bus_no,
            "message": f"Fatigue detected in Bus {bus_no}!",
            "timestamp": timestamp,
            "status": "Unresolved"
        }
        alerts_db.create_document(doc)  # fixed from db_fatigue → alerts_db
        return redirect('/dashboard')

    return render_template('simulate_fatigue.html')


@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    user = session['user']
    role = user['role']

    if role == 'admin':
        fatigue_alerts = alerts_db.get_query_result({"status": "High"})
        alert_messages = [doc['message'] for doc in fatigue_alerts]
        return render_template('admin_dash.html', user=user, alerts=alert_messages)
    
    elif role == 'driver':
        return render_template('driver_dashboard.html', user=user)
    
    elif role == 'parent':
        return render_template('parent_dashboard.html', user=session['user'], student=student)

    else:
        return "❌ Unknown role"
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')
@app.route('/parent_dashboard')
def parent_dashboard():
    if 'role' in session and session['role'] == 'parent':
        student_id = session['user'].get('student_id')

        if not student_id:
            return "⚠️ Student ID missing in session", 400

        # ✅ Fallback loop to avoid .get() issues
        student = None
        for doc in students_db:
            if doc['_id'] == student_id:
                student = doc
                break

        if not student:
            return f"❌ Student with ID '{student_id}' not found in database.", 404

        return render_template('parent_dashboard.html', user=session['user'], student=student)

    return redirect(url_for('login'))



    


@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    # Example: Fetch recent fatigue alerts (customize based on your app logic)
    fatigue_alerts = [doc for doc in alerts_db if doc.get('status') == 'High']
    alert_messages = [doc.get('message') for doc in fatigue_alerts]

    # Example: Fetch total number of buses, complaints, and students
    total_buses = len([bus for bus in buses_db])
    total_complaints = len([comp for comp in complaints_db])
    total_students = len([student for student in students_db])

    return render_template(
        'admin_dash.html',
        user=session['user'],
        alerts=alert_messages,
        total_buses=total_buses,
        total_complaints=total_complaints,
        total_students=total_students
    )

@app.route('/driver_dashboard')
def driver_dashboard():
    if 'user' not in session or session['user']['role'] != 'driver':
        return redirect('/login')
    return render_template('driver_dashboard.html', user=session['user'])
@app.route('/view_attendance_bus', methods=['GET'])
def view_attendance_bus():
    bus_numbers = list({record.get("bus_number", "").upper() for record in attendance_db})
    return render_template("admin_attendance_by_bus_form.html", bus_numbers=bus_numbers)

@app.route('/view_attendance_bus_result', methods=['POST'])
def view_attendance_bus_result():
    bus_number = request.form.get("bus_number", "").strip().upper()
    today = datetime.now().strftime("%Y-%m-%d")

    present_students = []

    for record in attendance_db:
        record_bus = record.get("bus_number", "").strip().upper()
        record_status = record.get("status", "").strip().lower()
        timestamp = record.get("timestamp")
        record_date = timestamp.split("T")[0] if timestamp else ""

        if record_bus == bus_number and record_date == today and record_status == "present":
            student_id = record.get("student_id")
            for student in students_db:
                if student.get("student_id") == student_id or student.get("_id") == student_id:
                    present_students.append({
                        "student_id": student_id,
                        "name": student.get("name") or student.get("student_name"),
                        "bus_number": record.get("bus_number"),
                        "photo": student.get("photo", ""),  # make sure filename exists
                        "timestamp": record.get("timestamp")
                    })
                    break

    return render_template("admin_attendance_result.html", students=present_students, bus_number=bus_number)


# bus tracking for admin
@app.route('/admin_map')
def admin_map():
    if 'user' not in session or session['user']['role'] != 'admin':
        return redirect('/login')
    return render_template('admin_map.html')

@app.route('/admin_map_data')
def admin_map_data():
    if 'user' not in session or session['user']['role'] != 'admin':
        return jsonify([])

    buses = list(buses_db)
    return jsonify(buses)



@app.route('/get_bus_location')
def get_bus_location():
    bus_number = request.args.get('bus_number')
    bus = next((b for b in buses_db if b.get('_id') == bus_number), None)

    if bus:
        return jsonify({
            "lat": float(bus.get('current_lat', 0.0)),
            "lng": float(bus.get('current_lng', 0.0))
        })
    return jsonify({"lat": 0.0, "lng": 0.0})




#parents_attendance
@app.route('/track_bus_parent')
def track_bus_parent():
    if 'user' not in session or session['role'] != 'parent':
        return redirect(url_for('login'))

    student_id = session['user'].get('student_id')
    student = students_db.get(student_id)

    if not student:
        return render_template('parent_bus_tracking.html', error="Student not found", bus=None)

    # Use 'bus_number' field from student
    bus_number = student.get('bus_number')
    if not bus_number:
        return render_template('parent_bus_tracking.html', error="Bus number missing in student record", bus=None)

    try:
        bus = buses_db[bus_number]
    except KeyError:
        return render_template('parent_bus_tracking.html', error=f"Bus '{bus_number}' not found", bus=None)

    return render_template('parent_bus_tracking.html', bus=bus)


@app.route('/view_attendanceP')
def view_attendanceP():
    if 'user' not in session or session['role'] != 'parent':
        return redirect(url_for('login'))

    student_id = session['user'].get('student_id')

    if not student_id:
        return "⚠️ Student ID not found in session.", 400

    # Get attendance records for this student
    attendance_records = []
    for doc in attendance_db:
        if doc.get("student_id") == student_id:
            # Extract only required fields and format date
            timestamp = doc.get("timestamp", "")
            date = timestamp.split("T")[0] if "T" in timestamp else timestamp

            attendance_records.append({
                "date": date,
                "status": doc.get("status", "").capitalize(),
                "time": timestamp.split("T")[1] if "T" in timestamp else "",
                "bus_number": doc.get("bus_number", "N/A")
            })

    # Sort by date descending (latest first)
    attendance_records.sort(key=lambda x: x["date"], reverse=True)

    return render_template('view_attendanceP.html', attendance=attendance_records)


#for admin 
@app.route('/upload_face', methods=['GET', 'POST'])
def upload_face():
    if request.method == 'POST':
        file = request.files.get('face_image')
        if not file:
            return "❌ No image uploaded"

        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        result = match_face(file_path)

        if result:
            attendance_db.create_document({
                "student_id": result["student_id"],
                "student_name": result["name"],
                "bus_number": result["bus_number"],
                "date": datetime.datetime.now().strftime("%Y-%m-%d"),
                "timestamp": datetime.datetime.now().isoformat(),
                "status": "Present"
            })

            return render_template("attendance_success.html", student=result)
        else:
            return render_template("attendance_fail.html", message="Face not recognized.")

    return render_template("upload_face.html")

@app.route("/submit_complaint", methods=["GET", "POST"])
def submit_complaint():
    message = None

    if request.method == "POST":
        issue_type = request.form.get("issue_type")
        bus_number = request.form.get("bus_number")
        description = request.form.get("description")

        next_id = f"C{int(datetime.now().timestamp())}"
        doc = {
            "_id": next_id,
            "issue_type": issue_type,
            "bus_number": bus_number,
            "description": description,
            "timestamp": datetime.now().isoformat()
        }

        complaints_db.create_document(doc)
        message = f"✅ Complaint submitted successfully! Your complaint ID is {next_id}"

    return render_template("submit_complaint.html", message=message)

@app.route('/view_complaints')
def view_complaints():
    if 'user' not in session or session['user']['role'] != 'admin':
        return redirect('/login')

    complaints = [doc for doc in complaints_db]
    return render_template('view_complaints.html', complaints=complaints)
#Manage Buses for admin
@app.route('/manage_buses', methods=['GET', 'POST'])
def manage_buses():
    if request.method == 'POST':
        action = request.form.get('action')
        bus_number = request.form.get('bus_number').strip().upper()

        if action == 'Add':
            doc = {
                '_id': bus_number,
                'driver_name': request.form.get('driver_name'),
                'driver_phone': request.form.get('driver_phone'),
                'route': request.form.get('route'),
                'latitude': float(request.form.get('latitude') or 0),
                'longitude': float(request.form.get('longitude') or 0)
            }
            if bus_number not in [b['_id'] for b in buses_db]:
                buses_db.create_document(doc)

        elif action == 'Update':
            doc = buses_db.get(bus_number)
            if doc:
                doc['driver_name'] = request.form.get('driver_name')
                doc['driver_phone'] = request.form.get('driver_phone')
                doc['route'] = request.form.get('route')
                doc['latitude'] = float(request.form.get('latitude') or 0)
                doc['longitude'] = float(request.form.get('longitude') or 0)
                doc.save()

        elif action == 'Delete':
            doc = buses_db.get(bus_number)
            if doc:
                doc.delete()

        return redirect(url_for('manage_buses'))

    # GET
    all_buses = [bus for bus in buses_db]
    return render_template('manage_buses.html', buses=all_buses)
@app.route('/debug_data')
def debug_data():
    users = [{"student_id": u.get("student_id"), "bus_number": u.get("bus_number")} for u in users_db]
    buses = [{"_id": b["_id"], "lat": b.get("current_lat"), "lng": b.get("current_lng")} for b in buses_db]
    return jsonify({"users_db": users, "buses_db": buses})
@app.route('/update_location', methods=['POST'])
def update_location():
    if 'user' not in session or session['user']['role'] != 'driver':
        return "Unauthorized", 403

    data = request.get_json()
    lat = data.get('lat')
    lng = data.get('lng')
    bus_number = session['user'].get('bus_number')

    bus = next((bus for bus in buses_db if bus['_id'] == bus_number), None)
    if not bus:
        return "Bus not found", 404

    bus['current_lat'] = lat
    bus['current_lng'] = lng
    bus.save()  # Save to Cloudant

    return "✅ Location updated"
# @app.route('/track_bus_parent', methods=['POST'])
# def track_bus_parent():
#     student_id = request.form.get("student_id", "").strip()

#     student = next((s for s in students_db if s.get("student_id") == student_id or s.get("_id") == student_id), None)
#     if not student:
#         return render_template("parent_bus_tracking.html", error="Student not found.", bus=None)

#     bus_number = student.get("bus_number")
#     bus = next((b for b in buses_db if b.get("bus_number") == bus_number), None)
#     if not bus:
#         return render_template("parent_bus_tracking.html", error="Bus not found.", bus=None)

#     return render_template("parent_bus_tracking.html", bus=bus)
@app.route('/test_student/<sid>')
def test_student(sid):
    doc = students_db.get(sid)
    if doc:
        return f"✅ Found: {doc['name']}"
    else:
        return "❌ Student not found"



if __name__ == '__main__':
    app.run(debug=True)
app.config['UPLOAD_FOLDER'] = 'static/uploads/test_faces'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max
print(file)
pint(request.files)