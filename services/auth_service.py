from extensions import bcrypt
from flask_jwt_extended import create_access_token
from datetime import datetime
import json

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
from utils import supabase_client as sb


def get_me(claims):
    return {"success": False, "message": "Not implemented."}, 501


def register_user(data):
    full_name = data.get("full_name", "").strip()
    username = data.get("username", "").strip()
    email = data.get("email", "").strip().lower()
    phone = data.get("phone", "").strip()
    password = data.get("password", "").strip()
    confirm_password = data.get("confirm_password", "").strip()

    if not all([full_name, username, email, phone, password, confirm_password]):
        return {"success": False, "message": "All fields are required."}, 400

    if not validate_email(email):
        return {"success": False, "message": "Invalid email address."}, 400

    if not validate_phone(phone):
<<<<<<< HEAD
        return {"success": False, "message": "Phone number must contain exactly 10 digits."}, 400
=======
        return {
            "success": False,
            "message": "Phone number must contain at least 8 digits."
        }, 400
>>>>>>> 3b492c6 (Apply local auth and UI updates)

    if not validate_password(password):
        return {
            "success": False,
<<<<<<< HEAD
            "message": "Password must contain at least 8 characters, one uppercase letter, one lowercase letter, one number and one special character."
=======
            "message": (
                "Password must contain at least "
                "8 characters, one uppercase letter, "
                "one lowercase letter, and one number."
            )
>>>>>>> 3b492c6 (Apply local auth and UI updates)
        }, 400

    if password != confirm_password:
        return {"success": False, "message": "Passwords do not match."}, 400

    # Check duplicates via Supabase
    try:
        existing_email = sb.select("users", filters={"email": email}, limit=1)
        if existing_email:
            return {"success": False, "message": "Email already exists."}, 409

        existing_username = sb.select("users", filters={"username": username}, limit=1)
        if existing_username:
            return {"success": False, "message": "Username already exists."}, 409

        existing_phone = sb.select("users", filters={"phone": phone}, limit=1)
        if existing_phone:
            return {"success": False, "message": "Phone number already exists."}, 409
    except Exception as e:
        return {"success": False, "message": "Registration check failed.", "error": str(e)}, 500

    password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

<<<<<<< HEAD
=======
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
        email_verified=True,  # Auto-verify for easier testing
        failed_login_attempts=0,
    )

    # ----------------------------------
    # Save User
    # ----------------------------------
>>>>>>> 3b492c6 (Apply local auth and UI updates)
    try:
        sb.insert("users", {
            "full_name": full_name,
            "username": username,
            "email": email,
            "phone": phone,
            "password_hash": password_hash,
            "role": "user",
            "account_status": "active",
            "email_verified": False,
            "failed_login_attempts": 0,
        })

<<<<<<< HEAD
        token = generate_verification_token(email)
        try:
            send_verification_email(email, token)
        except Exception:
            pass

        return {"success": True, "message": "Registration successful. Please verify your email."}, 201
=======
        db.session.add(new_user)
        db.session.commit()

        # Try to send verification email, but don't fail registration if it fails
        try:
            token = generate_verification_token(email)
            send_verification_email(email, token)
        except Exception as e:
            print(f"Warning: Could not send verification email: {e}")
            # Continue with registration even if email fails

        # Auto-login the user after registration
        access_token = create_access_token(
            identity=new_user.user_id,
            additional_claims={
                "email": new_user.email,
                "role": new_user.role
            }
        )

        return {
            "success": True,
            "message": "Registration successful!",
            "access_token": access_token,
            "user": {
                "user_id": new_user.user_id,
                "full_name": new_user.full_name,
                "email": new_user.email,
                "role": new_user.role
            }
        }, 201

>>>>>>> 3b492c6 (Apply local auth and UI updates)
    except Exception as e:
        return {"success": False, "message": "Registration failed.", "error": str(e)}, 500

<<<<<<< HEAD
=======
        db.session.rollback()
        import traceback
        traceback.print_exc()

        return {
            "success": False,
            "message": "Registration failed.",
            "error": str(e)
        }, 500
>>>>>>> 3b492c6 (Apply local auth and UI updates)

