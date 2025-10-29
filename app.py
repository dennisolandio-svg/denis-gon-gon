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
HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Student Control Panel</title>
<link href="https://cdn.jsdelivr.net/npm/tailwindcss@3.3.2/dist/tailwind.min.css" rel="stylesheet">
<style>
  body { font-family: 'Inter', sans-serif; background: #f1f5f9; }
  .sidebar { background: #1e293b; color: white; }
  .sidebar button { background: #3b82f6; }
  .sidebar button:hover { background: #2563eb; }
  .card:hover { transform: translateY(-3px); box-shadow: 0 10px 20px rgba(0,0,0,0.1); }
  #modal { background: rgba(0,0,0,0.6); }
</style>
</head>
<body class="flex h-screen overflow-hidden">

<!-- Sidebar -->
<aside class="sidebar w-64 flex flex-col p-6">
  <h2 class="text-xl font-bold mb-6">Student System</h2>
  <button onclick="showAdd()" class="w-full py-2 mb-4 rounded font-semibold">+ Add Student</button>
  <input id="search" placeholder="Search..." oninput="search(this.value)" class="p-2 rounded mb-2 text-black">
  <button onclick="exportData()" class="w-full py-2 mt-2 rounded bg-green-500 hover:bg-green-600">⬇ Export JSON</button>
  <hr class="my-4 border-gray-500">
  <div class="mt-auto text-gray-300">Total: <strong id="count">0</strong></div>
</aside>

<!-- Main Content -->
<main class="flex-1 flex flex-col overflow-hidden">
  <header class="bg-white shadow flex justify-between items-center px-6 py-4">
    <h3 class="text-lg font-semibold text-gray-700">Dashboard</h3>
    <input id="headerSearch" placeholder="Quick Search..." oninput="search(this.value)" class="p-2 border rounded w-72">
  </header>

  <div class="flex-1 overflow-y-auto p-6">
    <div id="list" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
      <p>Loading...</p>
    </div>
  </div>

  <footer class="bg-white p-4 text-center text-gray-500 shadow-inner">
    &copy; 2025 Student Management Panel
  </footer>
</main>

<!-- Modal -->
<div id="modal" class="fixed inset-0 hidden justify-center items-center">
  <div id="modalContent" class="bg-white p-6 rounded-lg w-96 shadow-lg">
    <h3 id="modalTitle" class="text-xl font-semibold mb-4">Add Student</h3>
    <input id="ename" placeholder="Full name" class="w-full p-2 mb-3 border rounded">
    <input id="egrade" type="number" placeholder="Grade" class="w-full p-2 mb-3 border rounded">
    <input id="esection" placeholder="Section" class="w-full p-2 mb-3 border rounded">
    <input id="econtact" placeholder="Contact" class="w-full p-2 mb-4 border rounded">
    <button onclick="save()" class="w-full py-2 bg-blue-600 text-white rounded hover:bg-blue-700">Save</button>
  </div>
</div>

<script>
let editId = null;
let editing = false;

async function load() {
  const res = await fetch('/students');
  const data = await res.json();
  render(data);
  const c = await fetch('/students/count');
  const n = await c.json();
  document.getElementById('count').textContent = n.count;
}

function render(data) {
  const list = document.getElementById('list');
  if (!data.length) { list.innerHTML = "<p class='col-span-full text-gray-500'>No students yet.</p>"; return; }
  list.innerHTML = data.map(s => `
    <div class="card bg-white p-4 rounded-lg shadow transition duration-200">
      <div class="student-info mb-3">
        <h3 class="font-semibold text-lg">${s.name}</h3>
        <small class="text-gray-500">Grade: ${s.grade} • Section: ${s.section}</small><br>
        <small class="text-gray-500">📞 ${s.contact}</small><br>
        <small class="text-gray-400">Registered: ${new Date(s.date_registered).toLocaleDateString()}</small>
      </div>
      <div class="flex justify-between">
        <button onclick="edit(${s.id})" class="px-3 py-1 bg-indigo-100 text-indigo-700 rounded hover:bg-indigo-200">✏️ Edit</button>
        <button onclick="remove(${s.id})" class="px-3 py-1 bg-red-100 text-red-600 rounded hover:bg-red-200">🗑️ Delete</button>
      </div>
    </div>
  `).join('');
}

function showAdd() {
  editing = false; editId = null;
  document.getElementById('modalTitle').textContent = "Add Student";
  ename.value = egrade.value = esection.value = econtact.value = "";
  document.getElementById('modal').style.display='flex';
}

async function save() {
  const d = { name:ename.value, grade:parseInt(egrade.value), section:esection.value, contact:econtact.value };
  if (!d.name || !d.grade || !d.section || !d.contact) return alert("Fill all fields");
  if (editing) {
    await fetch(`/student/${editId}`, {method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify(d)});
  } else {
    await fetch('/student', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(d)});
  }
  document.getElementById('modal').style.display='none';
  load();
}

async function edit(id) {
  editing = true;
  const res = await fetch(`/student/${id}`);
  const s = await res.json();
  editId = s.id;
  document.getElementById('modalTitle').textContent = "Edit Student";
  ename.value = s.name; egrade.value = s.grade; esection.value = s.section; econtact.value = s.contact;
  document.getElementById('modal').style.display='flex';
}

async function remove(id) {
  if (!confirm("Delete this student?")) return;
  await fetch(`/student/${id}`, {method:'DELETE'});
  load();
}

function search(q) {
  if (!q) return load();
  fetch('/students').then(r=>r.json()).then(d=>{
    render(d.filter(s=>s.name.toLowerCase().includes(q.toLowerCase())));
  });
}

function exportData() { window.location.href='/students/export'; }

load();
</script>

</body>
</html>

"""

# ---------- MAIN ----------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
