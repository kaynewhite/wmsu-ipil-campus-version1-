<<<<<<< HEAD
from flask import Blueprint, request, session, redirect, url_for, jsonify
from datetime import datetime
import bcrypt

from database import get_db
from email_utils import send_email, email_template, generate_code, store_code
from helpers import render

auth_bp = Blueprint("auth", __name__)

LOGO = '<img src="/static/images/wmsu_logo.png" alt="WMSU" style="width:100%;height:100%;object-fit:contain">'

# ─────────────────────────────────────────────
#  INDEX
# ─────────────────────────────────────────────

@auth_bp.route("/")
def index():
    if "user_id" in session:
        role = session.get("role")
        if role == "admin":   return redirect(url_for("admin.admin_dashboard"))
        if role == "teacher": return redirect(url_for("teacher.teacher_dashboard"))
        if role == "student": return redirect(url_for("student.student_dashboard"))
    return redirect(url_for("auth.login_page"))


# ─────────────────────────────────────────────
#  PAGE ROUTES
# ─────────────────────────────────────────────

@auth_bp.route("/login")
def login_page():
    if "user_id" in session:
        return redirect(url_for("auth.index"))
    return render(f"""
<div class="auth-bg">
  <div class="auth-card">
    <div class="auth-logo">
      <div class="logo-icon">{LOGO}</div>
      <h1>ExamSys</h1>
      <p>Western Mindanao State University</p>
    </div>
    <div class="alert-zone"></div>
    <div class="form-group">
      <label class="form-label">Email Address</label>
      <input type="email" id="email" class="form-input" placeholder="you@example.com">
    </div>
    <div class="form-group">
      <label class="form-label">Password</label>
      <input type="password" id="password" class="form-input" placeholder="••••••••">
    </div>
    <div style="text-align:right;margin-bottom:16px">
      <a href="/forgot-password" style="font-size:13px;color:var(--red);font-weight:500">Forgot Password?</a>
    </div>
    <button class="btn btn-primary w-full" onclick="doLogin()" style="justify-content:center">Sign In</button>
    <div class="auth-divider" style="margin:20px 0">or</div>
    <a href="/register" class="btn btn-secondary w-full" style="justify-content:center">Create Account</a>
  </div>
</div>
<script>
function doLogin(){{
  const email=document.getElementById('email').value.trim();
  const pass=document.getElementById('password').value;
  if(!email||!pass){{showAlert('Please fill in all fields.');return;}}
  fetch('/api/login',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{email,password:pass}})}})
  .then(r=>r.json()).then(d=>{{
    if(d.success){{
      if(d.redirect)location.href=d.redirect;
    }}else showAlert(d.error||'Login failed.');
  }});
}}
document.querySelectorAll('.form-input').forEach(i=>i.addEventListener('keydown',e=>e.key==='Enter'&&doLogin()));
</script>
""", "Login")


@auth_bp.route("/register")
def register_page():
    return render(f"""
<div class="auth-bg">
  <div class="auth-card" style="max-width:460px">
    <div class="auth-logo">
      <div class="logo-icon">{LOGO}</div>
      <h1>Create Account</h1>
      <p>Western Mindanao State University</p>
    </div>
    <div class="alert-zone"></div>
    <div class="form-group">
      <label class="form-label">Full Name</label>
      <input type="text" id="name" class="form-input" placeholder="Your full name">
    </div>
    <div class="form-group">
      <label class="form-label">Email Address</label>
      <input type="email" id="email" class="form-input" placeholder="you@example.com">
    </div>
    <div class="form-group">
      <label class="form-label">Role</label>
      <select id="role" class="form-input form-select">
        <option value="student">Student</option>
        <option value="teacher">Teacher</option>
      </select>
    </div>
    <div class="form-group">
      <label class="form-label">ID Number</label>
      <input type="text" id="user_id" class="form-input" placeholder="Enter your ID number">
      <small class="text-muted">Enter your Student ID or Teacher ID</small>
    </div>
    <div class="form-group">
      <label class="form-label">Password</label>
      <input type="password" id="password" class="form-input" placeholder="Min. 6 characters">
    </div>
    <div class="form-group">
      <label class="form-label">Confirm Password</label>
      <input type="password" id="confirm" class="form-input" placeholder="Repeat password">
    </div>
    <button class="btn btn-primary w-full" onclick="doRegister()" style="justify-content:center">Create Account</button>
    <p class="text-center text-sm text-muted mt-16">Already have an account? <a href="/login" style="color:var(--red);font-weight:600">Sign In</a></p>
  </div>
</div>
<script>
function doRegister(){{
  const name    =document.getElementById('name').value.trim();
  const email   =document.getElementById('email').value.trim();
  const role    =document.getElementById('role').value;
  const user_id =document.getElementById('user_id').value.trim();
  const pass    =document.getElementById('password').value;
  const conf    =document.getElementById('confirm').value;

  if(!name||!email||!user_id||!pass||!conf){{showAlert('Please fill in all fields.');return;}}
  if(pass.length<6){{showAlert('Password must be at least 6 characters.');return;}}
  if(pass!==conf){{showAlert('Passwords do not match.');return;}}
  if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)){{showAlert('Invalid email format.');return;}}

  fetch('/api/register',{{method:'POST',headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify({{name,email,role,user_id,password:pass}})}})
  .then(r=>r.json()).then(d=>{{
    if(d.success){{showAlert('Registration successful! Redirecting...','success');setTimeout(()=>location.href='/login',1500);}}
    else showAlert(d.error||'Registration failed.');
  }});
}}
</script>
""", "Register")


