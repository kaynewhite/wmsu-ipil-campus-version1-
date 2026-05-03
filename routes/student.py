import json
import random as rnd
from flask import Blueprint, request, session, redirect, url_for, jsonify

from database import get_db
from helpers import render, sidebar
from auth_utils import login_required, role_required

student_bp = Blueprint("student", __name__)

# ─────────────────────────────────────────────
# PAGE ROUTES
# ─────────────────────────────────────────────

@student_bp.route("/student")
@student_bp.route("/student/")
@login_required
@role_required("student")
def student_dashboard():
    db = get_db()
    sid = session["user_id"]

    # Get IDs of exams already taken
    taken_ids = [r["exam_id"] for r in db.execute(
        "SELECT exam_id FROM results WHERE student_id=?", (sid,)).fetchall()]

    # Fetch available exams not yet taken
    available = db.execute(
        """SELECT e.*, c.course_name FROM exams e
           JOIN courses c ON e.course_id=c.id
           WHERE e.id NOT IN ({}) AND e.is_active=1
           ORDER BY e.id DESC""".format(
            ",".join(str(i) for i in taken_ids) if taken_ids else "0"
        )
    ).fetchall()

    # Fetch student's grade history
    grades = db.execute(
        """SELECT r.*, e.title, e.passing_score, c.course_name
           FROM results r
           JOIN exams e ON r.exam_id=e.id
           JOIN courses c ON e.course_id=c.id
           WHERE r.student_id=? ORDER BY r.id DESC""",
        (sid,),
    ).fetchall()
    db.close()

    avail_cards = "".join(
        f"""<div class="card" style="margin-bottom:12px">
      <div class="flex justify-between items-center">
        <div><div class="font-bold">{e['title']}</div>
             <div class="text-sm text-muted">{e['course_name']} · {e['timer_minutes']} min</div></div>
        <a href="/student/exam/{e['id']}" class="btn btn-primary btn-sm">Take Exam</a>
      </div></div>"""
        for e in available
    )

    grade_rows = "".join(
        f"""<tr><td>{g['title']}</td><td>{g['course_name']}</td>
      <td>{g['score']:.1f}</td><td>{g['percentage']:.1f}%</td>
      <td><span class="badge {'badge-green' if g['percentage']>=g['passing_score'] else 'badge-red'}">
        {'Pass' if g['percentage']>=g['passing_score'] else 'Fail'}</span></td></tr>"""
        for g in grades
    )

    html = sidebar("student", "dashboard") + f"""
    <div class="topbar"><div><div class="page-title">My Dashboard</div><div class="page-sub">Welcome, {session.get('name')}</div></div></div>
    <div class="grid grid-2">
      <div>
        <h3 style="margin-bottom:12px;font-family:'Syne',sans-serif">Available Exams ({len(available)})</h3>
        {avail_cards or '<div class="card"><div class="empty-state"><div class="empty-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 3H5a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2V9l-6-6z"/><path d="M9 3v6h6"/><path d="M9 13h6"/><path d="M9 17h6"/></svg></div><p>No new exams available</p></div></div>'}
      </div>
      <div class="card">
        <h3 class="card-title" style="margin-bottom:16px">Grade History</h3>
        <div class="table-wrap">
          <table><thead><tr><th>Exam</th><th>Course</th><th>Score</th><th>%</th><th>Status</th></tr></thead>
          <tbody>{grade_rows or '<tr><td colspan="5"><div class="empty-state"><div class="empty-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19h16"/><path d="M7 15v4"/><path d="M12 11v8"/><path d="M17 7v12"/></svg></div><p>No grades yet</p></div></td></tr>'}</tbody></table>
        </div>
      </div>
    </div>
  </main></div>"""
    return render(html, "Dashboard")


@student_bp.route("/student/exams")
@student_bp.route("/student/exams/")
@login_required
@role_required("student")
def student_exams():
    db = get_db()
    sid = session["user_id"]

    taken_ids = [r["exam_id"] for r in db.execute(
        "SELECT exam_id FROM results WHERE student_id=?", (sid,)).fetchall()]

    available = db.execute(
        """SELECT e.*, c.course_name FROM exams e
           JOIN courses c ON e.course_id=c.id
           WHERE e.id NOT IN ({}) AND e.is_active=1
           ORDER BY e.id DESC""".format(
            ",".join(str(i) for i in taken_ids) if taken_ids else "0"
        )
    ).fetchall()
    db.close()

    avail_cards = "".join(
        f"""<div class=\"card\" style=\"margin-bottom:12px\">\n      <div class=\"flex justify-between items-center\">\n        <div><div class=\"font-bold\">{e['title']}</div>\n             <div class=\"text-sm text-muted\">{e['course_name']} · {e['timer_minutes']} min</div></div>\n        <a href=\"/student/exam/{e['id']}\" class=\"btn btn-primary btn-sm\">Take Exam</a>\n      </div></div>"""
        for e in available
    )

    html = sidebar("student", "exams") + f"""
    <div class=\"topbar\"><div><div class=\"page-title\">Available Exams</div><div class=\"page-sub\">Find the next exam to take</div></div></div>
    <div class="card">{avail_cards or '<div class="empty-state"><div class="empty-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 3H5a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2V9l-6-6z"/><path d="M9 3v6h6"/><path d="M9 13h6"/><path d="M9 17h6"/></svg></div><p>No new exams available</p></div>'}</div>
  </main></div>"""
    return render(html, "Available Exams")


