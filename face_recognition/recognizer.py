import os
from deepface import DeepFace
from cloudant_setup import students_db
from werkzeug.utils import secure_filename

def match_face(uploaded_image_path):
    try:
        for student in students_db:
            student_image_filename = student.get('image_path')
            if not student_image_filename:
                continue

            db_image_path = os.path.join('static', 'uploads', secure_filename(student_image_filename))
            if not os.path.exists(db_image_path):
                continue

            result = DeepFace.verify(
                img1_path=uploaded_image_path,
                img2_path=db_image_path,
                enforce_detection=True,
                model_name='VGG-Face',
                distance_metric='cosine'
            )

            if result.get('verified') and result.get('distance') < 0.45:
                return {
                    "name": student.get("name"),
                    "student_id": student.get("student_id"),
                    "bus_number": student.get("bus_number"),
                    "image": student.get("image_path")
                }
        return None
    except Exception as e:
        print(f"❌ Face match error: {e}")
        return None