@auth_bp.route("/verify")
def verify_page():
    email = request.args.get("email", "")
    vtype = request.args.get("type", "login")
    return render(f"""
<div class="auth-bg">
  <div class="auth-card">
    <div class="auth-logo">
      <div class="logo-icon">{LOGO}</div>
      <h1>Verify Your Email</h1>
      <p>We sent a 6-digit code to <strong>{email}</strong></p>
    </div>
    <div class="alert-zone"></div>
    <div class="form-group">
      <label class="form-label">Verification Code</label>
      <input type="text" id="code" class="form-input" placeholder="Enter 6-digit code" maxlength="6" style="font-size:24px;letter-spacing:8px;text-align:center">
    </div>
    <button class="btn btn-primary w-full" onclick="doVerify()" style="justify-content:center">Verify & Continue</button>
    <button class="btn btn-secondary w-full mt-8" onclick="resendCode()" style="justify-content:center">Resend Code</button>
    <p class="text-center text-sm text-muted mt-16"><a href="/login" style="color:var(--red)">← Back to Login</a></p>
  </div>
</div>
<script>
const EMAIL="{email}",VTYPE="{vtype}";
function doVerify(){{
  const code=document.getElementById('code').value.trim();
  if(code.length!==6){{showAlert('Enter the 6-digit code.');return;}}
  fetch('/api/verify',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{email:EMAIL,code,type:VTYPE}})}})
  .then(r=>r.json()).then(d=>{{
    if(d.success){{showAlert('Email verified successfully!','success');setTimeout(()=>location.href=d.redirect||'/',1200);}}
    else showAlert(d.error||'Verification failed.');
  }});
}}
function resendCode(){{
  fetch('/api/resend-code',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{email:EMAIL,type:VTYPE}})}})
  .then(r=>r.json()).then(d=>{{
    if(d.success)showAlert('New code sent to your email.','info');
    else showAlert(d.error||'Failed to resend.');
  }});
}}
document.getElementById('code').addEventListener('keydown',e=>e.key==='Enter'&&doVerify());
</script>
""", "Verify")


