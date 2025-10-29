from flask import Flask, request, jsonify, render_template_string, send_file
import json, io
from datetime import datetime

app = Flask(__name__)

# ---------- IN-MEMORY STORAGE ----------
students = []
next_id = 1

# ---------- API ----------
@app.route("/student", methods=["POST"])
def add_student():
    global next_id
    d = request.get_json()
    if not all(k in d for k in ("name", "grade", "section", "contact")):
        return jsonify({"error": "Missing fields"}), 400
    student = {
        "id": next_id,
        "name": d["name"],
        "grade": d["grade"],
        "section": d["section"],
        "contact": d["contact"],
        "date_registered": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    students.append(student)
    next_id += 1
    return jsonify({"message": "Added"}), 201

@app.route("/students", methods=["GET"])
def get_students():
    return jsonify(sorted(students, key=lambda s: s["id"], reverse=True))

@app.route("/student/<int:i>", methods=["GET"])
def get_student(i):
    s = next((st for st in students if st["id"] == i), None)
    return jsonify(s) if s else (jsonify({"error": "Not found"}), 404)

@app.route("/student/<int:i>", methods=["PUT"])
def update_student(i):
    d = request.get_json()
    s = next((st for st in students if st["id"] == i), None)
    if not s:
        return jsonify({"error": "Not found"}), 404
    s.update({
        "name": d.get("name", s["name"]),
        "grade": d.get("grade", s["grade"]),
        "section": d.get("section", s["section"]),
        "contact": d.get("contact", s["contact"]),
    })
    return jsonify({"message": "Updated"})

@app.route("/student/<int:i>", methods=["DELETE"])
def delete_student(i):
    global students
    before = len(students)
    students = [st for st in students if st["id"] != i]
    return jsonify({"message": "Deleted"} if len(students) < before else {"error": "Not found"})

@app.route("/students/count")
def count():
    return jsonify({"count": len(students)})

@app.route("/students/export")
def export():
    j = json.dumps(students, indent=2)
    buf = io.BytesIO(j.encode())
    buf.seek(0)
    return send_file(buf, mimetype="application/json", as_attachment=True, download_name="students.json")

@app.route("/")
def index():
    return render_template_string(HTML)

# ---------- FRONTEND (Glass UI) ----------
HTML = """<the same HTML as your version above>"""

# ---------- MAIN ----------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
