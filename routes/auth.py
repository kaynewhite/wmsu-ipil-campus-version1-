from flask import Blueprint, request, session, redirect, url_for, jsonify
from datetime import datetime
import bcrypt

from database import get_db
from email_utils import send_email, email_template, generate_code, store_code
from helpers import render, login_required

auth_bp = Blueprint("auth", __name__)

LOGO = '<img src="/static/images/wmsu_logo.png" alt="WMSU" style="width:100%;height:100%;object-fit:contain">'

# ─────────────────────────────────────────────
# INDEX
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
# PAGE ROUTES
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
    return render(rf"""
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
    if(d.success){{showAlert('Verification email sent. Check your inbox.','success');setTimeout(()=>location.href=d.redirect||'/verify?email='+encodeURIComponent(email)+'&type=register',1500);}}
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


@auth_bp.route("/profile")
@login_required
def profile_page():
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
    db.close()
    return render(f"""
<div class="auth-bg">
  <div class="auth-card" style="max-width:520px">
    <div class="auth-logo">
      <div class="logo-icon">{LOGO}</div>
      <h1>My Profile</h1>
      <p>Update your profile details securely.</p>
    </div>
    <div class="alert-zone"></div>
    <div class="form-group">
      <label class="form-label">Full Name</label>
      <input id="name" class="form-input" value="{user['name']}" placeholder="Your full name">
    </div>
    <div class="form-group">
      <label class="form-label">Email Address</label>
      <input id="email" class="form-input" type="email" value="{user['email']}" placeholder="you@example.com" readonly>
    </div>
    <div class="form-group">
      <label class="form-label">Student / Teacher ID</label>
      <input id="user_id" class="form-input" value="{user['user_id'] or ''}" placeholder="ID number">
    </div>
    <div class="form-group">
      <label class="form-label">Current Password</label>
      <input id="current_password" class="form-input" type="password" placeholder="Enter current password">
    </div>
    <div class="form-group">
      <label class="form-label">New Password</label>
      <input id="new_password" class="form-input" type="password" placeholder="Leave blank to keep current password">
    </div>
    <div class="form-group">
      <label class="form-label">Confirm New Password</label>
      <input id="confirm_password" class="form-input" type="password" placeholder="Repeat new password">
    </div>
    <button class="btn btn-primary w-full" onclick="saveProfile()" style="justify-content:center">Save Changes</button>
    <p class="text-center text-sm text-muted mt-16"><a href="/" style="color:var(--red)">← Back to dashboard</a></p>
  </div>
</div>
<script>
function saveProfile(){{
  const name=document.getElementById('name').value.trim();
  const user_id=document.getElementById('user_id').value.trim();
  const current_password=document.getElementById('current_password').value;
  const new_password=document.getElementById('new_password').value;
  const confirm_password=document.getElementById('confirm_password').value;

  if(!name||!user_id||!current_password){{ showAlert('Please fill in your current password and required fields.'); return; }}
  if(new_password && new_password.length < 6){{ showAlert('New password must be at least 6 characters.'); return; }}
  if(new_password && new_password !== confirm_password){{ showAlert('New passwords do not match.'); return; }}

  fetch('/api/profile', {{
    method:'POST',
    headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify({{name,user_id,current_password,new_password,confirm_password}})
  }}).then(r=>r.json()).then(d=>{{
    if(d.success){{ showAlert(d.message,'success'); }}
    else showAlert(d.error||'Profile update failed.');
  }});
}}
</script>
""", "Profile")


# ─────────────────────────────────────────────
# API ROUTES
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
        code = generate_code()
        store_code(db, None, email, code, "register",
                   pending_name=name,
                   pending_role=role,
                   pending_password=hashed,
                   pending_user_id=user_id)
        send_email(
            email,
            "ExamSys Registration Verification",
            email_template(
                "Verify Your Email Address", code,
                "Enter this code below to complete your account registration.",
            ),
        )
        return jsonify({"success": True, "redirect": f"/verify?email={email}&type=register"})
    except Exception as e:
        return jsonify({"error": f"Registration error: {str(e)}"})
    finally:
        db.close()


@auth_bp.route("/api/profile", methods=["POST"])
@login_required
def api_profile():
    data = request.json
    name = (data.get("name", "") or "").strip()
    user_id = (data.get("user_id", "") or "").strip()
    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")
    confirm_password = data.get("confirm_password", "")

    if not all([name, user_id, current_password]):
        return jsonify({"error": "All required fields are required."})
    if new_password and new_password != confirm_password:
        return jsonify({"error": "New passwords do not match."})

    db = get_db()
    try:
        user = db.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
        if not user:
            return jsonify({"error": "User not found."})
        if not bcrypt.checkpw(current_password.encode(), user["password"].encode()):
            return jsonify({"error": "Current password is incorrect."})
        if user_id != user["user_id"] and db.execute("SELECT id FROM users WHERE user_id=?", (user_id,)).fetchone():
            return jsonify({"error": "That ID is already in use."})

        query = "UPDATE users SET name=?, user_id=?"
        params = [name, user_id]
        if new_password:
            hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
            query += ", password=?"
            params.append(hashed)
        query += " WHERE id=?"
        params.append(session["user_id"])

        db.execute(query, tuple(params))
        db.commit()
        session["name"] = name
        return jsonify({"success": True, "message": "Profile updated successfully."})
    except Exception as e:
        return jsonify({"error": str(e)})
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
        if not user["is_verified"]:
            return jsonify({"error": "Your account is not verified yet. Please complete the signup verification email."})

        session["user_id"] = user["id"]
        session["role"]    = user["role"]
        session["name"]    = user["name"]

        if user["role"] == "admin":
            return jsonify({"success": True, "redirect": "/admin"})
        return jsonify({"success": True, "redirect": f"/{user['role']}"})
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
            return jsonify({"error": "No verification code found."})
        
        expires = datetime.strptime(rec["expires_at"], "%Y-%m-%d %H:%M:%S")
        if datetime.now() > expires:
            return jsonify({"error": "Code has expired."})
        if rec["code"] != code:
            return jsonify({"error": "Invalid code."})

        db.execute("DELETE FROM verification_codes WHERE id=?", (rec["id"],))
        db.commit()

        if vtype == "register":
            existing = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
            if existing:
                return jsonify({"error": "This email is already registered."})

            db.execute(
                "INSERT INTO users (name, email, password, role, user_id, is_verified) VALUES (?,?,?,?,?,1)",
                (rec["pending_name"], email, rec["pending_password"], rec["pending_role"], rec["pending_user_id"]),
            )
            db.commit()
            user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
            session["user_id"] = user["id"]
            session["role"]    = user["role"]
            session["name"]    = user["name"]
            redirect_map = {"admin": "/admin", "teacher": "/teacher", "student": "/student"}
            return jsonify({"success": True, "redirect": redirect_map.get(user["role"], "/")})

        return jsonify({"error": "Verification type not supported."})
    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        db.close()

@auth_bp.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"success": True})