@auth_bp.route("/forgot-password")
def forgot_page():
    step    = request.args.get("step", "1")
    user_id = request.args.get("user_id", "")

    if step == "1":
        return render(f"""
<div class="auth-bg">
  <div class="auth-card">
    <div class="auth-logo">
      <div class="logo-icon">{LOGO}</div>
      <h1>Forgot Password</h1>
      <p>Enter your Student ID or Teacher ID</p>
    </div>
    <div class="alert-zone"></div>
    <div class="form-group">
      <label class="form-label">ID Number</label>
      <input type="text" id="identifier" class="form-input" placeholder="Enter your Student ID or Teacher ID">
    </div>
    <button class="btn btn-primary w-full" onclick="sendReset()" style="justify-content:center">Verify ID</button>
    <p class="text-center text-sm text-muted mt-16"><a href="/login" style="color:var(--red)">← Back to Login</a></p>
  </div>
</div>
<script>
function sendReset(){{
  const identifier=document.getElementById('identifier').value.trim();
  if(!identifier){{showAlert('Please enter your ID number.');return;}}
  fetch('/api/forgot-password',{{method:'POST',headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify({{identifier}})}})
  .then(r=>r.json()).then(d=>{{
    if(d.success) location.href='/forgot-password?step=2&user_id='+encodeURIComponent(d.user_id);
    else showAlert(d.error||'ID not found.');
  }});
}}
</script>
""", "Forgot Password")

    # step == "2"
    return render(f"""
<div class="auth-bg">
  <div class="auth-card">
    <div class="auth-logo">
      <div class="logo-icon">{LOGO}</div>
      <h1>Reset Password</h1>
      <p>Enter your new password</p>
    </div>
    <div class="alert-zone"></div>
    <div class="form-group">
      <label class="form-label">New Password</label>
      <input type="password" id="newpass" class="form-input" placeholder="Min. 6 characters">
    </div>
    <div class="form-group">
      <label class="form-label">Confirm New Password</label>
      <input type="password" id="confirm" class="form-input" placeholder="Repeat new password">
    </div>
    <button class="btn btn-primary w-full" onclick="doReset()" style="justify-content:center">Reset Password</button>
    <p class="text-center text-sm text-muted mt-16"><a href="/login" style="color:var(--red)">← Back to Login</a></p>
  </div>
</div>
<script>
const UID="{user_id}";
function doReset(){{
  const newpass=document.getElementById('newpass').value;
  const confirm=document.getElementById('confirm').value;
  if(!newpass||!confirm){{showAlert('Fill in all fields.');return;}}
  if(newpass.length<6){{showAlert('Password must be at least 6 characters.');return;}}
  if(newpass!==confirm){{showAlert('Passwords do not match.');return;}}
  fetch('/api/reset-password',{{method:'POST',headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify({{user_id:UID,new_password:newpass}})}})
  .then(r=>r.json()).then(d=>{{
    if(d.success){{showAlert('Password reset successfully!','success');setTimeout(()=>location.href='/login',1500);}}
    else showAlert(d.error||'Reset failed.');
  }});
}}
</script>
""", "Reset Password")


# ─────────────────────────────────────────────
#  API ROUTES
# ─────────────────────────────────────────────

@auth_bp.route("/api/register", methods=["POST"])
def api_register():
    data     = request.json
    name     = (data.get("name",    "")).strip()
    email    = (data.get("email",   "")).strip().lower()
    password = data.get("password", "")
    role     = data.get("role",     "student")
    user_id  = (data.get("user_id", "")).strip()

    if not all([name, email, password, user_id]):
        return jsonify({"error": "All fields are required."})
    if role not in ["student", "teacher"]:
        return jsonify({"error": "Invalid role."})

    db = get_db()
    try:
        if db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone():
            return jsonify({"error": "Email already exists."})
        if db.execute("SELECT id FROM users WHERE user_id=?", (user_id,)).fetchone():
            return jsonify({"error": "That ID number is already taken."})

        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        db.execute(
            "INSERT INTO users (name, email, password, role, user_id) VALUES (?,?,?,?,?)",
            (name, email, hashed, role, user_id)
        )
        db.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": f"Registration error: {str(e)}"})
    finally:
        db.close()


@auth_bp.route("/api/login", methods=["POST"])
def api_login():
    data     = request.json
    email    = (data.get("email", "")).strip().lower()
    password = data.get("password", "")

    db = get_db()
    try:
        user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if not user:
            return jsonify({"error": "No account found with this email."})
        if not bcrypt.checkpw(password.encode(), user["password"].encode()):
            return jsonify({"error": "Incorrect password."})

        if user["role"] == "admin":
            session["user_id"] = user["id"]
            session["role"]    = "admin"
            session["name"]    = user["name"]
            return jsonify({"success": True, "redirect": "/admin"})

        code = generate_code()
        store_code(db, user["id"], email, code, "login")
        sent = send_email(
            email,
            "ExamSys Login Verification",
            email_template(
                "Login Verification Code", code,
                "Use this code to complete your login. It expires in 10 minutes.",
            ),
        )
        if not sent:
            print(f"[DEV] Verification code for {email}: {code}")

        session["pending_user_id"] = user["id"]
        session["pending_role"]    = user["role"]
        session["pending_name"]    = user["name"]
        return jsonify({"success": True, "redirect": f"/verify?email={email}&type=login"})
    except Exception as e:
        return jsonify({"error": f"Login error: {str(e)}"})
    finally:
        db.close()


