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
    db = get_db()
    tid = session.get("user_id")
    
    try:
        # Fetching aggregated statistics for the teacher
        stats = {
            "exams": db.execute("SELECT COUNT(*) FROM exams WHERE teacher_id=?", (tid,)).fetchone()[0],
            "students": db.execute("""
                SELECT COUNT(DISTINCT student_id) FROM results r 
                JOIN exams e ON r.exam_id=e.id 
                WHERE e.teacher_id=?""", (tid,)).fetchone()[0],
            "results": db.execute("""
                SELECT COUNT(*) FROM results r 
                JOIN exams e ON r.exam_id=e.id 
                WHERE e.teacher_id=?""", (tid,)).fetchone()[0],
            "essays": db.execute("""
                SELECT COUNT(*) FROM student_answers sa
                JOIN questions q ON sa.question_id=q.id
                JOIN exams e ON q.exam_id=e.id
                WHERE e.teacher_id=? AND q.type='essay'
                  AND sa.answer IS NOT NULL AND sa.answer!=''
                  AND NOT EXISTS(SELECT 1 FROM essay_reviews er WHERE er.answer_id=sa.id)""",
                (tid,)).fetchone()[0],
        }

        # Fetching the 5 most recent exams
        recent_exams = db.execute("""
            SELECT e.*, c.course_name,
                   (SELECT COUNT(*) FROM results r WHERE r.exam_id=e.id) AS submissions
            FROM exams e JOIN courses c ON e.course_id=c.id
            WHERE e.teacher_id=? ORDER BY e.id DESC LIMIT 5""", (tid,)).fetchall()
    finally:
        db.close()

    # Generate table rows for recent exams
    if recent_exams:
        exam_rows = "".join(f"""
            <tr>
                <td>{e['title']}</td>
                <td>{e['course_name']}</td>
                <td>{e['timer_minutes']} min</td>
                <td>{e['submissions']}</td>
                <td>
                    <a href="/teacher/exams/{e['id']}/results" class="btn btn-sm btn-secondary">View</a>
                </td>
            </tr>""" for e in recent_exams)
    else:
        exam_rows = """
            <tr>
                <td colspan="5">
                    <div class="empty-state">
                        <div class="empty-icon">📝</div>
                        <p>No exams yet. <a href="/teacher/exams/create" style="color:var(--red)">Create your first exam</a></p>
                    </div>
                </td>
            </tr>"""

    # Construct the final dashboard HTML
    html = sidebar("teacher", "dashboard") + f"""
    <div class="topbar">
      <div>
        <div class="page-title">Teacher Dashboard</div>
        <div class="page-sub">Welcome, {session.get('name', 'Teacher')}</div>
      </div>
      <a href="/teacher/exams/create" class="btn btn-primary">+ Create Exam</a>
    </div>

    <div class="grid grid-4" style="margin-bottom:24px">
      <div class="stat-card">
        <div class="stat-icon" style="background:#c0392b">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2"/></svg>
        </div>
        <div><div class="stat-label">My Exams</div><div class="stat-value">{stats['exams']}</div></div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:#2980b9">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2M9 7a4 4 0 100 8 4 4 0 000-8z"/></svg>
        </div>
        <div><div class="stat-label">Students Tested</div><div class="stat-value">{stats['students']}</div></div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:#27ae60">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4"/></svg>
        </div>
        <div><div class="stat-label">Submissions</div><div class="stat-value">{stats['results']}</div></div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:#f39c12">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5"/></svg>
        </div>
        <div><div class="stat-label">Pending Essays</div><div class="stat-value">{stats['essays']}</div></div>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Recent Exams</h3>
        <a href="/teacher/exams" class="btn btn-sm btn-secondary">View All</a>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
                <th>Exam Title</th>
                <th>Course</th>
                <th>Duration</th>
                <th>Submissions</th>
                <th>Actions</th>
            </tr>
          </thead>
          <tbody>{exam_rows}</tbody>
        </table>
      </div>
    </div>
    </main></div>"""

    return render(html, "Teacher Dashboard")

