from functools import wraps
from flask import session, redirect, url_for, jsonify

# ─────────────────────────────────────────────
#  AUTH DECORATORS
# ─────────────────────────────────────────────

def login_required(f):
    """Ensures the user is authenticated before accessing the route."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login_page"))
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    """Ensures the user is logged in AND has one of the allowed roles."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # 1. Check if logged in
            if "user_id" not in session:
                return redirect(url_for("auth.login_page"))
            
            # 2. Check if role matches
            user_role = session.get("role")
            if not user_role or user_role not in roles:
                # Return JSON for API calls or a 403 error for page loads
                return jsonify({"status": "error", "message": "Access Denied: Unauthorized role"}), 403
                
            return f(*args, **kwargs)
        return decorated
    return decorator


def render(html_content: str, title: str = "ExamSys") -> str:
    """Wrap page content in the full HTML shell (fonts, CSS, JS utilities)."""
    
    # Note: Using '|' instead of '·' to prevent encoding SyntaxErrors in some environments
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>{title} | ExamSys</title>
    
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,400&display=swap" rel="stylesheet">
    
    <style>
        :root {{
            --red: #c0392b; --red-dark: #922b21; --red-light: #e74c3c;
            --bg: #f0f2f5; --sidebar: #1a1a2e; --sidebar-w: 240px;
            --card: #fff; --border: #e8e8ec; --text: #1a1a2e; --muted: #6b7280;
            --success: #27ae60; --warning: #f39c12; --info: #2980b9;
            --radius: 12px; --shadow: 0 2px 16px rgba(0,0,0,.08);
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'DM Sans', sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; overflow-x: hidden; }}
        h1, h2, h3, h4 {{ font-family: 'Syne', sans-serif; }}
        a {{ color: inherit; text-decoration: none; }}
        button, input, select, textarea {{ font-family: inherit; }}

        /* SIDEBAR & LAYOUT */
        .layout {{ display: flex; min-height: 100vh; }}
        .sidebar {{ width: var(--sidebar-w); background: var(--sidebar); position: fixed; top: 0; left: 0; height: 100vh; display: flex; flex-direction: column; z-index: 100; transition: .3s; }}
        .sidebar-logo {{ padding: 24px 20px 20px; border-bottom: 1px solid rgba(255,255,255,.08); }}
        .sidebar-logo .brand {{ display: flex; align-items: center; gap: 10px; }}
        .sidebar-logo .brand-icon {{ width: 40px; height: 40px; border-radius: 8px; overflow: hidden; display: flex; align-items: center; justify-content: center; flex-shrink: 0; background: #fff; padding: 2px; }}
        .sidebar-logo .brand-icon img {{ width: 100%; height: 100%; object-fit: contain; }}
        .sidebar-logo .brand-name {{ font-family: 'Syne', sans-serif; font-weight: 700; font-size: 15px; color: #fff; line-height: 1.2; }}
        .sidebar-logo .brand-sub {{ font-size: 10px; color: rgba(255,255,255,.4); letter-spacing: .5px; }}
        
        .sidebar-nav {{ flex: 1; padding: 16px 0; overflow-y: auto; }}
        .nav-section {{ padding: 8px 16px 4px; font-size: 10px; letter-spacing: 1.5px; color: rgba(255,255,255,.3); text-transform: uppercase; font-weight: 600; }}
        .nav-item {{ display: flex; align-items: center; gap: 12px; padding: 10px 20px; color: rgba(255,255,255,.6); font-size: 14px; cursor: pointer; transition: .2s; border-left: 3px solid transparent; }}
        .nav-item:hover {{ color: #fff; background: rgba(255,255,255,.05); }}
        .nav-item.active {{ color: #fff; background: rgba(192,57,43,.15); border-left-color: var(--red); }}
        .nav-item svg {{ width: 18px; height: 18px; flex-shrink: 0; }}

        .sidebar-footer {{ padding: 16px 20px; border-top: 1px solid rgba(255,255,255,.08); }}
        .user-pill {{ display: flex; align-items: center; gap: 10px; }}
        .user-avatar {{ width: 34px; height: 34px; background: var(--red); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px; color: #fff; flex-shrink: 0; }}
        .user-info .name {{ font-size: 13px; font-weight: 500; color: #fff; }}
        .user-info .role {{ font-size: 11px; color: rgba(255,255,255,.4); text-transform: capitalize; }}
        .logout-btn {{ margin-top: 10px; width: 100%; padding: 8px; background: rgba(192,57,43,.2); border: 1px solid rgba(192,57,43,.3); color: var(--red-light); border-radius: 8px; cursor: pointer; font-size: 13px; transition: .2s; }}
        .logout-btn:hover {{ background: var(--red); color: #fff; }}

        /* MAIN CONTENT AREA */
        .main {{ margin-left: var(--sidebar-w); flex: 1; padding: 28px; animation: fadeIn .4s ease; }}
        .topbar {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 28px; }}
        .page-title {{ font-size: 26px; font-weight: 800; color: var(--text); }}
        .page-sub {{ font-size: 14px; color: var(--muted); margin-top: 2px; }}

        /* COMPONENTS */
        .card {{ background: var(--card); border-radius: var(--radius); box-shadow: var(--shadow); padding: 24px; }}
        .grid {{ display: grid; gap: 20px; }}
        .grid-2 {{ grid-template-columns: repeat(2, 1fr); }}
        .grid-3 {{ grid-template-columns: repeat(3, 1fr); }}
        
        .stat-card {{ background: var(--card); border-radius: var(--radius); padding: 20px; box-shadow: var(--shadow); display: flex; align-items: center; gap: 16px; animation: slideUp .4s ease both; }}
        .stat-icon {{ width: 48px; height: 48px; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; background: var(--red); }}
        .stat-icon svg {{ width: 24px; height: 24px; color: #fff; }}
        
        .form-input {{ width: 100%; padding: 10px 14px; border: 1.5px solid var(--border); border-radius: 8px; font-size: 14px; transition: .2s; }}
        .form-input:focus {{ outline: none; border-color: var(--red); box-shadow: 0 0 0 3px rgba(192,57,43,.1); }}

        .btn {{ display: inline-flex; align-items: center; gap: 8px; padding: 10px 20px; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; border: none; transition: .2s; }}
        .btn-primary {{ background: var(--red); color: #fff; }}
        .btn-primary:hover {{ background: var(--red-dark); transform: translateY(-1px); }}

        /* ALERTS */
        .alert {{ padding: 12px 16px; border-radius: 8px; font-size: 14px; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }}
        .alert-error {{ background: rgba(192,57,43,.08); border: 1px solid rgba(192,57,43,.2); color: var(--red); }}

        /* ANIMATIONS */
        @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
        @keyframes slideUp {{ from {{ opacity: 0; transform: translateY(20px); }} to {{ opacity: 1; transform: translateY(0); }} }}

        /* RESPONSIVE */
        @media(max-width: 768px) {{
            .sidebar {{ transform: translateX(-100%); }}
            .sidebar.open {{ transform: translateX(0); }}
            .main {{ margin-left: 0; padding: 16px; }}
            .grid-2, .grid-3 {{ grid-template-columns: 1fr; }}
            .hamburger {{ display: flex; }}
        }}
        
        .hamburger {{ display: none; position: fixed; top: 16px; left: 16px; z-index: 200; width: 40px; height: 40px; background: var(--sidebar); border-radius: 8px; align-items: center; justify-content: center; cursor: pointer; border: none; color: #fff; font-size: 20px; }}
    </style>
</head>
<body>
    {html_content}

    <script>
        function logout() {{
            if(confirm('Are you sure you want to sign out?')) {{
                fetch('/api/logout', {{ method: 'POST' }})
                .then(() => location.href = '/login');
            }}
        }}

        function openModal(id) {{ document.getElementById(id)?.classList.add('open'); }}
        function closeModal(id) {{ document.getElementById(id)?.classList.remove('open'); }}

        function showAlert(msg, type = 'error') {{
            const zone = document.querySelector('.alert-zone');
            if(!zone) return;
            const a = document.createElement('div');
            a.className = 'alert alert-' + type;
            a.innerHTML = `<span>${{msg}}</span>`;
            zone.prepend(a);
            setTimeout(() => a.remove(), 4000);
        }}

        // Mobile Sidebar Toggle
        const btn = document.querySelector('.hamburger');
        const sb = document.querySelector('.sidebar');
        if(btn && sb) {{
            btn.onclick = () => sb.classList.toggle('open');
        }}
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
         "M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"),
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
         "M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"),
        ("results", "Results",
         "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"),
    ],
    "student": [
        ("dashboard", "Dashboard",
         "M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z",
         "M9 22V12h6v10"),
        ("exams", "Available Exams",
         "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"),
        ("grades", "My Grades",
         "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"),
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
    initial = name[0].upper() if (name and len(name) > 0) else "U"
    role_label = _ROLE_LABELS.get(role, role.capitalize())

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
  <main class="main">
"""
from functools import wraps
from flask import session, redirect, url_for, jsonify


from functools import wraps
from flask import session, redirect, url_for, jsonify

# ─────────────────────────────────────────────
#  AUTH DECORATORS
# ─────────────────────────────────────────────

def login_required(f):
    """Ensures the user is logged in before accessing a route."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login_page"))
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    """Ensures the user is logged in AND has one of the allowed roles."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("auth.login_page"))
            
            # Using .get() is safer to avoid KeyErrors
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
    # Note: Using | instead of · for titles avoids potential encoding issues on some servers.
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} | WMSU ExamSys</title>
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
body{{font-family:'DM Sans',sans-serif;background:var(--bg);color:var(--text);min-height:100vh;overflow-x:hidden}}
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
.logout-btn{{margin-top:10px;width:100%;padding:8px;background:rgba(192,57,43,.2);border:1px solid rgba(192,57,43,.3);color:var(--red-light);border-radius:8px;cursor:pointer;font-size:13px;transition:.2s;border:none}}
.logout-btn:hover{{background:var(--red);color:#fff}}

/* MAIN */
.main{{margin-left:var(--sidebar-w);flex:1;padding:28px;animation:fadeIn .4s ease;min-width:0}}
.topbar{{display:flex;align-items:center;justify-content:space-between;margin-bottom:28px}}
.page-title{{font-size:26px;font-weight:800;color:var(--text)}}
.page-sub{{font-size:14px;color:var(--muted);margin-top:2px}}

/* CARDS */
.card{{background:var(--card);border-radius:var(--radius);box-shadow:var(--shadow);padding:24px;border:1px solid var(--border)}}
.card-header{{display:flex;align-items:center;justify-content:space-between;margin-bottom:20px}}
.card-title{{font-size:16px;font-weight:700}}
.grid{{display:grid;gap:20px}}
.grid-2{{grid-template-columns:repeat(2,1fr)}}
.grid-3{{grid-template-columns:repeat(3,1fr)}}
.grid-4{{grid-template-columns:repeat(4,1fr)}}

/* STAT CARDS */
.stat-card{{background:var(--card);border-radius:var(--radius);padding:20px;box-shadow:var(--shadow);display:flex;align-items:center;gap:16px;animation:slideUp .4s ease both;border:1px solid var(--border)}}
.stat-icon{{width:48px;height:48px;border-radius:10px;display:flex;align-items:center;justify-content:center;flex-shrink:0}}
.stat-icon svg{{width:24px;height:24px;color:#fff}}
.stat-label{{font-size:12px;color:var(--muted);font-weight:500;margin-bottom:4px}}
.stat-value{{font-size:28px;font-weight:800;font-family:'Syne',sans-serif}}

/* FORMS */
.form-group{{margin-bottom:16px}}
.form-label{{display:block;font-size:13px;font-weight:600;color:var(--text);margin-bottom:6px}}
.form-input{{width:100%;padding:10px 14px;border:1.5px solid var(--border);border-radius:8px;font-size:14px;transition:.2s;background:#fff;color:var(--text)}}
.form-input:focus{{outline:none;border-color:var(--red);box-shadow:0 0 0 3px rgba(192,57,43,.1)}}

/* BUTTONS */
.btn{{display:inline-flex;align-items:center;gap:8px;padding:10px 20px;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;border:none;transition:.2s;font-family:inherit}}
.btn-primary{{background:var(--red);color:#fff}}
.btn-primary:hover{{background:var(--red-dark);transform:translateY(-1px)}}
.btn-danger{{background:#e74c3c;color:#fff}}
.btn-danger:hover{{background:#c0392b}}

/* TABLE */
.table-wrap{{overflow-x:auto;background:var(--card);border-radius:var(--radius);border:1px solid var(--border)}}
table{{width:100%;border-collapse:collapse;font-size:14px}}
th{{text-align:left;padding:12px 14px;font-size:11px;letter-spacing:.8px;text-transform:uppercase;color:var(--muted);border-bottom:2px solid var(--border);font-weight:700}}
td{{padding:12px 14px;border-bottom:1px solid var(--border);vertical-align:middle}}

/* ALERTS */
.alert-zone{{position:fixed;top:20px;right:20px;z-index:9999;display:flex;flex-direction:column;gap:10px;max-width:320px}}
.alert{{padding:12px 16px;border-radius:8px;font-size:14px;box-shadow:var(--shadow);display:flex;align-items:center;gap:8px;animation:slideLeft .3s ease}}

/* ANIMATIONS */
@keyframes fadeIn{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes slideUp{{from{{opacity:0;transform:translateY(20px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes slideLeft{{from{{opacity:0;transform:translateX(20px)}}to{{opacity:1;transform:translateX(0)}}}}

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
<div class="alert-zone"></div>
{html_content}
<script>
function logout(){{
  if(confirm('Are you sure you want to sign out?')){{
    fetch('/api/logout',{{method:'POST'}}).then(()=>location.href='/login');
  }}
}}
function openModal(id){{document.getElementById(id).classList.add('open')}}
function closeModal(id){{document.getElementById(id).classList.remove('open')}}

function showAlert(msg, type='error'){{
  const zone = document.querySelector('.alert-zone');
  const a = document.createElement('div');
  a.className = 'alert alert-' + type;
  a.innerHTML = `<span>${{msg}}</span>`; // Using double braces for f-string escaping
  zone.prepend(a);
  setTimeout(()=>{{
    a.style.opacity = '0';
    setTimeout(()=>a.remove(), 300);
  }}, 4000);
}}

const hamburger = document.querySelector('.hamburger');
const sidebar = document.querySelector('.sidebar');
if(hamburger) hamburger.onclick = () => sidebar.classList.toggle('open');
</script>
</body>
</html>"""
from functools import wraps
from flask import session, redirect, url_for, jsonify

# ─────────────────────────────────────────────
#  AUTH DECORATORS
# ─────────────────────────────────────────────

def login_required(f):
    """Siguraduhon nga naka-login ang user."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login_page"))
        return f(*args, **kwargs)
    return decorated

def role_required(*roles):
    """Siguraduhon nga ang role sa user naa sa listahan sa gitugutan."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("auth.login_page"))
            if session.get("role") not in roles:
                return jsonify({"error": "Unauthorized Access"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator

# ─────────────────────────────────────────────
#  SIDEBAR CONFIGURATION
# ─────────────────────────────────────────────

_ROLE_LABELS = {
    "admin": "Administrator",
    "teacher": "Teacher",
    "student": "Student",
}

_NAV_ITEMS = {
    "admin": [
        ("dashboard", "Dashboard", 
         "M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z", "M9 22V12h6v10"),
        ("courses", "Courses", 
         "M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"),
        ("users", "Users", 
         "M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2", "M23 21v-2a4 4 0 00-3-3.87", "M16 3.13a4 4 0 010 7.75", "M9 7a4 4 0 100 8 4 4 0 000-8z"),
    ],
    "teacher": [
        ("dashboard", "Dashboard", 
         "M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z", "M9 22V12h6v10"),
        ("exams", "My Exams", 
         "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2", "M9 12l2 2 4-4"),
        ("essays", "Review Essays", 
         "M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"),
        ("results", "Results", 
         "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"),
    ],
    "student": [
        ("dashboard", "Dashboard", 
         "M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z", "M9 22V12h6v10"),
        ("exams", "Available Exams", 
         "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"),
        ("grades", "My Grades", 
         "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"),
    ],
}

# ─────────────────────────────────────────────
#  UI BUILDERS
# ─────────────────────────────────────────────

def sidebar(role: str, active: str = "dashboard") -> str:
    """I-build ang sidebar HTML base sa role."""
    name = session.get("name", "User")
    initial = name[0].upper() if (name and len(name) > 0) else "U"
    role_label = _ROLE_LABELS.get(role, role.capitalize())

    items_html = ""
    for item in _NAV_ITEMS.get(role, []):
        key, label = item[0], item[1]
        paths = "".join(
            f'<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="{p}"/>'
            for p in item[2:] if p
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
  <main class="main">
"""

def render(html_content: str, title: str = "ExamSys") -> str:
    """I-wrap ang content sa tibuok HTML shell (CSS ug JS)."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>{title} | WMSU ExamSys</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        /* [I-paste diri ang imong gi-provide nga CSS style block] */
        :root{{ --red:#c0392b; --red-dark:#922b21; --red-light:#e74c3c; --bg:#f0f2f5; --sidebar:#1a1a2e; --sidebar-w:240px; --card:#fff; --border:#e8e8ec; --text:#1a1a2e; --muted:#6b7280; --success:#27ae60; --radius:12px; --shadow:0 2px 16px rgba(0,0,0,.08); }}
        *{{margin:0;padding:0;box-sizing:border-box}}
        body{{font-family:'DM Sans',sans-serif;background:var(--bg);color:var(--text);min-height:100vh}}
        /* ... (ug uban pa nga CSS classes) ... */
    </style>
</head>
<body>
    <div class="alert-zone"></div>
    {html_content}
    <script>
        function logout() {{ 
            if(confirm('Are you sure you want to sign out?')) {{
                fetch('/api/logout', {{method:'POST'}}).then(()=>location.href='/login'); 
            }}
        }}
        const hamburger=document.querySelector('.hamburger');
        const sidebar=document.querySelector('.sidebar');
        if(hamburger) hamburger.onclick=()=>sidebar.classList.toggle('open');
    </script>
</body>
</html>"""


def sidebar(role: str, active: str = "dashboard") -> str:
    """Build the sidebar + open the .layout / .main wrappers (caller must close them)."""
    # Safety check: ensure name is a string and not empty before grabbing index 0
    name = session.get("name", "User")
    initial = name[0].upper() if (name and len(name) > 0) else "U"
    
    # Fallback to capitalized role if label isn't found
    role_label = _ROLE_LABELS.get(role, role.capitalize())

    items_html = ""
    for item in _NAV_ITEMS.get(role, []):
        key, label = item[0], item[1]
        
        # Build SVG paths dynamically from the tuple
        paths = "".join(
            f'<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="{p}"/>'
            for p in item[2:]
            if p
        )
        
        is_active = "active" if active == key else ""
        
        # Dashboard points to root of the role, others point to sub-path
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
  <main class="main">
"""
