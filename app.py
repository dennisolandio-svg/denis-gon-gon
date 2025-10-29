from flask import Flask, request, jsonify, render_template_string, send_file
import sqlite3, json, io
from datetime import datetime

app = Flask(__name__)
DB = "students.db"

# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            grade INTEGER NOT NULL,
            section TEXT NOT NULL,
            contact TEXT NOT NULL,
            date_registered TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

# ---------- API ----------
@app.route("/student", methods=["POST"])
def add_student():
    d = request.get_json()
    if not all(k in d for k in ("name", "grade", "section", "contact")):
        return jsonify({"error": "Missing fields"}), 400
    conn = db()
    conn.execute(
        "INSERT INTO students(name,grade,section,contact,date_registered) VALUES(?,?,?,?,?)",
        (d["name"], d["grade"], d["section"], d["contact"], datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Added"}), 201

@app.route("/students", methods=["GET"])
def students():
    conn = db()
    s = [dict(r) for r in conn.execute("SELECT * FROM students ORDER BY id DESC")]
    conn.close()
    return jsonify(s)

@app.route("/student/<int:i>", methods=["GET"])
def student(i):
    conn = db()
    c = conn.execute("SELECT * FROM students WHERE id=?", (i,))
    s = c.fetchone()
    conn.close()
    return jsonify(dict(s)) if s else (jsonify({"error":"Not found"}), 404)

@app.route("/student/<int:i>", methods=["PUT"])
def update(i):
    d = request.get_json()
    conn = db()
    c = conn.execute("SELECT * FROM students WHERE id=?", (i,))
    s = c.fetchone()
    if not s:
        return jsonify({"error":"Not found"}), 404
    conn.execute(
        "UPDATE students SET name=?,grade=?,section=?,contact=? WHERE id=?",
        (d.get("name", s["name"]), d.get("grade", s["grade"]),
         d.get("section", s["section"]), d.get("contact", s["contact"]), i)
    )
    conn.commit()
    conn.close()
    return jsonify({"message":"Updated"})

@app.route("/student/<int:i>", methods=["DELETE"])
def delete(i):
    conn = db()
    cur = conn.execute("DELETE FROM students WHERE id=?", (i,))
    conn.commit()
    ok = cur.rowcount
    conn.close()
    return jsonify({"message":"Deleted"} if ok else {"error":"Not found"})

@app.route("/students/count")
def count():
    conn = db()
    n = conn.execute("SELECT COUNT(*) c FROM students").fetchone()["c"]
    conn.close()
    return jsonify({"count": n})

@app.route("/students/export")
def export():
    conn = db()
    data = [dict(r) for r in conn.execute("SELECT * FROM students")]
    conn.close()
    j = json.dumps(data, indent=2)
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
<title>Student Control Center</title>
<style>
  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: linear-gradient(135deg, #2b2b4b, #1c1f26);
    color: #fff;
    font-family: 'Segoe UI', sans-serif;
    display: flex;
    flex-direction: column;
    min-height: 100vh;
  }
  header {
    backdrop-filter: blur(8px);
    background: rgba(255,255,255,0.1);
    padding: 1rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
  }
  h1 { font-size: 1.5rem; letter-spacing: 1px; }
  main {
    flex: 1;
    padding: 2rem;
    display: grid;
    grid-template-columns: 300px 1fr;
    gap: 2rem;
  }
  aside {
    backdrop-filter: blur(10px);
    background: rgba(255,255,255,0.07);
    border-radius: 16px;
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  aside input, aside button {
    width: 100%; padding: .7rem; border: none; border-radius: 8px;
  }
  aside input {
    background: rgba(255,255,255,0.15); color: #fff;
  }
  aside button {
    background: #4f9cff; color: white; cursor: pointer; font-weight: bold;
  }
  section {
    backdrop-filter: blur(10px);
    background: rgba(255,255,255,0.07);
    border-radius: 16px;
    padding: 1.5rem;
    overflow-y: auto;
  }
  .student {
    background: rgba(255,255,255,0.05);
    border-radius: 10px;
    padding: 1rem;
    margin-bottom: 1rem;
    transition: transform .2s ease;
  }
  .student:hover { transform: scale(1.02); }
  .actions button {
    margin-right: .5rem; background: none; border: none; color: #4f9cff; cursor: pointer;
  }
  footer {
    text-align: center;
    padding: .8rem;
    background: rgba(255,255,255,0.08);
    font-size: .9rem;
  }
  .count {
    font-weight: bold;
    font-size: 1.1rem;
    color: #82cfff;
  }
  #modal {
    position: fixed; top:0; left:0; right:0; bottom:0;
    display:none; justify-content:center; align-items:center;
    background: rgba(0,0,0,0.6);
  }
  #modalContent {
    background: rgba(255,255,255,0.1);
    backdrop-filter: blur(15px);
    padding: 2rem;
    border-radius: 12px;
    width: 300px;
  }
  #modalContent input {
    width: 100%; margin-bottom: .7rem; padding: .5rem;
    background: rgba(255,255,255,0.15); border:none; border-radius:6px; color:white;
  }
  #modalContent button {
    width: 100%; padding: .7rem; background: #4f9cff; border:none; color:white;
    border-radius:6px; font-weight:bold; cursor:pointer;
  }