@teacher_bp.route("/teacher/exams")
@login_required
@role_required("teacher")
def teacher_exams():
    db = get_db()
    tid = session.get("user_id")
    
    try:
        # Fetching all exams created by this teacher with submission and question counts
        exams = db.execute("""
            SELECT e.*, c.course_name,
                   (SELECT COUNT(*) FROM results r WHERE r.exam_id=e.id) AS submissions,
                   (SELECT COUNT(*) FROM questions q WHERE q.exam_id=e.id) AS q_count
            FROM exams e 
            JOIN courses c ON e.course_id=c.id
            WHERE e.teacher_id=? 
            ORDER BY e.id DESC""", (tid,)).fetchall()
    finally:
        db.close()

    # Generating the table rows
    if exams:
        rows = "".join(f"""
            <tr>
                <td>{e['title']}</td>
                <td>{e['course_name']}</td>
                <td>{e['q_count']} Qs</td>
                <td>{e['timer_minutes']} min</td>
                <td>{e['submissions']}</td>
                <td>
                    <div class="flex gap-4">
                        <a href="/teacher/exams/{e['id']}/edit" class="btn btn-sm btn-warning">Edit</a>
                        <a href="/teacher/exams/{e['id']}/results" class="btn btn-sm btn-secondary">Results</a>
                        <button class="btn btn-sm btn-danger" onclick="delExam({e['id']})">Delete</button>
                    </div>
                </td>
            </tr>""" for e in exams)
    else:
        rows = """
            <tr>
                <td colspan="6">
                    <div class="empty-state">
                        <div class="empty-icon">📝</div>
                        <p>No exams yet. <a href="/teacher/exams/create" style="color:var(--red)">Create your first one</a></p>
                    </div>
                </td>
            </tr>"""

    # Building the full page layout
    html = sidebar("teacher", "exams") + f"""
    <div class="topbar">
      <div><div class="page-title">My Exams</div></div>
      <a href="/teacher/exams/create" class="btn btn-primary">+ Create Exam</a>
    </div>
    
    <div class="alert-zone"></div>

    <div class="card">
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Title</th>
              <th>Course</th>
              <th>Questions</th>
              <th>Duration</th>
              <th>Submissions</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {rows}
          </tbody>
        </table>
      </div>
    </div>
    
    </main></div>

    <script>
    function delExam(id) {{
        if (!confirm('Are you sure? This will delete the exam and all student results permanently.')) return;
        
        fetch('/api/teacher/exams/' + id, {{ 
            method: 'DELETE' 
        }})
        .then(r => r.json())
        .then(d => {{
            if (d.success) {{
                location.reload();
            }} else {{
                // Assuming you have a showAlert function defined in your layout
                if (window.showAlert) showAlert(d.error);
                else alert(d.error);
            }}
        }})
        .catch(err => console.error('Error:', err));
    }}
    </script>
    """
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
        # Verify ownership and existence
        exam_data = db.execute("SELECT * FROM exams WHERE id=? AND teacher_id=?", (eid, session["user_id"])).fetchone()
        if not exam_data:
            db.close()
            return "Exam not found or access denied", 404
        
        # Load existing questions
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
    
    # Pre-select the course if editing
    course_opts = "".join(f'<option value="{c["id"]}" {"selected" if exam_data and exam_data["course_id"]==c["id"] else ""}>{c["course_name"]}</option>' for c in courses)

    html = sidebar("teacher", "exams") + f"""
    <div class="topbar">
        <div>
            <div class="page-title">{'Edit' if eid else 'Create'} Exam</div>
            <div class="page-sub">Manage your exam settings and questions</div>
        </div>
    </div>
    
    <div class="alert-zone"></div>
    
    <div class="grid grid-2" style="align-items:start; gap: 20px;">
        <div class="card">
            <h3 class="card-title" style="margin-bottom:20px">Exam Settings</h3>
            <div class="form-group">
                <label class="form-label">Exam Title</label>
                <input id="examTitle" class="form-input" value="{exam_data['title'] if exam_data else ''}" placeholder="e.g. Midterm Examination">
            </div>
            <div class="form-group">
                <label class="form-label">Course</label>
                <select id="examCourse" class="form-input form-select">{course_opts}</select>
            </div>
            <div class="form-group">
                <label class="form-label">Time Limit (minutes)</label>
                <input id="examTimer" type="number" class="form-input" value="{exam_data['timer_minutes'] if exam_data else '60'}" min="5">
            </div>
            <div class="form-group">
                <label class="form-label">Passing Score (%)</label>
                <input id="examPass" type="number" class="form-input" value="{exam_data['passing_score'] if exam_data else '60'}" min="0" max="100">
            </div>
        </div>

        <div class="card">
            <div class="flex justify-between items-center mb-16">
                <h3 class="card-title">Questions</h3>
                <button class="btn btn-primary btn-sm" onclick="addQuestion()">+ Add Question</button>
            </div>
            <div id="questions-list"></div>
            <div class="text-center text-muted text-sm" id="no-q-msg" style="padding: 40px 0;">No questions added yet.</div>
        </div>
    </div>

    <div style="margin-top:20px;text-align:right">
        <a href="/teacher/exams" class="btn btn-secondary" style="margin-right: 8px;">Cancel</a>
        <button class="btn btn-primary" onclick="saveExam()">{ 'Update Exam' if eid else 'Save Exam' }</button>
    </div>
    </main></div>

<script>
let questions = {questions_json};
let currentExamId = {eid if eid else 'null'};

function addQuestion() {{
    questions.push({{type:'mcq', text:'', choices:['','','',''], correct:'A', points:1}});
    renderQuestions();
}}

function removeQ(i) {{
    if(confirm('Delete this question?')) {{
        questions.splice(i, 1);
        renderQuestions();
    }}
}}

function renderQuestions() {{
    const list = document.getElementById('questions-list');
    const noMsg = document.getElementById('no-q-msg');
    
    noMsg.style.display = questions.length ? 'none' : 'block';
    
    list.innerHTML = questions.map((q, i) => {{
        let choicesHtml = '';
        
        if (q.type === 'mcq') {{
            const letters = ['A', 'B', 'C', 'D'];
            choicesHtml = `
                <div style="margin-top:12px">
                    <label class="form-label">Choices</label>
                    ${{[0,1,2,3].map(ci => `
                        <div style="display:flex;gap:8px;margin-bottom:6px">
                            <span style="width:24px;padding-top:10px;font-weight:700;color:var(--red)">${{letters[ci]}}</span>
                            <input class="form-input flex-1" placeholder="Choice ${{letters[ci]}}" value="${{q.choices[ci]||''}}" onchange="questions[${{i}}].choices[${{ci}}]=this.value">
                        </div>`).join('')}}
                    <div class="form-group">
                        <label class="form-label">Correct Answer</label>
                        <select class="form-input form-select" onchange="questions[${{i}}].correct=this.value">
                            ${{letters.map(l => `<option ${{q.correct===l?'selected':''}} value="${{l}}">${{l}}</option>`).join('')}}
                        </select>
                    </div>
                </div>`;
        }} else if (q.type === 'tf') {{
            choicesHtml = `
                <div class="form-group mt-8">
                    <label class="form-label">Correct Answer</label>
                    <select class="form-input form-select" onchange="questions[${{i}}].correct=this.value">
                        <option ${{q.correct==='True'?'selected':''}} value="True">True</option>
                        <option ${{q.correct==='False'?'selected':''}} value="False">False</option>
                    </select>
                </div>`;
        }} else if (q.type === 'identification') {{
            choicesHtml = `
                <div class="form-group mt-8">
                    <label class="form-label">Correct Answer</label>
                    <input class="form-input" placeholder="Expected answer" value="${{q.correct||''}}" onchange="questions[${{i}}].correct=this.value">
                </div>`;
        }}

        return `
            <div class="question-card" style="margin-bottom:20px; border: 1px solid #ddd; padding: 15px; border-radius: 8px; background: #fafafa;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
                    <span style="font-weight:700;font-size:14px;color:var(--red)">QUESTION ${{i+1}}</span>
                    <button class="btn btn-sm btn-danger" onclick="removeQ(${{i}})">Remove</button>
                </div>
                <div class="form-group">
                    <label class="form-label">Type</label>
                    <select class="form-input form-select" onchange="questions[${{i}}].type=this.value; if(this.value==='tf')questions[${{i}}].correct='True'; renderQuestions()">
                        <option ${{q.type==='mcq'?'selected':''}} value="mcq">Multiple Choice</option>
                        <option ${{q.type==='tf'?'selected':''}} value="tf">True / False</option>
                        <option ${{q.type==='essay'?'selected':''}} value="essay">Essay</option>
                        <option ${{q.type==='identification'?'selected':''}} value="identification">Identification</option>
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">Question Text</label>
                    <textarea class="form-input" rows="2" onchange="questions[${{i}}].text=this.value" placeholder="Type question here...">${{q.text}}</textarea>
                </div>
                <div class="form-group">
                    <label class="form-label">Points</label>
                    <input type="number" class="form-input" value="${{q.points}}" min="0.5" step="0.5" onchange="questions[${{i}}].points=parseFloat(this.value)" style="max-width:120px">
                </div>
                ${{choicesHtml}}
            </div>`;
    }}).join('');
}}

function saveExam() {{
    const title = document.getElementById('examTitle').value.trim();
    const course_id = document.getElementById('examCourse').value;
    const timer = parseInt(document.getElementById('examTimer').value);
    const passing = parseFloat(document.getElementById('examPass').value);
    
    if(!title) return showAlert('Please enter an exam title.');
    if(!questions.length) return showAlert('Please add at least one question.');
    
    // Simple validation for question texts
    if(questions.some(q => !q.text.trim())) return showAlert('All questions must have text.');

    fetch('/api/teacher/exams', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{
            exam_id: currentExamId,
            title, 
            course_id, 
            timer_minutes: timer, 
            passing_score: passing, 
            questions
        }})
    }})
    .then(r => r.json())
    .then(d => {{
        if(d.success) {{
            showAlert('Exam successfully saved!', 'success');
            setTimeout(() => location.href = '/teacher/exams', 1000);
        }} else {{
            showAlert(d.error || 'Failed to save exam.');
        }}
    }}).catch(err => {{
        showAlert('A server error occurred.');
        console.error(err);
    }});
}}

// Initial Render
renderQuestions();
</script>"""
    return render(html, "Exam Editor")
@teacher_bp.route("/teacher/exams/<int:eid>/results")
@login_required
@role_required("teacher")
def teacher_exam_results(eid):
    db = get_db()
    try:
        # Fetch exam metadata
        exam = db.execute(
            "SELECT e.*, c.course_name FROM exams e JOIN courses c ON e.course_id=c.id WHERE e.id=? AND e.teacher_id=?",
            (eid, session["user_id"]),
        ).fetchone()
        
        if not exam:
            return "Exam not found", 404

        # Fetch all student results for this exam
        results = db.execute(
            "SELECT r.*, u.name, u.email FROM results r JOIN users u ON r.student_id=u.id WHERE r.exam_id=? ORDER BY r.percentage DESC",
            (eid,),
        ).fetchall()
    finally:
        db.close()

    # Build Table Rows
    rows = "".join(
        f"""<tr>
            <td>{r['name']}</td>
            <td>{r['email']}</td>
            <td><strong>{r['score']:.1f}</strong></td>
            <td>{r['percentage']:.1f}%</td>
            <td><span class="badge badge-{'green' if r['percentage']>=exam['passing_score'] else 'red'}">
                {'Pass' if r['percentage']>=exam['passing_score'] else 'Fail'}</span></td>
            <td>{r['submitted_at'][:16]}</td>
        </tr>"""
        for r in results
    )

    html = sidebar("teacher", "exams") + f"""
    <div class="topbar">
      <div>
        <div class="page-title">{exam['title']}</div>
        <div class="page-sub">{exam['course_name']} · {exam['timer_minutes']} min · Passing Score: {exam['passing_score']}%</div>
      </div>
      <div style="display:flex;gap:10px">
        <button class="btn btn-secondary" onclick="exportPDF()">Export PDF</button>
        <button class="btn btn-success" onclick="exportExcel()">Export Excel</button>
      </div>
    </div>
    <div class="card">
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Student</th>
              <th>Email</th>
              <th>Score</th>
              <th>Percentage</th>
              <th>Status</th>
              <th>Submitted</th>
            </tr>
          </thead>
          <tbody>
            {rows or '<tr><td colspan="6"><div class="empty-state"><div class="empty-icon">📊</div><p>No submissions yet</p></div></td></tr>'}
          </tbody>
        </table>
      </div>
    </div>
    </main></div>
    <script>
    function exportPDF() {{ window.open('/api/teacher/exams/{eid}/export/pdf','_blank'); }}
    function exportExcel() {{ window.open('/api/teacher/exams/{eid}/export/excel','_blank'); }}
    </script>"""
    return render(html, "Exam Results")

