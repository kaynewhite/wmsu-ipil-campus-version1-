import os

# ─────────────────────────────────────────────
#  CONFIGURATION
# ─────────────────────────────────────────────
MAIL_USERNAME  = os.getenv("MAIL_USERNAME", "rheasusonhidalgo@gmail.com")
MAIL_PASSWORD  = os.getenv("MAIL_PASSWORD", "kdfi uhto wplg bhqy")
MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME", "ExamSys")
SECRET_KEY     = os.getenv("SECRET_KEY", "changeme_super_secret_key_2025")
DB_PATH        = os.getenv("DB_PATH", "examdb.sqlite")
EMAIL_ENABLED  = os.getenv("EMAIL_ENABLED", "true").lower() == "true"