@auth_bp.route("/api/verify", methods=["POST"])
def api_verify():
    data  = request.json
    email = data.get("email", "").strip().lower()
    code  = data.get("code",  "").strip()
    vtype = data.get("type",  "login")

    db = get_db()
    try:
        rec = db.execute(
            "SELECT * FROM verification_codes WHERE email=? AND type=? ORDER BY id DESC LIMIT 1",
            (email, vtype),
        ).fetchone()
        if not rec:
            return jsonify({"error": "No verification code found. Please request a new one."})
        if rec["attempts"] >= 5:
            return jsonify({"error": "Too many attempts. Please request a new code."})

        db.execute("UPDATE verification_codes SET attempts=attempts+1 WHERE id=?", (rec["id"],))
        db.commit()

        expires = datetime.strptime(rec["expires_at"], "%Y-%m-%d %H:%M:%S")
        if datetime.now() > expires:
            return jsonify({"error": "Code has expired. Please request a new one."})
        if rec["code"] != code:
            return jsonify({"error": "Invalid code. Please try again."})

        db.execute("DELETE FROM verification_codes WHERE id=?", (rec["id"],))
        db.commit()

        if vtype == "login":
            uid  = session.get("pending_user_id")
            role = session.get("pending_role")
            name = session.get("pending_name")
            if not uid:
                return jsonify({"error": "Session expired. Please login again."})
            session.clear()
            session["user_id"] = uid
            session["role"]    = role
            session["name"]    = name
            redirect_map = {"admin": "/admin", "teacher": "/teacher", "student": "/student"}
            return jsonify({"success": True, "redirect": redirect_map.get(role, "/")})

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": f"Verification error: {str(e)}"})
    finally:
        db.close()


@auth_bp.route("/api/resend-code", methods=["POST"])
def api_resend():
    data  = request.json
    email = data.get("email", "").strip().lower()
    vtype = data.get("type",  "login")

    db = get_db()
    try:
        user = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
        if not user:
            return jsonify({"error": "Email not found."})
        code  = generate_code()
        store_code(db, user["id"], email, code, vtype)
        title = "Login Verification Code" if vtype == "login" else "Password Reset Code"
        msg   = ("Use this code to complete your login."
                 if vtype == "login"
                 else "Use this code to reset your password.")
        send_email(email, f"ExamSys {title}", email_template(title, code, msg))
        print(f"[DEV] Resent code for {email}: {code}")
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"})
    finally:
        db.close()


@auth_bp.route("/api/forgot-password", methods=["POST"])
def api_forgot():
    data       = request.json
    identifier = (data.get("identifier", "")).strip()

    if not identifier:
        return jsonify({"error": "Please enter your ID number."})

    db = get_db()
    try:
        user = db.execute(
            "SELECT id, user_id FROM users WHERE user_id=? AND role!='admin'",
            (identifier,)
        ).fetchone()

        if not user:
            return jsonify({"error": "No account found with that ID number."})

        return jsonify({"success": True, "user_id": user["user_id"]})
    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"})
    finally:
        db.close()


@auth_bp.route("/api/reset-password", methods=["POST"])
def api_reset():
    data         = request.json
    user_id      = (data.get("user_id",     "")).strip()
    new_password = data.get("new_password", "")

    if not user_id:
        return jsonify({"error": "Invalid request."})
    if len(new_password) < 6:
        return jsonify({"error": "Password must be at least 6 characters."})

    db = get_db()
    try:
        user = db.execute(
            "SELECT id FROM users WHERE user_id=?", (user_id,)
        ).fetchone()

        if not user:
            return jsonify({"error": "Account not found."})

        hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        db.execute("UPDATE users SET password=? WHERE user_id=?", (hashed, user_id))
        db.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"})
    finally:
        db.close()


