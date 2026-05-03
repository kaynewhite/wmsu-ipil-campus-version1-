from flask import Blueprint, request, session, redirect, url_for, jsonify
from database import get_db
from helpers import render, sidebar
from auth_utils import login_required, role_required

admin_bp = Blueprint("admin", __name__)

# ─────────────────────────────────────────────
# PAGE ROUTES
# ─────────────────────────────────────────────

@admin_bp.route("/admin")
@admin_bp.route("/admin/")
@login_required
@role_required("admin")
def admin_dashboard():
    db = get_db()
    stats = {
        "users":   db.execute("SELECT COUNT(*) FROM users WHERE role!='admin'").fetchone()[0],
        "teachers": db.execute("SELECT COUNT(*) FROM users WHERE role='teacher'").fetchone()[0],
        "students": db.execute("SELECT COUNT(*) FROM users WHERE role='student'").fetchone()[0],
        "courses":  db.execute("SELECT COUNT(*) FROM courses").fetchone()[0],
        "exams":    db.execute("SELECT COUNT(*) FROM exams").fetchone()[0],
        "results":  db.execute("SELECT COUNT(*) FROM results").fetchone()[0],
    }
    db.close()

    html = sidebar("admin", "dashboard") + f"""
    <div class="topbar">
      <div><div class="page-title">Admin Dashboard</div><div class="page-sub">Welcome back, {session.get('name')}</div></div>
    </div>
    <div class="grid grid-3" style="margin-bottom:24px">
      <div class="stat-card" style="animation-delay:.0s"><div class="stat-icon" style="background:#c0392b"><svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2M9 7a4 4 0 100 8 4 4 0 000-8z"/></svg></div><div><div class="stat-label">Total Users</div><div style="font-size:28px;font-weight:700;margin-top:6px;color:var(--text)">{stats['users']}</div></div></div>
      <div class="stat-card" style="animation-delay:.1s"><div class="stat-icon" style="background:#2980b9"><svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg></div><div><div class="stat-label">Courses</div><div style="font-size:28px;font-weight:700;margin-top:6px;color:var(--text)">{stats['courses']}</div></div></div>
      <div class="stat-card" style="animation-delay:.2s"><div class="stat-icon" style="background:#27ae60"><svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg></div><div><div class="stat-label">Total Exams</div><div style="font-size:28px;font-weight:700;margin-top:6px;color:var(--text)">{stats['exams']}</div></div></div>
      <div class="stat-card" style="animation-delay:.3s"><div class="stat-icon" style="background:#8e44ad"><svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg></div><div><div class="stat-label">Teachers</div><div style="font-size:28px;font-weight:700;margin-top:6px;color:var(--text)">{stats['teachers']}</div></div></div>
      <div class="stat-card" style="animation-delay:.4s"><div class="stat-icon" style="background:#f39c12"><svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197"/></svg></div><div><div class="stat-label">Students</div><div style="font-size:28px;font-weight:700;margin-top:6px;color:var(--text)">{stats['students']}</div></div></div>
      <div class="stat-card" style="animation-delay:.5s"><div class="stat-icon" style="background:#16a085"><svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"/></svg></div><div><div class="stat-label">Submissions</div><div style="font-size:28px;font-weight:700;margin-top:6px;color:var(--text)">{stats['results']}</div></div></div>
    </div>
    <div class="card">
      <div class="card-header"><h3 class="card-title">System Overview</h3></div>
      <div class="grid grid-2" style="gap:20px;margin-top:18px">
        <div style="padding:18px 0">
          <div class="text-muted text-sm">Users</div>
          <div style="font-size:24px;font-weight:700;margin:10px 0 20px">{stats['users']}</div>
          <div class="text-muted text-sm">Teachers</div>
          <div style="font-size:24px;font-weight:700;margin:10px 0 0">{stats['teachers']}</div>
        </div>
        <div style="padding:18px 0">
          <div class="text-muted text-sm">Students</div>
          <div style="font-size:24px;font-weight:700;margin:10px 0 20px">{stats['students']}</div>
          <div class="text-muted text-sm">Active Courses</div>
          <div style="font-size:24px;font-weight:700;margin:10px 0 0">{stats['courses']}</div>
        </div>
      </div>
    </div>
    </main>
    </div>"""
    return render(html, "Admin Dashboard")


