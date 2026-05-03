import random
import string
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta

from config import EMAIL_ENABLED, MAIL_USERNAME, MAIL_PASSWORD, MAIL_FROM_NAME

def send_email(to_email: str, subject: str, body: str) -> bool:
    """Send an HTML email via Gmail SMTP. Returns True on success."""
    if not EMAIL_ENABLED:
        print(f"[EMAIL DISABLED] Would have sent to {to_email}: {subject}")
        return False

    try:
        msg = MIMEText(body, "html")
        msg["Subject"] = subject
        msg["From"]    = f"{MAIL_FROM_NAME} <{MAIL_USERNAME}>"
        msg["To"]      = to_email

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(MAIL_USERNAME, MAIL_PASSWORD)
        server.sendmail(MAIL_USERNAME, to_email, msg.as_string())
        server.quit()

        print("[EMAIL SENT SUCCESSFULLY]")
        return True

    except Exception as e:
        print("[EMAIL ERROR]", str(e))
        return False

def email_template(title: str, code: str, message: str) -> str:
    """Return a branded HTML email body."""
    return f"""
    <div style="font-family:'Segoe UI',sans-serif;max-width:480px;margin:auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.1)">
      <div style="background:#c0392b;padding:28px 32px">
        <h1 style="color:#fff;margin:0;font-size:22px;letter-spacing:1px">ExamSys</h1>
      </div>
      <div style="padding:32px">
        <h2 style="color:#1a1a2e;margin:0 0 8px">{title}</h2>
        <p style="color:#555;margin:0 0 24px">{message}</p>
        <div style="background:#f5f5f5;border-radius:8px;padding:20px;text-align:center">
          <span style="font-size:38px;font-weight:700;letter-spacing:10px;color:#c0392b">{code}</span>
        </div>
        <p style="color:#888;font-size:13px;margin:20px 0 0">
          This code expires in <strong>10 minutes</strong>. Do not share it with anyone.
        </p>
      </div>
      <div style="background:#f9f9f9;padding:16px 32px;text-align:center">
        <p style="color:#bbb;font-size:12px;margin:0">© 2025 ExamSys · Online Examination System</p>
      </div>
    </div>"""

def generate_code() -> str:
    """Return a random 6-digit numeric code."""
    return "".join(random.choices(string.digits, k=6))

def store_code(db, user_id, email: str, code: str, code_type: str,
               pending_name: str = None, pending_role: str = None,
               pending_password: str = None, pending_user_id: str = None):
    """Persist a fresh verification code (replaces any existing one of the same type)."""
    expires = (datetime.now() + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
    db.execute(
        "DELETE FROM verification_codes WHERE email=? AND type=?",
        (email, code_type),
    )
    db.execute(
        "INSERT INTO verification_codes (user_id, email, code, type, expires_at, pending_name, pending_role, pending_password, pending_user_id) VALUES (?,?,?,?,?,?,?,?,?)",
        (user_id, email, code, code_type, expires, pending_name, pending_role, pending_password, pending_user_id),
    )
    db.commit()