@auth_bp.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
=======
from flask import Blueprint, request, session, redirect, url_for, jsonify
from datetime import datetime
import bcrypt

from database import get_db
from email_utils import send_email, email_template, generate_code, store_code
from helpers import render

auth_bp = Blueprint("auth", __name__)

LOGO = '<img src="/static/images/wmsu_logo.png" alt="WMSU" style="width:100%;height:100%;object-fit:contain">'

# ─────────────────────────────────────────────
#  INDEX
# ─────────────────────────────────────────────

@auth_bp.route("/")
def index():
    if "user_id" in session:
        role = session.get("role")
        if role == "admin":   return redirect(url_for("admin.admin_dashboard"))
        if role == "teacher": return redirect(url_for("teacher.teacher_dashboard"))
        if role == "student": return redirect(url_for("student.student_dashboard"))
    return redirect(url_for("auth.login_page"))


# ─────────────────────────────────────────────
#  PAGE ROUTES
# ─────────────────────────────────────────────

@auth_bp.route("/login")
def login_page():
    if "user_id" in session:
        return redirect(url_for("auth.index"))
    return render(f"""
<div class="auth-bg">
  <div class="auth-card">
    <div class="auth-logo">
      <div class="logo-icon">{LOGO}</div>
      <h1>ExamSys</h1>
      <p>Western Mindanao State University</p>
    </div>
    <div class="alert-zone"></div>
    <div class="form-group">
      <label class="form-label">Email Address</label>
      <input type="email" id="email" class="form-input" placeholder="you@example.com">
    </div>
    <div class="form-group">
      <label class="form-label">Password</label>
      <input type="password" id="password" class="form-input" placeholder="••••••••">
    </div>
    <div style="text-align:right;margin-bottom:16px">
      <a href="/forgot-password" style="font-size:13px;color:var(--red);font-weight:500">Forgot Password?</a>
    </div>
    <button class="btn btn-primary w-full" onclick="doLogin()" style="justify-content:center">Sign In</button>
    <div class="auth-divider" style="margin:20px 0">or</div>
    <a href="/register" class="btn btn-secondary w-full" style="justify-content:center">Create Account</a>
  </div>
</div>
<script>
function doLogin(){{
  const email=document.getElementById('email').value.trim();
  const pass=document.getElementById('password').value;
  if(!email||!pass){{showAlert('Please fill in all fields.');return;}}
  fetch('/api/login',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{email,password:pass}})}})
  .then(r=>r.json()).then(d=>{{
    if(d.success){{
      if(d.redirect)location.href=d.redirect;
    }}else showAlert(d.error||'Login failed.');
  }});
}}
document.querySelectorAll('.form-input').forEach(i=>i.addEventListener('keydown',e=>e.key==='Enter'&&doLogin()));
</script>
""", "Login")


@auth_bp.route("/register")
def register_page():
    return render(f"""
<div class="auth-bg">
  <div class="auth-card" style="max-width:460px">
    <div class="auth-logo">
      <div class="logo-icon">{LOGO}</div>
      <h1>Create Account</h1>
      <p>Western Mindanao State University</p>
    </div>
    <div class="alert-zone"></div>
    <div class="form-group">
      <label class="form-label">Full Name</label>
      <input type="text" id="name" class="form-input" placeholder="Your full name">
    </div>
    <div class="form-group">
      <label class="form-label">Email Address</label>
      <input type="email" id="email" class="form-input" placeholder="you@example.com">
    </div>
    <div class="form-group">
      <label class="form-label">Role</label>
      <select id="role" class="form-input form-select">
        <option value="student">Student</option>
        <option value="teacher">Teacher</option>
      </select>
    </div>
    <div class="form-group">
      <label class="form-label">ID Number</label>
      <input type="text" id="user_id" class="form-input" placeholder="Enter your ID number">
      <small class="text-muted">Enter your Student ID or Teacher ID</small>
    </div>
    <div class="form-group">
      <label class="form-label">Password</label>
      <input type="password" id="password" class="form-input" placeholder="Min. 6 characters">
    </div>
    <div class="form-group">
      <label class="form-label">Confirm Password</label>
      <input type="password" id="confirm" class="form-input" placeholder="Repeat password">
    </div>
    <button class="btn btn-primary w-full" onclick="doRegister()" style="justify-content:center">Create Account</button>
    <p class="text-center text-sm text-muted mt-16">Already have an account? <a href="/login" style="color:var(--red);font-weight:600">Sign In</a></p>
  </div>
</div>
<script>
function doRegister(){{
  const name    =document.getElementById('name').value.trim();
  const email   =document.getElementById('email').value.trim();
  const role    =document.getElementById('role').value;
  const user_id =document.getElementById('user_id').value.trim();
  const pass    =document.getElementById('password').value;
  const conf    =document.getElementById('confirm').value;

  if(!name||!email||!user_id||!pass||!conf){{showAlert('Please fill in all fields.');return;}}
  if(pass.length<6){{showAlert('Password must be at least 6 characters.');return;}}
  if(pass!==conf){{showAlert('Passwords do not match.');return;}}
  if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)){{showAlert('Invalid email format.');return;}}

  fetch('/api/register',{{method:'POST',headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify({{name,email,role,user_id,password:pass}})}})
  .then(r=>r.json()).then(d=>{{
    if(d.success){{showAlert('Registration successful! Redirecting...','success');setTimeout(()=>location.href='/login',1500);}}
    else showAlert(d.error||'Registration failed.');
  }});
}}
</script>
""", "Register")