@admin_bp.route("/admin/courses")
@login_required
@role_required("admin")
def admin_courses():
    db = get_db()
    courses = db.execute("SELECT * FROM courses ORDER BY id DESC").fetchall()
    db.close()

    rows = "".join(
        f"""<tr><td>{c['id']}</td><td>{c['course_name']}</td>
      <td>
        <button class="btn btn-sm btn-warning" onclick="editCourse({c['id']},'{c['course_name']}')">Edit</button>
        <button class="btn btn-sm btn-danger"  onclick="delCourse({c['id']})">Delete</button>
      </td></tr>"""
        for c in courses
    )

    html = sidebar("admin", "courses") + f"""
    <div class="topbar">
      <div><div class="page-title">Courses</div><div class="page-sub">Manage all courses</div></div>
      <button class="btn btn-primary" onclick="openModal('addCourse')">+ Add Course</button>
    </div>
    <div class="alert-zone"></div>
    <div class="card"><div class="table-wrap">
      <table><thead><tr><th>ID</th><th>Course Name</th><th>Actions</th></tr></thead>
      <tbody>{rows or '<tr><td colspan="3"><div class="empty-state"><div class="empty-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5V5.5a1 1 0 011-1h6a1 1 0 011 1v14a1 1 0 01-1 1H5a1 1 0 01-1-1z"/><path d="M20 19.5V5.5a1 1 0 00-1-1h-6a1 1 0 00-1 1v14a1 1 0 001 1h6a1 1 0 001-1z"/></svg></div><p>No courses yet</p></div></td></tr>'}</tbody></table>
    </div></div>

    <div class="modal-overlay" id="addCourse"><div class="modal">
      <div class="modal-header"><h3 class="modal-title">Add Course</h3><button class="modal-close" onclick="closeModal('addCourse')">×</button></div>
      <div class="form-group"><label class="form-label">Course Name</label><input id="courseName" class="form-input" placeholder="e.g. Mathematics 101"></div>
      <button class="btn btn-primary w-full" onclick="addCourse()">Add Course</button>
    </div></div>

    <div class="modal-overlay" id="editCourse"><div class="modal">
      <div class="modal-header"><h3 class="modal-title">Edit Course</h3><button class="modal-close" onclick="closeModal('editCourse')">×</button></div>
      <input type="hidden" id="editCourseId">
      <div class="form-group"><label class="form-label">Course Name</label><input id="editCourseName" class="form-input"></div>
      <button class="btn btn-primary w-full" onclick="saveCourse()">Save Changes</button>
    </div></div>
    </main></div>
    <script>
    function addCourse(){{
      const name=document.getElementById('courseName').value.trim();
      if(!name)return showAlert('Enter course name.');
      fetch('/api/admin/courses',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{name}})}})
      .then(r=>r.json()).then(d=>{{if(d.success)location.reload();else showAlert(d.error);}});
    }}
    function editCourse(id,name){{document.getElementById('editCourseId').value=id;document.getElementById('editCourseName').value=name;openModal('editCourse');}}
    function saveCourse(){{
      const id=document.getElementById('editCourseId').value;
      const name=document.getElementById('editCourseName').value.trim();
      if(!name)return showAlert('Enter course name.');
      fetch('/api/admin/courses/'+id,{{method:'PUT',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{name}})}})
      .then(r=>r.json()).then(d=>{{if(d.success)location.reload();else showAlert(d.error);}});
    }}
    function delCourse(id){{
      if(!confirm('Delete this course?'))return;
      fetch('/api/admin/courses/'+id,{{method:'DELETE'}}).then(r=>r.json()).then(d=>{{if(d.success)location.reload();else showAlert(d.error);}});
    }}
    </script>"""
    return render(html, "Courses")