@teacher_bp.route("/teacher/essays")
@login_required
@role_required("teacher")
def teacher_essays():
    db = get_db()
    try:
        # Fetch essay answers including those already reviewed
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
    finally:
        db.close()

    # Build Cards for Grading
    cards = "".join(
        f"""<div class="card" style="margin-bottom:16px; border-left: 4px solid {'#27ae60' if e['points_given'] is not None else '#f39c12'}">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px">
        <div>
            <div class="font-bold" style="font-size:1.1rem">{e['student_name']}</div>
            <div class="text-sm text-muted">{e['exam_title']}</div>
        </div>
        <span class="badge {'badge-green' if e['points_given'] is not None else 'badge-orange'}">
          {'Reviewed' if e['points_given'] is not None else 'Pending Review'}
        </span>
      </div>
      <div style="background:#f9f9f9; padding:12px; border-radius:8px; margin-bottom:12px">
        <p class="text-sm font-bold" style="color:var(--red); margin-bottom:4px">Question:</p>
        <p class="text-sm">{e['question_text']}</p>
      </div>
      <p class="text-sm font-bold" style="margin-bottom:4px">Student's Answer:</p>
      <p class="text-sm text-muted" style="margin-bottom:16px; white-space:pre-wrap; background:#fff; border:1px solid #eee; padding:10px; border-radius:4px">
        {e['answer'] or '<i class="text-muted">No answer provided</i>'}
      </p>
      <div style="display:flex;gap:12px;align-items:center">
        <div style="flex:0 0 120px">
            <label class="text-xs font-bold">Points (Max: {e['max_points']})</label>
            <input type="number" id="pts_{e['answer_id']}" class="form-input" placeholder="0.0" value="{e['points_given'] if e['points_given'] is not None else ''}" step="0.5" min="0" max="{e['max_points']}">
        </div>
        <div class="flex-1">
            <label class="text-xs font-bold">Teacher Feedback</label>
            <input type="text" id="fb_{e['answer_id']}" class="form-input" placeholder="Good job, but explain more..." value="{e['feedback'] or ''}">
        </div>
        <button class="btn btn-primary" style="margin-top:18px" onclick="saveReview({e['answer_id']})">Save Grade</button>
      </div>
    </div>"""
        for e in essays
    )

    html = sidebar("teacher", "essays") + f"""
    <div class="topbar">
        <div>
            <div class="page-title">Essay Reviews</div>
            <div class="page-sub">Grade student submissions and provide feedback</div>
        </div>
    </div>
    <div class="alert-zone"></div>
    <div style="max-width:900px; margin: 0 auto">
        {cards or '<div class="empty-state"><div class="empty-icon">✏️</div><p>No essay answers found to review.</p></div>'}
    </div>
    </main></div>
    <script>
    function saveReview(id){{
      const ptsInput = document.getElementById('pts_'+id);
      const pts = parseFloat(ptsInput.value);
      const fb = document.getElementById('fb_'+id).value;
      const maxPts = parseFloat(ptsInput.getAttribute('max'));

      if(isNaN(pts)) return showAlert('Please enter a numeric score.');
      if(pts < 0 || pts > maxPts) return showAlert('Points must be between 0 and ' + maxPts);

      fetch('/api/teacher/essays/'+id, {{
        method:'POST',
        headers:{{'Content-Type':'application/json'}},
        body:JSON.stringify({{points:pts, feedback:fb}})
      }})
      .then(r=>r.json()).then(d=>{{
        if(d.success) {{
            showAlert('Grade saved successfully!','success');
            setTimeout(()=>location.reload(), 800);
        }} else showAlert(d.error);
      }});
    }}
    </script>"""
    return render(html, "Essays")