@auth_bp.route("/verify")
def verify_page():
    email = request.args.get("email", "")
    vtype = request.args.get("type", "login")
    return render(f"""
<div class="auth-bg">
  <div class="auth-card">
    <div class="auth-logo">
      <div class="logo-icon">{LOGO}</div>
      <h1>Verify Your Email</h1>
      <p>We sent a 6-digit code to <strong>{email}</strong></p>
    </div>
    <div class="alert-zone"></div>
    <div class="form-group">
      <label class="form-label">Verification Code</label>
      <input type="text" id="code" class="form-input" placeholder="Enter 6-digit code" maxlength="6" style="font-size:24px;letter-spacing:8px;text-align:center">
    </div>
    <button class="btn btn-primary w-full" onclick="doVerify()" style="justify-content:center">Verify & Continue</button>
    <button class="btn btn-secondary w-full mt-8" onclick="resendCode()" style="justify-content:center">Resend Code</button>
    <p class="text-center text-sm text-muted mt-16"><a href="/login" style="color:var(--red)">← Back to Login</a></p>
  </div>
</div>
<script>
const EMAIL="{email}",VTYPE="{vtype}";
function doVerify(){{
  const code=document.getElementById('code').value.trim();
  if(code.length!==6){{showAlert('Enter the 6-digit code.');return;}}
  fetch('/api/verify',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{email:EMAIL,code,type:VTYPE}})}})
  .then(r=>r.json()).then(d=>{{
    if(d.success){{showAlert('Email verified successfully!','success');setTimeout(()=>location.href=d.redirect||'/',1200);}}
    else showAlert(d.error||'Verification failed.');
  }});
}}
function resendCode(){{
  fetch('/api/resend-code',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{email:EMAIL,type:VTYPE}})}})
  .then(r=>r.json()).then(d=>{{
    if(d.success)showAlert('New code sent to your email.','info');
    else showAlert(d.error||'Failed to resend.');
  }});
}}
document.getElementById('code').addEventListener('keydown',e=>e.key==='Enter'&&doVerify());
</script>
""", "Verify")