def verify_email(token):
    email = verify_verification_token(token)
    if not email:
        return {"success": False, "message": "Invalid or expired verification link."}, 400

    try:
        user = sb.select("users", filters={"email": email}, single=True)
    except Exception:
        user = None

    if not user:
        return {"success": False, "message": "User not found."}, 404

    if user.get("email_verified"):
        return {"success": True, "message": "Email already verified."}, 200

    try:
        sb.update("users", {"email": email}, {"email_verified": True})
    except Exception as e:
        return {"success": False, "message": "Verification failed.", "error": str(e)}, 500

    return {"success": True, "message": "Email verified successfully."}, 200


def login_user(data):
    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()

    if not email or not password:
        return {"success": False, "message": "Email and password are required."}, 400

    try:
        user = sb.select("users", filters={"email": email}, single=True)
    except Exception:
        user = None

    if not user:
        return {"success": False, "message": "Invalid email or password."}, 401

    if user.get("account_status") != "active":
        return {"success": False, "message": "Your account is inactive. Please contact support."}, 403

<<<<<<< HEAD
    if not user.get("email_verified"):
        return {"success": False, "message": "Please verify your email before logging in."}, 403
=======
    # Allow login without email verification for testing
    if not user.email_verified:
        print("Warning: User logging in without verified email.")
>>>>>>> 3b492c6 (Apply local auth and UI updates)

    if not bcrypt.check_password_hash(user.get("password_hash", ""), password):
        return {"success": False, "message": "Invalid email or password."}, 401

    access_token = create_access_token(
        identity=str(user.get("user_id")),
        additional_claims={
            "email": user.get("email"),
            "role": user.get("role"),
        }
    )

    try:
        sb.update("users", {"email": email}, {"last_login": datetime.utcnow().isoformat()})
    except Exception:
        pass

    return {
        "success": True,
        "message": "Login successful.",
        "access_token": access_token,
        "user": {
            "user_id": user.get("user_id"),
            "full_name": user.get("full_name"),
            "email": user.get("email"),
            "role": user.get("role"),
        }
    }, 200


def forgot_password(data):
    email = data.get("email", "").strip().lower()

    if not email:
        return {"success": False, "message": "Email is required."}, 400

    try:
        user = sb.select("users", filters={"email": email}, single=True)
    except Exception:
        user = None

    if user:
<<<<<<< HEAD
        token = generate_reset_token(email)
        try:
            send_reset_email(email, token)
        except Exception:
            pass

    return {"success": True, "message": "If an account exists, a password reset link has been sent."}, 200


def reset_password(token, data):
    password = data.get("password", "")
    confirm_password = data.get("confirm_password", "")

=======
        try:
            token = generate_reset_token(email)
            send_reset_email(email, token)
        except Exception as e:
            print(f"Warning: Could not send reset email: {e}")
        
    return {
        "success": True,
        "message": "If an account exists, a password reset link has been sent."
    }, 200


def reset_password(token, data):
    password = data.get("password", "").strip()
    confirm_password = data.get("confirm_password", "").strip()
    
>>>>>>> 3b492c6 (Apply local auth and UI updates)
    if not password or not confirm_password:
        return {"success": False, "message": "Password fields are required."}, 400

    if password != confirm_password:
        return {"success": False, "message": "Passwords do not match."}, 400

    if not validate_password(password):
        return {
            "success": False,
<<<<<<< HEAD
            "message": "Password must contain at least 8 characters, one uppercase letter, one lowercase letter, one number and one special character."
=======
            "message": (
                "Password must contain at least "
                "8 characters, one uppercase letter, "
                "one lowercase letter, and one number."
            )
>>>>>>> 3b492c6 (Apply local auth and UI updates)
        }, 400

    email = verify_reset_token(token)
    if not email:
        return {"success": False, "message": "Invalid or expired reset link."}, 400

    try:
        user = sb.select("users", filters={"email": email}, single=True)
    except Exception:
        user = None

    if not user:
        return {"success": False, "message": "User not found."}, 404

    password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    try:
        sb.update("users", {"email": email}, {"password_hash": password_hash})
    except Exception as e:
        return {"success": False, "message": "Password reset failed.", "error": str(e)}, 500

    return {"success": True, "message": "Password reset successfully."}, 200
