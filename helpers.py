from functools import wraps
from flask import session, redirect, url_for, jsonify

_ROLE_LABELS = {
    "admin": "Administrator",
    "teacher": "Teacher",
    "student": "Student",
}

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
            if "user_id" not in session:
                return redirect(url_for("auth.login_page"))
            user_role = session.get("role")
            if not user_role or user_role not in roles:
                return jsonify({"status": "error", "message": "Access Denied: Unauthorized role"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


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
      <div class="brand" onclick="toggleSidebar()" style="cursor: pointer;">
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
      <button class="profile-btn" onclick="location.href='/profile'"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg><span>Profile</span></button>
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
      <button class="logout-btn" onclick="logout()"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><path d="M16 17l5-5-5-5"/><path d="M21 12H9"/></svg><span>Sign Out</span></button>
    </div>
  </aside>
  <main class="main">
"""


def render(html_content: str, title: str = "ExamSys") -> str:
    """Wrap page content in the full HTML shell (fonts, CSS, JS utilities)."""
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

        .layout {{ display: flex; min-height: 100vh; transition: margin-left .3s ease; }}
        .sidebar {{ width: var(--sidebar-w); background: var(--sidebar); position: fixed; top: 0; left: 0; height: 100vh; display: flex; flex-direction: column; z-index: 100; transition: width .3s ease; overflow: hidden; }}
        .sidebar-logo {{ padding: 24px 20px 20px; border-bottom: 1px solid rgba(255,255,255,.08); }}
        .sidebar-logo .brand {{ display: flex; align-items: center; gap: 10px; transition: justify-content .3s ease; }}
        .sidebar-logo .brand-icon {{ width: 40px; height: 40px; border-radius: 8px; overflow: hidden; display: flex; align-items: center; justify-content: center; flex-shrink: 0; background: #fff; padding: 2px; }}
        .sidebar-logo .brand-icon img {{ width: 100%; height: 100%; object-fit: contain; }}
        .sidebar-logo .brand-name {{ font-family: 'Syne', sans-serif; font-weight: 700; font-size: 15px; color: #fff; line-height: 1.2; }}
        .sidebar-logo .brand-sub {{ font-size: 10px; color: rgba(255,255,255,.4); letter-spacing: .5px; }}
        .sidebar-nav {{ flex: 1; padding: 12px 0; overflow-y: auto; }}
        .nav-section {{ padding: 8px 16px 4px; font-size: 10px; letter-spacing: 1.5px; color: rgba(255,255,255,.3); text-transform: uppercase; font-weight: 600; }}
        .nav-item {{ display: flex; align-items: center; gap: 12px; padding: 10px 20px; color: rgba(255,255,255,.6); font-size: 14px; cursor: pointer; transition: .2s; border-left: 3px solid transparent; }}
        .nav-item:hover {{ color: #fff; background: rgba(255,255,255,.05); }}
        .nav-item.active {{ color: #fff; background: rgba(192,57,43,.15); border-left-color: var(--red); }}
        .nav-item svg {{ width: 18px; height: 18px; flex-shrink: 0; }}
        .sidebar-footer {{ padding: 12px 16px; border-top: 1px solid rgba(255,255,255,.08); display: flex; flex-direction: column; gap: 12px; }}
        .user-pill {{ display: flex; align-items: center; gap: 10px; }}
        .user-avatar {{ width: 34px; height: 34px; background: var(--red); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px; color: #fff; flex-shrink: 0; }}
        .user-info .name {{ font-size: 13px; font-weight: 500; color: #fff; }}
        .user-info .role {{ font-size: 11px; color: rgba(255,255,255,.4); text-transform: capitalize; }}
        .profile-btn {{ display: flex; align-items: center; gap: 12px; padding: 10px 20px; color: rgba(255,255,255,.6); font-size: 14px; cursor: pointer; transition: .2s; border: none; background: transparent; width: 100%; text-align: left; border-radius: 0; }}
        .profile-btn:hover {{ color: #fff; background: rgba(255,255,255,.05); }}
        .profile-btn svg {{ width: 18px; height: 18px; flex-shrink: 0; }}
        .logout-btn {{ display: flex; align-items: center; gap: 8px; width: 100%; padding: 10px 16px; border: 1px solid rgba(255,255,255,.12); border-radius: 8px; background: rgba(255,255,255,.06); color: rgba(255,255,255,.85); cursor: pointer; transition: .2s; font-size: 13px; }}
        .logout-btn:hover {{ background: rgba(255,255,255,.12); color: #fff; }}
        .logout-btn svg {{ width: 16px; height: 16px; }}
        .main {{ margin-left: var(--sidebar-w); flex: 1; padding: 28px; animation: fadeIn .4s ease; transition: margin-left .3s ease; }}
        .layout.collapsed .sidebar {{ width: 80px; }}
        .layout.collapsed .main {{ margin-left: 80px; }}
        .layout.collapsed .sidebar-logo {{ padding: 20px 12px 16px; }}
        .layout.collapsed .sidebar-logo .brand {{ justify-content: center; }}
        .layout.collapsed .sidebar-logo .brand-name,
        .layout.collapsed .sidebar-logo .brand-sub,
        .layout.collapsed .nav-section,
        .layout.collapsed .sidebar-footer .user-info,
        .layout.collapsed .logout-btn span,
        .layout.collapsed .profile-btn span {{ display: none; }}
        .layout.collapsed .nav-item {{ justify-content: center; padding: 14px 0; }}
        .layout.collapsed .nav-item span {{ display: none; }}
        .layout.collapsed .profile-btn {{ justify-content: center; padding: 14px 0; }}
        .layout.collapsed .sidebar-footer {{ align-items: center; padding: 12px 12px; gap: 12px; }}
        .layout.collapsed .sidebar-footer .user-pill {{ justify-content: center; }}
        .topbar {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 28px; }}
        .page-title {{ font-size: 26px; font-weight: 800; color: var(--text); }}
        .page-sub {{ font-size: 14px; color: var(--muted); margin-top: 2px; }}
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
        .btn-secondary {{ background: #fff; color: var(--text); border: 1.5px solid var(--border); }}
        .btn-secondary:hover {{ background: #f4f5f8; }}
        .w-full {{ width: 100%; }}
        .auth-bg {{ min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 32px 16px; background: linear-gradient(180deg, #f9fafb 0%, #eceff3 100%); }}
        .auth-card {{ width: 100%; max-width: 480px; background: var(--card); border-radius: 24px; box-shadow: var(--shadow); padding: 32px; border: 1px solid rgba(0,0,0,.04); }}
        .auth-logo {{ display: grid; gap: 12px; text-align: center; margin-bottom: 24px; }}
        .logo-icon {{ width: 68px; height: 68px; margin: 0 auto; border-radius: 18px; overflow: hidden; background: #fff; display: flex; align-items: center; justify-content: center; box-shadow: 0 10px 30px rgba(0,0,0,.06); }}
        .auth-logo h1 {{ margin: 0; font-size: 28px; letter-spacing: -0.04em; }}
        .auth-logo p {{ color: var(--muted); font-size: 14px; margin: 0; }}
        .auth-divider {{ display: block; text-align: center; color: var(--muted); font-size: 13px; }}
        .form-select {{ appearance: none; width: 100%; padding: 10px 14px; border: 1.5px solid var(--border); border-radius: 8px; background: #fff; color: var(--text); cursor: pointer; }}
        .form-group {{ margin-bottom: 18px; }}
        .form-label {{ display: block; margin-bottom: 8px; font-size: 14px; font-weight: 600; color: var(--text); }}
        .flex {{ display: flex; }}
        .items-center {{ align-items: center; }}
        .justify-between {{ justify-content: space-between; }}
        .flex-1 {{ flex: 1; }}
        .grid-4 {{ grid-template-columns: repeat(4, 1fr); }}
        .table-wrap {{ overflow-x: auto; border-radius: var(--radius); background: var(--card); box-shadow: var(--shadow); }}
        .table-wrap table {{ width: 100%; border-collapse: collapse; }}
        .table-wrap th, .table-wrap td {{ padding: 14px 16px; border-bottom: 1px solid var(--border); }}
        .table-wrap th {{ text-align: left; font-size: 13px; color: var(--muted); text-transform: uppercase; letter-spacing: .4px; }}
        .card-header {{ display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 22px; }}
        .card-title {{ font-size: 18px; font-weight: 700; color: var(--text); margin: 0; }}
        .badge-orange {{ background: rgba(243,156,18,.12); color: #f39c12; }}
        .btn-danger {{ background: #d64541; color: #fff; }}
        .btn-danger:hover {{ background: #b53d36; }}
        .modal-overlay {{ position: fixed; inset: 0; display: none; align-items: center; justify-content: center; background: rgba(12,17,43,.65); padding: 20px; z-index: 250; }}
        .modal-overlay.open {{ display: flex; }}
        .modal {{ width: 100%; max-width: 520px; background: var(--card); border-radius: var(--radius); padding: 28px; box-shadow: var(--shadow); }}
        .modal-header {{ display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 20px; }}
        .modal-title {{ font-size: 18px; font-weight: 700; }}
        .modal-close {{ background: transparent; border: none; color: var(--muted); font-size: 22px; cursor: pointer; }}
        .text-center {{ text-align: center; }}
        .text-sm {{ font-size: 13px; }}
        .text-muted {{ color: var(--muted); }}
        .empty-icon svg {{ width: 50px; height: 50px; stroke: currentColor; }}
        .mt-16 {{ margin-top: 16px; }}
        .mt-8 {{ margin-top: 8px; }}
        .alert-zone {{ display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px; }}
        .alert {{ padding: 12px 16px; border-radius: 8px; font-size: 14px; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }}
        .alert-success {{ background: rgba(39,174,96,.08); border: 1px solid rgba(39,174,96,.2); color: #27ae60; }}
        .alert-info {{ background: rgba(41,128,185,.08); border: 1px solid rgba(41,128,185,.2); color: #2980b9; }}
        .btn-success {{ background: #27ae60; color: #fff; }}
        .btn-success:hover {{ background: #219150; }}
        .btn-warning {{ background: #f39c12; color: #fff; }}
        .btn-warning:hover {{ background: #d47e0f; }}
        .btn-sm {{ padding: 8px 14px; font-size: 13px; }}
        .badge {{ display: inline-flex; align-items: center; padding: 5px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; letter-spacing: .4px; }}
        .badge-green {{ background: rgba(39,174,96,.12); color: #27ae60; }}
        .badge-red {{ background: rgba(192,57,43,.12); color: #c0392b; }}
        .empty-state {{ padding: 40px; text-align: center; color: var(--muted); }}
        .empty-icon {{ font-size: 44px; margin-bottom: 14px; }}
        .question-card {{ background: var(--card); border-radius: var(--radius); box-shadow: var(--shadow); padding: 24px; }}
        .question-num {{ font-size: 13px; color: var(--muted); margin-bottom: 8px; }}
        .question-text {{ font-size: 18px; font-weight: 700; margin-bottom: 20px; line-height: 1.5; }}
        .choice-item {{ display: flex; align-items: center; gap: 14px; padding: 14px 16px; border: 1px solid var(--border); border-radius: 12px; margin-bottom: 12px; cursor: pointer; transition: .2s; }}
        .choice-item.selected {{ border-color: var(--red); background: rgba(192,57,43,.08); }}
        .choice-letter {{ width: 28px; height: 28px; border-radius: 50%; background: var(--red); color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; }}
        .progress {{ background: rgba(0,0,0,.05); border-radius: 999px; height: 10px; overflow: hidden; margin-top: 10px; }}
        .progress-bar {{ height: 100%; background: var(--red); width: 0%; transition: width .3s ease; }}
        .q-nav {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 10px; }}
        .q-dot {{ width: 34px; height: 34px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; border: 1px solid var(--border); cursor: pointer; transition: .2s; }}
        .q-dot.current {{ background: var(--red); color: #fff; border-color: var(--red); }}
        .q-dot.answered {{ background: rgba(39,174,96,.1); border-color: rgba(39,174,96,.3); }}
        .timer-display {{ background: #fff; border: 1px solid var(--border); border-radius: 12px; padding: 12px 18px; font-weight: 700; color: var(--red); min-width: 120px; text-align: center; }}
        @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
        @keyframes slideUp {{ from {{ opacity: 0; transform: translateY(20px); }} to {{ opacity: 1; transform: translateY(0); }} }}
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
    <script>
        function logout() {{
            if(confirm('Are you sure you want to sign out?')) {{
                fetch('/api/logout', {{ method: 'POST' }})
                .then(() => location.href = '/login');
            }}
        }}

        function openModal(id) {{ document.getElementById(id)?.classList.add('open'); }}
        function closeModal(id) {{ document.getElementById(id)?.classList.remove('open'); }}
        function toggleSidebar() {{ const layout = document.querySelector('.layout'); layout?.classList.toggle('collapsed'); }}

        function showAlert(msg, type = 'error') {{
            const zone = document.querySelector('.alert-zone');
            if(!zone) return;
            const a = document.createElement('div');
            a.className = 'alert alert-' + type;
            a.innerHTML = `<span>${{msg}}</span>`;
            zone.prepend(a);
            setTimeout(() => a.remove(), 4000);
        }}
    </script>

    {html_content}

    <script>
        const btn = document.querySelector('.hamburger');
        const sb = document.querySelector('.sidebar');
        if(btn && sb) {{
            btn.onclick = () => sb.classList.toggle('open');
        }}
    </script>
</body>
</html>"""