# FIX PARA SA SCREENSHOT: teacher/results
@teacher_bp.route("/teacher/results")
@login_required
@role_required("teacher")
def teacher_results():
    db = get_db()
    tid = session.get("user_id")
    
    # Query updated to include submission counts for better context
    exams = db.execute("""
        SELECT e.*, c.course_name,
               (SELECT COUNT(*) FROM results r WHERE r.exam_id=e.id) AS submissions
        FROM exams e 
        JOIN courses c ON e.course_id=c.id 
        WHERE e.teacher_id=? 
        ORDER BY e.id DESC""", (tid,)).fetchall()
    db.close()

    # Generating stylized links for each exam
    links = "".join(f"""
        <a href="/teacher/exams/{e['id']}/results" class="stat-card" 
           style="display:flex; justify-content:space-between; align-items:center; text-decoration:none; color:inherit; margin-bottom:12px; padding:20px; border:1px solid #eee">
            <div>
                <div style="font-weight:700; font-size:1.1rem; color:var(--dark)">{e['title']}</div>
                <div style="font-size:0.85rem; color:#666">{e['course_name']}</div>
            </div>
            <div style="text-align:right">
                <div class="stat-value" style="font-size:1.2rem">{e['submissions']}</div>
                <div class="stat-label" style="font-size:0.7rem; text-transform:uppercase">Submissions</div>
            </div>
        </a>""" for e in exams)

    html = sidebar("teacher", "results") + f"""
    <div class="topbar">
        <div>
            <div class="page-title">Overall Results</div>
            <div class="page-sub">Select an exam to view detailed student scores and analytics</div>
        </div>
    </div>
    
    <div class="card">
        <div class="card-header">
            <h3 class="card-title">My Exams</h3>
        </div>
        <div style="margin-top:20px">
            {links or '''
            <div class="empty-state">
                <div class="empty-icon">📊</div>
                <p>No exams created yet. <a href="/teacher/exams/create" style="color:var(--red)">Create one now</a> to see results.</p>
            </div>'''}
        </div>
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

    # Validation
    if not title: 
        return jsonify({"success": False, "error": "Exam title is required."})
    if not questions: 
        return jsonify({"success": False, "error": "At least one question is required."})

    db = get_db()
    try:
        if eid:
            # Update existing exam (ensure teacher ownership)
            db.execute("""
                UPDATE exams 
                SET course_id=?, title=?, timer_minutes=?, passing_score=? 
                WHERE id=? AND teacher_id=?""",
                (course_id, title, timer, passing, eid, session["user_id"]))
            
            # Wipe old questions to prevent duplicates/orphans
            db.execute("DELETE FROM questions WHERE exam_id=?", (eid,))
        else:
            # Create new exam record
            cur = db.execute("""
                INSERT INTO exams (course_id, teacher_id, title, timer_minutes, passing_score) 
                VALUES (?, ?, ?, ?, ?)""",
                (course_id, session["user_id"], title, timer, passing))
            eid = cur.lastrowid

        # Batch insert the current state of questions
        for q in questions:
            # Only MCQs need the choices JSON; others (Essay, T/F) use NULL
            choices_json = json.dumps(q.get("choices", [])) if q.get("type") == "mcq" else None
            
            db.execute("""
                INSERT INTO questions (exam_id, question_text, type, choices, correct_answer, points) 
                VALUES (?, ?, ?, ?, ?, ?)""",
                (eid, q["text"], q["type"], choices_json, q.get("correct", ""), q.get("points", 1)))
        
        db.commit()
        return jsonify({"success": True, "exam_id": eid})

    except Exception as e:
        # Rollback is implicit in some DB wrappers on error, but it's good practice to be aware of it
        return jsonify({"success": False, "error": f"Database error: {str(e)}"})
    finally:
        db.close()

@teacher_bp.route("/api/teacher/exams/<int:eid>", methods=["DELETE"])
@login_required
@role_required("teacher")
def api_del_exam(eid):
    db = get_db()
    try:
        # 1. Security Check: Ensure the exam exists and belongs to the current teacher
        exam = db.execute("SELECT id FROM exams WHERE id=? AND teacher_id=?", 
                          (eid, session["user_id"])).fetchone()
        
        if not exam:
            return jsonify({"success": False, "error": "Exam not found or access denied."}), 404

        # 2. Manual Cascade: Delete related data in order of dependency
        # Delete student answers associated with this exam's questions
        db.execute("""
            DELETE FROM student_answers 
            WHERE question_id IN (SELECT id FROM questions WHERE exam_id=?)
        """, (eid,))
        
        # Delete essay reviews linked to those answers
        db.execute("""
            DELETE FROM essay_reviews 
            WHERE answer_id IN (
                SELECT sa.id FROM student_answers sa 
                JOIN questions q ON sa.question_id = q.id 
                WHERE q.exam_id = ?
            )
        """, (eid,))

        # Delete the high-level results/scores
        db.execute("DELETE FROM results WHERE exam_id=?", (eid,))
        
        # Delete the actual questions
        db.execute("DELETE FROM questions WHERE exam_id=?", (eid,))
        
        # Finally, delete the exam record itself
        db.execute("DELETE FROM exams WHERE id=?", (eid,))
        
        db.commit()
        return jsonify({"success": True})

    except Exception as e:
        # In case of any error, we don't commit anything to keep data integrity
        return jsonify({"success": False, "error": f"Deletion failed: {str(e)}"})
    
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
        # 1. Update or Insert the essay review
        existing = db.execute("SELECT id FROM essay_reviews WHERE answer_id=?", (aid,)).fetchone()
        
        if existing:
            db.execute("""
                UPDATE essay_reviews 
                SET points_given=?, feedback=?, teacher_id=?, reviewed_at=CURRENT_TIMESTAMP 
                WHERE answer_id=?""",
                (points, feedback, session["user_id"], aid))
        else:
            db.execute("""
                INSERT INTO essay_reviews (answer_id, teacher_id, points_given, feedback) 
                VALUES (?, ?, ?, ?)""",
                (aid, session["user_id"], points, feedback))

        # 2. Update the answer status 
        # (Considered 'correct' if points are awarded, though essays are subjective)
        db.execute("UPDATE student_answers SET is_correct=? WHERE id=?", (1 if points > 0 else 0, aid))

        # 3. Recalculate the student's total exam score
        # Fetch the student_id and exam_id for this answer
        info = db.execute("""
            SELECT sa.student_id, q.exam_id 
            FROM student_answers sa 
            JOIN questions q ON sa.question_id = q.id 
            WHERE sa.id = ?""", (aid,)).fetchone()

        if info:
            student_id = info['student_id']
            exam_id = info['exam_id']

            # Sum up points from auto-graded questions and reviewed essays
            # We use COALESCE to treat unreviewed essays or nulls as 0
            new_total = db.execute("""
                SELECT SUM(
                    CASE 
                        WHEN q.type = 'essay' THEN COALESCE(er.points_given, 0)
                        WHEN sa.is_correct = 1 THEN q.points
                        ELSE 0 
                    END
                ) as total_score
                FROM student_answers sa
                JOIN questions q ON sa.question_id = q.id
                LEFT JOIN essay_reviews er ON sa.id = er.answer_id
                WHERE sa.student_id = ? AND q.exam_id = ?
            """, (student_id, exam_id)).fetchone()['total_score'] or 0

            # Get max possible points for percentage calculation
            max_points = db.execute("SELECT SUM(points) FROM questions WHERE exam_id=?", (exam_id,)).fetchone()[0] or 1
            percentage = (new_total / max_points) * 100

            # Update the results table so the student sees their updated grade
            db.execute("""
                UPDATE results 
                SET score=?, percentage=? 
                WHERE student_id=? AND exam_id=?""",
                (new_total, percentage, student_id, exam_id))

        db.commit()
        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    finally:
        db.close()

@teacher_bp.route("/api/teacher/exams/<int:eid>/export/pdf")
@login_required
@role_required("teacher")
def export_pdf(eid):
    db = get_db()
    try:
        # Fetch exam and course details
        exam = db.execute("""
            SELECT e.*, c.course_name 
            FROM exams e 
            JOIN courses c ON e.course_id=c.id 
            WHERE e.id=? AND e.teacher_id=?""", 
            (eid, session["user_id"])).fetchone()
            
        if not exam:
            return "Exam not found or access denied", 404
            
        # Fetch results
        results = db.execute("""
            SELECT r.*, u.name, u.email 
            FROM results r 
            JOIN users u ON r.student_id=u.id 
            WHERE r.exam_id=? 
            ORDER BY r.percentage DESC""", 
            (eid,)).fetchall()
    finally:
        db.close()

    # Create table rows with basic styling classes
    rows = "".join(f"""
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{r['name']}</td>
            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{r['email']}</td>
            <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: center;">{r['score']:.1f}</td>
            <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: center;">{r['percentage']:.1f}%</td>
            <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: center; color: {'green' if r['percentage']>=exam['passing_score'] else 'red'};">
                {'PASSED' if r['percentage']>=exam['passing_score'] else 'FAILED'}
            </td>
        </tr>""" for r in results)

    # Professional Print Template
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Results - {exam['title']}</title>
        <style>
            body {{ font-family: sans-serif; color: #333; line-height: 1.6; padding: 40px; }}
            .header {{ text-align: center; border-bottom: 2px solid #c0392b; margin-bottom: 30px; padding-bottom: 10px; }}
            .header h1 {{ margin: 0; color: #c0392b; }}
            .meta {{ margin-bottom: 20px; display: flex; justify-content: space-between; font-size: 0.9rem; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th {{ background-color: #f8f9fa; text-align: left; padding: 12px 8px; border-bottom: 2px solid #ddd; }}
            .footer {{ margin-top: 50px; font-size: 0.8rem; text-align: center; color: #888; }}
            @media print {{
                .no-print {{ display: none; }}
                body {{ padding: 0; }}
            }}
        </style>
    </head>
    <body>
        <div class="no-print" style="background: #fff3cd; padding: 10px; margin-bottom: 20px; text-align: center; border: 1px solid #ffeeba;">
            <strong>Print Preview:</strong> Press <code>Ctrl + P</code> (or Cmd + P) and select "Save as PDF" to generate the file.
        </div>

        <div class="header">
            <h1>Exam Results Report</h1>
            <p>{exam['course_name']}</p>
        </div>

        <div class="meta">
            <div>
                <strong>Exam:</strong> {exam['title']}<br>
                <strong>Teacher:</strong> {session.get('name')}<br>
                <strong>Date:</strong> {datetime.now().strftime('%B %d, %Y')}
            </div>
            <div style="text-align: right;">
                <strong>Passing Score:</strong> {exam['passing_score']}%<br>
                <strong>Total Students:</strong> {len(results)}
            </div>
        </div>

        <table>
            <thead>
                <tr>
                    <th>Student Name</th>
                    <th>Email</th>
                    <th style="text-align: center;">Score</th>
                    <th style="text-align: center;">%</th>
                    <th style="text-align: center;">Status</th>
                </tr>
            </thead>
            <tbody>
                {rows if results else '<tr><td colspan="5" style="text-align:center; padding:20px;">No records found.</td></tr>'}
            </tbody>
        </table>

        <div class="footer">
            Generated by Gemini Exam System &copy; {datetime.now().year}
        </div>
    </body>
    </html>
    """

    resp = make_response(html)
    resp.headers["Content-Type"] = "text/html"
    # Keeping the .html extension for now so browsers render it correctly for printing
    resp.headers["Content-Disposition"] = f'inline; filename="results_{eid}.html"'
    return resp

import json
from datetime import datetime
from flask import Blueprint, request, session, redirect, url_for, jsonify, make_response

from database import get_db
from helpers import render, sidebar
from auth_utils import login_required, role_required

teacher_bp = Blueprint("teacher", __name__)

# ... (Previous routes like dashboard, editor, and results go here) ...

@teacher_bp.route("/api/teacher/exams/<int:eid>/export/excel")
@login_required
@role_required("teacher")
def export_excel(eid):
    db = get_db()
    try:
        # 1. Fetch exam details and verify ownership
        exam = db.execute(
            "SELECT title, passing_score FROM exams WHERE id=? AND teacher_id=?", 
            (eid, session["user_id"])
        ).fetchone()
        
        if not exam:
            return "Exam not found or access denied", 404

        # 2. Fetch student results
        results = db.execute("""
            SELECT r.*, u.name, u.email 
            FROM results r 
            JOIN users u ON r.student_id=u.id 
            WHERE r.exam_id=? 
            ORDER BY r.percentage DESC""", 
            (eid,)
        ).fetchall()
        
    finally:
        db.close()

    # 3. Build CSV content
    # Headers
    lines = ["Name,Email,Score,Percentage,Status,Submitted At"]
    
    for r in results:
        status = "Pass" if r["percentage"] >= exam["passing_score"] else "Fail"
        
        # We wrap strings in quotes to prevent commas in names from breaking the CSV structure
        line = (
            f'"{r["name"]}",'
            f'"{r["email"]}",'
            f'{r["score"]:.1f},'
            f'{r["percentage"]:.1f}%,'
            f'{status},'
            f'"{r["submitted_at"][:16]}"'
        )
        lines.append(line)

    # 4. Generate Response
    output = "\n".join(lines)
    resp = make_response(output)
    
    # Force browser to download as .csv
    resp.headers["Content-Type"] = "text/csv"
    resp.headers["Content-Disposition"] = f'attachment; filename="results_{eid}.csv"'
    
    return resp

# ─────────────────────────────────────────────
#  PAGE ROUTES
# ─────────────────────────────────────────────

@teacher_bp.route("/teacher")
@teacher_bp.route("/teacher/")
@login_required
@role_required("teacher")
def teacher_dashboard():
    db = get_db()
    tid = session["user_id"]
    
    try:
        # Aggregate Statistics for the Stat Cards
        stats = {
            "exams": db.execute("SELECT COUNT(*) FROM exams WHERE teacher_id=?", (tid,)).fetchone()[0],
            "students": db.execute("""
                SELECT COUNT(DISTINCT student_id) FROM results r 
                JOIN exams e ON r.exam_id=e.id WHERE e.teacher_id=?""", (tid,)).fetchone()[0],
            "results": db.execute("""
                SELECT COUNT(*) FROM results r 
                JOIN exams e ON r.exam_id=e.id WHERE e.teacher_id=?""", (tid,)).fetchone()[0],
            "essays": db.execute("""
                SELECT COUNT(*) FROM student_answers sa
                JOIN questions q ON sa.question_id=q.id
                JOIN exams e ON q.exam_id=e.id
                WHERE e.teacher_id=? AND q.type='essay'
                  AND sa.answer IS NOT NULL AND sa.answer!=''
                  AND NOT EXISTS(SELECT 1 FROM essay_reviews er WHERE er.answer_id=sa.id)""",
                (tid,)).fetchone()[0],
        }

        # Fetch the 5 most recent exams
        recent_exams = db.execute("""
            SELECT e.*, c.course_name,
                    (SELECT COUNT(*) FROM results r WHERE r.exam_id=e.id) AS submissions
            FROM exams e JOIN courses c ON e.course_id=c.id
            WHERE e.teacher_id=? ORDER BY e.id DESC LIMIT 5""", (tid,)).fetchall()
    finally:
        db.close()

    # Build Recent Exam Table Rows
    exam_rows = "".join(
        f"""<tr>
            <td>{e['title']}</td>
            <td>{e['course_name']}</td>
            <td>{e['timer_minutes']} min</td>
            <td><strong>{e['submissions']}</strong></td>
            <td><a href="/teacher/exams/{e['id']}/results" class="btn btn-sm btn-secondary">View</a></td>
        </tr>"""
        for e in recent_exams
    )

    # Assemble Final HTML
    html = sidebar("teacher", "dashboard") + f"""
    <div class="topbar">
      <div>
        <div class="page-title">Teacher Dashboard</div>
        <div class="page-sub">Welcome back, {session.get('name')}</div>
      </div>
      <a href="/teacher/exams/create" class="btn btn-primary">+ Create Exam</a>
    </div>

    <div class="grid grid-4" style="margin-bottom:24px">
      <div class="stat-card">
        <div class="stat-icon" style="background:#c0392b">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2"/></svg>
        </div>
        <div>
            <div class="stat-label">My Exams</div>
            <div class="stat-value">{stats['exams']}</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background:#2980b9">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2M9 7a4 4 0 100 8 4 4 0 000-8z"/></svg>
        </div>
        <div>
            <div class="stat-label">Students Tested</div>
            <div class="stat-value">{stats['students']}</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background:#27ae60">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4"/></svg>
        </div>
        <div>
            <div class="stat-label">Submissions</div>
            <div class="stat-value">{stats['results']}</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background:#f39c12">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5"/></svg>
        </div>
        <div>
            <div class="stat-label">Pending Essays</div>
            <div class="stat-value">{stats['essays']}</div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Recent Exams</h3>
        <a href="/teacher/exams" class="btn btn-sm btn-secondary">View All</a>
      </div>
      <div class="table-wrap">
        <table>
            <thead>
                <tr>
                    <th>Exam Title</th>
                    <th>Course</th>
                    <th>Duration</th>
                    <th>Submissions</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {exam_rows or '<tr><td colspan="5"><div class="empty-state"><div class="empty-icon">📝</div><p>No exams yet. <a href="/teacher/exams/create" style="color:var(--red)">Create your first exam</a></p></div></td></tr>'}
            </tbody>
        </table>
      </div>
    </div>
    </main></div>"""
    
    return render(html, "Teacher Dashboard")