@auth_bp.route("/forgot-password")
def forgot_page():
    step    = request.args.get("step", "1")
    user_id = request.args.get("user_id", "")

    if step == "1":
        return render(f"""
<div class="auth-bg">
  <div class="auth-card">
    <div class="auth-logo">
      <div class="logo-icon">{LOGO}</div>
      <h1>Forgot Password</h1>
      <p>Enter your Student ID or Teacher ID</p>
    </div>
    <div class="alert-zone"></div>
    <div class="form-group">
      <label class="form-label">ID Number</label>
      <input type="text" id="identifier" class="form-input" placeholder="Enter your Student ID or Teacher ID">
    </div>
    <button class="btn btn-primary w-full" onclick="sendReset()" style="justify-content:center">Verify ID</button>
    <p class="text-center text-sm text-muted mt-16"><a href="/login" style="color:var(--red)">← Back to Login</a></p>
  </div>
</div>
<script>
function sendReset(){{
  const identifier=document.getElementById('identifier').value.trim();
  if(!identifier){{showAlert('Please enter your ID number.');return;}}
  fetch('/api/forgot-password',{{method:'POST',headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify({{identifier}})}})
  .then(r=>r.json()).then(d=>{{
    if(d.success) location.href='/forgot-password?step=2&user_id='+encodeURIComponent(d.user_id);
    else showAlert(d.error||'ID not found.');
  }});
}}
</script>
""", "Forgot Password")

    # step == "2"
    return render(f"""
<div class="auth-bg">
  <div class="auth-card">
    <div class="auth-logo">
      <div class="logo-icon">{LOGO}</div>
      <h1>Reset Password</h1>
      <p>Enter your new password</p>
    </div>
    <div class="alert-zone"></div>
    <div class="form-group">
      <label class="form-label">New Password</label>
      <input type="password" id="newpass" class="form-input" placeholder="Min. 6 characters">
    </div>
    <div class="form-group">
      <label class="form-label">Confirm New Password</label>
      <input type="password" id="confirm" class="form-input" placeholder="Repeat new password">
    </div>
    <button class="btn btn-primary w-full" onclick="doReset()" style="justify-content:center">Reset Password</button>
    <p class="text-center text-sm text-muted mt-16"><a href="/login" style="color:var(--red)">← Back to Login</a></p>
  </div>
</div>
<script>
const UID="{user_id}";
function doReset(){{
  const newpass=document.getElementById('newpass').value;
  const confirm=document.getElementById('confirm').value;
  if(!newpass||!confirm){{showAlert('Fill in all fields.');return;}}
  if(newpass.length<6){{showAlert('Password must be at least 6 characters.');return;}}
  if(newpass!==confirm){{showAlert('Passwords do not match.');return;}}
  fetch('/api/reset-password',{{method:'POST',headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify({{user_id:UID,new_password:newpass}})}})
  .then(r=>r.json()).then(d=>{{
    if(d.success){{showAlert('Password reset successfully!','success');setTimeout(()=>location.href='/login',1500);}}
    else showAlert(d.error||'Reset failed.');
  }});
}}
</script>
""", "Reset Password")


# ─────────────────────────────────────────────
#  API ROUTES
# ─────────────────────────────────────────────

@auth_bp.route("/api/register", methods=["POST"])
def api_register():
    data     = request.json
    name     = (data.get("name",    "")).strip()
    email    = (data.get("email",   "")).strip().lower()
    password = data.get("password", "")
    role     = data.get("role",     "student")
    user_id  = (data.get("user_id", "")).strip()

    if not all([name, email, password, user_id]):
        return jsonify({"error": "All fields are required."})
    if role not in ["student", "teacher"]:
        return jsonify({"error": "Invalid role."})

    db = get_db()
    try:
        if db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone():
            return jsonify({"error": "Email already exists."})
        if db.execute("SELECT id FROM users WHERE user_id=?", (user_id,)).fetchone():
            return jsonify({"error": "That ID number is already taken."})

        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        db.execute(
            "INSERT INTO users (name, email, password, role, user_id) VALUES (?,?,?,?,?)",
            (name, email, hashed, role, user_id)
        )
        db.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": f"Registration error: {str(e)}"})
    finally:
        db.close()


@auth_bp.route("/api/login", methods=["POST"])
def api_login():
    data     = request.json
    email    = (data.get("email", "")).strip().lower()
    password = data.get("password", "")

    db = get_db()
    try:
        user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if not user:
            return jsonify({"error": "No account found with this email."})
        if not bcrypt.checkpw(password.encode(), user["password"].encode()):
            return jsonify({"error": "Incorrect password."})

        if user["role"] == "admin":
            session["user_id"] = user["id"]
            session["role"]    = "admin"
            session["name"]    = user["name"]
            return jsonify({"success": True, "redirect": "/admin"})

        code = generate_code()
        store_code(db, user["id"], email, code, "login")
        sent = send_email(
            email,
            "ExamSys Login Verification",
            email_template(
                "Login Verification Code", code,
                "Use this code to complete your login. It expires in 10 minutes.",
            ),
        )
        if not sent:
            print(f"[DEV] Verification code for {email}: {code}")

        session["pending_user_id"] = user["id"]
        session["pending_role"]    = user["role"]
        session["pending_name"]    = user["name"]
        return jsonify({"success": True, "redirect": f"/verify?email={email}&type=login"})
    except Exception as e:
        return jsonify({"error": f"Login error: {str(e)}"})
    finally:
        db.close()