@student_bp.route("/student/grades")
@login_required
@role_required("student")
def student_grades():
    db = get_db()
    grades = db.execute(
        """SELECT r.*, e.title, e.passing_score, c.course_name
           FROM results r
           JOIN exams e ON r.exam_id=e.id
           JOIN courses c ON e.course_id=c.id
           WHERE r.student_id=? ORDER BY r.id DESC""",
        (session["user_id"],),
    ).fetchall()
    db.close()

    avg = sum(g["percentage"] for g in grades) / len(grades) if grades else 0
    rows = "".join(
        f"""<tr><td>{g['title']}</td><td>{g['course_name']}</td>
      <td>{g['score']:.1f}</td><td>{g['percentage']:.1f}%</td>
      <td><span class="badge {'badge-green' if g['percentage']>=g['passing_score'] else 'badge-red'}">
        {'Pass' if g['percentage']>=g['passing_score'] else 'Fail'}</span></td>
      <td>{g['submitted_at'][:16]}</td></tr>"""
        for g in grades
    )

    html = sidebar("student", "grades") + f"""
    <div class="topbar"><div><div class="page-title">My Grades</div><div class="page-sub">Overall Average: {avg:.1f}%</div></div></div>
    <div class="card"><div class="table-wrap">
      <table><thead><tr><th>Exam</th><th>Course</th><th>Score</th><th>Percentage</th><th>Status</th><th>Date</th></tr></thead>
      <tbody>{rows or '<tr><td colspan="6"><div class="empty-state"><div class="empty-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19h16"/><path d="M7 15v4"/><path d="M12 11v8"/><path d="M17 7v12"/></svg></div><p>No grades yet</p></div></td></tr>'}</tbody></table>
    </div></div>
  </main></div>"""
    return render(html, "My Grades")


