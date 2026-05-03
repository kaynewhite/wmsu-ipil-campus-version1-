import json
from datetime import datetime
from flask import Blueprint, request, session, redirect, url_for, jsonify, make_response

from database import get_db
from helpers import render, sidebar
from auth_utils import login_required, role_required

teacher_bp = Blueprint("teacher", __name__)

# ─────────────────────────────────────────────
#  PAGE ROUTES
# ─────────────────────────────────────────────

@teacher_bp.route("/teacher")
@teacher_bp.route("/teacher/")
@login_required
@role_required("teacher")
def teacher_dashboard():
    db  = get_db()
    tid = session["user_id"]
    stats = {
        "exams":   db.execute("SELECT COUNT(*) FROM exams WHERE teacher_id=?", (tid,)).fetchone()[0],
        "students":db.execute(
            "SELECT COUNT(DISTINCT student_id) FROM results r JOIN exams e ON r.exam_id=e.id WHERE e.teacher_id=?",
            (tid,)).fetchone()[0],
        "results": db.execute(
            "SELECT COUNT(*) FROM results r JOIN exams e ON r.exam_id=e.id WHERE e.teacher_id=?",
            (tid,)).fetchone()[0],
        "essays":  db.execute("""
            SELECT COUNT(*) FROM student_answers sa
            JOIN questions q ON sa.question_id=q.id
            JOIN exams e ON q.exam_id=e.id
            WHERE e.teacher_id=? AND q.type='essay'
              AND sa.answer IS NOT NULL AND sa.answer!=''
              AND NOT EXISTS(SELECT 1 FROM essay_reviews er WHERE er.answer_id=sa.id)""",
            (tid,)).fetchone()[0],
    }
    recent_exams = db.execute("""
        SELECT e.*, c.course_name,
                (SELECT COUNT(*) FROM results r WHERE r.exam_id=e.id) AS submissions
        FROM exams e JOIN courses c ON e.course_id=c.id
        WHERE e.teacher_id=? ORDER BY e.id DESC LIMIT 5""", (tid,)).fetchall()
    db.close()

    exam_rows = "".join(
        f"""<tr><td>{e['title']}</td><td>{e['course_name']}</td><td>{e['timer_minutes']} min</td>
      <td>{e['submissions']}</td>
      <td><a href="/teacher/exams/{e['id']}/results" class="btn btn-sm btn-secondary">View</a></td></tr>"""
        for e in recent_exams
    )

    html = sidebar("teacher", "dashboard") + f"""
    <div class="topbar">
      <div><div class="page-title">Teacher Dashboard</div><div class="page-sub">Welcome, {session.get('name')}</div></div>
      <a href="/teacher/exams/create" class="btn btn-primary">+ Create Exam</a>
    </div>
    <div class="grid grid-4" style="margin-bottom:24px">
      <div class="stat-card"><div class="stat-icon" style="background:#c0392b"><svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2"/></svg></div><div><div class="stat-label">My Exams</div><div class="stat-value">{stats['exams']}</div></div></div>
      <div class="stat-card"><div class="stat-icon" style="background:#2980b9"><svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2M9 7a4 4 0 100 8 4 4 0 000-8z"/></svg></div><div><div class="stat-label">Students Tested</div><div class="stat-value">{stats['students']}</div></div></div>
      <div class="stat-card"><div class="stat-icon" style="background:#27ae60"><svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4"/></svg></div><div><div class="stat-label">Submissions</div><div class="stat-value">{stats['results']}</div></div></div>
      <div class="stat-card"><div class="stat-icon" style="background:#f39c12"><svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5"/></svg></div><div><div class="stat-label">Pending Essays</div><div class="stat-value">{stats['essays']}</div></div></div>
    </div>
    <div class="card">
      <div class="card-header"><h3 class="card-title">Recent Exams</h3><a href="/teacher/exams" class="btn btn-sm btn-secondary">View All</a></div>
      <div class="table-wrap">
        <table><thead><tr><th>Exam Title</th><th>Course</th><th>Duration</th><th>Submissions</th><th>Actions</th></tr></thead>
        <tbody>{exam_rows or '<tr><td colspan="5"><div class="empty-state"><div class="empty-icon">📝</div><p>No exams yet. <a href="/teacher/exams/create" style="color:var(--red)">Create your first exam</a></p></div></td></tr>'}</tbody></table>
      </div>
    </div>
  </main></div>"""
    return render(html, "Teacher Dashboard")

@teacher_bp.route("/teacher/exams")
@login_required
@role_required("teacher")
def teacher_exams():
    db = get_db()
    exams = db.execute("""
        SELECT e.*, c.course_name,
                (SELECT COUNT(*) FROM results r WHERE r.exam_id=e.id) AS submissions,
                (SELECT COUNT(*) FROM questions q WHERE q.exam_id=e.id) AS q_count
        FROM exams e JOIN courses c ON e.course_id=c.id
        WHERE e.teacher_id=? ORDER BY e.id DESC""", (session["user_id"],)).fetchall()
    db.close()

    rows = "".join(
        f"""<tr><td>{e['title']}</td><td>{e['course_name']}</td><td>{e['q_count']} Qs</td>
      <td>{e['timer_minutes']} min</td><td>{e['submissions']}</td>
      <td>
        <a href="/teacher/exams/{e['id']}/edit"    class="btn btn-sm btn-warning">Edit</a>
        <a href="/teacher/exams/{e['id']}/results" class="btn btn-sm btn-secondary">Results</a>
        <button class="btn btn-sm btn-danger" onclick="delExam({e['id']})">Delete</button>
      </td></tr>"""
        for e in exams
    )

    html = sidebar("teacher", "exams") + f"""
    <div class="topbar"><div><div class="page-title">My Exams</div></div><a href="/teacher/exams/create" class="btn btn-primary">+ Create Exam</a></div>
    <div class="alert-zone"></div>
    <div class="card"><div class="table-wrap">
      <table><thead><tr><th>Title</th><th>Course</th><th>Questions</th><th>Duration</th><th>Submissions</th><th>Actions</th></tr></thead>
      <tbody>{rows or '<tr><td colspan="6"><div class="empty-state"><div class="empty-icon">📝</div><p>No exams yet</p></div></td></tr>'}</tbody></table>
    </div></div>
  </main></div>
<script>
function delExam(id){{
  if(!confirm('Delete this exam and all its data?'))return;
  fetch('/api/teacher/exams/'+id,{{method:'DELETE'}}).then(r=>r.json()).then(d=>{{if(d.success)location.reload();else showAlert(d.error);}});
}}
</script>"""
    return render(html, "My Exams")

@teacher_bp.route("/teacher/exams/create")
@teacher_bp.route("/teacher/exams/<int:eid>/edit")
@login_required
@role_required("teacher")
def teacher_exam_editor(eid=None):
    db = get_db()
    courses = db.execute("SELECT * FROM courses ORDER BY course_name").fetchall()
    
    exam_data = None
    questions_json = "[]"
    
    if eid:
        exam_data = db.execute("SELECT * FROM exams WHERE id=? AND teacher_id=?", (eid, session["user_id"])).fetchone()
        if not exam_data:
            db.close()
            return "Exam not found or access denied", 404
        
        qs = db.execute("SELECT * FROM questions WHERE exam_id=?", (eid,)).fetchall()
        qs_list = []
        for q in qs:
            qs_list.append({
                "type": q["type"],
                "text": q["question_text"],
                "choices": json.loads(q["choices"]) if q["choices"] else ["","","",""],
                "correct": q["correct_answer"],
                "points": q["points"]
            })
        questions_json = json.dumps(qs_list)
    
    db.close()
    course_opts = "".join(f'<option value="{c["id"]}" {"selected" if exam_data and exam_data["course_id"]==c["id"] else ""}>{c["course_name"]}</option>' for c in courses)

    html = sidebar("teacher", "exams") + f"""
    <div class="topbar"><div><div class="page-title">{'Edit' if eid else 'Create'} Exam</div><div class="page-sub">Manage your exam settings and questions</div></div></div>
    <div class="alert-zone"></div>
    <div class="grid grid-2" style="align-items:start">
      <div class="card">
        <h3 class="card-title" style="margin-bottom:20px">Exam Settings</h3>
        <div class="form-group"><label class="form-label">Exam Title</label><input id="examTitle" class="form-input" value="{exam_data['title'] if exam_data else ''}" placeholder="e.g. Midterm Examination"></div>
        <div class="form-group"><label class="form-label">Course</label><select id="examCourse" class="form-input form-select">{course_opts}</select></div>
        <div class="form-group"><label class="form-label">Time Limit (minutes)</label><input id="examTimer" type="number" class="form-input" value="{exam_data['timer_minutes'] if exam_data else '60'}" min="5"></div>
        <div class="form-group"><label class="form-label">Passing Score (%)</label><input id="examPass" type="number" class="form-input" value="{exam_data['passing_score'] if exam_data else '60'}" min="0" max="100"></div>
      </div>
      <div class="card">
        <div class="flex justify-between items-center mb-16">
          <h3 class="card-title">Questions</h3>
          <button class="btn btn-primary btn-sm" onclick="addQuestion()">+ Add Question</button>
        </div>
        <div id="questions-list"></div>
        <div class="text-center text-muted text-sm" id="no-q-msg">No questions added yet.</div>
      </div>
    </div>
    <div style="margin-top:20px;text-align:right">
      <button class="btn btn-primary" onclick="saveExam()">{ 'Update Exam' if eid else 'Save Exam' }</button>
    </div>
  </main></div>
<script>
let questions = {questions_json};
let currentExamId = {eid if eid else 'null'};

function addQuestion(){{
  questions.push({{type:'mcq',text:'',choices:['','','',''],correct:'A',points:1}});
  renderQuestions();
}}
function removeQ(i){{questions.splice(i,1);renderQuestions();}}
function renderQuestions(){{
  const list=document.getElementById('questions-list');
  const noMsg=document.getElementById('no-q-msg');
  noMsg.style.display=questions.length?'none':'block';
  list.innerHTML=questions.map((q,i)=>{{
    let choicesHtml='';
    if(q.type==='mcq'){{
      const letters='ABCDEFGH';
      choicesHtml=`<div style="margin-top:12px">
        <label class="form-label">Choices</label>
        ${{[0,1,2,3].map(ci=>`<div style="display:flex;gap:8px;margin-bottom:6px">
          <span style="width:24px;padding-top:10px;font-weight:700;color:var(--red)">${{letters[ci]}}</span>
          <input class="form-input flex-1" placeholder="Choice ${{letters[ci]}}" value="${{q.choices[ci]||''}}" onchange="questions[${{i}}].choices[${{ci}}]=this.value">
        </div>`).join('')}}
        <div class="form-group"><label class="form-label">Correct Answer</label>
        <select class="form-input form-select" onchange="questions[${{i}}].correct=this.value">
          ${{['A','B','C','D'].map(l=>`<option ${{q.correct===l?'selected':''}} value="${{l}}">${{l}}</option>`).join('')}}
        </select></div>
      </div>`;
    }}else if(q.type==='tf'){{
      choicesHtml=`<div class="form-group mt-8"><label class="form-label">Correct Answer</label>
        <select class="form-input form-select" onchange="questions[${{i}}].correct=this.value">
          <option ${{q.correct==='True'?'selected':''}} value="True">True</option>
          <option ${{q.correct==='False'?'selected':''}} value="False">False</option>
        </select></div>`;
    }}else if(q.type==='identification'){{
      choicesHtml=`<div class="form-group mt-8"><label class="form-label">Correct Answer</label>
        <input class="form-input" placeholder="Expected answer" value="${{q.correct||''}}" onchange="questions[${{i}}].correct=this.value"></div>`;
    }}
    return `<div class="question-card" style="margin-bottom:12px; border: 1px solid #eee; padding: 15px; border-radius: 8px;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
        <span style="font-weight:700;font-size:13px;color:var(--red)">Q${{i+1}}</span>
        <button class="btn btn-sm btn-danger" onclick="removeQ(${{i}})">Remove</button>
      </div>
      <div class="form-group"><label class="form-label">Question Type</label>
        <select class="form-input form-select" onchange="questions[${{i}}].type=this.value;renderQuestions()">
          <option ${{q.type==='mcq'?'selected':''}} value="mcq">Multiple Choice</option>
          <option ${{q.type==='tf'?'selected':''}} value="tf">True / False</option>
          <option ${{q.type==='essay'?'selected':''}} value="essay">Essay</option>
          <option ${{q.type==='identification'?'selected':''}} value="identification">Identification</option>
        </select>
      </div>
      <div class="form-group"><label class="form-label">Question</label>
        <textarea class="form-input" rows="2" onchange="questions[${{i}}].text=this.value">${{q.text}}</textarea>
      </div>
      <div class="form-group"><label class="form-label">Points</label>
        <input type="number" class="form-input" value="${{q.points}}" min="0.5" step="0.5" onchange="questions[${{i}}].points=parseFloat(this.value)" style="max-width:100px">
      </div>
      ${{choicesHtml}}
    </div>`;
  }}).join('');
}}
function saveExam() {{
  const title=document.getElementById('examTitle').value.trim();
  const course_id=document.getElementById('examCourse').value;
  const timer=parseInt(document.getElementById('examTimer').value);
  const passing=parseFloat(document.getElementById('examPass').value);
  
  if(!title) return showAlert('Enter exam title.');
  if(!questions.length) return showAlert('Add at least one question.');
  
  fetch('/api/teacher/exams', {{
    method:'POST',
    headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify({{
      exam_id: currentExamId,
      title, course_id, timer_minutes:timer, passing_score:passing, questions
    }})
  }})
  .then(r=>r.json()).then(d=>{{
    if(d.success){{
      showAlert('Exam saved!','success');
      setTimeout(()=>location.href='/teacher/exams',1500);
    }} else showAlert(d.error);
  }});
}}
renderQuestions();
</script>"""
    return render(html, "Exam Editor")

@teacher_bp.route("/teacher/exams/<int:eid>/results")
@login_required
@role_required("teacher")
def teacher_exam_results(eid):
    db = get_db()
    exam = db.execute(
        "SELECT e.*, c.course_name FROM exams e JOIN courses c ON e.course_id=c.id WHERE e.id=? AND e.teacher_id=?",
        (eid, session["user_id"]),
    ).fetchone()
    if not exam:
        db.close()
        return "Exam not found", 404

    results = db.execute(
        "SELECT r.*, u.name, u.email FROM results r JOIN users u ON r.student_id=u.id WHERE r.exam_id=? ORDER BY r.percentage DESC",
        (eid,),
    ).fetchall()
    db.close()

    rows = "".join(
        f"""<tr><td>{r['name']}</td><td>{r['email']}</td>
      <td>{r['score']:.1f}</td><td>{r['percentage']:.1f}%</td>
      <td><span class="badge badge-{'green' if r['percentage']>=exam['passing_score'] else 'red'}">
        {'Pass' if r['percentage']>=exam['passing_score'] else 'Fail'}</span></td>
      <td>{r['submitted_at'][:16]}</td></tr>"""
        for r in results
    )

    html = sidebar("teacher", "exams") + f"""
    <div class="topbar">
      <div><div class="page-title">{exam['title']}</div>
        <div class="page-sub">{exam['course_name']} · {exam['timer_minutes']} min · Passing: {exam['passing_score']}%</div></div>
      <div style="display:flex;gap:10px">
        <button class="btn btn-secondary" onclick="exportPDF()">Export PDF</button>
        <button class="btn btn-success"    onclick="exportExcel()">Export Excel</button>
      </div>
    </div>
    <div class="card"><div class="table-wrap">
      <table><thead><tr><th>Student</th><th>Email</th><th>Score</th><th>Percentage</th><th>Status</th><th>Submitted</th></tr></thead>
      <tbody>{rows or '<tr><td colspan="6"><div class="empty-state"><div class="empty-icon">📊</div><p>No submissions yet</p></div></td></tr>'}</tbody></table>
    </div></div>
  </main></div>
<script>
function exportPDF()  {{ window.open('/api/teacher/exams/{eid}/export/pdf','_blank'); }}
function exportExcel(){{ window.open('/api/teacher/exams/{eid}/export/excel','_blank'); }}
</script>"""
    return render(html, "Exam Results")

@teacher_bp.route("/teacher/essays")
@login_required
@role_required("teacher")
def teacher_essays():
    db = get_db()
    essays = db.execute("""
        SELECT sa.id AS answer_id, sa.answer, u.name AS student_name,
                q.question_text, q.points AS max_points, e.title AS exam_title,
                er.points_given, er.feedback
        FROM student_answers sa
        JOIN questions q ON sa.question_id=q.id
        JOIN exams e ON q.exam_id=e.id
        JOIN users u ON sa.student_id=u.id
        LEFT JOIN essay_reviews er ON er.answer_id=sa.id
        WHERE e.teacher_id=? AND q.type='essay'
        ORDER BY sa.id DESC""", (session["user_id"],)).fetchall()
    db.close()

    cards = "".join(
        f"""<div class="card" style="margin-bottom:16px">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px">
        <div><div class="font-bold">{e['student_name']}</div><div class="text-sm text-muted">{e['exam_title']}</div></div>
        <span class="badge {'badge-green' if e['points_given'] is not None else 'badge-orange'}">
          {'Reviewed' if e['points_given'] is not None else 'Pending'}</span>
      </div>
      <p class="text-sm font-bold" style="margin-bottom:6px">Q: {e['question_text']}</p>
      <p class="text-sm text-muted" style="margin-bottom:12px;white-space:pre-wrap">{e['answer'] or '(No answer)'}</p>
      <div style="display:flex;gap:12px;align-items:center">
        <input type="number" id="pts_{e['answer_id']}" class="form-input" placeholder="Points" value="{e['points_given'] or ''}" max="{e['max_points']}" style="max-width:100px">
        <input type="text"   id="fb_{e['answer_id']}"  class="form-input flex-1" placeholder="Feedback (optional)" value="{e['feedback'] or ''}">
        <button class="btn btn-primary btn-sm" onclick="saveReview({e['answer_id']})">Save</button>
      </div>
      <p class="text-sm text-muted mt-8">Max points: {e['max_points']}</p>
    </div>"""
        for e in essays
    )

    html = sidebar("teacher", "essays") + f"""
    <div class="topbar"><div><div class="page-title">Essay Reviews</div><div class="page-sub">Review and grade student essay answers</div></div></div>
    <div class="alert-zone"></div>
    {cards or '<div class="empty-state"><div class="empty-icon">✏️</div><p>No essay answers to review</p></div>'}
  </main></div>
<script>
function saveReview(id){{
  const pts=parseFloat(document.getElementById('pts_'+id).value);
  const fb=document.getElementById('fb_'+id).value;
  if(isNaN(pts))return showAlert('Enter valid points.');
  fetch('/api/teacher/essays/'+id,{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{points:pts,feedback:fb}})}})
  .then(r=>r.json()).then(d=>{{if(d.success)showAlert('Review saved!','success');else showAlert(d.error);}});
}}
</script>"""
    return render(html, "Essays")

# FIX PARA SA SCREENSHOT: teacher/results
@teacher_bp.route("/teacher/results")
@login_required
@role_required("teacher")
def teacher_results():
    db    = get_db()
    exams = db.execute(
        "SELECT e.*, c.course_name FROM exams e JOIN courses c ON e.course_id=c.id WHERE e.teacher_id=? ORDER BY e.id DESC",
        (session["user_id"],),
    ).fetchall()
    db.close()

    links = "".join(
        f'<a href="/teacher/exams/{e["id"]}/results" class="btn btn-secondary" style="margin-bottom:8px; display:inline-block; width:100%; text-align:left; padding: 15px">'
        f'<strong>{e["title"]}</strong> <br><small>{e["course_name"]}</small></a><br>'
        for e in exams
    )

    html = sidebar("teacher", "results") + f"""
    <div class="topbar"><div><div class="page-title">Overall Results</div><div class="page-sub">Select an exam to view detailed scores</div></div></div>
    <div class="card">
      <h3 class="card-title" style="margin-bottom:20px">My Exams</h3>
      {links or '<div class="empty-state"><div class="empty-icon">📊</div><p>No exams created yet</p></div>'}
    </div>
  </main></div>"""
    return render(html, "Results")

# ─────────────────────────────────────────────
#  API ROUTES
# ─────────────────────────────────────────────

@teacher_bp.route("/api/teacher/exams", methods=["POST"])
@login_required
@role_required("teacher")
def api_save_exam():
    data      = request.json
    eid       = data.get("exam_id")
    title     = (data.get("title", "")).strip()
    course_id = data.get("course_id")
    timer     = data.get("timer_minutes", 60)
    passing   = data.get("passing_score", 60)
    questions = data.get("questions", [])

    if not title: return jsonify({"error": "Title required."})
    if not questions: return jsonify({"error": "At least one question required."})

    db = get_db()
    try:
        if eid:
            db.execute("UPDATE exams SET course_id=?, title=?, timer_minutes=?, passing_score=? WHERE id=? AND teacher_id=?",
                (course_id, title, timer, passing, eid, session["user_id"]))
            db.execute("DELETE FROM questions WHERE exam_id=?", (eid,))
        else:
            cur = db.execute("INSERT INTO exams (course_id, teacher_id, title, timer_minutes, passing_score) VALUES (?,?,?,?,?)",
                (course_id, session["user_id"], title, timer, passing))
            eid = cur.lastrowid

        for q in questions:
            choices_json = json.dumps(q.get("choices", [])) if q.get("type") == "mcq" else None
            db.execute("INSERT INTO questions (exam_id, question_text, type, choices, correct_answer, points) VALUES (?,?,?,?,?,?)",
                (eid, q["text"], q["type"], choices_json, q.get("correct", ""), q.get("points", 1)))
        db.commit()
        return jsonify({"success": True, "exam_id": eid})
    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        db.close()

@teacher_bp.route("/api/teacher/exams/<int:eid>", methods=["DELETE"])
@login_required
@role_required("teacher")
def api_del_exam(eid):
    db = get_db()
    try:
        exam = db.execute("SELECT id FROM exams WHERE id=? AND teacher_id=?", (eid, session["user_id"])).fetchone()
        if not exam: return jsonify({"error": "Exam not found."})
        db.execute("DELETE FROM student_answers WHERE exam_id=?", (eid,))
        db.execute("DELETE FROM results WHERE exam_id=?", (eid,))
        db.execute("DELETE FROM questions WHERE exam_id=?", (eid,))
        db.execute("DELETE FROM exams WHERE id=?", (eid,))
        db.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        db.close()

@teacher_bp.route("/api/teacher/essays/<int:aid>", methods=["POST"])
@login_required
@role_required("teacher")
def api_review_essay(aid):
    data     = request.json
    points   = data.get("points", 0)
    feedback = data.get("feedback", "")
    db = get_db()
    try:
        existing = db.execute("SELECT id FROM essay_reviews WHERE answer_id=?", (aid,)).fetchone()
        if existing:
            db.execute("UPDATE essay_reviews SET points_given=?, feedback=?, teacher_id=?, reviewed_at=CURRENT_TIMESTAMP WHERE answer_id=?",
                (points, feedback, session["user_id"], aid))
        else:
            db.execute("INSERT INTO essay_reviews (answer_id, teacher_id, points_given, feedback) VALUES (?,?,?,?)",
                (aid, session["user_id"], points, feedback))
        db.execute("UPDATE student_answers SET is_correct=? WHERE id=?", (1 if points > 0 else 0, aid))
        db.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        db.close()

@teacher_bp.route("/api/teacher/exams/<int:eid>/export/pdf")
@login_required
@role_required("teacher")
def export_pdf(eid):
    db = get_db()
    exam = db.execute("SELECT e.*, c.course_name FROM exams e JOIN courses c ON e.course_id=c.id WHERE e.id=? AND e.teacher_id=?", (eid, session["user_id"])).fetchone()
    if not exam:
        db.close()
        return "Not found", 404
    results = db.execute("SELECT r.*, u.name, u.email FROM results r JOIN users u ON r.student_id=u.id WHERE r.exam_id=? ORDER BY r.percentage DESC", (eid,)).fetchall()
    db.close()
    rows = "".join(f"<tr><td>{r['name']}</td><td>{r['email']}</td><td>{r['score']:.1f}</td><td>{r['percentage']:.1f}%</td><td>{'Pass' if r['percentage']>=exam['passing_score'] else 'Fail'}</td></tr>" for r in results)
    html = f"<html><body><h1>{exam['title']}</h1><table>{rows}</table></body></html>"
    resp = make_response(html)
    resp.headers["Content-Type"] = "text/html"
    resp.headers["Content-Disposition"] = f'attachment; filename="results_{eid}.html"'
    return resp

@teacher_bp.route("/api/teacher/exams/<int:eid>/export/excel")
@login_required
@role_required("teacher")
def export_excel(eid):
    db = get_db()
    exam = db.execute("SELECT * FROM exams WHERE id=? AND teacher_id=?", (eid, session["user_id"])).fetchone()
    results = db.execute("SELECT r.*, u.name, u.email FROM results r JOIN users u ON r.student_id=u.id WHERE r.exam_id=? ORDER BY r.percentage DESC", (eid,)).fetchall()
    db.close()
    lines = ["Name,Email,Score,Percentage,Status,Submitted"]
    for r in results:
        status = "Pass" if r["percentage"] >= exam["passing_score"] else "Fail"
        lines.append(f'"{r["name"]}","{r["email"]}",{r["score"]:.1f},{r["percentage"]:.1f},{status},{r["submitted_at"][:16]}')
    resp = make_response("\n".join(lines))
    resp.headers["Content-Type"] = "text/csv"
    resp.headers["Content-Disposition"] = f'attachment; filename="results_{eid}.csv"'

import json
from datetime import datetime
from flask import Blueprint, request, session, redirect, url_for, jsonify, make_response

from database import get_db
from helpers import render, sidebar
from auth_utils import login_required, role_required

teacher_bp = Blueprint("teacher", __name__)

# ─────────────────────────────────────────────
#  PAGE ROUTES
# ─────────────────────────────────────────────

@teacher_bp.route("/teacher")
@teacher_bp.route("/teacher/")
@login_required
@role_required("teacher")
def teacher_dashboard():
    db  = get_db()
    tid = session["user_id"]
    stats = {
        "exams":   db.execute("SELECT COUNT(*) FROM exams WHERE teacher_id=?", (tid,)).fetchone()[0],
        "students":db.execute(
            "SELECT COUNT(DISTINCT student_id) FROM results r JOIN exams e ON r.exam_id=e.id WHERE e.teacher_id=?",
            (tid,)).fetchone()[0],
        "results": db.execute(
            "SELECT COUNT(*) FROM results r JOIN exams e ON r.exam_id=e.id WHERE e.teacher_id=?",
            (tid,)).fetchone()[0],
        "essays":  db.execute("""
            SELECT COUNT(*) FROM student_answers sa
            JOIN questions q ON sa.question_id=q.id
            JOIN exams e ON q.exam_id=e.id
            WHERE e.teacher_id=? AND q.type='essay'
              AND sa.answer IS NOT NULL AND sa.answer!=''
              AND NOT EXISTS(SELECT 1 FROM essay_reviews er WHERE er.answer_id=sa.id)""",
            (tid,)).fetchone()[0],
    }
    recent_exams = db.execute("""
        SELECT e.*, c.course_name,
                (SELECT COUNT(*) FROM results r WHERE r.exam_id=e.id) AS submissions
        FROM exams e JOIN courses c ON e.course_id=c.id
        WHERE e.teacher_id=? ORDER BY e.id DESC LIMIT 5""", (tid,)).fetchall()
    db.close()

    exam_rows = "".join(
        f"""<tr><td>{e['title']}</td><td>{e['course_name']}</td><td>{e['timer_minutes']} min</td>
      <td>{e['submissions']}</td>
      <td><a href="/teacher/exams/{e['id']}/results" class="btn btn-sm btn-secondary">View</a></td></tr>"""
        for e in recent_exams
    )

    html = sidebar("teacher", "dashboard") + f"""
    <div class="topbar">
      <div><div class="page-title">Teacher Dashboard</div><div class="page-sub">Welcome, {session.get('name')}</div></div>
      <a href="/teacher/exams/create" class="btn btn-primary">+ Create Exam</a>
    </div>
    <div class="grid grid-4" style="margin-bottom:24px">
      <div class="stat-card"><div class="stat-icon" style="background:#c0392b"><svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2"/></svg></div><div><div class="stat-label">My Exams</div><div class="stat-value">{stats['exams']}</div></div></div>
      <div class="stat-card"><div class="stat-icon" style="background:#2980b9"><svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2M9 7a4 4 0 100 8 4 4 0 000-8z"/></svg></div><div><div class="stat-label">Students Tested</div><div class="stat-value">{stats['students']}</div></div></div>
      <div class="stat-card"><div class="stat-icon" style="background:#27ae60"><svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4"/></svg></div><div><div class="stat-label">Submissions</div><div class="stat-value">{stats['results']}</div></div></div>
      <div class="stat-card"><div class="stat-icon" style="background:#f39c12"><svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5"/></svg></div><div><div class="stat-label">Pending Essays</div><div class="stat-value">{stats['essays']}</div></div></div>
    </div>
    <div class="card">
      <div class="card-header"><h3 class="card-title">Recent Exams</h3><a href="/teacher/exams" class="btn btn-sm btn-secondary">View All</a></div>
      <div class="table-wrap">
        <table><thead><tr><th>Exam Title</th><th>Course</th><th>Duration</th><th>Submissions</th><th>Actions</th></tr></thead>
        <tbody>{exam_rows or '<tr><td colspan="5"><div class="empty-state"><div class="empty-icon">📝</div><p>No exams yet. <a href="/teacher/exams/create" style="color:var(--red)">Create your first exam</a></p></div></td></tr>'}</tbody></table>
      </div>
    </div>
  </main></div>"""
    return render(html, "Teacher Dashboard")

@teacher_bp.route("/teacher/exams")
@login_required
@role_required("teacher")
def teacher_exams():
    db = get_db()
    exams = db.execute("""
        SELECT e.*, c.course_name,
                (SELECT COUNT(*) FROM results r WHERE r.exam_id=e.id) AS submissions,
                (SELECT COUNT(*) FROM questions q WHERE q.exam_id=e.id) AS q_count
        FROM exams e JOIN courses c ON e.course_id=c.id
        WHERE e.teacher_id=? ORDER BY e.id DESC""", (session["user_id"],)).fetchall()
    db.close()

    rows = "".join(
        f"""<tr><td>{e['title']}</td><td>{e['course_name']}</td><td>{e['q_count']} Qs</td>
      <td>{e['timer_minutes']} min</td><td>{e['submissions']}</td>
      <td>
        <a href="/teacher/exams/{e['id']}/edit"    class="btn btn-sm btn-warning">Edit</a>
        <a href="/teacher/exams/{e['id']}/results" class="btn btn-sm btn-secondary">Results</a>
        <button class="btn btn-sm btn-danger" onclick="delExam({e['id']})">Delete</button>
      </td></tr>"""
        for e in exams
    )

    html = sidebar("teacher", "exams") + f"""
    <div class="topbar"><div><div class="page-title">My Exams</div></div><a href="/teacher/exams/create" class="btn btn-primary">+ Create Exam</a></div>
    <div class="alert-zone"></div>
    <div class="card"><div class="table-wrap">
      <table><thead><tr><th>Title</th><th>Course</th><th>Questions</th><th>Duration</th><th>Submissions</th><th>Actions</th></tr></thead>
      <tbody>{rows or '<tr><td colspan="6"><div class="empty-state"><div class="empty-icon">📝</div><p>No exams yet</p></div></td></tr>'}</tbody></table>
    </div></div>
  </main></div>
<script>
function delExam(id){{
  if(!confirm('Delete this exam and all its data?'))return;
  fetch('/api/teacher/exams/'+id,{{method:'DELETE'}}).then(r=>r.json()).then(d=>{{if(d.success)location.reload();else showAlert(d.error);}});
}}
</script>"""
    return render(html, "My Exams")

@teacher_bp.route("/teacher/exams/create")
@teacher_bp.route("/teacher/exams/<int:eid>/edit")
@login_required
@role_required("teacher")
def teacher_exam_editor(eid=None):
    db = get_db()
    courses = db.execute("SELECT * FROM courses ORDER BY course_name").fetchall()
    
    exam_data = None
    questions_json = "[]"
    
    if eid:
        exam_data = db.execute("SELECT * FROM exams WHERE id=? AND teacher_id=?", (eid, session["user_id"])).fetchone()
        if not exam_data:
            db.close()
            return "Exam not found or access denied", 404
        
        qs = db.execute("SELECT * FROM questions WHERE exam_id=?", (eid,)).fetchall()
        qs_list = []
        for q in qs:
            qs_list.append({
                "type": q["type"],
                "text": q["question_text"],
                "choices": json.loads(q["choices"]) if q["choices"] else ["","","",""],
                "correct": q["correct_answer"],
                "points": q["points"]
            })
        questions_json = json.dumps(qs_list)
    
    db.close()
    course_opts = "".join(f'<option value="{c["id"]}" {"selected" if exam_data and exam_data["course_id"]==c["id"] else ""}>{c["course_name"]}</option>' for c in courses)

    html = sidebar("teacher", "exams") + f"""
    <div class="topbar"><div><div class="page-title">{'Edit' if eid else 'Create'} Exam</div><div class="page-sub">Manage your exam settings and questions</div></div></div>
    <div class="alert-zone"></div>
    <div class="grid grid-2" style="align-items:start">
      <div class="card">
        <h3 class="card-title" style="margin-bottom:20px">Exam Settings</h3>
        <div class="form-group"><label class="form-label">Exam Title</label><input id="examTitle" class="form-input" value="{exam_data['title'] if exam_data else ''}" placeholder="e.g. Midterm Examination"></div>
        <div class="form-group"><label class="form-label">Course</label><select id="examCourse" class="form-input form-select">{course_opts}</select></div>
        <div class="form-group"><label class="form-label">Time Limit (minutes)</label><input id="examTimer" type="number" class="form-input" value="{exam_data['timer_minutes'] if exam_data else '60'}" min="5"></div>
        <div class="form-group"><label class="form-label">Passing Score (%)</label><input id="examPass" type="number" class="form-input" value="{exam_data['passing_score'] if exam_data else '60'}" min="0" max="100"></div>
      </div>
      <div class="card">
        <div class="flex justify-between items-center mb-16">
          <h3 class="card-title">Questions</h3>
          <button class="btn btn-primary btn-sm" onclick="addQuestion()">+ Add Question</button>
        </div>
        <div id="questions-list"></div>
        <div class="text-center text-muted text-sm" id="no-q-msg">No questions added yet.</div>
      </div>
    </div>
    <div style="margin-top:20px;text-align:right">
      <button class="btn btn-primary" onclick="saveExam()">{ 'Update Exam' if eid else 'Save Exam' }</button>
    </div>
  </main></div>
<script>
let questions = {questions_json};
let currentExamId = {eid if eid else 'null'};

function addQuestion(){{
  questions.push({{type:'mcq',text:'',choices:['','','',''],correct:'A',points:1}});
  renderQuestions();
}}
function removeQ(i){{questions.splice(i,1);renderQuestions();}}
function renderQuestions(){{
  const list=document.getElementById('questions-list');
  const noMsg=document.getElementById('no-q-msg');
  noMsg.style.display=questions.length?'none':'block';
  list.innerHTML=questions.map((q,i)=>{{
    let choicesHtml='';
    if(q.type==='mcq'){{
      const letters='ABCDEFGH';
      choicesHtml=`<div style="margin-top:12px">
        <label class="form-label">Choices</label>
        ${{[0,1,2,3].map(ci=>`<div style="display:flex;gap:8px;margin-bottom:6px">
          <span style="width:24px;padding-top:10px;font-weight:700;color:var(--red)">${{letters[ci]}}</span>
          <input class="form-input flex-1" placeholder="Choice ${{letters[ci]}}" value="${{q.choices[ci]||''}}" onchange="questions[${{i}}].choices[${{ci}}]=this.value">
        </div>`).join('')}}
        <div class="form-group"><label class="form-label">Correct Answer</label>
        <select class="form-input form-select" onchange="questions[${{i}}].correct=this.value">
          ${{['A','B','C','D'].map(l=>`<option ${{q.correct===l?'selected':''}} value="${{l}}">${{l}}</option>`).join('')}}
        </select></div>
      </div>`;
    }}else if(q.type==='tf'){{
      choicesHtml=`<div class="form-group mt-8"><label class="form-label">Correct Answer</label>
        <select class="form-input form-select" onchange="questions[${{i}}].correct=this.value">
          <option ${{q.correct==='True'?'selected':''}} value="True">True</option>
          <option ${{q.correct==='False'?'selected':''}} value="False">False</option>
        </select></div>`;
    }}else if(q.type==='identification'){{
      choicesHtml=`<div class="form-group mt-8"><label class="form-label">Correct Answer</label>
        <input class="form-input" placeholder="Expected answer" value="${{q.correct||''}}" onchange="questions[${{i}}].correct=this.value"></div>`;
    }}
    return `<div class="question-card" style="margin-bottom:12px; border: 1px solid #eee; padding: 15px; border-radius: 8px;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
        <span style="font-weight:700;font-size:13px;color:var(--red)">Q${{i+1}}</span>
        <button class="btn btn-sm btn-danger" onclick="removeQ(${{i}})">Remove</button>
      </div>
      <div class="form-group"><label class="form-label">Question Type</label>
        <select class="form-input form-select" onchange="questions[${{i}}].type=this.value;renderQuestions()">
          <option ${{q.type==='mcq'?'selected':''}} value="mcq">Multiple Choice</option>
          <option ${{q.type==='tf'?'selected':''}} value="tf">True / False</option>
          <option ${{q.type==='essay'?'selected':''}} value="essay">Essay</option>
          <option ${{q.type==='identification'?'selected':''}} value="identification">Identification</option>
        </select>
      </div>
      <div class="form-group"><label class="form-label">Question</label>
        <textarea class="form-input" rows="2" onchange="questions[${{i}}].text=this.value">${{q.text}}</textarea>
      </div>
      <div class="form-group"><label class="form-label">Points</label>
        <input type="number" class="form-input" value="${{q.points}}" min="0.5" step="0.5" onchange="questions[${{i}}].points=parseFloat(this.value)" style="max-width:100px">
      </div>
      ${{choicesHtml}}
    </div>`;
  }}).join('');
}}
function saveExam() {{
  const title=document.getElementById('examTitle').value.trim();
  const course_id=document.getElementById('examCourse').value;
  const timer=parseInt(document.getElementById('examTimer').value);
  const passing=parseFloat(document.getElementById('examPass').value);
  
  if(!title) return showAlert('Enter exam title.');
  if(!questions.length) return showAlert('Add at least one question.');
  
  fetch('/api/teacher/exams', {{
    method:'POST',
    headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify({{
      exam_id: currentExamId,
      title, course_id, timer_minutes:timer, passing_score:passing, questions
    }})
  }})
  .then(r=>r.json()).then(d=>{{
    if(d.success){{
      showAlert('Exam saved!','success');
      setTimeout(()=>location.href='/teacher/exams',1500);
    }} else showAlert(d.error);
  }});
}}
renderQuestions();
</script>"""
    return render(html, "Exam Editor")

@teacher_bp.route("/teacher/exams/<int:eid>/results")
@login_required
@role_required("teacher")
def teacher_exam_results(eid):
    db = get_db()
    exam = db.execute(
        "SELECT e.*, c.course_name FROM exams e JOIN courses c ON e.course_id=c.id WHERE e.id=? AND e.teacher_id=?",
        (eid, session["user_id"]),
    ).fetchone()
    if not exam:
        db.close()
        return "Exam not found", 404

    results = db.execute(
        "SELECT r.*, u.name, u.email FROM results r JOIN users u ON r.student_id=u.id WHERE r.exam_id=? ORDER BY r.percentage DESC",
        (eid,),
    ).fetchall()
    db.close()

    rows = "".join(
        f"""<tr><td>{r['name']}</td><td>{r['email']}</td>
      <td>{r['score']:.1f}</td><td>{r['percentage']:.1f}%</td>
      <td><span class="badge badge-{'green' if r['percentage']>=exam['passing_score'] else 'red'}">
        {'Pass' if r['percentage']>=exam['passing_score'] else 'Fail'}</span></td>
      <td>{r['submitted_at'][:16]}</td></tr>"""
        for r in results
    )

    html = sidebar("teacher", "exams") + f"""
    <div class="topbar">
      <div><div class="page-title">{exam['title']}</div>
        <div class="page-sub">{exam['course_name']} · {exam['timer_minutes']} min · Passing: {exam['passing_score']}%</div></div>
      <div style="display:flex;gap:10px">
        <button class="btn btn-secondary" onclick="exportPDF()">Export PDF</button>
        <button class="btn btn-success"    onclick="exportExcel()">Export Excel</button>
      </div>
    </div>
    <div class="card"><div class="table-wrap">
      <table><thead><tr><th>Student</th><th>Email</th><th>Score</th><th>Percentage</th><th>Status</th><th>Submitted</th></tr></thead>
      <tbody>{rows or '<tr><td colspan="6"><div class="empty-state"><div class="empty-icon">📊</div><p>No submissions yet</p></div></td></tr>'}</tbody></table>
    </div></div>
  </main></div>
<script>
function exportPDF()  {{ window.open('/api/teacher/exams/{eid}/export/pdf','_blank'); }}
function exportExcel(){{ window.open('/api/teacher/exams/{eid}/export/excel','_blank'); }}
</script>"""
    return render(html, "Exam Results")

@teacher_bp.route("/teacher/essays")
@login_required
@role_required("teacher")
def teacher_essays():
    db = get_db()
    essays = db.execute("""
        SELECT sa.id AS answer_id, sa.answer, u.name AS student_name,
                q.question_text, q.points AS max_points, e.title AS exam_title,
                er.points_given, er.feedback
        FROM student_answers sa
        JOIN questions q ON sa.question_id=q.id
        JOIN exams e ON q.exam_id=e.id
        JOIN users u ON sa.student_id=u.id
        LEFT JOIN essay_reviews er ON er.answer_id=sa.id
        WHERE e.teacher_id=? AND q.type='essay'
        ORDER BY sa.id DESC""", (session["user_id"],)).fetchall()
    db.close()

    cards = "".join(
        f"""<div class="card" style="margin-bottom:16px">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px">
        <div><div class="font-bold">{e['student_name']}</div><div class="text-sm text-muted">{e['exam_title']}</div></div>
        <span class="badge {'badge-green' if e['points_given'] is not None else 'badge-orange'}">
          {'Reviewed' if e['points_given'] is not None else 'Pending'}</span>
      </div>
      <p class="text-sm font-bold" style="margin-bottom:6px">Q: {e['question_text']}</p>
      <p class="text-sm text-muted" style="margin-bottom:12px;white-space:pre-wrap">{e['answer'] or '(No answer)'}</p>
      <div style="display:flex;gap:12px;align-items:center">
        <input type="number" id="pts_{e['answer_id']}" class="form-input" placeholder="Points" value="{e['points_given'] or ''}" max="{e['max_points']}" style="max-width:100px">
        <input type="text"   id="fb_{e['answer_id']}"  class="form-input flex-1" placeholder="Feedback (optional)" value="{e['feedback'] or ''}">
        <button class="btn btn-primary btn-sm" onclick="saveReview({e['answer_id']})">Save</button>
      </div>
      <p class="text-sm text-muted mt-8">Max points: {e['max_points']}</p>
    </div>"""
        for e in essays
    )

    html = sidebar("teacher", "essays") + f"""
    <div class="topbar"><div><div class="page-title">Essay Reviews</div><div class="page-sub">Review and grade student essay answers</div></div></div>
    <div class="alert-zone"></div>
    {cards or '<div class="empty-state"><div class="empty-icon">✏️</div><p>No essay answers to review</p></div>'}
  </main></div>
<script>
function saveReview(id){{
  const pts=parseFloat(document.getElementById('pts_'+id).value);
  const fb=document.getElementById('fb_'+id).value;
  if(isNaN(pts))return showAlert('Enter valid points.');
  fetch('/api/teacher/essays/'+id,{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{points:pts,feedback:fb}})}})
  .then(r=>r.json()).then(d=>{{if(d.success)showAlert('Review saved!','success');else showAlert(d.error);}});
}}
</script>"""
    return render(html, "Essays")

# FIX PARA SA SCREENSHOT: teacher/results
@teacher_bp.route("/teacher/results")
@login_required
@role_required("teacher")
def teacher_results():
    db    = get_db()
    exams = db.execute(
        "SELECT e.*, c.course_name FROM exams e JOIN courses c ON e.course_id=c.id WHERE e.teacher_id=? ORDER BY e.id DESC",
        (session["user_id"],),
    ).fetchall()
    db.close()

    links = "".join(
        f'<a href="/teacher/exams/{e["id"]}/results" class="btn btn-secondary" style="margin-bottom:8px; display:inline-block; width:100%; text-align:left; padding: 15px">'
        f'<strong>{e["title"]}</strong> <br><small>{e["course_name"]}</small></a><br>'
        for e in exams
    )

    html = sidebar("teacher", "results") + f"""
    <div class="topbar"><div><div class="page-title">Overall Results</div><div class="page-sub">Select an exam to view detailed scores</div></div></div>
    <div class="card">
      <h3 class="card-title" style="margin-bottom:20px">My Exams</h3>
      {links or '<div class="empty-state"><div class="empty-icon">📊</div><p>No exams created yet</p></div>'}
    </div>
  </main></div>"""
    return render(html, "Results")

# ─────────────────────────────────────────────
#  API ROUTES
# ─────────────────────────────────────────────

@teacher_bp.route("/api/teacher/exams", methods=["POST"])
@login_required
@role_required("teacher")
def api_save_exam():
    data      = request.json
    eid       = data.get("exam_id")
    title     = (data.get("title", "")).strip()
    course_id = data.get("course_id")
    timer     = data.get("timer_minutes", 60)
    passing   = data.get("passing_score", 60)
    questions = data.get("questions", [])

    if not title: return jsonify({"error": "Title required."})
    if not questions: return jsonify({"error": "At least one question required."})

    db = get_db()
    try:
        if eid:
            db.execute("UPDATE exams SET course_id=?, title=?, timer_minutes=?, passing_score=? WHERE id=? AND teacher_id=?",
                (course_id, title, timer, passing, eid, session["user_id"]))
            db.execute("DELETE FROM questions WHERE exam_id=?", (eid,))
        else:
            cur = db.execute("INSERT INTO exams (course_id, teacher_id, title, timer_minutes, passing_score) VALUES (?,?,?,?,?)",
                (course_id, session["user_id"], title, timer, passing))
            eid = cur.lastrowid

        for q in questions:
            choices_json = json.dumps(q.get("choices", [])) if q.get("type") == "mcq" else None
            db.execute("INSERT INTO questions (exam_id, question_text, type, choices, correct_answer, points) VALUES (?,?,?,?,?,?)",
                (eid, q["text"], q["type"], choices_json, q.get("correct", ""), q.get("points", 1)))
        db.commit()
        return jsonify({"success": True, "exam_id": eid})
    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        db.close()

@teacher_bp.route("/api/teacher/exams/<int:eid>", methods=["DELETE"])
@login_required
@role_required("teacher")
def api_del_exam(eid):
    db = get_db()
    try:
        exam = db.execute("SELECT id FROM exams WHERE id=? AND teacher_id=?", (eid, session["user_id"])).fetchone()
        if not exam: return jsonify({"error": "Exam not found."})
        db.execute("DELETE FROM student_answers WHERE exam_id=?", (eid,))
        db.execute("DELETE FROM results WHERE exam_id=?", (eid,))
        db.execute("DELETE FROM questions WHERE exam_id=?", (eid,))
        db.execute("DELETE FROM exams WHERE id=?", (eid,))
        db.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        db.close()

@teacher_bp.route("/api/teacher/essays/<int:aid>", methods=["POST"])
@login_required
@role_required("teacher")
def api_review_essay(aid):
    data     = request.json
    points   = data.get("points", 0)
    feedback = data.get("feedback", "")
    db = get_db()
    try:
        existing = db.execute("SELECT id FROM essay_reviews WHERE answer_id=?", (aid,)).fetchone()
        if existing:
            db.execute("UPDATE essay_reviews SET points_given=?, feedback=?, teacher_id=?, reviewed_at=CURRENT_TIMESTAMP WHERE answer_id=?",
                (points, feedback, session["user_id"], aid))
        else:
            db.execute("INSERT INTO essay_reviews (answer_id, teacher_id, points_given, feedback) VALUES (?,?,?,?)",
                (aid, session["user_id"], points, feedback))
        db.execute("UPDATE student_answers SET is_correct=? WHERE id=?", (1 if points > 0 else 0, aid))
        db.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        db.close()

@teacher_bp.route("/api/teacher/exams/<int:eid>/export/pdf")
@login_required
@role_required("teacher")
def export_pdf(eid):
    db = get_db()
    exam = db.execute("SELECT e.*, c.course_name FROM exams e JOIN courses c ON e.course_id=c.id WHERE e.id=? AND e.teacher_id=?", (eid, session["user_id"])).fetchone()
    if not exam:
        db.close()
        return "Not found", 404
    results = db.execute("SELECT r.*, u.name, u.email FROM results r JOIN users u ON r.student_id=u.id WHERE r.exam_id=? ORDER BY r.percentage DESC", (eid,)).fetchall()
    db.close()
    rows = "".join(f"<tr><td>{r['name']}</td><td>{r['email']}</td><td>{r['score']:.1f}</td><td>{r['percentage']:.1f}%</td><td>{'Pass' if r['percentage']>=exam['passing_score'] else 'Fail'}</td></tr>" for r in results)
    html = f"<html><body><h1>{exam['title']}</h1><table>{rows}</table></body></html>"
    resp = make_response(html)
    resp.headers["Content-Type"] = "text/html"
    resp.headers["Content-Disposition"] = f'attachment; filename="results_{eid}.html"'
    return resp

@teacher_bp.route("/api/teacher/exams/<int:eid>/export/excel")
@login_required
@role_required("teacher")
def export_excel(eid):
    db = get_db()
    exam = db.execute("SELECT * FROM exams WHERE id=? AND teacher_id=?", (eid, session["user_id"])).fetchone()
    results = db.execute("SELECT r.*, u.name, u.email FROM results r JOIN users u ON r.student_id=u.id WHERE r.exam_id=? ORDER BY r.percentage DESC", (eid,)).fetchall()
    db.close()
    lines = ["Name,Email,Score,Percentage,Status,Submitted"]
    for r in results:
        status = "Pass" if r["percentage"] >= exam["passing_score"] else "Fail"
        lines.append(f'"{r["name"]}","{r["email"]}",{r["score"]:.1f},{r["percentage"]:.1f},{status},{r["submitted_at"][:16]}')
    resp = make_response("\n".join(lines))
    resp.headers["Content-Type"] = "text/csv"
    resp.headers["Content-Disposition"] = f'attachment; filename="results_{eid}.csv"'

    return resp
