 
from functools import wraps
from flask import session, redirect, url_for, jsonify


# ─────────────────────────────────────────────
#  AUTH DECORATORS
# ─────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login_page"))
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("auth.login_page"))
            if session.get("role") not in roles:
                return jsonify({"error": "Unauthorized"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


# ─────────────────────────────────────────────
#  HTML PAGE RENDERER
# ─────────────────────────────────────────────

def render(html_content: str, title: str = "ExamSys") -> str:
    """Wrap page content in the full HTML shell (fonts, CSS, JS utilities)."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · ExamSys</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,400&display=swap" rel="stylesheet">
<style>
:root{{
  --red:#c0392b;--red-dark:#922b21;--red-light:#e74c3c;
  --bg:#f0f2f5;--sidebar:#1a1a2e;--sidebar-w:240px;
  --card:#fff;--border:#e8e8ec;--text:#1a1a2e;--muted:#6b7280;
  --success:#27ae60;--warning:#f39c12;--info:#2980b9;
  --radius:12px;--shadow:0 2px 16px rgba(0,0,0,.08);
}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'DM Sans',sans-serif;background:var(--bg);color:var(--text);min-height:100vh}}
h1,h2,h3,h4{{font-family:'Syne',sans-serif}}
a{{color:inherit;text-decoration:none}}
button,input,select,textarea{{font-family:inherit}}

/* SIDEBAR */
.layout{{display:flex;min-height:100vh}}
.sidebar{{width:var(--sidebar-w);background:var(--sidebar);position:fixed;top:0;left:0;height:100vh;display:flex;flex-direction:column;z-index:100;transition:.3s}}
.sidebar-logo{{padding:24px 20px 20px;border-bottom:1px solid rgba(255,255,255,.08)}}
.sidebar-logo .brand{{display:flex;align-items:center;gap:10px}}
.sidebar-logo .brand-icon{{width:40px;height:40px;border-radius:8px;overflow:hidden;display:flex;align-items:center;justify-content:center;flex-shrink:0;background:#fff;padding:2px}}
.sidebar-logo .brand-icon img{{width:100%;height:100%;object-fit:contain}}
.sidebar-logo .brand-name{{font-family:'Syne',sans-serif;font-weight:700;font-size:15px;color:#fff;line-height:1.2}}
.sidebar-logo .brand-sub{{font-size:10px;color:rgba(255,255,255,.4);letter-spacing:.5px}}
.sidebar-nav{{flex:1;padding:16px 0;overflow-y:auto}}
.nav-section{{padding:8px 16px 4px;font-size:10px;letter-spacing:1.5px;color:rgba(255,255,255,.3);text-transform:uppercase;font-weight:600}}
.nav-item{{display:flex;align-items:center;gap:12px;padding:10px 20px;color:rgba(255,255,255,.6);font-size:14px;cursor:pointer;transition:.2s;border-left:3px solid transparent}}
.nav-item:hover{{color:#fff;background:rgba(255,255,255,.05)}}
.nav-item.active{{color:#fff;background:rgba(192,57,43,.15);border-left-color:var(--red)}}
.nav-item svg{{width:18px;height:18px;flex-shrink:0}}
.sidebar-footer{{padding:16px 20px;border-top:1px solid rgba(255,255,255,.08)}}
.user-pill{{display:flex;align-items:center;gap:10px}}
.user-avatar{{width:34px;height:34px;background:var(--red);border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:14px;color:#fff;flex-shrink:0}}
.user-info .name{{font-size:13px;font-weight:500;color:#fff}}
.user-info .role{{font-size:11px;color:rgba(255,255,255,.4);text-transform:capitalize}}
.logout-btn{{margin-top:10px;width:100%;padding:8px;background:rgba(192,57,43,.2);border:1px solid rgba(192,57,43,.3);color:var(--red-light);border-radius:8px;cursor:pointer;font-size:13px;transition:.2s}}
.logout-btn:hover{{background:var(--red);color:#fff}}

/* MAIN */
.main{{margin-left:var(--sidebar-w);flex:1;padding:28px;animation:fadeIn .4s ease}}
.topbar{{display:flex;align-items:center;justify-content:space-between;margin-bottom:28px}}
.page-title{{font-size:26px;font-weight:800;color:var(--text)}}
.page-sub{{font-size:14px;color:var(--muted);margin-top:2px}}

/* CARDS */
.card{{background:var(--card);border-radius:var(--radius);box-shadow:var(--shadow);padding:24px}}
.card-header{{display:flex;align-items:center;justify-content:space-between;margin-bottom:20px}}
.card-title{{font-size:16px;font-weight:700}}
.grid{{display:grid;gap:20px}}
.grid-2{{grid-template-columns:repeat(2,1fr)}}
.grid-3{{grid-template-columns:repeat(3,1fr)}}
.grid-4{{grid-template-columns:repeat(4,1fr)}}

/* STAT CARDS */
.stat-card{{background:var(--card);border-radius:var(--radius);padding:20px;box-shadow:var(--shadow);display:flex;align-items:center;gap:16px;animation:slideUp .4s ease both}}
.stat-icon{{width:48px;height:48px;border-radius:10px;display:flex;align-items:center;justify-content:center;flex-shrink:0}}
.stat-icon svg{{width:24px;height:24px;color:#fff}}
.stat-label{{font-size:12px;color:var(--muted);font-weight:500;margin-bottom:4px}}
.stat-value{{font-size:28px;font-weight:800;font-family:'Syne',sans-serif}}

/* FORMS */
.form-group{{margin-bottom:16px}}
.form-label{{display:block;font-size:13px;font-weight:600;color:var(--text);margin-bottom:6px}}
.form-input{{width:100%;padding:10px 14px;border:1.5px solid var(--border);border-radius:8px;font-size:14px;transition:.2s;background:#fff;color:var(--text)}}
.form-input:focus{{outline:none;border-color:var(--red);box-shadow:0 0 0 3px rgba(192,57,43,.1)}}
.form-select{{appearance:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%23666' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 12px center}}
textarea.form-input{{resize:vertical;min-height:80px}}

/* BUTTONS */
.btn{{display:inline-flex;align-items:center;gap:8px;padding:10px 20px;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;border:none;transition:.2s;font-family:inherit}}
.btn-primary{{background:var(--red);color:#fff}}
.btn-primary:hover{{background:var(--red-dark);transform:translateY(-1px)}}
.btn-secondary{{background:#f0f2f5;color:var(--text)}}
.btn-secondary:hover{{background:#e4e6ea}}
.btn-success{{background:var(--success);color:#fff}}
.btn-warning{{background:var(--warning);color:#fff}}
.btn-danger{{background:#e74c3c;color:#fff}}
.btn-danger:hover{{background:#c0392b}}
.btn-sm{{padding:6px 14px;font-size:12px}}
.btn-icon{{padding:8px;border-radius:8px}}

/* TABLE */
.table-wrap{{overflow-x:auto}}
table{{width:100%;border-collapse:collapse;font-size:14px}}
th{{text-align:left;padding:10px 14px;font-size:11px;letter-spacing:.8px;text-transform:uppercase;color:var(--muted);border-bottom:2px solid var(--border);font-weight:700}}
td{{padding:12px 14px;border-bottom:1px solid var(--border);vertical-align:middle}}
tr:hover td{{background:#fafafa}}
.badge{{display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.5px}}
.badge-red{{background:rgba(192,57,43,.12);color:var(--red)}}
.badge-green{{background:rgba(39,174,96,.12);color:var(--success)}}
.badge-blue{{background:rgba(41,128,185,.12);color:var(--info)}}
.badge-orange{{background:rgba(243,156,18,.12);color:var(--warning)}}

/* ALERTS */
.alert{{padding:12px 16px;border-radius:8px;font-size:14px;margin-bottom:16px;display:flex;align-items:center;gap:8px}}
.alert-error{{background:rgba(192,57,43,.08);border:1px solid rgba(192,57,43,.2);color:var(--red)}}
.alert-success{{background:rgba(39,174,96,.08);border:1px solid rgba(39,174,96,.2);color:var(--success)}}
.alert-info{{background:rgba(41,128,185,.08);border:1px solid rgba(41,128,185,.2);color:var(--info)}}

/* AUTH PAGES */
.auth-bg{{min-height:100vh;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#1a1a2e 0%,#2d1a1a 50%,#1a1a2e 100%);padding:20px;position:relative;overflow:hidden}}
.auth-bg::before{{content:'';position:absolute;inset:0;background:radial-gradient(circle at 20% 50%,rgba(192,57,43,.15) 0%,transparent 60%),radial-gradient(circle at 80% 20%,rgba(192,57,43,.1) 0%,transparent 50%);pointer-events:none}}
.auth-card{{background:#fff;border-radius:20px;padding:40px;width:100%;max-width:420px;box-shadow:0 24px 80px rgba(0,0,0,.4);animation:slideUp .5s ease;position:relative}}
.auth-logo{{text-align:center;margin-bottom:28px}}
.auth-logo .logo-icon{{width:80px;height:80px;border-radius:50%;overflow:hidden;display:inline-flex;align-items:center;justify-content:center;margin-bottom:12px;background:#fff;box-shadow:0 4px 16px rgba(192,57,43,.2);padding:4px}}
.auth-logo .logo-icon img{{width:100%;height:100%;object-fit:contain}}
.auth-logo h1{{font-size:22px;font-weight:800;color:var(--text)}}
.auth-logo p{{font-size:13px;color:var(--muted);margin-top:4px}}
.auth-divider{{text-align:center;margin:16px 0;color:var(--muted);font-size:13px;position:relative}}
.auth-divider::before{{content:'';position:absolute;left:0;top:50%;width:42%;height:1px;background:var(--border)}}
.auth-divider::after{{content:'';position:absolute;right:0;top:50%;width:42%;height:1px;background:var(--border)}}

/* MODAL */
.modal-overlay{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:1000;align-items:center;justify-content:center;padding:20px;backdrop-filter:blur(4px)}}
.modal-overlay.open{{display:flex}}
.modal{{background:#fff;border-radius:16px;padding:28px;width:100%;max-width:500px;max-height:90vh;overflow-y:auto;animation:slideUp .3s ease}}
.modal-header{{display:flex;align-items:center;justify-content:space-between;margin-bottom:20px}}
.modal-title{{font-size:18px;font-weight:700}}
.modal-close{{width:32px;height:32px;border-radius:8px;border:none;background:#f0f2f5;cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:18px}}

/* PROGRESS */
.progress{{height:8px;background:var(--border);border-radius:99px;overflow:hidden}}
.progress-bar{{height:100%;background:var(--red);border-radius:99px;transition:width .3s}}

/* TIMER */
.timer-display{{font-family:'Syne',sans-serif;font-size:28px;font-weight:800;color:var(--red);text-align:center;padding:12px;background:rgba(192,57,43,.08);border-radius:10px;margin-bottom:16px}}
.timer-display.warning{{animation:pulse 1s infinite;color:#e74c3c}}

/* MISC */
.empty-state{{text-align:center;padding:48px 20px;color:var(--muted)}}
.empty-icon{{font-size:48px;margin-bottom:12px}}
.flex{{display:flex}}.flex-1{{flex:1}}.items-center{{align-items:center}}.justify-between{{justify-content:space-between}}.gap-8{{gap:8px}}.gap-12{{gap:12px}}.gap-16{{gap:16px}}.mt-8{{margin-top:8px}}.mt-16{{margin-top:16px}}.mt-20{{margin-top:20px}}.mb-16{{margin-bottom:16px}}.text-center{{text-align:center}}.text-sm{{font-size:13px}}.text-muted{{color:var(--muted)}}.font-bold{{font-weight:700}}.w-full{{width:100%}}

/* EXAM TAKING */
.question-card{{background:#fff;border-radius:var(--radius);padding:24px;box-shadow:var(--shadow);margin-bottom:16px}}
.question-num{{font-size:12px;font-weight:700;color:var(--red);text-transform:uppercase;letter-spacing:.8px;margin-bottom:8px}}
.question-text{{font-size:16px;font-weight:500;line-height:1.6;margin-bottom:20px}}
.choice-item{{display:flex;align-items:flex-start;gap:12px;padding:12px 14px;border:1.5px solid var(--border);border-radius:8px;margin-bottom:8px;cursor:pointer;transition:.2s}}
.choice-item:hover{{border-color:var(--red);background:rgba(192,57,43,.04)}}
.choice-item.selected{{border-color:var(--red);background:rgba(192,57,43,.08)}}
.choice-letter{{width:26px;height:26px;border-radius:6px;background:var(--border);display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;flex-shrink:0;transition:.2s}}
.choice-item.selected .choice-letter{{background:var(--red);color:#fff}}

/* QUESTION NAV */
.q-nav{{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px}}
.q-dot{{width:32px;height:32px;border-radius:6px;border:1.5px solid var(--border);display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;cursor:pointer;transition:.2s}}
.q-dot:hover{{border-color:var(--red)}}
.q-dot.answered{{background:var(--red);color:#fff;border-color:var(--red)}}
.q-dot.current{{border-color:var(--red);color:var(--red)}}

/* ANIMATIONS */
@keyframes fadeIn{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes slideUp{{from{{opacity:0;transform:translateY(20px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.6}}}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}

/* RESPONSIVE */
@media(max-width:768px){{
  .sidebar{{transform:translateX(-100%)}}.sidebar.open{{transform:translateX(0)}}
  .main{{margin-left:0;padding:16px}}.grid-2,.grid-3,.grid-4{{grid-template-columns:1fr}}
  .hamburger{{display:flex}}
}}
.hamburger{{display:none;position:fixed;top:16px;left:16px;z-index:200;width:40px;height:40px;background:var(--sidebar);border-radius:8px;align-items:center;justify-content:center;cursor:pointer;border:none;color:#fff;font-size:20px}}
</style>
</head>
<body>
{html_content}
<script>
function logout(){{
  fetch('/api/logout',{{method:'POST'}}).then(()=>location.href='/login');
}}
function openModal(id){{document.getElementById(id).classList.add('open')}}
function closeModal(id){{document.getElementById(id).classList.remove('open')}}
function showAlert(msg,type='error'){{
  const a=document.createElement('div');
  a.className='alert alert-'+type;
  a.innerHTML=`<span>${{msg}}</span>`;
  document.querySelector('.alert-zone')?.prepend(a);
  setTimeout(()=>a.remove(),4000);
}}
const hamburger=document.querySelector('.hamburger');
const sidebar=document.querySelector('.sidebar');
if(hamburger)hamburger.onclick=()=>sidebar.classList.toggle('open');
</script>
</body>
</html>"""


# ─────────────────────────────────────────────
#  SIDEBAR BUILDER
# ─────────────────────────────────────────────

_NAV_ITEMS = {
    "admin": [
        ("dashboard", "Dashboard",
         "M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z",
         "M9 22V12h6v10"),
        ("courses", "Courses",
         "M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253",
         "", ""),
        ("users", "Users",
         "M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2",
         "M23 21v-2a4 4 0 00-3-3.87",
         "M16 3.13a4 4 0 010 7.75",
         "M9 7a4 4 0 100 8 4 4 0 000-8z"),
    ],
    "teacher": [
        ("dashboard", "Dashboard",
         "M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z",
         "M9 22V12h6v10"),
        ("exams", "My Exams",
         "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2",
         "M9 12l2 2 4-4"),
        ("essays", "Review Essays",
         "M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z",
         ""),
        ("results", "Results",
         "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z",
         ""),
    ],
    "student": [
        ("dashboard", "Dashboard",
         "M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z",
         "M9 22V12h6v10"),
        ("exams", "Available Exams",
         "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2",
         ""),
        ("grades", "My Grades",
         "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z",
         ""),
    ],
}

_ROLE_LABELS = {
    "admin": "Administrator",
    "teacher": "Teacher",
    "student": "Student",
}


def sidebar(role: str, active: str = "dashboard") -> str:
    """Build the sidebar + open the .layout / .main wrappers (caller must close them)."""
    name = session.get("name", "User")
    initial = name[0].upper() if name else "U"
    role_label = _ROLE_LABELS.get(role, role)

    items_html = ""
    for item in _NAV_ITEMS.get(role, []):
        key, label = item[0], item[1]
        paths = "".join(
            f'<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="{p}"/>'
            for p in item[2:]
            if p
        )
        is_active = "active" if active == key else ""
        href = f"/{role}/{key if key != 'dashboard' else ''}"
        items_html += f"""
        <a href="{href}" class="nav-item {is_active}">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">{paths}</svg>
          <span>{label}</span>
        </a>"""

    return f"""
<button class="hamburger">☰</button>
<div class="layout">
  <aside class="sidebar">
    <div class="sidebar-logo">
      <div class="brand">
        <div class="brand-icon">
          <img src="/static/images/wmsu_logo.png" alt="WMSU Logo">
        </div>
        <div>
          <div class="brand-name">WMSU ExamSys</div>
          <div class="brand-sub">Examination System</div>
        </div>
      </div>
    </div>
    <nav class="sidebar-nav">
      <div class="nav-section">Menu</div>
      {items_html}
    </nav>
    <div class="sidebar-footer">
      <div class="user-pill">
        <div class="user-avatar">{initial}</div>
        <div class="user-info">
          <div class="name">{name}</div>
          <div class="role">{role_label}</div>
        </div>
      </div>
      <button class="logout-btn" onclick="logout()">Sign Out</button>
    </div>
  </aside>
 
from functools import wraps
from flask import session, redirect, url_for, jsonify


# ─────────────────────────────────────────────
#  AUTH DECORATORS
# ─────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login_page"))
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("auth.login_page"))
            if session.get("role") not in roles:
                return jsonify({"error": "Unauthorized"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


# ─────────────────────────────────────────────
#  HTML PAGE RENDERER
# ─────────────────────────────────────────────

def render(html_content: str, title: str = "ExamSys") -> str:
    """Wrap page content in the full HTML shell (fonts, CSS, JS utilities)."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · ExamSys</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,400&display=swap" rel="stylesheet">
<style>
:root{{
  --red:#c0392b;--red-dark:#922b21;--red-light:#e74c3c;
  --bg:#f0f2f5;--sidebar:#1a1a2e;--sidebar-w:240px;
  --card:#fff;--border:#e8e8ec;--text:#1a1a2e;--muted:#6b7280;
  --success:#27ae60;--warning:#f39c12;--info:#2980b9;
  --radius:12px;--shadow:0 2px 16px rgba(0,0,0,.08);
}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'DM Sans',sans-serif;background:var(--bg);color:var(--text);min-height:100vh}}
h1,h2,h3,h4{{font-family:'Syne',sans-serif}}
a{{color:inherit;text-decoration:none}}
button,input,select,textarea{{font-family:inherit}}

/* SIDEBAR */
.layout{{display:flex;min-height:100vh}}
.sidebar{{width:var(--sidebar-w);background:var(--sidebar);position:fixed;top:0;left:0;height:100vh;display:flex;flex-direction:column;z-index:100;transition:.3s}}
.sidebar-logo{{padding:24px 20px 20px;border-bottom:1px solid rgba(255,255,255,.08)}}
.sidebar-logo .brand{{display:flex;align-items:center;gap:10px}}
.sidebar-logo .brand-icon{{width:40px;height:40px;border-radius:8px;overflow:hidden;display:flex;align-items:center;justify-content:center;flex-shrink:0;background:#fff;padding:2px}}
.sidebar-logo .brand-icon img{{width:100%;height:100%;object-fit:contain}}
.sidebar-logo .brand-name{{font-family:'Syne',sans-serif;font-weight:700;font-size:15px;color:#fff;line-height:1.2}}
.sidebar-logo .brand-sub{{font-size:10px;color:rgba(255,255,255,.4);letter-spacing:.5px}}
.sidebar-nav{{flex:1;padding:16px 0;overflow-y:auto}}
.nav-section{{padding:8px 16px 4px;font-size:10px;letter-spacing:1.5px;color:rgba(255,255,255,.3);text-transform:uppercase;font-weight:600}}
.nav-item{{display:flex;align-items:center;gap:12px;padding:10px 20px;color:rgba(255,255,255,.6);font-size:14px;cursor:pointer;transition:.2s;border-left:3px solid transparent}}
.nav-item:hover{{color:#fff;background:rgba(255,255,255,.05)}}
.nav-item.active{{color:#fff;background:rgba(192,57,43,.15);border-left-color:var(--red)}}
.nav-item svg{{width:18px;height:18px;flex-shrink:0}}
.sidebar-footer{{padding:16px 20px;border-top:1px solid rgba(255,255,255,.08)}}
.user-pill{{display:flex;align-items:center;gap:10px}}
.user-avatar{{width:34px;height:34px;background:var(--red);border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:14px;color:#fff;flex-shrink:0}}
.user-info .name{{font-size:13px;font-weight:500;color:#fff}}
.user-info .role{{font-size:11px;color:rgba(255,255,255,.4);text-transform:capitalize}}
.logout-btn{{margin-top:10px;width:100%;padding:8px;background:rgba(192,57,43,.2);border:1px solid rgba(192,57,43,.3);color:var(--red-light);border-radius:8px;cursor:pointer;font-size:13px;transition:.2s}}
.logout-btn:hover{{background:var(--red);color:#fff}}

/* MAIN */
.main{{margin-left:var(--sidebar-w);flex:1;padding:28px;animation:fadeIn .4s ease}}
.topbar{{display:flex;align-items:center;justify-content:space-between;margin-bottom:28px}}
.page-title{{font-size:26px;font-weight:800;color:var(--text)}}
.page-sub{{font-size:14px;color:var(--muted);margin-top:2px}}

/* CARDS */
.card{{background:var(--card);border-radius:var(--radius);box-shadow:var(--shadow);padding:24px}}
.card-header{{display:flex;align-items:center;justify-content:space-between;margin-bottom:20px}}
.card-title{{font-size:16px;font-weight:700}}
.grid{{display:grid;gap:20px}}
.grid-2{{grid-template-columns:repeat(2,1fr)}}
.grid-3{{grid-template-columns:repeat(3,1fr)}}
.grid-4{{grid-template-columns:repeat(4,1fr)}}

/* STAT CARDS */
.stat-card{{background:var(--card);border-radius:var(--radius);padding:20px;box-shadow:var(--shadow);display:flex;align-items:center;gap:16px;animation:slideUp .4s ease both}}
.stat-icon{{width:48px;height:48px;border-radius:10px;display:flex;align-items:center;justify-content:center;flex-shrink:0}}
.stat-icon svg{{width:24px;height:24px;color:#fff}}
.stat-label{{font-size:12px;color:var(--muted);font-weight:500;margin-bottom:4px}}
.stat-value{{font-size:28px;font-weight:800;font-family:'Syne',sans-serif}}

/* FORMS */
.form-group{{margin-bottom:16px}}
.form-label{{display:block;font-size:13px;font-weight:600;color:var(--text);margin-bottom:6px}}
.form-input{{width:100%;padding:10px 14px;border:1.5px solid var(--border);border-radius:8px;font-size:14px;transition:.2s;background:#fff;color:var(--text)}}
.form-input:focus{{outline:none;border-color:var(--red);box-shadow:0 0 0 3px rgba(192,57,43,.1)}}
.form-select{{appearance:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%23666' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 12px center}}
textarea.form-input{{resize:vertical;min-height:80px}}

/* BUTTONS */
.btn{{display:inline-flex;align-items:center;gap:8px;padding:10px 20px;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;border:none;transition:.2s;font-family:inherit}}
.btn-primary{{background:var(--red);color:#fff}}
.btn-primary:hover{{background:var(--red-dark);transform:translateY(-1px)}}
.btn-secondary{{background:#f0f2f5;color:var(--text)}}
.btn-secondary:hover{{background:#e4e6ea}}
.btn-success{{background:var(--success);color:#fff}}
.btn-warning{{background:var(--warning);color:#fff}}
.btn-danger{{background:#e74c3c;color:#fff}}
.btn-danger:hover{{background:#c0392b}}
.btn-sm{{padding:6px 14px;font-size:12px}}
.btn-icon{{padding:8px;border-radius:8px}}

/* TABLE */
.table-wrap{{overflow-x:auto}}
table{{width:100%;border-collapse:collapse;font-size:14px}}
th{{text-align:left;padding:10px 14px;font-size:11px;letter-spacing:.8px;text-transform:uppercase;color:var(--muted);border-bottom:2px solid var(--border);font-weight:700}}
td{{padding:12px 14px;border-bottom:1px solid var(--border);vertical-align:middle}}
tr:hover td{{background:#fafafa}}
.badge{{display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.5px}}
.badge-red{{background:rgba(192,57,43,.12);color:var(--red)}}
.badge-green{{background:rgba(39,174,96,.12);color:var(--success)}}
.badge-blue{{background:rgba(41,128,185,.12);color:var(--info)}}
.badge-orange{{background:rgba(243,156,18,.12);color:var(--warning)}}

/* ALERTS */
.alert{{padding:12px 16px;border-radius:8px;font-size:14px;margin-bottom:16px;display:flex;align-items:center;gap:8px}}
.alert-error{{background:rgba(192,57,43,.08);border:1px solid rgba(192,57,43,.2);color:var(--red)}}
.alert-success{{background:rgba(39,174,96,.08);border:1px solid rgba(39,174,96,.2);color:var(--success)}}
.alert-info{{background:rgba(41,128,185,.08);border:1px solid rgba(41,128,185,.2);color:var(--info)}}

/* AUTH PAGES */
.auth-bg{{min-height:100vh;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#1a1a2e 0%,#2d1a1a 50%,#1a1a2e 100%);padding:20px;position:relative;overflow:hidden}}
.auth-bg::before{{content:'';position:absolute;inset:0;background:radial-gradient(circle at 20% 50%,rgba(192,57,43,.15) 0%,transparent 60%),radial-gradient(circle at 80% 20%,rgba(192,57,43,.1) 0%,transparent 50%);pointer-events:none}}
.auth-card{{background:#fff;border-radius:20px;padding:40px;width:100%;max-width:420px;box-shadow:0 24px 80px rgba(0,0,0,.4);animation:slideUp .5s ease;position:relative}}
.auth-logo{{text-align:center;margin-bottom:28px}}
.auth-logo .logo-icon{{width:80px;height:80px;border-radius:50%;overflow:hidden;display:inline-flex;align-items:center;justify-content:center;margin-bottom:12px;background:#fff;box-shadow:0 4px 16px rgba(192,57,43,.2);padding:4px}}
.auth-logo .logo-icon img{{width:100%;height:100%;object-fit:contain}}
.auth-logo h1{{font-size:22px;font-weight:800;color:var(--text)}}
.auth-logo p{{font-size:13px;color:var(--muted);margin-top:4px}}
.auth-divider{{text-align:center;margin:16px 0;color:var(--muted);font-size:13px;position:relative}}
.auth-divider::before{{content:'';position:absolute;left:0;top:50%;width:42%;height:1px;background:var(--border)}}
.auth-divider::after{{content:'';position:absolute;right:0;top:50%;width:42%;height:1px;background:var(--border)}}

/* MODAL */
.modal-overlay{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:1000;align-items:center;justify-content:center;padding:20px;backdrop-filter:blur(4px)}}
.modal-overlay.open{{display:flex}}
.modal{{background:#fff;border-radius:16px;padding:28px;width:100%;max-width:500px;max-height:90vh;overflow-y:auto;animation:slideUp .3s ease}}
.modal-header{{display:flex;align-items:center;justify-content:space-between;margin-bottom:20px}}
.modal-title{{font-size:18px;font-weight:700}}
.modal-close{{width:32px;height:32px;border-radius:8px;border:none;background:#f0f2f5;cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:18px}}

/* PROGRESS */
.progress{{height:8px;background:var(--border);border-radius:99px;overflow:hidden}}
.progress-bar{{height:100%;background:var(--red);border-radius:99px;transition:width .3s}}

/* TIMER */
.timer-display{{font-family:'Syne',sans-serif;font-size:28px;font-weight:800;color:var(--red);text-align:center;padding:12px;background:rgba(192,57,43,.08);border-radius:10px;margin-bottom:16px}}
.timer-display.warning{{animation:pulse 1s infinite;color:#e74c3c}}

/* MISC */
.empty-state{{text-align:center;padding:48px 20px;color:var(--muted)}}
.empty-icon{{font-size:48px;margin-bottom:12px}}
.flex{{display:flex}}.flex-1{{flex:1}}.items-center{{align-items:center}}.justify-between{{justify-content:space-between}}.gap-8{{gap:8px}}.gap-12{{gap:12px}}.gap-16{{gap:16px}}.mt-8{{margin-top:8px}}.mt-16{{margin-top:16px}}.mt-20{{margin-top:20px}}.mb-16{{margin-bottom:16px}}.text-center{{text-align:center}}.text-sm{{font-size:13px}}.text-muted{{color:var(--muted)}}.font-bold{{font-weight:700}}.w-full{{width:100%}}

/* EXAM TAKING */
.question-card{{background:#fff;border-radius:var(--radius);padding:24px;box-shadow:var(--shadow);margin-bottom:16px}}
.question-num{{font-size:12px;font-weight:700;color:var(--red);text-transform:uppercase;letter-spacing:.8px;margin-bottom:8px}}
.question-text{{font-size:16px;font-weight:500;line-height:1.6;margin-bottom:20px}}
.choice-item{{display:flex;align-items:flex-start;gap:12px;padding:12px 14px;border:1.5px solid var(--border);border-radius:8px;margin-bottom:8px;cursor:pointer;transition:.2s}}
.choice-item:hover{{border-color:var(--red);background:rgba(192,57,43,.04)}}
.choice-item.selected{{border-color:var(--red);background:rgba(192,57,43,.08)}}
.choice-letter{{width:26px;height:26px;border-radius:6px;background:var(--border);display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;flex-shrink:0;transition:.2s}}
.choice-item.selected .choice-letter{{background:var(--red);color:#fff}}

/* QUESTION NAV */
.q-nav{{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px}}
.q-dot{{width:32px;height:32px;border-radius:6px;border:1.5px solid var(--border);display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;cursor:pointer;transition:.2s}}
.q-dot:hover{{border-color:var(--red)}}
.q-dot.answered{{background:var(--red);color:#fff;border-color:var(--red)}}
.q-dot.current{{border-color:var(--red);color:var(--red)}}

/* ANIMATIONS */
@keyframes fadeIn{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes slideUp{{from{{opacity:0;transform:translateY(20px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.6}}}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}

/* RESPONSIVE */
@media(max-width:768px){{
  .sidebar{{transform:translateX(-100%)}}.sidebar.open{{transform:translateX(0)}}
  .main{{margin-left:0;padding:16px}}.grid-2,.grid-3,.grid-4{{grid-template-columns:1fr}}
  .hamburger{{display:flex}}
}}
.hamburger{{display:none;position:fixed;top:16px;left:16px;z-index:200;width:40px;height:40px;background:var(--sidebar);border-radius:8px;align-items:center;justify-content:center;cursor:pointer;border:none;color:#fff;font-size:20px}}
</style>
</head>
<body>
{html_content}
<script>
function logout(){{
  fetch('/api/logout',{{method:'POST'}}).then(()=>location.href='/login');
}}
function openModal(id){{document.getElementById(id).classList.add('open')}}
function closeModal(id){{document.getElementById(id).classList.remove('open')}}
function showAlert(msg,type='error'){{
  const a=document.createElement('div');
  a.className='alert alert-'+type;
  a.innerHTML=`<span>${{msg}}</span>`;
  document.querySelector('.alert-zone')?.prepend(a);
  setTimeout(()=>a.remove(),4000);
}}
const hamburger=document.querySelector('.hamburger');
const sidebar=document.querySelector('.sidebar');
if(hamburger)hamburger.onclick=()=>sidebar.classList.toggle('open');
</script>
</body>
</html>"""


# ─────────────────────────────────────────────
#  SIDEBAR BUILDER
# ─────────────────────────────────────────────

_NAV_ITEMS = {
    "admin": [
        ("dashboard", "Dashboard",
         "M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z",
         "M9 22V12h6v10"),
        ("courses", "Courses",
         "M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253",
         "", ""),
        ("users", "Users",
         "M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2",
         "M23 21v-2a4 4 0 00-3-3.87",
         "M16 3.13a4 4 0 010 7.75",
         "M9 7a4 4 0 100 8 4 4 0 000-8z"),
    ],
    "teacher": [
        ("dashboard", "Dashboard",
         "M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z",
         "M9 22V12h6v10"),
        ("exams", "My Exams",
         "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2",
         "M9 12l2 2 4-4"),
        ("essays", "Review Essays",
         "M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z",
         ""),
        ("results", "Results",
         "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z",
         ""),
    ],
    "student": [
        ("dashboard", "Dashboard",
         "M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z",
         "M9 22V12h6v10"),
        ("exams", "Available Exams",
         "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2",
         ""),
        ("grades", "My Grades",
         "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z",
         ""),
    ],
}

_ROLE_LABELS = {
    "admin": "Administrator",
    "teacher": "Teacher",
    "student": "Student",
}


def sidebar(role: str, active: str = "dashboard") -> str:
    """Build the sidebar + open the .layout / .main wrappers (caller must close them)."""
    name = session.get("name", "User")
    initial = name[0].upper() if name else "U"
    role_label = _ROLE_LABELS.get(role, role)

    items_html = ""
    for item in _NAV_ITEMS.get(role, []):
        key, label = item[0], item[1]
        paths = "".join(
            f'<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="{p}"/>'
            for p in item[2:]
            if p
        )
        is_active = "active" if active == key else ""
        href = f"/{role}/{key if key != 'dashboard' else ''}"
        items_html += f"""
        <a href="{href}" class="nav-item {is_active}">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">{paths}</svg>
          <span>{label}</span>
        </a>"""

    return f"""
<button class="hamburger">☰</button>
<div class="layout">
  <aside class="sidebar">
    <div class="sidebar-logo">
      <div class="brand">
        <div class="brand-icon">
          <img src="/static/images/wmsu_logo.png" alt="WMSU Logo">
        </div>
        <div>
          <div class="brand-name">WMSU ExamSys</div>
          <div class="brand-sub">Examination System</div>
        </div>
      </div>
    </div>
    <nav class="sidebar-nav">
      <div class="nav-section">Menu</div>
      {items_html}
    </nav>
    <div class="sidebar-footer">
      <div class="user-pill">
        <div class="user-avatar">{initial}</div>
        <div class="user-info">
          <div class="name">{name}</div>
          <div class="role">{role_label}</div>
        </div>
      </div>
      <button class="logout-btn" onclick="logout()">Sign Out</button>
    </div>
  </aside>
 
  <main class="main">"""