</style>
</head>
<body>

<header>
  <h1>🎓 Student Control Center</h1>
  <div class="count">Total: <span id="count">0</span></div>
</header>

<main>
  <aside>
    <h3>Add New</h3>
    <input id="name" placeholder="Full name">
    <input id="grade" type="number" placeholder="Year">
    <input id="section" placeholder="Section">
    <input id="contact" placeholder="Contact">
    <button onclick="add()">Add Student</button>
    <hr style="border-color:rgba(255,255,255,0.1)">
    <input id="search" placeholder="Search..." oninput="search(this.value)">
    <button onclick="exportData()">Export JSON</button>
  </aside>

  <section id="list">
    <p style="opacity:.7">Loading students...</p>
  </section>
</main>

<footer>&copy; 2025 Student System — Glass Edition</footer>

<div id="modal">
  <div id="modalContent">
    <h3>Edit Student</h3>
    <input id="ename">
    <input id="egrade" type="number">
    <input id="esection">
    <input id="econtact">
    <button onclick="saveEdit()">Save Changes</button>
  </div>
</div>

<script>
let editId = null;
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
  if (!data.length) {
    list.innerHTML = "<p style='opacity:.7'>No students found.</p>";
    return;
  }
  list.innerHTML = data.map(s => `
    <div class='student'>
      <div><strong>${s.name}</strong> (${s.grade}-${s.section})</div>
      <div style='font-size:.9rem;opacity:.8'>📞 ${s.contact}</div>
      <div style='font-size:.8rem;opacity:.6'>Registered ${new Date(s.date_registered).toLocaleDateString()}</div>
      <div class='actions'>
        <button onclick='edit(${s.id})'>✏️</button>
        <button onclick='remove(${s.id})'>🗑️</button>
      </div>
    </div>`).join('');
}
async function add() {
  const d = { name:name.value, grade:parseInt(grade.value), section:section.value, contact:contact.value };
  if (!d.name || !d.grade || !d.section || !d.contact) return alert("Fill all fields");
  await fetch('/student', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(d)});
  name.value=grade.value=section.value=contact.value="";
  load();
}
async function remove(id) {
  if (!confirm("Delete this student?")) return;
  await fetch(`/student/${id}`, {method:'DELETE'});
  load();
}
async function edit(id) {
  const res = await fetch(`/student/${id}`);
  const s = await res.json();
  editId = s.id;
  ename.value = s.name; egrade.value = s.grade; esection.value = s.section; econtact.value = s.contact;
  document.getElementById('modal').style.display='flex';
}
async function saveEdit() {
  const d = { name:ename.value, grade:parseInt(egrade.value), section:esection.value, contact:econtact.value };
  await fetch(`/student/${editId}`, {method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify(d)});
  document.getElementById('modal').style.display='none';
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

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
