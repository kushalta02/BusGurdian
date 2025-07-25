import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
from flask import Flask, render_template, request, redirect, session,jsonify
from cloudant_setup import users_db
from cloudant_setup import alerts_db
from cloudant_setup import buses_db
from cloudant_setup import attendance_db
from cloudant_setup import students_db
from cloudant_setup import complaints_db
from datetime import datetime
from werkzeug.utils import secure_filename
from face_recognition.recognizer import match_face

app = Flask(__name__)
app.secret_key = 'mysecretkey'  # required for session
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create the folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        for user in users_db:
            if user['email'] == email and user['password'] == password:
                session['user'] = {
                    'id': user['_id'],
                    'email': user['email'],
                    'role': user['role'],
                    'name': user.get('name', ''),
                    'bus_number': user.get('bus_number')  # needed for drivers
                }

                # Redirect based on role
                if user['role'] == 'admin':
                    return redirect('/dashboard')
                elif user['role'] == 'parent':
                    return redirect('/parent_dashboard')
                elif user['role'] == 'driver':
                    return redirect('/driver_dashboard')

        return "❌ Invalid email or password."

    return render_template('login.html')
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
        return render_template('parent_dashboard.html', user=user)

    else:
        return "❌ Unknown role"
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')
@app.route('/parent_dashboard')
def parent_dashboard():
    if 'user' not in session or session['user']['role'] != 'parent':
        return redirect('/login')
    return render_template('parent_dashboard.html', user=session['user'])
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
@app.route("/view_attendanceP", methods=["POST"])
def view_attendance_parent():
    student_id = request.form.get("student_id", "").strip()
    student_name = request.form.get("student_name", "").strip().lower()
    today = datetime.now().strftime("%Y-%m-%d")

    student_found = None
    attendance_status = "Absent"

    # Search for student in students_db
    for student in students_db:
        sid = student.get("student_id") or student.get("_id")
        sname = (student.get("name") or student.get("student_name", "")).lower()

        if sid == student_id and sname == student_name:
            student_found = student
            break

    if student_found:
        for record in attendance_db:
            rid = record.get("student_id")
            rdate = record.get("timestamp", "").split("T")[0] if record.get("timestamp") else ""
            status = record.get("status", "").lower()

            if rid == student_id and rdate == today and status == "present":
                attendance_status = "Present"
                break

    return render_template("parent_attendance_result.html", student=student_found, status=attendance_status, today=today)



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
@app.route('/track_bus_parent', methods=['POST'])
def track_bus_parent():
    student_id = request.form.get("student_id", "").strip()

    student = next((s for s in students_db if s.get("student_id") == student_id or s.get("_id") == student_id), None)
    if not student:
        return render_template("parent_bus_tracking.html", error="Student not found.", bus=None)

    bus_number = student.get("bus_number")
    bus = next((b for b in buses_db if b.get("bus_number") == bus_number), None)
    if not bus:
        return render_template("parent_bus_tracking.html", error="Bus not found.", bus=None)

    return render_template("parent_bus_tracking.html", bus=bus)



if __name__ == '__main__':
    app.run(debug=True)
app.config['UPLOAD_FOLDER'] = 'static/uploads/test_faces'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max
print(file)
pint(request.files)