@auth_bp.route("/api/verify", methods=["POST"])
def api_verify():
    data  = request.json
    email = data.get("email", "").strip().lower()
    code  = data.get("code",  "").strip()
    vtype = data.get("type",  "login")

    db = get_db()
    try:
        rec = db.execute(
            "SELECT * FROM verification_codes WHERE email=? AND type=? ORDER BY id DESC LIMIT 1",
            (email, vtype),
        ).fetchone()
        if not rec:
            return jsonify({"error": "No verification code found. Please request a new one."})
        if rec["attempts"] >= 5:
            return jsonify({"error": "Too many attempts. Please request a new code."})

        db.execute("UPDATE verification_codes SET attempts=attempts+1 WHERE id=?", (rec["id"],))
        db.commit()

        expires = datetime.strptime(rec["expires_at"], "%Y-%m-%d %H:%M:%S")
        if datetime.now() > expires:
            return jsonify({"error": "Code has expired. Please request a new one."})
        if rec["code"] != code:
            return jsonify({"error": "Invalid code. Please try again."})

        db.execute("DELETE FROM verification_codes WHERE id=?", (rec["id"],))
        db.commit()

        if vtype == "login":
            uid  = session.get("pending_user_id")
            role = session.get("pending_role")
            name = session.get("pending_name")
            if not uid:
                return jsonify({"error": "Session expired. Please login again."})
            session.clear()
            session["user_id"] = uid
            session["role"]    = role
            session["name"]    = name
            redirect_map = {"admin": "/admin", "teacher": "/teacher", "student": "/student"}
            return jsonify({"success": True, "redirect": redirect_map.get(role, "/")})

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": f"Verification error: {str(e)}"})
    finally:
        db.close()


@auth_bp.route("/api/resend-code", methods=["POST"])
def api_resend():
    data  = request.json
    email = data.get("email", "").strip().lower()
    vtype = data.get("type",  "login")

    db = get_db()
    try:
        user = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
        if not user:
            return jsonify({"error": "Email not found."})
        code  = generate_code()
        store_code(db, user["id"], email, code, vtype)
        title = "Login Verification Code" if vtype == "login" else "Password Reset Code"
        msg   = ("Use this code to complete your login."
                 if vtype == "login"
                 else "Use this code to reset your password.")
        send_email(email, f"ExamSys {title}", email_template(title, code, msg))
        print(f"[DEV] Resent code for {email}: {code}")
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"})
    finally:
        db.close()


@auth_bp.route("/api/forgot-password", methods=["POST"])
def api_forgot():
    data       = request.json
    identifier = (data.get("identifier", "")).strip()

    if not identifier:
        return jsonify({"error": "Please enter your ID number."})

    db = get_db()
    try:
        user = db.execute(
            "SELECT id, user_id FROM users WHERE user_id=? AND role!='admin'",
            (identifier,)
        ).fetchone()

        if not user:
            return jsonify({"error": "No account found with that ID number."})

        return jsonify({"success": True, "user_id": user["user_id"]})
    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"})
    finally:
        db.close()


@auth_bp.route("/api/reset-password", methods=["POST"])
def api_reset():
    data         = request.json
    user_id      = (data.get("user_id",     "")).strip()
    new_password = data.get("new_password", "")

    if not user_id:
        return jsonify({"error": "Invalid request."})
    if len(new_password) < 6:
        return jsonify({"error": "Password must be at least 6 characters."})

    db = get_db()
    try:
        user = db.execute(
            "SELECT id FROM users WHERE user_id=?", (user_id,)
        ).fetchone()

        if not user:
            return jsonify({"error": "Account not found."})

        hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        db.execute("UPDATE users SET password=? WHERE user_id=?", (hashed, user_id))
        db.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"})
    finally:
        db.close()


@auth_bp.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
>>>>>>> e2dc1e8a74b897af2d3a59c50788a81339e5c41f
    return jsonify({"success": True})