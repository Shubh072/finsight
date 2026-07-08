from models.user import User
from database.db import db
from extensions import bcrypt
from flask_jwt_extended import create_access_token
from datetime import datetime

from utils.validators import (
    validate_email,
    validate_password,
    validate_phone,
)

from utils.token import (
    generate_verification_token,
    verify_verification_token,
)

from utils.password_token import (
    generate_reset_token,
    verify_reset_token,
)

from utils.email_service import (
    send_verification_email,
    send_reset_email
)


def get_me(claims):
    # Backwards compatible helper; routes currently call this via get_me_service.
    # Kept minimal for Phase 1 auth.
    return {"success": False, "message": "Not implemented."}, 501


def register_user(data):
    """
    Register a new user.
    """

    # ----------------------------------
    # Read Request Data
    # ----------------------------------
    full_name = data.get("full_name", "").strip()
    username = data.get("username", "").strip()
    email = data.get("email", "").strip().lower()
    phone = data.get("phone", "").strip()
    password = data.get("password", "")
    confirm_password = data.get("confirm_password", "")

    # ----------------------------------
    # Required Fields Validation
    # ----------------------------------
    if not all([
        full_name,
        username,
        email,
        phone,
        password,
        confirm_password
    ]):
        return {
            "success": False,
            "message": "All fields are required."
        }, 400

    # ----------------------------------
    # Validate Email
    # ----------------------------------
    if not validate_email(email):
        return {
            "success": False,
            "message": "Invalid email address."
        }, 400

    # ----------------------------------
    # Validate Phone
    # ----------------------------------
    if not validate_phone(phone):
        return {
            "success": False,
            "message": "Phone number must contain exactly 10 digits."
        }, 400

    # ----------------------------------
    # Validate Password
    # ----------------------------------
    if not validate_password(password):
        return {
            "success": False,
            "message": (
                "Password must contain at least "
                "8 characters, one uppercase letter, "
                "one lowercase letter, one number "
                "and one special character."
            )
        }, 400

    # ----------------------------------
    # Confirm Password
    # ----------------------------------
    if password != confirm_password:
        return {
            "success": False,
            "message": "Passwords do not match."
        }, 400

    # ----------------------------------
    # Check Duplicate Email
    # ----------------------------------
    existing_email = User.query.filter_by(email=email).first()

    if existing_email:
        return {
            "success": False,
            "message": "Email already exists."
        }, 409

    # ----------------------------------
    # Check Duplicate Username
    # ----------------------------------
    existing_username = User.query.filter_by(username=username).first()

    if existing_username:
        return {
            "success": False,
            "message": "Username already exists."
        }, 409

    # ----------------------------------
    # Check Duplicate Phone
    # ----------------------------------
    existing_phone = User.query.filter_by(phone=phone).first()

    if existing_phone:
        return {
            "success": False,
            "message": "Phone number already exists."
        }, 409

    # ----------------------------------
    # Hash Password
    # ----------------------------------
    password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    # ----------------------------------
    # Create User Object
    # ----------------------------------
    new_user = User(
        full_name=full_name,
        username=username,
        email=email,
        phone=phone,
        password_hash=password_hash,
        role="user",
        account_status="active",
        email_verified=False,
        failed_login_attempts=0,
    )

    # ----------------------------------
    # Save User
    # ----------------------------------
    try:

        db.session.add(new_user)
        db.session.commit()

        # Generate verification token
        token = generate_verification_token(email)

        # Send verification email
        send_verification_email(email, token)

        return {
            "success": True,
            "message": "Registration successful. Please verify your email."
        }, 201

    except Exception as e:

        db.session.rollback()

        return {
            "success": False,
            "message": "Registration failed.",
            "error": str(e)
        }, 500

def verify_email(token):

    email = verify_verification_token(token)

    if not email:
        return {
            "success": False,
            "message": "Invalid or expired verification link."
        }, 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return {
            "success": False,
            "message": "User not found."
        }, 404

    if user.email_verified:
        return {
            "success": True,
            "message": "Email already verified."
        }, 200

    user.email_verified = True

    db.session.commit()

    return {
        "success": True,
        "message": "Email verified successfully."
    }, 200


def login_user(data):

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return {
            "success": False,
            "message": "Email and password are required."
        }, 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return {
            "success": False,
            "message": "Invalid email or password."
        }, 401

    # Check account status
    if user.account_status != "active":
        return {
            "success": False,
            "message": "Your account is inactive. Please contact support."
        }, 403

    # Check email verification
    if not user.email_verified:
        return {
            "success": False,
            "message": "Please verify your email before logging in."
        }, 403

    if not bcrypt.check_password_hash(user.password_hash, password):
        return {
            "success": False,
            "message": "Invalid email or password."
        }, 401

    access_token = create_access_token(
        identity=user.user_id,
        additional_claims={
            "email": user.email,
            "role": user.role
        }
    )

    user.last_login = datetime.utcnow()
    db.session.commit()

    return {
        "success": True,
        "message": "Login successful.",
        "access_token": access_token,
        "user": {
            "user_id": user.user_id,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role
        }
    }, 200

def forgot_password(data):
    email = data.get("email", "").strip().lower()
    
    if not email:
        return {
            "success": False,
            "message": "Email is required."
        }, 400
        
    user = User.query.filter_by(email=email).first()
    
    if user:
        token = generate_reset_token(email)
        send_reset_email(email, token)
        
    return {
        "success": True,
        "message": "If an account exists, a password reset link has been sent."
    }, 200


def reset_password(token, data):
    password = data.get("password", "")
    confirm_password = data.get("confirm_password", "")
    
    if not password or not confirm_password:
        return {
            "success": False,
            "message": "Password fields are required."
        }, 400
        
    if password != confirm_password:
        return {
            "success": False,
            "message": "Passwords do not match."
        }, 400
        
    if not validate_password(password):
        return {
            "success": False,
            "message": (
                "Password must contain at least "
                "8 characters, one uppercase letter, "
                "one lowercase letter, one number "
                "and one special character."
            )
        }, 400
        
    email = verify_reset_token(token)
    
    if not email:
        return {
            "success": False,
            "message": "Invalid or expired reset link."
        }, 400
        
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return {
            "success": False,
            "message": "User not found."
        }, 404
        
    user.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
    db.session.commit()
    
    return {
        "success": True,
        "message": "Password reset successfully."
    }, 200