@teacher_bp.route("/teacher/exams")
@login_required
@role_required("teacher")
def teacher_exams():
    db = get_db()
    try:
        # Fetch all exams with subqueries for submission and question counts
        exams = db.execute("""
            SELECT e.*, c.course_name,
                   (SELECT COUNT(*) FROM results r WHERE r.exam_id=e.id) AS submissions,
                   (SELECT COUNT(*) FROM questions q WHERE q.exam_id=e.id) AS q_count
            FROM exams e 
            JOIN courses c ON e.course_id=c.id
            WHERE e.teacher_id=? 
            ORDER BY e.id DESC""", (session["user_id"],)).fetchall()
    finally:
        db.close()

    # Build the table rows dynamically
    rows = "".join(
        f"""<tr>
            <td><strong>{e['title']}</strong></td>
            <td>{e['course_name']}</td>
            <td><span class="badge badge-secondary">{e['q_count']} Qs</span></td>
            <td>{e['timer_minutes']} min</td>
            <td>{e['submissions']}</td>
            <td>
                <div style="display:flex; gap:5px">
                    <a href="/teacher/exams/{e['id']}/edit" class="btn btn-sm btn-warning">Edit</a>
                    <a href="/teacher/exams/{e['id']}/results" class="btn btn-sm btn-secondary">Results</a>
                    <button class="btn btn-sm btn-danger" onclick="delExam({e['id']})">Delete</button>
                </div>
            </td>
        </tr>"""
        for e in exams
    )

    # Construct the full page HTML
    html = sidebar("teacher", "exams") + f"""
    <div class="topbar">
        <div>
            <div class="page-title">My Exams</div>
            <div class="page-sub">Manage your exam papers and monitor student activity</div>
        </div>
        <a href="/teacher/exams/create" class="btn btn-primary">+ Create New Exam</a>
    </div>
    
    <div class="alert-zone"></div>
    
    <div class="card">
        <div class="table-wrap">
            <table>
                <thead>
                    <tr>
                        <th>Title</th>
                        <th>Course</th>
                        <th>Questions</th>
                        <th>Duration</th>
                        <th>Submissions</th>
                        <th style="width:200px">Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {rows or '<tr><td colspan="6"><div class="empty-state"><div class="empty-icon">📝</div><p>No exams created yet. Click "Create Exam" to get started.</p></div></td></tr>'}
                </tbody>
            </table>
        </div>
    </div>
    </main></div>

    <script>
    function delExam(id) {{
        if(!confirm('Are you sure you want to delete this exam? This will permanently remove all student results and cannot be undone.')) return;
        
        fetch('/api/teacher/exams/' + id, {{ method: 'DELETE' }})
            .then(r => r.json())
            .then(d => {{
                if(d.success) {{
                    location.reload();
                }} else {{
                    showAlert(d.error || 'Failed to delete exam.');
                }}
            }});
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
        # Fetch exam metadata and verify teacher ownership
        exam_data = db.execute("SELECT * FROM exams WHERE id=? AND teacher_id=?", 
                               (eid, session["user_id"])).fetchone()
        
        if not exam_data:
            db.close()
            return "Exam not found or access denied", 404
        
        # Fetch existing questions and format them for the JS frontend
        qs = db.execute("SELECT * FROM questions WHERE exam_id=?", (eid,)).fetchall()
        qs_list = []
        for q in qs:
            qs_list.append({
                "type": q["type"],
                "text": q["question_text"],
                # Standardize choices to a 4-item list for MCQs
                "choices": json.loads(q["choices"]) if q["choices"] else ["","","",""],
                "correct": q["correct_answer"],
                "points": q["points"]
            })
        questions_json = json.dumps(qs_list)
    
    db.close()

    # Create HTML options for the course dropdown
    course_opts = "".join(f'<option value="{c["id"]}" {"selected" if exam_data and exam_data["course_id"]==c["id"] else ""}>{c["course_name"]}</option>' for c in courses)

    html = sidebar("teacher", "exams") + f"""
    <div class="topbar">
        <div>
            <div class="page-title">{'Edit' if eid else 'Create'} Exam</div>
            <div class="page-sub">Configure exam details and question bank</div>
        </div>
    </div>
    
    <div class="alert-zone"></div>
    
    <div class="grid grid-2" style="align-items:start">
      <div class="card">
        <h3 class="card-title" style="margin-bottom:20px">General Settings</h3>
        <div class="form-group">
            <label class="form-label">Exam Title</label>
            <input id="examTitle" class="form-input" value="{exam_data['title'] if exam_data else ''}" placeholder="e.g. Final Examination">
        </div>
        <div class="form-group">
            <label class="form-label">Course</label>
            <select id="examCourse" class="form-input form-select">{course_opts}</select>
        </div>
        <div class="grid grid-2">
            <div class="form-group">
                <label class="form-label">Time Limit (mins)</label>
                <input id="examTimer" type="number" class="form-input" value="{exam_data['timer_minutes'] if exam_data else '60'}" min="5">
            </div>
            <div class="form-group">
                <label class="form-label">Passing Score (%)</label>
                <input id="examPass" type="number" class="form-input" value="{exam_data['passing_score'] if exam_data else '60'}" min="0" max="100">
            </div>
        </div>
      </div>

      <div class="card">
        <div class="flex justify-between items-center mb-16">
          <h3 class="card-title">Questions</h3>
          <button class="btn btn-primary btn-sm" onclick="addQuestion()">+ Add Question</button>
        </div>
        <div id="questions-list"></div>
        <div class="text-center text-muted" id="no-q-msg" style="padding:40px 0;">
            <div style="font-size:2rem; margin-bottom:10px;">📝</div>
            No questions added yet.
        </div>
      </div>
    </div>

    <div style="margin-top:20px; text-align:right">
      <button class="btn btn-success" onclick="saveExam()" style="padding: 12px 30px;">
        { 'Update Changes' if eid else 'Create Exam' }
      </button>
    </div>
    </main></div>

    <script>
    let questions = {questions_json};
    let currentExamId = {eid if eid else 'null'};

    function addQuestion() {{
        questions.push({{type:'mcq', text:'', choices:['','','',''], correct:'A', points:1}});
        renderQuestions();
    }}

    function removeQ(i) {{
        if(confirm('Remove this question?')) {{
            questions.splice(i,1);
            renderQuestions();
        }}
    }}

    function renderQuestions() {{
        const list = document.getElementById('questions-list');
        const noMsg = document.getElementById('no-q-msg');
        noMsg.style.display = questions.length ? 'none' : 'block';
        
        list.innerHTML = questions.map((q, i) => {{
            let choicesHtml = '';
            
            if(q.type === 'mcq') {{
                const letters = 'ABCD';
                choicesHtml = `
                    <div style="margin-top:12px; background:#f9f9f9; padding:10px; border-radius:4px;">
                        <label class="form-label">Multiple Choice Options</label>
                        ${{[0,1,2,3].map(ci => `
                            <div style="display:flex; gap:8px; margin-bottom:6px">
                                <span style="width:24px; padding-top:10px; font-weight:700;">${{letters[ci]}}</span>
                                <input class="form-input flex-1" value="${{q.choices[ci]||''}}" 
                                       onchange="questions[${{i}}].choices[${{ci}}]=this.value" placeholder="Option ${{letters[ci]}}">
                            </div>`).join('')}}
                        <div class="form-group mt-8">
                            <label class="form-label">Select Correct Answer</label>
                            <select class="form-input form-select" onchange="questions[${{i}}].correct=this.value">
                                ${{['A','B','C','D'].map(l => `<option ${{q.correct===l?'selected':''}} value="${{l}}">${{l}}</option>`).join('')}}
                            </select>
                        </div>
                    </div>`;
            }} else if(q.type === 'tf') {{
                choicesHtml = `
                    <div class="form-group mt-8">
                        <label class="form-label">Correct Answer</label>
                        <select class="form-input form-select" onchange="questions[${{i}}].correct=this.value">
                            <option ${{q.correct==='True'?'selected':''}} value="True">True</option>
                            <option ${{q.correct==='False'?'selected':''}} value="False">False</option>
                        </select>
                    </div>`;
            }} else if(q.type === 'identification') {{
                choicesHtml = `
                    <div class="form-group mt-8">
                        <label class="form-label">Accepted Correct Answer</label>
                        <input class="form-input" placeholder="Enter the exact answer" value="${{q.correct||''}}" 
                               onchange="questions[${{i}}].correct=this.value">
                    </div>`;
            }}

            return `
                <div class="question-card" style="margin-bottom:15px; border: 1px solid #ddd; padding: 15px; border-radius: 8px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px">
                        <span class="badge badge-secondary">Question ${{i+1}}</span>
                        <button class="btn btn-sm btn-danger" onclick="removeQ(${{i}})">Delete</button>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Type</label>
                        <select class="form-input form-select" onchange="questions[${{i}}].type=this.value; renderQuestions()">
                            <option ${{q.type==='mcq'?'selected':''}} value="mcq">Multiple Choice</option>
                            <option ${{q.type==='tf'?'selected':''}} value="tf">True / False</option>
                            <option ${{q.type==='essay'?'selected':''}} value="essay">Essay</option>
                            <option ${{q.type==='identification'?'selected':''}} value="identification">Identification</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Question Text</label>
                        <textarea class="form-input" rows="2" onchange="questions[${{i}}].text=this.value">${{q.text}}</textarea>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Points Allocation</label>
                        <input type="number" class="form-input" value="${{q.points}}" min="1" step="1" 
                               onchange="questions[${{i}}].points=parseFloat(this.value)" style="max-width:120px">
                    </div>
                    ${{choicesHtml}}
                </div>`;
        }}).join('');
    }}

    function saveExam() {{
        const title = document.getElementById('examTitle').value.trim();
        const course_id = document.getElementById('examCourse').value;
        const timer = parseInt(document.getElementById('examTimer').value);
        const passing = parseFloat(document.getElementById('examPass').value);
        
        if(!title) return showAlert('Please enter an exam title.');
        if(!questions.length) return showAlert('Please add at least one question.');
        
        fetch('/api/teacher/exams', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{
                exam_id: currentExamId,
                title, course_id, timer_minutes: timer, passing_score: passing, questions
            }})
        }})
        .then(r => r.json()).then(d => {{
            if(d.success) {{
                showAlert('Exam saved successfully!', 'success');
                setTimeout(() => location.href = '/teacher/exams', 1000);
            }} else {{
                showAlert(d.error);
            }}
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
    
    # 1. Fetch Exam Details with Course Name
    exam = db.execute("""
        SELECT e.*, c.course_name 
        FROM exams e 
        JOIN courses c ON e.course_id=c.id 
        WHERE e.id=? AND e.teacher_id=?""",
        (eid, session["user_id"]),
    ).fetchone()
    
    if not exam:
        db.close()
        return "Exam not found", 404

    # 2. Fetch all student submissions for this specific exam
    results = db.execute("""
        SELECT r.*, u.name, u.email 
        FROM results r 
        JOIN users u ON r.student_id=u.id 
        WHERE r.exam_id=? 
        ORDER BY r.percentage DESC""",
        (eid,),
    ).fetchall()
    db.close()

    # 3. Generate table rows with conditional badge colors
    rows = "".join(
        f"""<tr>
            <td><strong>{r['name']}</strong></td>
            <td>{r['email']}</td>
            <td>{r['score']:.1f}</td>
            <td>{r['percentage']:.1f}%</td>
            <td>
                <span class="badge" style="background: {'#27ae60' if r['percentage']>=exam['passing_score'] else '#c0392b'}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem;">
                    {'Pass' if r['percentage']>=exam['passing_score'] else 'Fail'}
                </span>
            </td>
            <td>{r['submitted_at'][:16]}</td>
        </tr>"""
        for r in results
    )

    # 4. Construct the HTML Response
    html = sidebar("teacher", "exams") + f"""
    <div class="topbar">
      <div>
        <div class="page-title">{exam['title']} Results</div>
        <div class="page-sub">
            <span style="color:var(--red); font-weight:bold;">{exam['course_name']}</span> 
            | Duration: {exam['timer_minutes']}m 
            | Passing: {exam['passing_score']}%
        </div>
      </div>
      <div style="display:flex; gap:10px">
        <button class="btn btn-secondary" onclick="exportPDF()">📄 Export PDF</button>
        <button class="btn btn-success" onclick="exportExcel()">📊 Export Excel</button>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Student Performance List</h3>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Student</th>
              <th>Email</th>
              <th>Score</th>
              <th>Percentage</th>
              <th>Status</th>
              <th>Submitted At</th>
            </tr>
          </thead>
          <tbody>
            {rows or '<tr><td colspan="6"><div class="empty-state"><div class="empty-icon">📊</div><p>No students have submitted this exam yet.</p></div></td></tr>'}
          </tbody>
        </table>
      </div>
    </div>
    </main></div>

    <script>
    // These functions trigger the API endpoints you built earlier
    function exportPDF() {{ 
        window.open('/api/teacher/exams/{eid}/export/pdf', '_blank'); 
    }}
    function exportExcel() {{ 
        window.open('/api/teacher/exams/{eid}/export/excel', '_blank'); 
    }}
    </script>"""

    return render(html, f"Results: {exam['title']}")
@teacher_bp.route("/teacher/essays")
@login_required
@role_required("teacher")
def teacher_essays():
    db = get_db()
    # Fetching essays along with their review status (if any)
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

    # Build the Card UI for each essay
    cards = "".join(
        f"""<div class="card" style="margin-bottom:20px; border-left: 5px solid {'#27ae60' if e['points_given'] is not None else '#f39c12'}">
      <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px">
        <div>
            <div style="font-weight:700; font-size:1.1rem">{e['student_name']}</div>
            <div class="text-sm text-muted">{e['exam_title']}</div>
        </div>
        <span class="badge" style="background: {'#27ae60' if e['points_given'] is not None else '#f39c12'}; color:white">
          {'Reviewed' if e['points_given'] is not None else 'Pending Review'}
        </span>
      </div>
      
      <div style="background:#f8f9fa; padding:12px; border-radius:6px; margin-bottom:12px">
        <p class="text-sm font-bold" style="color:var(--red); margin-bottom:4px">Question Prompt:</p>
        <p style="margin:0; font-style:italic">"{e['question_text']}"</p>
      </div>

      <p class="text-sm font-bold" style="margin-bottom:6px">Student Answer:</p>
      <div style="background:white; border:1px solid #eee; padding:15px; border-radius:6px; margin-bottom:15px; min-height:60px; white-space:pre-wrap">{e['answer'] or '<em class="text-muted">No answer provided.</em>'}</div>
      
      <div style="display:flex; gap:12px; align-items:center; background:#fff9f0; padding:15px; border-radius:8px">
        <div style="flex: 0 0 120px">
            <label class="text-xs font-bold uppercase">Points (Max {e['max_points']})</label>
            <input type="number" id="pts_{e['answer_id']}" class="form-input" placeholder="0" 
                   value="{e['points_given'] if e['points_given'] is not None else ''}" 
                   max="{e['max_points']}" step="0.5">
        </div>
        <div class="flex-1">
            <label class="text-xs font-bold uppercase">Teacher Feedback</label>
            <input type="text" id="fb_{e['answer_id']}" class="form-input" 
                   placeholder="Well explained, but missing key details..." 
                   value="{e['feedback'] or ''}">
        </div>
        <div style="align-self: flex-end">
            <button class="btn btn-primary" onclick="saveReview({e['answer_id']}, {e['max_points']})">Submit Grade</button>
        </div>
      </div>
    </div>"""
        for e in essays
    )

    html = sidebar("teacher", "essays") + f"""
    <div class="topbar">
        <div>
            <div class="page-title">Essay Grading Queue</div>
            <div class="page-sub">Read and provide feedback for essay-type questions</div>
        </div>
    </div>
    
    <div class="alert-zone"></div>
    
    <div style="max-width:900px; margin: 0 auto">
        {cards or '''
        <div class="empty-state">
            <div class="empty-icon">🎉</div>
            <p>All caught up! No pending essays to grade.</p>
        </div>'''}
    </div>
  </main></div>

<script>
function saveReview(id, maxPts) {{
    const ptsInput = document.getElementById('pts_'+id);
    const pts = parseFloat(ptsInput.value);
    const fb = document.getElementById('fb_'+id).value;
    
    if(isNaN(pts)) return showAlert('Please enter a numeric score.');
    if(pts < 0) return showAlert('Points cannot be negative.');
    if(pts > maxPts) return showAlert('Points cannot exceed the maximum of ' + maxPts);

    fetch('/api/teacher/essays/' + id, {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ points: pts, feedback: fb }})
    }})
    .then(r => r.json())
    .then(d => {{
        if(d.success) {{
            showAlert('Grade submitted successfully!', 'success');
            // Optional: Subtle UI update instead of reload
            setTimeout(() => location.reload(), 800);
        }} else {{
            showAlert(d.error);
        }}
    }});
}}
</script>"""
    return render(html, "Essay Reviews")
# FIX PARA SA SCREENSHOT: teacher/results
@teacher_bp.route("/teacher/results")
@login_required
@role_required("teacher")
def teacher_results():
    db = get_db()
    tid = session.get("user_id")
    
    # Query updated to include submission counts for better context
    exams = db.execute("""
        SELECT e.*, c.course_name,
               (SELECT COUNT(*) FROM results r WHERE r.exam_id=e.id) AS submissions
        FROM exams e 
        JOIN courses c ON e.course_id=c.id 
        WHERE e.teacher_id=? 
        ORDER BY e.id DESC""", (tid,)).fetchall()
    db.close()

    # Generating stylized links for each exam
    links = "".join(f"""
        <a href="/teacher/exams/{e['id']}/results" class="stat-card" 
           style="display:flex; justify-content:space-between; align-items:center; text-decoration:none; color:inherit; margin-bottom:12px; padding:20px; border:1px solid #eee">
            <div>
                <div style="font-weight:700; font-size:1.1rem; color:var(--dark)">{e['title']}</div>
                <div style="font-size:0.85rem; color:#666">{e['course_name']}</div>
            </div>
            <div style="text-align:right">
                <div class="stat-value" style="font-size:1.2rem">{e['submissions']}</div>
                <div class="stat-label" style="font-size:0.7rem; text-transform:uppercase">Submissions</div>
            </div>
        </a>""" for e in exams)

    html = sidebar("teacher", "results") + f"""
    <div class="topbar">
        <div>
            <div class="page-title">Overall Results</div>
            <div class="page-sub">Select an exam to view detailed student scores and analytics</div>
        </div>
    </div>
    
    <div class="card">
        <div class="card-header">
            <h3 class="card-title">My Exams</h3>
        </div>
        <div style="margin-top:20px">
            {links or '''
            <div class="empty-state">
                <div class="empty-icon">📊</div>
                <p>No exams created yet. <a href="/teacher/exams/create" style="color:var(--red)">Create one now</a> to see results.</p>
            </div>'''}
        </div>
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

    # Validation
    if not title: 
        return jsonify({"success": False, "error": "Exam title is required."})
    if not questions: 
        return jsonify({"success": False, "error": "At least one question is required."})

    db = get_db()
    try:
        if eid:
            # Update existing exam (Security: ensure current teacher owns it)
            db.execute("""
                UPDATE exams 
                SET course_id=?, title=?, timer_minutes=?, passing_score=? 
                WHERE id=? AND teacher_id=?""",
                (course_id, title, timer, passing, eid, session["user_id"]))
            
            # Wipe old questions to replace with the new state from the frontend
            db.execute("DELETE FROM questions WHERE exam_id=?", (eid,))
        else:
            # Create new exam record
            cur = db.execute("""
                INSERT INTO exams (course_id, teacher_id, title, timer_minutes, passing_score) 
                VALUES (?, ?, ?, ?, ?)""",
                (course_id, session["user_id"], title, timer, passing))
            eid = cur.lastrowid

        # Insert the updated question list
        for q in questions:
            # Only MCQs need the choices JSON; Essay/Identification use NULL
            choices_json = json.dumps(q.get("choices", [])) if q.get("type") == "mcq" else None
            
            db.execute("""
                INSERT INTO questions (exam_id, question_text, type, choices, correct_answer, points) 
                VALUES (?, ?, ?, ?, ?, ?)""",
                (eid, q["text"], q["type"], choices_json, q.get("correct", ""), q.get("points", 1)))
        
        db.commit()
        return jsonify({"success": True, "exam_id": eid})

    except Exception as e:
        # If anything goes wrong, we don't commit anything to the database
        return jsonify({"success": False, "error": f"Database error: {str(e)}"})
    finally:
        db.close()

@teacher_bp.route("/api/teacher/exams/<int:eid>", methods=["DELETE"])
@login_required
@role_required("teacher")
def api_del_exam(eid):
    db = get_db()
    try:
        # Security Check: Verify the exam exists and belongs to this teacher
        exam = db.execute("SELECT id FROM exams WHERE id=? AND teacher_id=?", 
                          (eid, session["user_id"])).fetchone()
        if not exam: 
            return jsonify({"success": False, "error": "Exam not found or access denied."})

        # Manual Cascade Delete (if foreign key constraints aren't set to ON DELETE CASCADE)
        # 1. Delete essay reviews associated with this exam's answers
        db.execute("""
            DELETE FROM essay_reviews WHERE answer_id IN 
            (SELECT sa.id FROM student_answers sa 
             JOIN questions q ON sa.question_id = q.id 
             WHERE q.exam_id = ?)""", (eid,))
        
        # 2. Delete student answers
        db.execute("DELETE FROM student_answers WHERE question_id IN (SELECT id FROM questions WHERE exam_id=?)", (eid,))
        
        # 3. Delete results and questions
        db.execute("DELETE FROM results WHERE exam_id=?", (eid,))
        db.execute("DELETE FROM questions WHERE exam_id=?", (eid,))
        
        # 4. Finally, delete the exam itself
        db.execute("DELETE FROM exams WHERE id=?", (eid,))
        
        db.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    finally:
        db.close()

@teacher_bp.route("/api/teacher/exams/<int:eid>/export/pdf")
@login_required
@role_required("teacher")
def export_pdf(eid):
    db = get_db()
    try:
        # Check ownership first
        exam = db.execute("""
            SELECT e.*, c.course_name 
            FROM exams e 
            JOIN courses c ON e.course_id=c.id 
            WHERE e.id=? AND e.teacher_id=?""", 
            (eid, session["user_id"])
        ).fetchone()
        
        if not exam:
            return "Exam not found or access denied", 403

        results = db.execute("""
            SELECT r.*, u.name, u.email 
            FROM results r 
            JOIN users u ON r.student_id=u.id 
            WHERE r.exam_id=? 
            ORDER BY r.percentage DESC""", (eid,)).fetchall()
    finally:
        db.close()

    # Create a professional looking HTML table for the 'PDF' (HTML Export)
    rows = "".join(f"""
        <tr>
            <td style="border:1px solid #ddd; padding:8px;">{r['name']}</td>
            <td style="border:1px solid #ddd; padding:8px;">{r['email']}</td>
            <td style="border:1px solid #ddd; padding:8px; text-align:center;">{r['score']:.1f}</td>
            <td style="border:1px solid #ddd; padding:8px; text-align:center;">{r['percentage']:.1f}%</td>
            <td style="border:1px solid #ddd; padding:8px; text-align:center; font-weight:bold; color:{'green' if r['percentage']>=exam['passing_score'] else 'red'};">
                {'Pass' if r['percentage']>=exam['passing_score'] else 'Fail'}
            </td>
        </tr>""" for r in results)

    html = f"""
    <html>
    <head><style>body{{font-family:sans-serif;}} table{{width:100%; border-collapse:collapse;}} th{{background:#f2f2f2;}}</style></head>
    <body>
        <h1 style="color:#333;">{exam['title']}</h1>
        <p><strong>Course:</strong> {exam['course_name']} | <strong>Passing Score:</strong> {exam['passing_score']}%</p>
        <hr>
        <table>
            <thead>
                <tr>
                    <th style="border:1px solid #ddd; padding:8px;">Student Name</th>
                    <th style="border:1px solid #ddd; padding:8px;">Email</th>
                    <th style="border:1px solid #ddd; padding:8px;">Score</th>
                    <th style="border:1px solid #ddd; padding:8px;">%</th>
                    <th style="border:1px solid #ddd; padding:8px;">Status</th>
                </tr>
            </thead>
            <tbody>{rows or '<tr><td colspan="5" style="text-align:center;">No results available.</td></tr>'}</tbody>
        </table>
        <p style="font-size:0.8em; color:gray; margin-top:20px;">Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    </body>
    </html>"""
    
    resp = make_response(html)
    # We name it .html because modern browsers handle HTML-to-PDF printing better than raw HTML-to-PDF libraries in basic setups
    resp.headers["Content-Type"] = "text/html"
    resp.headers["Content-Disposition"] = f'attachment; filename="Report_{eid}.html"'
    return resp

@teacher_bp.route("/api/teacher/exams/<int:eid>/export/excel")
@login_required
@role_required("teacher")
def export_excel(eid):
    db = get_db()
    try:
        # Check ownership first
        exam = db.execute("SELECT passing_score FROM exams WHERE id=? AND teacher_id=?", 
                          (eid, session["user_id"])).fetchone()
        
        if not exam:
            return "Exam not found or access denied", 403

        results = db.execute("""
            SELECT r.*, u.name, u.email 
            FROM results r 
            JOIN users u ON r.student_id=u.id 
            WHERE r.exam_id=? 
            ORDER BY r.percentage DESC""", (eid,)).fetchall()
    finally:
        db.close()

    # CSV Generation with proper headers
    lines = ["Name,Email,Score,Percentage,Status,Date Submitted"]
    for r in results:
        status = "Pass" if r["percentage"] >= exam["passing_score"] else "Fail"
        # Using double quotes for strings to handle any commas in names/emails
        lines.append(f'"{r["name"]}","{r["email"]}",{r["score"]:.1f},{r["percentage"]:.1f}%,{status},"{r["submitted_at"][:16]}"')
    
    csv_output = "\n".join(lines)
    resp = make_response(csv_output)
    resp.headers["Content-Type"] = "text/csv"
    resp.headers["Content-Disposition"] = f'attachment; filename="Results_Exam_{eid}.csv"'
    return resp