@student_bp.route("/student/exam/<int:eid>")
@login_required
@role_required("student")
def student_take_exam(eid):
    db = get_db()
    sid = session["user_id"]

    # Prevention: Already taken
    already = db.execute("SELECT id FROM results WHERE student_id=? AND exam_id=?", (sid, eid)).fetchone()
    if already:
        db.close()
        return render(sidebar("student", "exams") + """
            <div class="card text-center" style="margin:40px auto;max-width:400px">
              <div class="empty-icon" style="font-size:64px"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="11" width="16" height="9" rx="2"/><path d="M8 11V7a4 4 0 018 0v4"/></svg></div>
              <h2 style="margin:16px 0 8px">Already Submitted</h2>
              <p class="text-muted">You have already taken this exam. Only one attempt is allowed.</p>
              <a href="/student" class="btn btn-primary" style="margin-top:20px">Back to Dashboard</a>
            </div>
            </main></div>""", "Exam")

    exam = db.execute("SELECT * FROM exams WHERE id=? AND is_active=1", (eid,)).fetchone()
    if not exam:
        db.close()
        return "Exam not found", 404

    questions = db.execute("SELECT * FROM questions WHERE exam_id=?", (eid,)).fetchall()
    q_list = [dict(q) for q in questions]
    rnd.shuffle(q_list) # Randomize question order for students
    db.close()

    q_json = json.dumps(q_list)

    html = sidebar("student", "exams") + f"""
    <div class="topbar">
      <div><div class="page-title">{exam['title']}</div><div class="page-sub">{exam['timer_minutes']} minutes · {len(q_list)} questions</div></div>
      <div class="timer-display" id="timerDisplay">--:--</div>
    </div>
    <div class="grid grid-2" style="align-items:start">
      <div id="question-area"></div>
      <div>
        <div class="card" style="margin-bottom:16px">
          <h4 style="margin-bottom:12px;font-family:'Syne',sans-serif">Question Navigator</h4>
          <div class="q-nav" id="q-nav"></div>
          <div class="progress mt-8"><div class="progress-bar" id="q-progress" style="width:0%"></div></div>
          <p class="text-sm text-muted mt-8"><span id="answered-count">0</span>/{len(q_list)} answered</p>
        </div>
        <button class="btn btn-primary w-full" onclick="submitExam()" style="margin-bottom:10px">Submit Exam</button>
      </div>
    </div>
  </main></div>
<script>
const EXAM_ID={eid}, TIMER_MINS={exam['timer_minutes']};
const QUESTIONS={q_json};
let answers={{}}, currentQ=0;
let timerEnd=Date.now()+TIMER_MINS*60*1000;

function renderQuestion(){{
  const q=QUESTIONS[currentQ];
  const letters='ABCDEFGH';
  let body='';
  if(q.type==='mcq'){{
    const choices=JSON.parse(q.choices||'[]');
    body=choices.map((c,i)=>`
      <div class="choice-item ${{answers[q.id]===letters[i]?'selected':''}}" onclick="selectAnswer('${{q.id}}','${{letters[i]}}')">
        <div class="choice-letter">${{letters[i]}}</div><div>${{c}}</div>
      </div>`).join('');
  }}else if(q.type==='tf'){{
    body=['True','False'].map(v=>`
      <div class="choice-item ${{answers[q.id]===v?'selected':''}}" onclick="selectAnswer('${{q.id}}','${{v}}')">
        <div class="choice-letter">${{v[0]}}</div><div>${{v}}</div>
      </div>`).join('');
  }}else if(q.type==='identification'){{
    body=`<input class="form-input" placeholder="Your answer" value="${{answers[q.id]||''}}" oninput="answers[q.id]=this.value">`;
  }}
  document.getElementById('question-area').innerHTML=`
    <div class="question-card">
      <div class="question-num">Question ${{currentQ+1}} of ${{QUESTIONS.length}}</div>
      <div class="question-text">${{q.question_text}}</div>
      ${{body}}
      <div style="display:flex;justify-content:space-between;margin-top:20px">
        ${{currentQ>0?'<button class="btn btn-secondary" onclick="goQ(currentQ-1)">← Previous</button>':'<span></span>'}}
        ${{currentQ<QUESTIONS.length-1?'<button class="btn btn-primary" onclick="goQ(currentQ+1)">Next →</button>':'<button class="btn btn-success" onclick="submitExam()">Submit Exam</button>'}}
      </div>
    </div>`;
  renderNav();
}}
function selectAnswer(qid,val){{ answers[qid]=val; renderQuestion(); }}
function goQ(i){{ currentQ=i; renderQuestion(); }}
function renderNav(){{
  const nav=document.getElementById('q-nav');
  nav.innerHTML=QUESTIONS.map((q,i)=>`<div class="q-dot ${{i===currentQ?'current':''}} ${{answers[q.id]!==undefined?'answered':''}}" onclick="goQ(${{i}})">${{i+1}}</div>`).join('');
  const answered=Object.keys(answers).length;
  document.getElementById('answered-count').textContent=answered;
  document.getElementById('q-progress').style.width=(answered/QUESTIONS.length*100)+'%';
}}
function updateTimer(){{
  const left=Math.max(0,timerEnd-Date.now());
  const m=Math.floor(left/60000),s=Math.floor((left%60000)/1000);
  document.getElementById('timerDisplay').textContent=String(m).padStart(2,'0')+':'+String(s).padStart(2,'0');
  if(left===0)submitExam();
}}
function submitExam(){{
  if(!confirm('Submit exam now?'))return;
  fetch('/api/student/submit',{{method:'POST',headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify({{exam_id:EXAM_ID,answers}})}})
  .then(r=>r.json()).then(d=>{{
    if(d.success){{
      alert('Exam submitted successfully!');
      location.href='/student';
    }}else alert('Error: '+(d.error||'Submission failed'));
  }});
}}
renderQuestion();
setInterval(updateTimer,1000);
</script>"""
    return render(html, "Take Exam")


# ─────────────────────────────────────────────
# API ROUTES
# ─────────────────────────────────────────────

@student_bp.route("/api/student/submit", methods=["POST"])
@login_required
@role_required("student")
def api_submit_exam():
    data = request.json
    exam_id = data.get("exam_id")
    answers = data.get("answers", {})
    sid = session["user_id"]

    db = get_db()
    try:
        # Check duplicate submission
        if db.execute("SELECT id FROM results WHERE student_id=? AND exam_id=?", (sid, exam_id)).fetchone():
            return jsonify({"error": "You have already submitted this exam."})

        exam = db.execute("SELECT * FROM exams WHERE id=?", (exam_id,)).fetchone()
        questions = db.execute("SELECT * FROM questions WHERE exam_id=?", (exam_id,)).fetchall()
        
        score = 0
        total_points = sum(q["points"] for q in questions)

        for q in questions:
            qid = str(q["id"])
            ans = answers.get(qid, "")
            is_correct = 0
            
            if q["type"] in ["mcq", "tf", "identification"]:
                if (q["correct_answer"] or "").strip().lower() == (ans or "").strip().lower():
                    score += q["points"]
                    is_correct = 1
            
            db.execute(
                "INSERT INTO student_answers (student_id, exam_id, question_id, answer, is_correct) VALUES (?,?,?,?,?)",
                (sid, exam_id, q["id"], ans, is_correct),
            )

        pct = (score / total_points * 100) if total_points > 0 else 0
        db.execute(
            "INSERT INTO results (student_id, exam_id, score, percentage) VALUES (?,?,?,?)",
            (sid, exam_id, score, pct),
        )
        db.commit()
        return jsonify({"success": True, "score": score, "percentage": pct})
    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        db.close()