@admin_bp.route("/admin/users")
@login_required
@role_required("admin")
def admin_users():
    db = get_db()
    users = db.execute("SELECT * FROM users WHERE role!='admin' ORDER BY id DESC").fetchall()
    db.close()

    rows = "".join(
        f"""<tr>
      <td>{u['id']}</td><td>{u['name']}</td><td>{u['email']}</td>
      <td><span class="badge badge-{'blue' if u['role']=='teacher' else 'green'}">{u['role']}</span></td>
      <td>
        <select onchange="changeRole({u['id']},this.value)" class="form-input form-select" style="padding:4px 8px;font-size:12px;width:auto">
          <option {'selected' if u['role']=='student' else ''} value="student">Student</option>
          <option {'selected' if u['role']=='teacher' else ''} value="teacher">Teacher</option>
        </select>
      </td>
      <td><button class="btn btn-sm btn-danger" onclick="delUser({u['id']})">Delete</button></td>
    </tr>"""
        for u in users
    )

    html = sidebar("admin", "users") + f"""
    <div class="topbar"><div><div class="page-title">Users</div><div class="page-sub">Manage all accounts</div></div></div>
    <div class="alert-zone"></div>
    <div class="card"><div class="table-wrap">
      <table><thead><tr><th>ID</th><th>Name</th><th>Email</th><th>Role</th><th>Change Role</th><th>Actions</th></tr></thead>
      <tbody>{rows or '<tr><td colspan="6"><div class="empty-state"><div class="empty-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 12a4 4 0 100-8 4 4 0 000 8z"/><path d="M6 20c0-3.3 2.7-6 6-6s6 2.7 6 6"/></svg></div><p>No users yet</p></div></td></tr>'}</tbody></table>
    </div></div>
    </main></div>
    <script>
    function changeRole(id,role){{
      fetch('/api/admin/users/'+id+'/role',{{method:'PUT',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{role}})}})
      .then(r=>r.json()).then(d=>{{if(d.success)showAlert('Role updated.','success');else showAlert(d.error);}});
    }}
    function delUser(id){{
      if(!confirm('Delete this user? This cannot be undone.'))return;
      fetch('/api/admin/users/'+id,{{method:'DELETE'}}).then(r=>r.json()).then(d=>{{if(d.success)location.reload();else showAlert(d.error);}});
    }}
    </script>"""
    return render(html, "Users")


# ─────────────────────────────────────────────
# API ROUTES
# ─────────────────────────────────────────────

@admin_bp.route("/api/admin/courses", methods=["POST"])
@login_required
@role_required("admin")
def api_add_course():
    name = (request.json.get("name", "")).strip()
    if not name:
        return jsonify({"error": "Course name required."})
    db = get_db()
    try:
        db.execute("INSERT INTO courses (course_name) VALUES (?)", (name,))
        db.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        db.close()


@admin_bp.route("/api/admin/courses/<int:cid>", methods=["PUT", "DELETE"])
@login_required
@role_required("admin")
def api_course(cid):
    db = get_db()
    try:
        if request.method == "PUT":
            name = (request.json.get("name", "")).strip()
            if not name:
                return jsonify({"error": "Name required."})
            db.execute("UPDATE courses SET course_name=? WHERE id=?", (name, cid))
        else:
            db.execute("DELETE FROM courses WHERE id=?", (cid,))
        db.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        db.close()


@admin_bp.route("/api/admin/users/<int:uid>", methods=["DELETE"])
@login_required
@role_required("admin")
def api_del_user(uid):
    db = get_db()
    try:
        db.execute("DELETE FROM users WHERE id=? AND role!='admin'", (uid,))
        db.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        db.close()


@admin_bp.route("/api/admin/users/<int:uid>/role", methods=["PUT"])
@login_required
@role_required("admin")
def api_user_role(uid):
    role = request.json.get("role", "")
    if role not in ["student", "teacher"]:
        return jsonify({"error": "Invalid role."})
    db = get_db()
    try:
        db.execute("UPDATE users SET role=? WHERE id=? AND role!='admin'", (role, uid))
        db.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        db.close()
