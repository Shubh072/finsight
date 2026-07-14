import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(exist_ok=True)
DEFAULT_DB_PATH = INSTANCE_DIR / "finsight.db"

# Supabase Configuration
# ==========================
SUPABASE_URL = os.getenv("VITE_SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("VITE_SUPABASE_ANON_KEY", "")

# Database Configuration
# ==========================
# Use SQLite for easier development (no separate database server required)
SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or f"sqlite:///{DEFAULT_DB_PATH}"
SQLALCHEMY_TRACK_MODIFICATIONS = False

# ==========================
# Security
# ==========================
SECRET_KEY = os.getenv("SECRET_KEY", "finsight-dev-secret-key-change-in-production")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "finsight-jwt-secret-key-change-in-production")

# ==========================
# Email Configuration
# ==========================
MAIL_SERVER = os.getenv("MAIL_SERVER")
MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True") == "True"
MAIL_USE_SSL = False
MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")

# ==========================
# Application
# ==========================
APP_NAME = "FinSight"
APP_URL = os.getenv("APP_URL", "http://localhost:5000")

RESET_TOKEN_EXPIRY_MINUTES = 15
EMAIL_VERIFICATION_EXPIRY_MINUTES = 30

# ==========================
# Upload Configuration
# ==========================
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB
UPLOAD_FOLDER = "uploads"

# ==========================
# SQLAlchemy (kept for compatibility, but we use Supabase REST API)
# ==========================
SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///finsight_local.db")
SQLALCHEMY_TRACK_MODIFICATIONS = False
