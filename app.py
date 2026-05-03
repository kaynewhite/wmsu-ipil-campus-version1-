from dotenv import load_dotenv
import os

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

# Initialize the database on startup for all environments (including gunicorn/Render).
init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() in ("1", "true", "yes")

    print("\n" + "=" * 55)
    print("  ExamSys · Online Examination System")
    print("=" * 55)
    print(f"  URL:   http://127.0.0.1:{port}")
    print("  Admin: admin@admin.com / admin123")
    print("=" * 55)
    print("  NOTE: Check console for email verification")
    print("        codes if SMTP is not configured.")
    print("=" * 55 + "\n")
    app.run(debug=debug, host="0.0.0.0", port=port)
