import os
from dotenv import load_dotenv

load_dotenv()

# ==========================
# Database Configuration
# ==========================
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "finsight_db"),
    "port": int(os.getenv("DB_PORT", 3306)),
}

SQLALCHEMY_DATABASE_URI = (
    f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
    f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
)

SQLALCHEMY_TRACK_MODIFICATIONS = False

# ==========================
# Security
# ==========================
SECRET_KEY = os.getenv("SECRET_KEY")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

# ==========================
# Email Configuration
# ==========================
# ==========================
# Email
# ==========================

MAIL_SERVER = os.getenv("MAIL_SERVER")
MAIL_PORT = int(os.getenv("MAIL_PORT", 587))

MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True") == "True"
MAIL_USE_SSL = False

MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")

MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")# ==========================
# Application
# ==========================
APP_NAME = "FinSight"
APP_URL = os.getenv("APP_URL", "http://localhost:5000")

RESET_TOKEN_EXPIRY_MINUTES = 15
EMAIL_VERIFICATION_EXPIRY_MINUTES = 30