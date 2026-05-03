"""
========================================================
  ONLINE EXAMINATION SYSTEM - Modular Flask App
  Tech: Python Flask, SQLite, bcrypt, SMTP (Gmail)
========================================================

SETUP INSTRUCTIONS:
1. Install dependencies:
   pip install flask bcrypt

2. Configure Gmail SMTP in config.py (use App Password):
   - Google Account > Security > 2-Step Verification > App Passwords

3. Run:
   python app.py

4. Visit: http://localhost:5000
   Admin login: admin@admin.com / admin123
"""


from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from config import SECRET_KEY
from database import init_db
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.teacher import teacher_bp
from routes.student import student_bp

app = Flask(__name__, static_folder='static')


 
app.secret_key = SECRET_KEY

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(teacher_bp)
app.register_blueprint(student_bp)

if __name__ == "__main__":
    init_db()
    print("\n" + "=" * 55)
    print("  ExamSys · Online Examination System")
    print("=" * 55)
    print("  URL:   http://localhost:5000")
    print("  Admin: admin@admin.com / admin123")
    print("=" * 55)
    print("  NOTE: Check console for email verification")
    print("        codes if SMTP is not configured.")
    print("=" * 55 + "\n")
    app.run(debug=True, port=5000)