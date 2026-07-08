from database.db import db
from sqlalchemy.sql import func

class User(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)

    full_name = db.Column(db.String(150), nullable=False)

    username = db.Column(db.String(50), unique=True, nullable=False)

    email = db.Column(db.String(150), unique=True, nullable=False)

    phone = db.Column(db.String(20), unique=True)

    password_hash = db.Column(db.String(255), nullable=False)

    profile_photo = db.Column(db.String(500))

    role = db.Column(
        db.Enum("user", "admin", "support"),
        default="user",
        nullable=False
    )

    account_status = db.Column(
        db.Enum("active", "inactive", "suspended", "deleted"),
        default="active",
        nullable=False
    )

    email_verified = db.Column(db.Boolean, default=False)

    failed_login_attempts = db.Column(db.Integer, default=0)

    last_login = db.Column(db.DateTime)

    created_at = db.Column(
        db.DateTime,
        server_default=func.now()
    )

    updated_at = db.Column(
        db.DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )